//! Experimental Btrfs stream CAS. Immutable verified objects; no published
//! manifest until EOF and the producer reports successful completion.
//! Does NOT mutate Snapper metadata, mounts or existing Harbor backups.
use anyhow::{Context, Result, anyhow, ensure};
use fastcdc::v2020::StreamCDC;
use fs2::FileExt;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet, HashSet};
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

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SnapshotIdentity {
    pub source_uuid: Uuid,
    pub parent_uuid: Option<Uuid>,
    pub parent_archive: Option<String>,
    pub protocol: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Manifest {
    format: u32,
    repository: Uuid,
    name: String,
    raw_sha256: String,
    raw_size: u64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    identity: Option<SnapshotIdentity>,
    objects: Vec<Entry>,
}

#[derive(Debug, PartialEq, Eq)]
pub struct IngestStats {
    pub new_objects: usize,
    pub reused_objects: usize,
    pub raw_sha256: String,
}

#[derive(Debug, Serialize)]
pub struct ArchiveInfo {
    pub name: String,
    pub raw_size: u64,
    pub source_uuid: Option<Uuid>,
    pub parent_archive: Option<String>,
}

/// Exact preview of an explicit deletion; no mutation until the complete
/// plan digest is confirmed. A plan is bound to both repository ID and state.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GcPlan {
    pub repository: Uuid,
    pub remove_archives: Vec<String>,
    pub retain_archives: Vec<String>,
    pub orphan_objects: usize,
    pub reclaim_bytes: u64,
    pub plan_sha256: String,
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
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW)
        .open(path)?;
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

fn checked_real_directory(path: &Path) -> Result<()> {
    // Preserve the underlying OS error (including transient network errno),
    // rather than treating EHOSTDOWN as a permanent "not a directory".
    let metadata = fs::symlink_metadata(path)?;
    ensure!(
        metadata.file_type().is_dir(),
        "repository component must be a real directory"
    );
    Ok(())
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
        checked_real_directory(root).context("repository root unavailable")?;
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
        repo.check_directories()?;
        Ok(repo)
    }
    pub fn id(&self) -> Uuid {
        self.id
    }
    fn guard(&self) -> Result<()> {
        checked_real_directory(&self.root).context("repository root inaccessible")?;
        let marker = self.root.join(".harbor-repo-id");
        let mut id_string = String::new();
        open_regular(&marker)?
            .take(80)
            .read_to_string(&mut id_string)?;
        ensure!(
            Uuid::parse_str(id_string.trim())? == self.id,
            "repository identity changed"
        );
        self.check_directories()
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
    fn check_directories(&self) -> Result<()> {
        for name in ["objects", "manifests"] {
            let path = self.root.join(name);
            checked_real_directory(&path)
                .with_context(|| format!("missing or unsafe repository directory: {name}"))?;
        }
        Ok(())
    }

    fn object_path(&self, hash: &str, create: bool) -> Result<PathBuf> {
        ensure!(valid_hash(hash), "invalid object digest");
        let prefix = self.root.join("objects").join(&hash[..2]);
        if !prefix.exists() && create {
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
        let path = self.object_path(&entry.hash, false)?;
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
    fn inspect_existing_object(&self, hash: &str, raw_size: usize) -> Result<Entry> {
        self.guard()?;
        let path = self.object_path(hash, false)?;
        let fd = open_regular(&path)?;
        ensure!(
            fd.metadata()?.len() <= (MAX_CHUNK * 2) as u64,
            "existing compressed chunk exceeds safety limit"
        );
        let mut stored = Vec::new();
        fd.take((MAX_CHUNK * 2 + 1) as u64)
            .read_to_end(&mut stored)?;
        ensure!(!stored.is_empty(), "existing compressed chunk is empty");
        let raw = zstd::bulk::decompress(&stored, raw_size)
            .context("existing compressed chunk cannot be decompressed")?;
        ensure!(
            raw.len() == raw_size && blake3::hash(&raw).to_hex().as_str() == hash,
            "existing compressed chunk raw BLAKE3 mismatch"
        );
        Ok(Entry {
            hash: hash.to_string(),
            raw_size,
            zstd_sha256: hex_digest(&stored),
            zstd_size: stored.len(),
        })
    }

    /// Repository-side read lease, held for the *entire* restoration.
    /// Future destructive GC must acquire the same file's exclusive lock.
    /// This guarantees exclusion on filesystems that correctly implement
    /// flock(); remote NFS/SMB semantics require independent qualification.
    pub fn read_lease(&self) -> Result<File> {
        self.guard()?;
        let path = self.root.join(".harbor-repo.lock");
        ensure!(!path.is_symlink(), "unsafe repository lock path");
        let fd = OpenOptions::new()
            .create(true)
            .truncate(false)
            .read(true)
            .write(true)
            .mode(0o600)
            .custom_flags(libc::O_NOFOLLOW)
            .open(path)?;
        FileExt::lock_shared(&fd)?;
        self.guard()?;
        Ok(fd)
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
            .custom_flags(libc::O_NOFOLLOW)
            .open(lock_path)?;
        fd.lock_exclusive()?;
        Ok(fd)
    }
    /// A bounded, read-only list of committed CAS archives.
    pub fn list_archives(&self) -> Result<Vec<ArchiveInfo>> {
        self.guard()?;
        let mut results = Vec::new();
        for entry in fs::read_dir(self.root.join("manifests"))?.take(10_000) {
            let entry = entry?;
            let name = entry.file_name().to_string_lossy().to_string();
            if !name.ends_with(".json") {
                continue;
            }
            let stem = name.trim_end_matches(".json");
            if !safe_name(stem) {
                continue;
            }
            // Invalid/corrupt archives cannot masquerade as verified entries.
            let manifest = self.load_manifest(stem)?;
            results.push(ArchiveInfo {
                name: stem.to_string(),
                raw_size: manifest.raw_size,
                source_uuid: manifest
                    .identity
                    .as_ref()
                    .map(|identity| identity.source_uuid),
                parent_archive: manifest
                    .identity
                    .and_then(|identity| identity.parent_archive),
            });
        }
        results.sort_by(|a, b| a.name.cmp(&b.name));
        Ok(results)
    }

    // Enumerate *all* manifests, with no silent truncation. Fail closed on
    // unsupported entries: a future format may have undiscovered references.
    fn all_manifests(&self) -> Result<BTreeMap<String, Manifest>> {
        self.guard()?;
        let mut found = BTreeMap::new();
        for entry in fs::read_dir(self.root.join("manifests"))? {
            let entry = entry?;
            let name = entry
                .file_name()
                .into_string()
                .map_err(|_| anyhow!("non-UTF8 manifest name"))?;
            ensure!(
                name.ends_with(".json"),
                "unexpected file in manifests: {name}"
            );
            let archive = name.strip_suffix(".json").unwrap();
            ensure!(safe_name(archive), "unsafe manifest filename");
            ensure!(
                found.len() < 10_000,
                "manifest inventory exceeds safety cap"
            );
            let manifest = self.load_manifest(archive)?;
            found.insert(archive.to_string(), manifest);
        }
        Ok(found)
    }

    /// Inventory object paths without trusting the prefix/extension alone.
    /// Unpublished chunks from interrupted ingests are swept on explicit GC.
    fn all_objects(&self) -> Result<BTreeMap<String, (PathBuf, u64)>> {
        self.guard()?;
        let mut found = BTreeMap::new();
        for prefix in fs::read_dir(self.root.join("objects"))? {
            let prefix = prefix?;
            let label = prefix
                .file_name()
                .into_string()
                .map_err(|_| anyhow!("non-UTF8 object prefix"))?;
            ensure!(
                label.len() == 2
                    && label
                        .bytes()
                        .all(|c| c.is_ascii_hexdigit() && !c.is_ascii_uppercase()),
                "unexpected object prefix"
            );
            checked_real_directory(&prefix.path())?;
            for entry in fs::read_dir(prefix.path())? {
                let entry = entry?;
                let filename = entry
                    .file_name()
                    .into_string()
                    .map_err(|_| anyhow!("non-UTF8 object filename"))?;
                let hash = filename
                    .strip_suffix(".zst")
                    .ok_or_else(|| anyhow!("unexpected object filename"))?;
                ensure!(
                    valid_hash(hash) && hash.starts_with(&label),
                    "malformed object filename or prefix"
                );
                let md = fs::symlink_metadata(entry.path())?;
                ensure!(md.file_type().is_file(), "non-regular object entry");
                ensure!(
                    found.len() < 2_000_000,
                    "object inventory exceeds safety cap"
                );
                found.insert(hash.to_string(), (entry.path(), md.len()));
            }
        }
        Ok(found)
    }

    fn gc_plan_locked(&self, requested: &[String]) -> Result<GcPlan> {
        ensure!(requested.len() <= 10_000, "too many explicit archive names");
        let selected: BTreeSet<String> = requested.iter().cloned().collect();
        ensure!(
            requested.len() == selected.len(),
            "duplicate archive selection"
        );
        for name in &selected {
            ensure!(safe_name(name), "invalid archive selection");
        }
        let manifests = self.all_manifests()?;
        for name in &selected {
            ensure!(manifests.contains_key(name), "unknown archive: {name}");
        }

        let mut retained_hashes = BTreeSet::new();
        let mut sha = Sha256::new();
        sha.update(b"Harbor CAS GC plan v1\0");
        sha.update(self.id.as_bytes());
        // Bind confirm token to every manifest's content, including archives
        // not slated for deletion. This prevents stale-plan confirmation.
        for (name, manifest) in &manifests {
            let mut original = Vec::new();
            open_regular(&self.manifest_path(name)?)?
                .take(MAX_MANIFEST + 1)
                .read_to_end(&mut original)?;
            ensure!(
                original.len() as u64 <= MAX_MANIFEST,
                "oversized manifest during GC"
            );
            sha.update((name.len() as u64).to_le_bytes());
            sha.update(name.as_bytes());
            sha.update((original.len() as u64).to_le_bytes());
            sha.update(Sha256::digest(&original));
            if !selected.contains(name) {
                // The complete retained incremental dependency graph must be
                // present, acyclic and UUID-consistent before deleting anything.
                // This also protects against preexisting malformed graph roots.
                let mut node = name.as_str();
                let mut visited = BTreeSet::new();
                while let Some(identity) = manifests
                    .get(node)
                    .and_then(|manifest| manifest.identity.as_ref())
                {
                    ensure!(visited.insert(node), "cyclic retained parent graph");
                    ensure!(visited.len() <= 128, "retained parent depth exceeded");
                    ensure!(
                        identity.protocol == 2,
                        "unsupported retained Btrfs protocol"
                    );
                    match (&identity.parent_uuid, &identity.parent_archive) {
                        (None, None) => break,
                        (Some(parent_uuid), Some(parent)) => {
                            ensure!(
                                !selected.contains(parent),
                                "retained archive {name} still needs parent {parent}"
                            );
                            let ancestor = manifests.get(parent).ok_or_else(|| {
                                anyhow!("retained archive {name} has missing parent {parent}")
                            })?;
                            ensure!(
                                ancestor
                                    .identity
                                    .as_ref()
                                    .is_some_and(|i| i.source_uuid == *parent_uuid),
                                "retained archive {name} parent UUID mismatch"
                            );
                            node = parent;
                        }
                        _ => return Err(anyhow!("incomplete retained parent link")),
                    }
                }
                for part in &manifest.objects {
                    retained_hashes.insert(part.hash.clone());
                }
                // No existing retained backup may depend on a missing or
                // damaged stream, even if the selected archive is removable.
                self.verify(name)?;
            }
        }
        for name in &selected {
            sha.update(name.as_bytes());
            sha.update([0u8]);
        }
        let objects = self.all_objects()?;
        let mut orphans = 0usize;
        let mut reclaim_bytes = 0u64;
        for (hash, (_, size)) in &objects {
            sha.update(hash.as_bytes());
            sha.update(size.to_le_bytes());
            if !retained_hashes.contains(hash) {
                orphans += 1;
                reclaim_bytes = reclaim_bytes
                    .checked_add(*size)
                    .ok_or_else(|| anyhow!("reclaim size overflow"))?;
            }
        }
        for hash in retained_hashes {
            ensure!(
                objects.contains_key(&hash),
                "retained object missing: {hash}"
            );
        }
        Ok(GcPlan {
            repository: self.id,
            remove_archives: selected.into_iter().collect(),
            retain_archives: manifests
                .keys()
                .filter(|n| !requested.contains(n))
                .cloned()
                .collect(),
            orphan_objects: orphans,
            reclaim_bytes,
            plan_sha256: hex_digest(&sha.finalize()),
        })
    }

    /// Build dry-run under the exclusive repository lock, including immutable
    /// manifest graph, bytewise verification of all remaining archives, and
    /// a conservative object inventory. No file is removed.
    pub fn gc_preview(&self, names: &[String]) -> Result<GcPlan> {
        let _lock = self.lock()?;
        self.gc_plan_locked(names)
    }

    /// The *same* exclusive lock is held from plan validation to fsync after
    /// manifest deletion and orphan sweep. Manifest-first deletions make
    /// crashes leave reclaimable orphans, never retained streams without data.
    pub fn gc_confirm(&self, names: &[String], expected_digest: &str) -> Result<GcPlan> {
        ensure!(valid_hash(expected_digest), "invalid plan token");
        let _lock = self.lock()?;
        let plan = self.gc_plan_locked(names)?;
        ensure!(
            plan.plan_sha256 == expected_digest,
            "repository changed since preview; re-run dry-run"
        );
        let manifest_dir = self.root.join("manifests");
        for name in &plan.remove_archives {
            self.guard()?;
            fs::remove_file(self.manifest_path(name)?)?;
            sync_directory(&manifest_dir)?;
        }
        // Recalculate after manifest deletion: if an error/crash interrupted
        // removal, a later explicit empty-selection sweep can reclaim orphans.
        let current = self.all_manifests()?;
        let referenced: BTreeSet<_> = current
            .values()
            .flat_map(|m| m.objects.iter().map(|e| e.hash.clone()))
            .collect();
        let objects = self.all_objects()?;
        for (hash, (path, _)) in objects {
            if !referenced.contains(&hash) {
                self.guard()?;
                fs::remove_file(&path)?;
                sync_directory(path.parent().context("missing object parent")?)?;
            }
        }
        Ok(plan)
    }

    pub fn snapshot_identity(&self, name: &str) -> Result<Option<SnapshotIdentity>> {
        Ok(self.load_manifest(name)?.identity)
    }

    fn validate_snapshot_identity(&self, name: &str, identity: &SnapshotIdentity) -> Result<()> {
        ensure!(identity.protocol == 2, "unsupported Btrfs send protocol");
        ensure!(!identity.source_uuid.is_nil(), "missing source UUID");
        match (identity.parent_uuid, identity.parent_archive.as_deref()) {
            (None, None) => Ok(()),
            (Some(parent_uuid), Some(parent_name)) => {
                ensure!(parent_uuid != identity.source_uuid, "self-parent snapshot");
                ensure!(parent_name != name, "self-parent archive");
                let parent = self.load_manifest(parent_name)?;
                ensure!(
                    parent
                        .identity
                        .as_ref()
                        .is_some_and(|i| i.source_uuid == parent_uuid),
                    "incremental parent is not a verified archived snapshot"
                );
                Ok(())
            }
            _ => Err(anyhow!(
                "incremental parent UUID and parent archive must both be specified"
            )),
        }
    }

    pub fn ingest<R: Read, F: FnOnce() -> bool>(
        &self,
        name: &str,
        stream: R,
        eof_success: F,
    ) -> Result<IngestStats> {
        self.ingest_inner(name, stream, eof_success, None, &mut |_: u64| {})
    }

    pub fn ingest_snapshot<R: Read, F: FnOnce() -> bool>(
        &self,
        name: &str,
        stream: R,
        eof_success: F,
        identity: SnapshotIdentity,
    ) -> Result<IngestStats> {
        self.ingest_inner(name, stream, eof_success, Some(identity), &mut |_: u64| {})
    }

    /// Report bytes already read from the Btrfs send stream (not destination
    /// bytes and not a forecast of final compressed size).
    pub fn ingest_snapshot_with_progress<R: Read, F: FnOnce() -> bool, P: FnMut(u64)>(
        &self,
        name: &str,
        stream: R,
        eof_success: F,
        identity: SnapshotIdentity,
        mut progress: P,
    ) -> Result<IngestStats> {
        self.ingest_inner(name, stream, eof_success, Some(identity), &mut progress)
    }

    fn ingest_inner<R: Read, F: FnOnce() -> bool>(
        &self,
        name: &str,
        stream: R,
        eof_success: F,
        identity: Option<SnapshotIdentity>,
        progress: &mut dyn FnMut(u64),
    ) -> Result<IngestStats> {
        let manifest_path = self.manifest_path(name)?;
        let _lock = self.lock()?;
        if let Some(ref identity) = identity {
            self.validate_snapshot_identity(name, identity)?;
        }
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
            // Level 1 is the throughput-oriented default. Existing chunks are
            // accepted by their *decoded* BLAKE3 rather than zstd bytes;
            // zstd versions/levels may encode identical data differently.
            let packed = zstd::bulk::compress(&chunk.data, 1)?;
            let mut entry = Entry {
                hash: hash.clone(),
                raw_size: chunk.data.len(),
                zstd_sha256: hex_digest(&packed),
                zstd_size: packed.len(),
            };
            self.guard()?;
            let path = self.object_path(&hash, true)?;
            let directory = path.parent().context("object has no parent")?;
            if write_unique(
                directory,
                path.file_name().unwrap().to_str().unwrap(),
                &packed,
            )? {
                new_objects += 1;
            } else {
                entry = self
                    .inspect_existing_object(&hash, chunk.data.len())
                    .context("existing content-addressed object differs or is corrupt")?;
                reused_objects += 1;
            }
            entries.push(entry);
            progress(raw_size);
        }
        ensure!(
            eof_success(),
            "producer did not confirm successful EOF; no manifest published"
        );
        self.guard()?;
        let hexsha = format!("{:x}", raw_digest.finalize());
        // The receiver can acknowledge a completed write and subsequently
        // expose different bytes after a real NFS/SMB interruption. Re-read
        // ALL committed objects and the ordered stream from the repository
        // before publishing an immutable manifest. The readback is a
        // deliberate integrity-over-throughput tradeoff for this release.
        let mut readback_sha256 = Sha256::new();
        for entry in &entries {
            readback_sha256.update(
                self.read_object(entry)
                    .context("remote object readback failed; archive not committed")?,
            );
        }
        ensure!(
            format!("{:x}", readback_sha256.finalize()) == hexsha,
            "remote readback stream SHA-256 mismatch; archive not committed"
        );
        self.guard()?;
        let manifest = Manifest {
            format: 1,
            repository: self.id,
            name: name.to_string(),
            raw_sha256: hexsha.clone(),
            raw_size,
            identity,
            objects: entries,
        };
        let data = serde_json::to_vec(&manifest)?;
        ensure!((data.len() as u64) <= MAX_MANIFEST, "manifest too large");
        if manifest_path.exists() || manifest_path.is_symlink() {
            let previous = self.load_manifest(name)?;
            ensure!(
                previous.raw_sha256 == manifest.raw_sha256
                    && previous.raw_size == manifest.raw_size
                    && previous.objects == manifest.objects
                    && previous.identity == manifest.identity,
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
                        && previous.objects == manifest.objects
                        && previous.identity == manifest.identity,
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
    /// Return the fully verified chain, from original full send to target.
    pub fn verified_restore_chain(&self, name: &str) -> Result<Vec<String>> {
        let mut seen = HashSet::new();
        let mut chain = Vec::new();
        let mut current = name.to_owned();
        let mut expected_uuid: Option<Uuid> = None;
        loop {
            ensure!(seen.insert(current.clone()), "cyclic incremental chain");
            ensure!(seen.len() <= 128, "incremental chain depth exceeded");
            let manifest = self.load_manifest(&current)?;
            let identity = manifest
                .identity
                .ok_or_else(|| anyhow!("missing Btrfs snapshot provenance"))?;
            ensure!(identity.protocol == 2, "unsupported Btrfs stream protocol");
            if let Some(expected) = expected_uuid {
                ensure!(
                    identity.source_uuid == expected,
                    "incremental parent UUID mismatch"
                );
            }
            self.verify(&current)?;
            chain.push(current.clone());
            match (identity.parent_uuid, identity.parent_archive) {
                (None, None) => break,
                (Some(uuid), Some(parent)) => {
                    expected_uuid = Some(uuid);
                    current = parent;
                }
                _ => return Err(anyhow!("incomplete parent chain")),
            }
        }
        chain.reverse();
        Ok(chain)
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
