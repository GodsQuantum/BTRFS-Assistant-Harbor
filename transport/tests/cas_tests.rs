use harbor_transport::cas::Repository;
use std::io::Cursor;
use tempfile::TempDir;

fn contents() -> Vec<u8> {
    // Nonperiodic deterministic data: identical regions must re-synchronize
    // after insertion. The former periodic pattern forced max-size cuts.
    let mut x = 0x9e3779b97f4a7c15_u64;
    let mut data = Vec::with_capacity(50_331_648);
    for _ in 0..50_331_648 {
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        data.push((x >> 24) as u8);
    }
    data
}

#[test]
fn failed_send_does_not_publish_but_resend_reuses_chunks() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let input = contents();
    let failed = repo.ingest("snap-a", Cursor::new(&input), || false);
    assert!(failed.is_err());
    assert!(!repo.manifest_exists("snap-a"));
    let first = repo.ingest("snap-a", Cursor::new(&input), || true).unwrap();
    assert_eq!(first.new_objects, 0);
    assert!(first.reused_objects > 0);
    repo.verify("snap-a").unwrap();
    let mut recovered = Vec::new();
    repo.recover_into("snap-a", &mut recovered).unwrap();
    assert_eq!(input, recovered);
}

#[test]
fn changed_input_still_completes_coherent_manifest_after_failure() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let input = contents();
    repo.ingest("snap-x", Cursor::new(&input), || false)
        .unwrap_err();
    let mut changed = b"new Btrfs send prefix".to_vec();
    changed.extend_from_slice(&input);
    let next = repo
        .ingest("snap-x", Cursor::new(&changed), || true)
        .unwrap();
    assert!(
        next.reused_objects > 0,
        "CDC ought to match unchanged suffix"
    );
    let mut got = Vec::new();
    repo.recover_into("snap-x", &mut got).unwrap();
    assert_eq!(changed, got);
}

#[test]
fn mismatched_final_archive_never_overwrites() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    repo.ingest("snap-y", Cursor::new(b"hello"), || true)
        .unwrap();
    let error = repo
        .ingest("snap-y", Cursor::new(b"goodbye"), || true)
        .unwrap_err();
    assert!(format!("{error}").contains("existing manifest"));
    let mut got = Vec::new();
    repo.recover_into("snap-y", &mut got).unwrap();
    assert_eq!(got, b"hello");
}

#[test]
fn corrupt_object_is_rejected_before_recovery_writes_anything() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    repo.ingest("snap-z", Cursor::new(contents()), || true)
        .unwrap();
    let object = std::fs::read_dir(temp.path().join("objects"))
        .unwrap()
        .flat_map(|d| std::fs::read_dir(d.unwrap().path()).unwrap())
        .next()
        .unwrap()
        .unwrap()
        .path();
    std::fs::write(object, b"damaged").unwrap();
    assert!(repo.verify("snap-z").is_err());
    let mut output = Vec::new();
    assert!(repo.recover_into("snap-z", &mut output).is_err());
    assert!(output.is_empty());
}

#[test]
fn repo_marker_is_required_to_avoid_offline_mount_fallback() {
    let temp = TempDir::new().unwrap();
    assert!(Repository::open(temp.path()).is_err());
    let repo = Repository::initialize(temp.path()).unwrap();
    assert_eq!(repo.id(), Repository::open(temp.path()).unwrap().id());
    std::fs::remove_file(temp.path().join(".harbor-repo-id")).unwrap();
    assert!(repo.ingest("new", Cursor::new(b"test"), || true).is_err());
}

#[test]
fn unsafe_archive_names_are_rejected() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    for name in ["../escape", "/root", "", "a/b", "space name"] {
        assert!(repo.ingest(name, Cursor::new(b"data"), || true).is_err());
    }
}

#[test]
fn completed_same_archive_is_idempotent() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let first = repo
        .ingest("same", Cursor::new(b"the same bytes"), || true)
        .unwrap();
    let second = repo
        .ingest("same", Cursor::new(b"the same bytes"), || true)
        .unwrap();
    assert_eq!(first.raw_sha256, second.raw_sha256);
    assert_eq!(second.new_objects, 0);
}

#[cfg(unix)]
#[test]
fn private_backup_objects_and_manifests() {
    use std::os::unix::fs::PermissionsExt;
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    repo.ingest("private", Cursor::new(b"private snapshots"), || true)
        .unwrap();
    let object = std::fs::read_dir(temp.path().join("objects"))
        .unwrap()
        .flat_map(|d| std::fs::read_dir(d.unwrap().path()).unwrap())
        .next()
        .unwrap()
        .unwrap()
        .path();
    let manifest = temp.path().join("manifests/private.json");
    for path in [object, manifest] {
        let mode = std::fs::metadata(path).unwrap().permissions().mode();
        assert_eq!(
            mode & 0o077,
            0,
            "backup content must not be group/world readable"
        );
    }
}

struct TimedOutStream {
    bytes: Vec<u8>,
    pos: usize,
    stop_at: usize,
}
impl std::io::Read for TimedOutStream {
    fn read(&mut self, buf: &mut [u8]) -> std::io::Result<usize> {
        if self.pos >= self.stop_at {
            return Err(std::io::Error::from(std::io::ErrorKind::TimedOut));
        }
        let end = (self.pos + buf.len())
            .min(self.stop_at)
            .min(self.bytes.len());
        let n = end - self.pos;
        buf[..n].copy_from_slice(&self.bytes[self.pos..end]);
        self.pos = end;
        Ok(n)
    }
}
#[test]
fn mid_stream_timeout_does_not_publish_and_next_attempt_reuses_committed_objects() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let bytes = contents();
    let failed = repo.ingest(
        "timeout",
        TimedOutStream {
            bytes: bytes.clone(),
            pos: 0,
            stop_at: 28 * 1024 * 1024,
        },
        || true,
    );
    assert!(failed.is_err());
    assert!(!repo.manifest_exists("timeout"));
    let second = repo
        .ingest("timeout", Cursor::new(&bytes), || true)
        .unwrap();
    assert!(second.reused_objects > 0);
    assert_eq!(repo.verify("timeout").unwrap(), bytes.len() as u64);
}

#[test]
fn valid_existing_same_raw_chunk_with_other_zstd_level_must_be_reused() {
    let tmp = TempDir::new().unwrap();
    let repo = Repository::initialize(tmp.path()).unwrap();
    let bytes = b"compressed block ".repeat(90_000);
    let first = repo.ingest("level3", Cursor::new(&bytes), || true).unwrap();
    assert!(first.new_objects >= 1);
    let obj = std::fs::read_dir(tmp.path().join("objects"))
        .unwrap()
        .flat_map(|folder| std::fs::read_dir(folder.unwrap().path()).unwrap())
        .next()
        .unwrap()
        .unwrap()
        .path();
    let alternate = zstd::bulk::compress(&bytes, 17).unwrap();
    assert_ne!(std::fs::read(&obj).unwrap(), alternate);
    std::fs::write(&obj, alternate).unwrap();
    // A valid raw chunk may already be present from a different compression
    // setting; a new backup must not reject the block or trust bad metadata.
    let second = repo
        .ingest("level17", Cursor::new(&bytes), || true)
        .unwrap();
    assert_eq!(second.new_objects, 0);
    assert!(second.reused_objects > 0);
    assert_eq!(repo.verify("level17").unwrap(), bytes.len() as u64);
}

#[test]
fn corrupted_remote_object_before_commit_does_not_publish_manifest() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let input = vec![0xABu8; 3 * 1024 * 1024];
    let result = repo.ingest("must-not-publish", Cursor::new(&input), || {
        let object = std::fs::read_dir(temp.path().join("objects"))
            .unwrap()
            .flat_map(|dir| std::fs::read_dir(dir.unwrap().path()).unwrap())
            .next()
            .unwrap()
            .unwrap()
            .path();
        std::fs::write(object, b"remote-server-corrupted-the-object").unwrap();
        true
    });
    assert!(
        result.is_err(),
        "corrupted remote object was improperly accepted"
    );
    assert!(
        !repo.manifest_exists("must-not-publish"),
        "unsafe to publish manifest before remote objects are verified"
    );
}

#[test]
fn progress_events_are_monotonic_and_measure_source_bytes_only() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let data = vec![0xabu8; 3 * 1024 * 1024];
    let mut samples = Vec::new();
    repo.ingest_snapshot_with_progress(
        "progress",
        Cursor::new(&data),
        || true,
        harbor_transport::cas::SnapshotIdentity {
            source_uuid: uuid::Uuid::new_v4(),
            parent_uuid: None,
            parent_archive: None,
            protocol: 2,
        },
        |count| samples.push(count),
    )
    .unwrap();
    assert!(!samples.is_empty());
    assert_eq!(*samples.last().unwrap(), data.len() as u64);
    assert!(samples.windows(2).all(|a| a[0] < a[1]));
    assert_eq!(repo.verify("progress").unwrap(), data.len() as u64);
}

#[test]
fn shared_restore_lease_blocks_exclusive_ingest_until_reader_exits() {
    use std::sync::mpsc;
    use std::time::Duration;
    let temp = TempDir::new().unwrap();
    let repository = Repository::initialize(temp.path()).unwrap();
    let lease = repository.read_lease().unwrap();
    let path = temp.path().to_owned();
    let (tx, rx) = mpsc::channel();
    let task = std::thread::spawn(move || {
        let repo = Repository::open(&path).unwrap();
        let result = repo.ingest("after-reader", Cursor::new(b"stream"), || true);
        tx.send(result.is_ok()).unwrap();
    });
    assert!(
        rx.recv_timeout(Duration::from_millis(120)).is_err(),
        "writer must not pass exclusive repository lock while restore is reading"
    );
    drop(lease);
    assert!(rx.recv_timeout(Duration::from_secs(5)).unwrap());
    task.join().unwrap();
    assert_eq!(repository.verify("after-reader").unwrap(), 6);
}
