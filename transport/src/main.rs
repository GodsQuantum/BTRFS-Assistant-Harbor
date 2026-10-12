use anyhow::{Context, Result, bail, ensure};
use clap::{Parser, Subcommand};
use harbor_transport::cas::Repository;
use serde_json::json;
use std::fs::{File, OpenOptions};
use std::io;
use std::os::unix::fs::OpenOptionsExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;

const BTRFS_BINARY: &str = "/usr/bin/btrfs";

#[derive(Parser)]
#[command(
    name = "harbor-transport",
    about = "Experimental Btrfs Assistant resilient send transport"
)]
struct Cli {
    #[command(subcommand)]
    action: Action,
}

#[derive(Subcommand)]
enum Action {
    Init {
        #[arg(long)]
        repo: PathBuf,
        #[arg(long)]
        allow_local: bool,
    },
    /// Synthetic lab data only; does NOT validate a Btrfs source.
    IngestFile {
        #[arg(long)]
        repo: PathBuf,
        #[arg(long)]
        name: String,
        #[arg(long)]
        file: PathBuf,
        #[arg(long)]
        experimental: bool,
        #[arg(long)]
        allow_local: bool,
    },
    /// Send exactly one immutable Btrfs snapshot, optionally from a matching parent.
    Send {
        #[arg(long)]
        repo: PathBuf,
        #[arg(long)]
        name: String,
        #[arg(long)]
        snapshot: PathBuf,
        #[arg(long)]
        parent: Option<PathBuf>,
        #[arg(long, default_value_t = 5)]
        retries: u32,
        #[arg(long)]
        experimental: bool,
        #[arg(long)]
        allow_local: bool,
    },
    Verify {
        #[arg(long)]
        repo: PathBuf,
        #[arg(long)]
        name: String,
    },
    /// Reconstruct raw Btrfs-send bytes to a NEW file, without modifying system subvolumes.
    RecoverFile {
        #[arg(long)]
        repo: PathBuf,
        #[arg(long)]
        name: String,
        #[arg(long)]
        output: PathBuf,
    },
}

fn gate_target(root: &Path, allow_local: bool) -> Result<()> {
    ensure!(
        root.is_absolute() && !root.is_symlink() && root.is_dir(),
        "repository root must be an existing absolute real directory"
    );
    if allow_local {
        return Ok(());
    }
    let output = Command::new("/usr/bin/findmnt")
        .arg("-n")
        .arg("-T")
        .arg(root)
        .args(["-o", "FSTYPE"])
        .output()
        .context("cannot validate destination mount type")?;
    ensure!(
        output.status.success(),
        "destination mount identity unavailable"
    );
    let kind = String::from_utf8(output.stdout)?.trim().to_lowercase();
    ensure!(
        matches!(kind.as_str(), "nfs" | "nfs4" | "cifs" | "fuse.sshfs"),
        "not a supported mounted network filesystem; explicitly allow local only if intentional"
    );
    Ok(())
}

fn readonly_btrfs_uuid(path: &Path) -> Result<String> {
    ensure!(
        path.is_absolute() && path.is_dir() && !path.is_symlink(),
        "source must be an existing absolute non-symlink Btrfs snapshot"
    );
    let property = Command::new(BTRFS_BINARY)
        .args(["property", "get", "-ts"])
        .arg(path)
        .arg("ro")
        .output()
        .context("btrfs property get failed")?;
    ensure!(
        property.status.success(),
        "failed inspecting Btrfs readonly property"
    );
    ensure!(
        String::from_utf8(property.stdout)?
            .lines()
            .any(|line| line.trim() == "ro=true"),
        "snapshot must be immutable (Btrfs readonly=true)"
    );
    let info = Command::new(BTRFS_BINARY)
        .args(["subvolume", "show"])
        .arg(path)
        .output()
        .context("btrfs subvolume show failed")?;
    ensure!(info.status.success(), "source is not a Btrfs subvolume");
    let output = String::from_utf8(info.stdout)?;
    let uuid = output
        .lines()
        .filter_map(|line| line.trim().strip_prefix("UUID:").map(str::trim))
        .next()
        .unwrap_or("");
    ensure!(
        !uuid.is_empty() && uuid != "-",
        "Btrfs snapshot UUID not available"
    );
    Ok(uuid.to_string())
}

fn transient_io(error: &anyhow::Error) -> bool {
    error.chain().any(|cause| {
        cause
            .downcast_ref::<io::Error>()
            .is_some_and(|e| matches!(e.raw_os_error(), Some(110 | 104 | 107 | 113 | 116 | 112)))
    })
}

fn run_send(
    repo_root: &Path,
    name: &str,
    snapshot: &Path,
    parent: Option<&Path>,
    retries: u32,
) -> Result<()> {
    ensure!(retries <= 100, "retry bound exceeded");
    let repository = Repository::open(repo_root)?;
    let expected_repo_id = repository.id();
    let source_uuid = readonly_btrfs_uuid(snapshot)?;
    let parent_uuid = match parent {
        Some(p) => Some(readonly_btrfs_uuid(p)?),
        None => None,
    };
    for attempt in 0..=retries {
        // Reopen rather than reusing a stale fd after a temporary unmount.
        let fresh = Repository::open(repo_root)?;
        ensure!(
            fresh.id() == expected_repo_id,
            "repository identity changed across reconnect"
        );
        ensure!(
            readonly_btrfs_uuid(snapshot)? == source_uuid,
            "source snapshot identity changed across retry"
        );
        if let Some(p) = parent {
            ensure!(
                readonly_btrfs_uuid(p)? == parent_uuid.clone().unwrap(),
                "incremental parent identity changed across retry"
            );
        }
        let mut command = Command::new(BTRFS_BINARY);
        command.arg("send").args(["--proto", "2"]);
        if let Some(p) = parent {
            command.arg("-p").arg(p);
        }
        command.arg(snapshot);
        command
            .stdin(Stdio::null())
            .stdout(Stdio::piped())
            .stderr(Stdio::inherit());
        let mut child = command.spawn().context("cannot launch btrfs send")?;
        let mut source = child.stdout.take().context("send stdout was not piped")?;
        let result = fresh.ingest(name, &mut source, || {
            child.wait().is_ok_and(|status| status.success())
        });
        drop(source);
        if let Err(ref e) = result {
            let _ = child.kill();
            let _ = child.wait();
            if transient_io(e) && attempt < retries {
                let backoff = (1u64 << attempt.min(5)).min(30);
                eprintln!(
                    "Transient I/O error: {e:#}; retry {}/{} after {backoff}s",
                    attempt + 1,
                    retries
                );
                thread::sleep(Duration::from_secs(backoff));
                continue;
            }
        }
        let stats = result?;
        println!(
            "{}",
            json!({
                "status": "completed", "name": name, "new_objects": stats.new_objects,
                "reused_objects": stats.reused_objects, "stream_sha256": stats.raw_sha256,
                "source_uuid": source_uuid, "parent_uuid": parent_uuid,
            })
        );
        return Ok(());
    }
    bail!("all retries exhausted")
}

fn recover_file(repo: &Repository, name: &str, output: &Path) -> Result<()> {
    ensure!(
        output.is_absolute() && !output.is_symlink() && output != Path::new("/"),
        "output must be an explicit absolute new file"
    );
    repo.verify(name)?;
    let mut stream = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(0o600)
        .open(output)
        .context("output file already exists or is inaccessible")?;
    let result = (|| {
        let bytes = repo.recover_into(name, &mut stream)?;
        stream.sync_all()?;
        println!(
            "{}",
            json!({"status": "recovered", "output": output, "raw_bytes": bytes})
        );
        Ok(())
    })();
    drop(stream);
    if result.is_err() {
        let _ = std::fs::remove_file(output);
    }
    result
}

fn execute(action: Action) -> Result<()> {
    match action {
        Action::Init { repo, allow_local } => {
            gate_target(&repo, allow_local)?;
            let repo = Repository::initialize(&repo)?;
            println!("{}", json!({"status": "initialized", "repo_id": repo.id()}));
        }
        Action::IngestFile {
            repo,
            name,
            file,
            experimental,
            allow_local,
        } => {
            ensure!(experimental, "lab ingest requires --experimental");
            gate_target(&repo, allow_local)?;
            ensure!(
                file.is_file() && !file.is_symlink(),
                "invalid input stream file"
            );
            let repo = Repository::open(&repo)?;
            let stream = File::open(file)?;
            let stats = repo.ingest(&name, stream, || true)?;
            println!(
                "{}",
                json!({"status": "completed", "new_objects": stats.new_objects,
                "reused_objects": stats.reused_objects, "stream_sha256": stats.raw_sha256})
            );
        }
        Action::Send {
            repo,
            name,
            snapshot,
            parent,
            retries,
            experimental,
            allow_local,
        } => {
            ensure!(
                experimental,
                "uncertified Btrfs transport requires --experimental"
            );
            gate_target(&repo, allow_local)?;
            run_send(&repo, &name, &snapshot, parent.as_deref(), retries)?;
        }
        Action::Verify { repo, name } => {
            let repo = Repository::open(&repo)?;
            let raw_bytes = repo.verify(&name)?;
            println!(
                "{}",
                json!({"status": "verified", "name": name, "raw_bytes": raw_bytes})
            );
        }
        Action::RecoverFile { repo, name, output } => {
            let repo = Repository::open(&repo)?;
            recover_file(&repo, &name, &output)?;
        }
    }
    Ok(())
}

fn main() {
    let cli = Cli::parse();
    if let Err(error) = execute(cli.action) {
        eprintln!("harbor-transport: {error:#}");
        std::process::exit(2);
    }
}
