//! Experimental Btrfs stream CAS. Immutable verified objects; no published
//! manifest until EOF and the producer reports successful completion.
//! Does NOT mutate Snapper metadata, mounts or existing Harbor backups.
use anyhow::{Context, Result, anyhow, ensure};
use fastcdc::v2020::StreamCDC;
use fs2::FileExt;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
#[cfg(unix)]
use std::os::unix::fs::OpenOptionsExt;
use std::path::{Path, PathBuf};
use uuid::Uuid;

const MIN_CHUNK: usize = 1024 * 1024;
const AVG_CHUNK: usize = 4 * 1024 * 1024;
const MAX_CHUNK: usize = 16 * 1024 * 1024;
const MAX_MANIFEST: u64 = 64 * 1024 * 1024;
const MAX_OBJECTS: usize = 250_000;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
struct Entry {
    hash: String,
    raw_size: usize,
    zstd_sha256: String,
    zstd_size: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Manifest {
    format: u32,
    repository: Uuid,
    name: String,
    raw_sha256: String,
    raw_size: u64,
    objects: Vec<Entry>,
}

#[derive(Debug, PartialEq, Eq)]
pub struct IngestStats {
    pub new_objects: usize,
    pub reused_objects: usize,
    pub raw_sha256: String,
}

pub struct Repository {
    root: PathBuf,
    id: Uuid,
}

fn hex_digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

fn valid_hash(hash: &str) -> bool {
    hash.len() == 64
        && hash
            .bytes()
            .all(|c| c.is_ascii_hexdigit() && !c.is_ascii_uppercase())
}
fn safe_name(name: &str) -> bool {
    !name.is_empty()
        && name.len() <= 160
        && name
            .bytes()
            .all(|c| c.is_ascii_alphanumeric() || b"_.-".contains(&c))
        && name != "."
        && name != ".."
        && !name.starts_with('.')
}
fn open_regular(path: &Path) -> Result<File> {
    ensure!(!path.is_symlink(), "refusing symlink: {}", path.display());
    let file = File::open(path)?;
    ensure!(file.metadata()?.is_file(), "not regular file");
    Ok(file)
}
fn sync_directory(directory: &Path) -> Result<()> {
    File::open(directory)?
        .sync_all()
        .context("fsync repository directory")
}
fn write_unique(directory: &Path, name: &str, content: &[u8]) -> Result<bool> {
    ensure!(
        directory.is_dir() && !directory.is_symlink(),
        "object directory unavailable"
    );
    let dest = directory.join(name);
    ensure!(!dest.is_symlink(), "refusing symlink object");
    let tmp = directory.join(format!(".harbor-temp-{}", Uuid::new_v4()));
    let result = (|| -> Result<bool> {
        let mut tmpfile = OpenOptions::new()
            .write(true)
            .create_new(true)
            .mode(0o600)
            .open(&tmp)?;
        tmpfile.write_all(content)?;
        tmpfile.sync_all()?;
        match fs::hard_link(&tmp, &dest) {
            Ok(()) => {
                sync_directory(directory)?;
                Ok(true)
            }
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => Ok(false),
            Err(error) => Err(error).context("atomic no-clobber hardlink publication"),
        }
    })();
    let _ = fs::remove_file(&tmp);
    result
}

impl Repository {
    pub fn initialize(root: &Path) -> Result<Self> {
        ensure!(
            root.is_dir() && !root.is_symlink(),
            "root must be an existing directory"
        );
        let marker = root.join(".harbor-repo-id");
        if marker.exists() || marker.is_symlink() {
            return Self::open(root);
        }
        let id = Uuid::new_v4();
        if !write_unique(root, ".harbor-repo-id", id.to_string().as_bytes())? {
            return Self::open(root);
        }
        let repo = Self {
            root: root.to_path_buf(),
            id,
        };
        repo.ensure_directories()?;
        Ok(repo)
    }
    pub fn open(root: &Path) -> Result<Self> {
        ensure!(
            root.is_dir() && !root.is_symlink(),
            "repository root unavailable"
        );
        let marker = root.join(".harbor-repo-id");
        let mut id_string = String::new();
        open_regular(&marker)?
            .take(80)
            .read_to_string(&mut id_string)?;
        let id = Uuid::parse_str(id_string.trim()).context("invalid repository marker")?;
        let repo = Self {
            root: root.to_path_buf(),
            id,
        };
        repo.ensure_directories()?;
        Ok(repo)
    }
    pub fn id(&self) -> Uuid {
        self.id
    }
    fn guard(&self) -> Result<()> {
        ensure!(
            self.root.is_dir() && !self.root.is_symlink(),
            "repository root inaccessible"
        );
        let marker = self.root.join(".harbor-repo-id");
        let mut id_string = String::new();
        open_regular(&marker)?
            .take(80)
            .read_to_string(&mut id_string)?;
        ensure!(
            Uuid::parse_str(id_string.trim())? == self.id,
            "repository identity changed"
        );
        self.ensure_directories()
    }
    fn ensure_directories(&self) -> Result<()> {
        for name in ["objects", "manifests"] {
            let path = self.root.join(name);
            if !path.exists() {
                fs::create_dir(&path)?;
            }
            ensure!(
                path.is_dir() && !path.is_symlink(),
                "unsafe repository subdirectory"
            );
        }
        Ok(())
    }
    fn object_path(&self, hash: &str) -> Result<PathBuf> {
        ensure!(valid_hash(hash), "invalid object digest");
        let prefix = self.root.join("objects").join(&hash[..2]);
        if !prefix.exists() {
            fs::create_dir(&prefix)?;
        }
        ensure!(
            prefix.is_dir() && !prefix.is_symlink(),
            "unsafe object directory"
        );
        Ok(prefix.join(format!("{hash}.zst")))
    }
    fn manifest_path(&self, name: &str) -> Result<PathBuf> {
        ensure!(safe_name(name), "invalid archive name");
        Ok(self.root.join("manifests").join(format!("{name}.json")))
    }
    pub fn manifest_exists(&self, name: &str) -> bool {
        self.manifest_path(name).is_ok_and(|p| p.exists())
    }
    fn load_manifest(&self, name: &str) -> Result<Manifest> {
        self.guard()?;
        let manifest_path = self.manifest_path(name)?;
        let f = open_regular(&manifest_path)?;
        ensure!(f.metadata()?.len() <= MAX_MANIFEST, "oversized manifest");
        let manifest: Manifest = serde_json::from_reader(f)?;
        ensure!(
            manifest.format == 1 && manifest.repository == self.id && manifest.name == name,
            "manifest identity mismatch"
        );
        ensure!(valid_hash(&manifest.raw_sha256), "invalid raw digest");
        ensure!(manifest.objects.len() <= MAX_OBJECTS, "too many objects");
        let mut raw_length = 0u64;
        for obj in &manifest.objects {
            ensure!(
                valid_hash(&obj.hash) && valid_hash(&obj.zstd_sha256),
                "invalid object metadata"
            );
            ensure!(
                (1..=MAX_CHUNK).contains(&obj.raw_size),
                "invalid object raw length"
            );
            ensure!(
                (1..=MAX_CHUNK * 2).contains(&obj.zstd_size),
                "invalid compressed length"
            );
            raw_length = raw_length
                .checked_add(obj.raw_size as u64)
                .ok_or_else(|| anyhow!("raw length overflow"))?;
        }
        ensure!(raw_length == manifest.raw_size, "manifest length mismatch");
        Ok(manifest)
    }
    fn read_object(&self, entry: &Entry) -> Result<Vec<u8>> {
        self.guard()?;
        let path = self.object_path(&entry.hash)?;
        let f = open_regular(&path)?;
        ensure!(
            f.metadata()?.len() == entry.zstd_size as u64,
            "compressed object size mismatch"
        );
        let mut compressed = Vec::new();
        f.take((MAX_CHUNK * 2 + 1) as u64)
            .read_to_end(&mut compressed)?;
        ensure!(
            compressed.len() == entry.zstd_size,
            "truncated compressed object"
        );
        ensure!(
            hex_digest(&compressed) == entry.zstd_sha256,
            "compressed SHA-256 mismatch"
        );
        let raw = zstd::bulk::decompress(&compressed, entry.raw_size)
            .context("cannot decompress object")?;
        ensure!(raw.len() == entry.raw_size, "decompressed length mismatch");
        ensure!(
            blake3::hash(&raw).to_hex().as_str() == entry.hash,
            "raw object BLAKE3 mismatch"
        );
        Ok(raw)
    }
    fn lock(&self) -> Result<File> {
        self.guard()?;
        let lock_path = self.root.join(".harbor-repo.lock");
        ensure!(!lock_path.is_symlink(), "unsafe lock path");
        let fd = OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .open(lock_path)?;
        fd.lock_exclusive()?;
        Ok(fd)
    }
    pub fn ingest<R: Read, F: FnOnce() -> bool>(
        &self,
        name: &str,
        stream: R,
        eof_success: F,
    ) -> Result<IngestStats> {
        let manifest_path = self.manifest_path(name)?;
        let _lock = self.lock()?;
        let mut raw_digest = Sha256::new();
        let mut raw_size = 0u64;
        let mut entries = Vec::new();
        let mut new_objects = 0usize;
        let mut reused_objects = 0usize;
        let cdc = StreamCDC::new(stream, MIN_CHUNK, AVG_CHUNK, MAX_CHUNK);
        for chunk in cdc {
            let chunk = chunk.context("source stream read failed")?;
            ensure!(!chunk.data.is_empty(), "empty data chunk");
            ensure!(
                entries.len() < MAX_OBJECTS,
                "source exceeds maximum object index"
            );
            raw_digest.update(&chunk.data);
            raw_size = raw_size
                .checked_add(chunk.data.len() as u64)
                .ok_or_else(|| anyhow!("raw size overflow"))?;
            let hash = blake3::hash(&chunk.data).to_hex().to_string();
            let packed = zstd::bulk::compress(&chunk.data, 3)?;
            let entry = Entry {
                hash: hash.clone(),
                raw_size: chunk.data.len(),
                zstd_sha256: hex_digest(&packed),
                zstd_size: packed.len(),
            };
            self.guard()?;
            let path = self.object_path(&hash)?;
            let directory = path.parent().context("object has no parent")?;
            if write_unique(
                directory,
                path.file_name().unwrap().to_str().unwrap(),
                &packed,
            )? {
                new_objects += 1;
            } else {
                self.read_object(&entry)
                    .context("existing content-addressed object differs")?;
                reused_objects += 1;
            }
            entries.push(entry);
        }
        ensure!(
            eof_success(),
            "producer did not confirm successful EOF; no manifest published"
        );
        self.guard()?;
        let hexsha = format!("{:x}", raw_digest.finalize());
        let manifest = Manifest {
            format: 1,
            repository: self.id,
            name: name.to_string(),
            raw_sha256: hexsha.clone(),
            raw_size,
            objects: entries,
        };
        let data = serde_json::to_vec(&manifest)?;
        ensure!((data.len() as u64) <= MAX_MANIFEST, "manifest too large");
        if manifest_path.exists() || manifest_path.is_symlink() {
            let previous = self.load_manifest(name)?;
            ensure!(
                previous.raw_sha256 == manifest.raw_sha256
                    && previous.raw_size == manifest.raw_size
                    && previous.objects == manifest.objects,
                "existing manifest differs; will not overwrite archive"
            );
        } else {
            let created = write_unique(
                manifest_path.parent().unwrap(),
                manifest_path.file_name().unwrap().to_str().unwrap(),
                &data,
            )?;
            if !created {
                let previous = self.load_manifest(name)?;
                ensure!(
                    previous.raw_sha256 == manifest.raw_sha256
                        && previous.objects == manifest.objects,
                    "existing manifest differs"
                );
            }
        }
        Ok(IngestStats {
            new_objects,
            reused_objects,
            raw_sha256: hexsha,
        })
    }
    pub fn verify(&self, name: &str) -> Result<u64> {
        let manifest = self.load_manifest(name)?;
        let mut digest = Sha256::new();
        let mut len = 0u64;
        for entry in &manifest.objects {
            let chunk = self.read_object(entry)?;
            len += chunk.len() as u64;
            digest.update(&chunk);
        }
        ensure!(
            len == manifest.raw_size && format!("{:x}", digest.finalize()) == manifest.raw_sha256,
            "full stream checksum mismatch"
        );
        Ok(len)
    }
    pub fn recover_into<W: Write>(&self, name: &str, output: &mut W) -> Result<u64> {
        // Full integrity pass first. On corruption, refuse to write any output.
        let expected = self.verify(name)?;
        let manifest = self.load_manifest(name)?;
        for entry in &manifest.objects {
            output.write_all(&self.read_object(entry)?)?;
        }
        Ok(expected)
    }
}
