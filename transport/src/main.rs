use anyhow::{Context, Result, ensure};
use clap::{Parser, Subcommand};
use harbor_transport::cas::{Repository, SnapshotIdentity};
use harbor_transport::mount_probe::actual_filesystem;
use harbor_transport::retry::retry_transient;
use serde_json::json;
use std::fs::{File, OpenOptions};
use std::os::unix::fs::OpenOptionsExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;
use uuid::Uuid;

const BTRFS_BINARY: &str = "btrfs";

/// Scoped filesystem ownership for PKEXEC_UID. The privileged sender is
/// launched first; only the receiver-side repository I/O runs as the
/// authenticated desktop user's FSUID/FSGID. No mounts or ACLs are changed.
struct RepoAccess {
    old_uid: libc::c_int,
    old_gid: libc::c_int,
}

impl RepoAccess {
    fn begin() -> Result<Option<Self>> {
        if unsafe { libc::geteuid() } != 0 {
            return Ok(None);
        }
        let Some(uid_string) = std::env::var("PKEXEC_UID").ok() else {
            return Ok(None);
        };
        let uid: libc::uid_t = uid_string.parse().context("PKEXEC_UID not numeric")?;
        if uid == 0 {
            return Ok(None);
        }
        let user = unsafe { libc::getpwuid(uid) };
        ensure!(
            !user.is_null(),
            "authenticated user not found in passwd database"
        );
        let gid = unsafe { (*user).pw_gid };
        let old_gid = unsafe { libc::setfsgid(gid) };
        let old_uid = unsafe { libc::setfsuid(uid) };
        // Linux setfsuid/setfsgid return the old value even if the change was
        // denied. Explicitly verify rather than silently writing root-owned data.
        let actual_uid = unsafe { libc::setfsuid(libc::uid_t::MAX) };
        let actual_gid = unsafe { libc::setfsgid(libc::gid_t::MAX) };
        if actual_uid != uid as libc::c_int || actual_gid != gid as libc::c_int {
            unsafe {
                libc::setfsuid(old_uid as libc::uid_t);
                libc::setfsgid(old_gid as libc::gid_t);
            }
            anyhow::bail!("could not assume user filesystem ownership");
        }
        Ok(Some(Self { old_uid, old_gid }))
    }
}

impl Drop for RepoAccess {
    fn drop(&mut self) {
        unsafe {
            libc::setfsuid(self.old_uid as libc::uid_t);
            libc::setfsgid(self.old_gid as libc::gid_t);
        }
    }
}

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
        #[arg(long)]
        parent_archive: Option<String>,
        #[arg(long, default_value_t = 5)]
        retries: u32,
        #[arg(long)]
        experimental: bool,
        #[arg(long)]
        allow_local: bool,
    },
    /// Preflight a full or incremental restore chain, or receive into empty Btrfs staging.
    Receive {
        #[arg(long)]
        repo: PathBuf,
        #[arg(long)]
        name: String,
        #[arg(long)]
        staging: PathBuf,
        #[arg(long, conflicts_with = "confirm")]
        preview: bool,
        #[arg(long, conflicts_with = "preview")]
        confirm: bool,
    },
    /// Preview, or explicitly confirm, a graph-safe CAS archive prune + orphan sweep.
    /// Default is a read-only dry-run. No implicit retention policy or Snapper deletion.
    Prune {
        #[arg(long)]
        repo: PathBuf,
        #[arg(long = "name")]
        names: Vec<String>,
        /// SHA256 plan token emitted by dry-run; required for any deletion.
        #[arg(long)]
        confirm_plan: Option<String>,
    },
    /// List committed CAS archives, without modifying their data.
    List {
        #[arg(long)]
        repo: PathBuf,
    },
    Verify {
        #[arg(long)]
        repo: PathBuf,
        #[arg(long)]
        name: String,
    },
    /// Validate Btrfs send stream commands/CRCs in addition to archive hashes.
    VerifyStream {
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

/// A CAS prune depends on a repository-wide exclusive flock. Only
/// explicitly recognized LOCAL filesystems are accepted for destructive GC.
/// Network, user-space and unknown future filesystems fail closed until an
/// independently proven cross-client lock protocol is implemented.
fn destructive_prune_fs_allowed(kind: &str) -> bool {
    matches!(
        kind.to_ascii_lowercase().as_str(),
        "btrfs" | "ext4" | "ext3" | "ext2" | "xfs" | "zfs" | "f2fs" | "bcachefs" | "tmpfs"
    )
}

fn gate_target(root: &Path, allow_local: bool) -> Result<()> {
    ensure!(root.is_absolute(), "repository root must be absolute");
    let root_stat = std::fs::symlink_metadata(root)
        .context("cannot inspect network destination before transfer")?;
    ensure!(
        root_stat.file_type().is_dir(),
        "destination must be a real directory, not a symlink"
    );
    if allow_local {
        return Ok(());
    }
    let kind = actual_filesystem(root)?.to_lowercase();
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

fn run_send(
    repo_root: &Path,
    name: &str,
    snapshot: &Path,
    parent: Option<&Path>,
    parent_archive: Option<&str>,
    retries: u32,
    allow_local: bool,
) -> Result<()> {
    ensure!(
        parent.is_some() == parent_archive.is_some(),
        "incremental --parent requires --parent-archive from a completed backup"
    );
    ensure!(retries <= 100, "retry bound exceeded");
    // The mount may already be temporarily disconnected BEFORE send starts.
    // Retry preflight rather than aborting on a transient EHOSTDOWN.
    let expected_repo_id = retry_transient(
        retries,
        || {
            let _owner = RepoAccess::begin()?;
            gate_target(repo_root, allow_local)?;
            Ok(Repository::open(repo_root)?.id())
        },
        |seconds| {
            eprintln!("Network repository unavailable during preflight; retry after {seconds}s");
            thread::sleep(Duration::from_secs(seconds));
        },
    )?
    .value;
    let source_uuid = readonly_btrfs_uuid(snapshot)?;
    let parent_uuid = match parent {
        Some(p) => Some(readonly_btrfs_uuid(p)?),
        None => None,
    };
    let identity = SnapshotIdentity {
        source_uuid: Uuid::parse_str(&source_uuid)?,
        parent_uuid: parent_uuid
            .as_ref()
            .map(|id| Uuid::parse_str(id))
            .transpose()?,
        parent_archive: parent_archive.map(str::to_owned),
        protocol: 2,
    };
    let outcome = retry_transient(
        retries,
        || {
            let fresh = {
                let _owner = RepoAccess::begin()?;
                gate_target(repo_root, allow_local)?;
                // Reopen after a temporary NFS/SMB connection failure.
                Repository::open(repo_root)?
            };
            ensure!(
                fresh.id() == expected_repo_id,
                "repository identity changed across reconnect"
            );
            if let Some(parent_name) = parent_archive {
                let _owner = RepoAccess::begin()?;
                let archived = fresh.snapshot_identity(parent_name)?.ok_or_else(|| {
                    anyhow::anyhow!("incremental parent archive lacks source identity")
                })?;
                ensure!(
                    Some(archived.source_uuid) == identity.parent_uuid,
                    "incremental parent archive UUID changed or is incorrect"
                );
            }
            ensure!(
                readonly_btrfs_uuid(snapshot)? == source_uuid,
                "source snapshot identity changed across retry"
            );
            if let Some(p) = parent {
                ensure!(
                    readonly_btrfs_uuid(p)? == parent_uuid.as_deref().unwrap_or(""),
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
            let result = {
                let _owner = RepoAccess::begin()?;
                let mut last_report = std::time::Instant::now();
                fresh.ingest_snapshot_with_progress(
                    name,
                    &mut source,
                    || child.wait().is_ok_and(|status| status.success()),
                    identity.clone(),
                    |bytes| {
                        if last_report.elapsed() >= Duration::from_millis(750) {
                            // Framed, parseable progress on stderr. A retry
                            // starts at zero; the Qt UI labels this as bytes
                            // read from source, not remote bytes committed.
                            eprintln!("HARBOR_PROGRESS_BYTES={bytes}");
                            last_report = std::time::Instant::now();
                        }
                    },
                )
            };
            drop(source);
            if result.is_err() {
                let _ = child.kill();
                let _ = child.wait();
            }
            result
        },
        |seconds| {
            eprintln!("Transient transport error; retrying after {seconds}s");
            thread::sleep(Duration::from_secs(seconds));
        },
    )?;
    let stats = outcome.value;
    println!(
        "{}",
        json!({
            "status": "completed", "name": name, "new_objects": stats.new_objects,
            "reused_objects": stats.reused_objects, "stream_sha256": stats.raw_sha256,
            "source_uuid": source_uuid, "parent_uuid": parent_uuid,
            "network_retries": outcome.retries,
        })
    );
    Ok(())
}

fn verify_btrfs_stream(repo: &Repository, name: &str) -> Result<()> {
    let _lease = repo.read_lease()?;
    // A valid incremental stream is not a recoverable backup when its base
    // manifest or any of its ancestors is absent/corrupt. Scheduled jobs use
    // verify-stream for idempotency and parent selection, so first validate
    // the complete chain and only then run the native parser in base->child
    // order. Identity-free legacy laboratory archives retain the standalone
    // stream verifier (they cannot claim incremental recoverability).
    let archives = if repo.snapshot_identity(name)?.is_some() {
        repo.verified_restore_chain(name)?
    } else {
        repo.verify(name)?;
        vec![name.to_owned()]
    };
    for archive in archives {
        let mut child = Command::new(BTRFS_BINARY)
            .arg("receive")
            .arg("--dump")
            .arg("-e")
            .stdin(Stdio::piped())
            .stdout(Stdio::null())
            .stderr(Stdio::null())
            .spawn()
            .context("cannot run Btrfs stream validator")?;
        let mut input = child
            .stdin
            .take()
            .context("Btrfs validator stdin unavailable")?;
        let copy = repo.recover_into(&archive, &mut input);
        drop(input);
        if let Err(err) = copy {
            let _ = child.kill();
            let _ = child.wait();
            return Err(err).with_context(|| {
                format!("archive {archive} retrieval failed during native validation")
            });
        }
        let status = child.wait()?;
        ensure!(
            status.success(),
            "Btrfs stream is invalid (native receive --dump rejected archive {archive})"
        );
    }
    Ok(())
}

fn recover_file(repo: &Repository, name: &str, output: &Path) -> Result<()> {
    ensure!(
        output.is_absolute() && !output.is_symlink() && output != Path::new("/"),
        "output must be an explicit absolute new file"
    );
    let _lease = repo.read_lease()?;
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

fn recover_btrfs(
    repo: &Repository,
    name: &str,
    staging: &Path,
    preview: bool,
    confirm: bool,
) -> Result<()> {
    ensure!(preview || confirm, "choose --preview or explicit --confirm");
    ensure!(
        staging.is_absolute()
            && staging != Path::new("/")
            && staging.is_dir()
            && !staging.is_symlink()
            && staging.read_dir()?.next().is_none(),
        "restore staging must be an empty absolute real directory, not system root"
    );
    let (chain, _lease) = {
        let _owner = RepoAccess::begin()?;
        let lease = repo.read_lease()?;
        (repo.verified_restore_chain(name)?, lease)
    };
    if preview {
        println!(
            "{}",
            json!({"status": "verified-preview", "chain": chain, "staging": staging})
        );
        return Ok(());
    }
    // Receiver touches ONLY a separately chosen empty directory on a Btrfs mount.
    // Never overwrite an existing local Snapper snapshot or activate a rollback here.
    ensure!(
        actual_filesystem(staging)? == "btrfs",
        "restore staging must reside on a Btrfs filesystem"
    );
    for archived in &chain {
        let mut child = Command::new(BTRFS_BINARY)
            .arg("receive")
            .arg("-e")
            .arg("--max-errors")
            .arg("1")
            .arg(staging)
            .stdin(Stdio::piped())
            .stdout(Stdio::null())
            .stderr(Stdio::inherit())
            .spawn()
            .context("cannot spawn btrfs receive")?;
        let mut sink = child.stdin.take().context("receiver stdin not available")?;
        let result = {
            let _owner = RepoAccess::begin()?;
            repo.recover_into(archived, &mut sink)
        };
        drop(sink);
        if let Err(err) = result {
            let _ = child.kill();
            let _ = child.wait();
            return Err(err).context("Btrfs receive stream failed; inspect staging before retry");
        }
        ensure!(
            child.wait()?.success(),
            "Btrfs receive failed; partial staging requires manual inspection"
        );
    }
    println!(
        "{}",
        json!({"status": "received-staging", "chain": chain, "staging": staging})
    );
    Ok(())
}

fn execute(action: Action) -> Result<()> {
    match action {
        Action::Init { repo, allow_local } => {
            let _owner = RepoAccess::begin()?;
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
            let _owner = RepoAccess::begin()?;
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
            parent_archive,
            retries,
            experimental,
            allow_local,
        } => {
            ensure!(
                experimental,
                "uncertified Btrfs transport requires --experimental"
            );
            run_send(
                &repo,
                &name,
                &snapshot,
                parent.as_deref(),
                parent_archive.as_deref(),
                retries,
                allow_local,
            )?;
        }
        Action::Receive {
            repo,
            name,
            staging,
            preview,
            confirm,
        } => {
            let repo = Repository::open(&repo)?;
            recover_btrfs(&repo, &name, &staging, preview, confirm)?;
        }
        Action::VerifyStream { repo, name } => {
            let _owner = RepoAccess::begin()?;
            let repository = Repository::open(&repo)?;
            verify_btrfs_stream(&repository, &name)?;
            println!(
                "{}",
                json!({"status": "native-btrfs-stream-verified", "name": name})
            );
        }
        Action::Prune {
            repo,
            names,
            confirm_plan,
        } => {
            let _owner = RepoAccess::begin()?;
            let repository = Repository::open(&repo)?;
            let (status, plan) = if let Some(expected) = confirm_plan {
                let fs_kind = actual_filesystem(&repo)?;
                ensure!(
                    destructive_prune_fs_allowed(&fs_kind),
                    "destructive CAS pruning on network filesystem {fs_kind} is disabled until multi-client NFS/SMB locks are certified; dry-run remains supported"
                );
                ("pruned", repository.gc_confirm(&names, &expected)?)
            } else {
                ("dry-run", repository.gc_preview(&names)?)
            };
            println!("{}", json!({"status":status, "plan":plan}));
        }
        Action::List { repo } => {
            let _owner = RepoAccess::begin()?;
            let repo = Repository::open(&repo)?;
            let _reader = repo.read_lease()?;
            println!("{}", serde_json::to_string(&repo.list_archives()?)?);
        }
        Action::Verify { repo, name } => {
            let _owner = RepoAccess::begin()?;
            let repo = Repository::open(&repo)?;
            let _reader = repo.read_lease()?;
            let raw_bytes = repo.verify(&name)?;
            println!(
                "{}",
                json!({"status": "verified", "name": name, "raw_bytes": raw_bytes})
            );
        }
        Action::RecoverFile { repo, name, output } => {
            let _owner = RepoAccess::begin()?;
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

#[cfg(test)]
mod remote_prune_safety_tests {
    use super::destructive_prune_fs_allowed;
    #[test]
    fn network_lock_modes_are_not_assumed_to_be_distributed() {
        for kind in [
            "nfs",
            "nfs4",
            "NFS4",
            "cifs",
            "smb3",
            "fuse.sshfs",
            "fuse.rclone",
            "ceph",
            "glusterfs",
            "9p",
            "overlay",
            "unknown-rpc-fs",
        ] {
            assert!(!destructive_prune_fs_allowed(kind), "unsafe remote {kind}");
        }
    }
    #[test]
    fn filesystem_types_used_by_existing_local_tests_still_work() {
        for kind in [
            "btrfs", "ext4", "ext3", "ext2", "xfs", "zfs", "f2fs", "bcachefs", "tmpfs",
        ] {
            assert!(destructive_prune_fs_allowed(kind), "local fixture {kind}");
        }
    }
}
