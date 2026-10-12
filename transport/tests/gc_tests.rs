use harbor_transport::cas::{Repository, SnapshotIdentity};
use std::io::Cursor;
use std::sync::mpsc;
use std::time::Duration;
use tempfile::TempDir;
use uuid::Uuid;

fn add(repo: &Repository, name: &str, data: &[u8]) {
    repo.ingest(name, Cursor::new(data), || true).unwrap();
}

fn add_snap(repo: &Repository, name: &str, uuid: Uuid, parent: Option<(Uuid, &str)>) {
    let (parent_uuid, parent_archive) = match parent {
        Some((id, name)) => (Some(id), Some(name.to_string())),
        None => (None, None),
    };
    repo.ingest_snapshot(
        name,
        Cursor::new(format!("synthetic-{name}").into_bytes()),
        || true,
        SnapshotIdentity {
            source_uuid: uuid,
            parent_uuid,
            parent_archive,
            protocol: 2,
        },
    )
    .unwrap();
}

#[test]
fn dry_run_does_not_remove_any_archive_or_object() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    add(&repo, "keep", b"keep data");
    add(&repo, "discard", b"other data");
    let before = repo.list_archives().unwrap();
    let plan = repo.gc_preview(&["discard".into()]).unwrap();
    assert_eq!(plan.remove_archives, vec!["discard"]);
    assert_eq!(plan.retain_archives, vec!["keep"]);
    assert_eq!(plan.orphan_objects, 1);
    assert!(plan.reclaim_bytes > 0);
    assert_eq!(repo.list_archives().unwrap().len(), before.len());
    repo.verify("keep").unwrap();
    repo.verify("discard").unwrap();
}

#[test]
fn confirmed_prune_keeps_shared_objects_and_all_retained_streams() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    add(&repo, "one", b"common");
    add(&repo, "two", b"common");
    add(&repo, "third", b"independent");
    let plan = repo.gc_preview(&["one".into(), "third".into()]).unwrap();
    assert_eq!(plan.orphan_objects, 1);
    repo.gc_confirm(&["one".into(), "third".into()], &plan.plan_sha256)
        .unwrap();
    assert!(!repo.manifest_exists("one"));
    assert!(!repo.manifest_exists("third"));
    assert_eq!(repo.verify("two").unwrap(), 6);
    let after = repo.gc_preview(&[]).unwrap();
    assert_eq!(after.orphan_objects, 0);
}

#[test]
fn parent_with_retained_child_must_never_be_pruned() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let first = Uuid::new_v4();
    let second = Uuid::new_v4();
    add_snap(&repo, "base", first, None);
    add_snap(&repo, "delta", second, Some((first, "base")));
    assert!(repo.gc_preview(&["base".into()]).is_err());
    assert!(repo.gc_confirm(&["base".into()], &"0".repeat(64)).is_err());
    assert!(repo.manifest_exists("base"));
    assert!(repo.manifest_exists("delta"));
    let safe = repo.gc_preview(&["delta".into()]).unwrap();
    repo.gc_confirm(&["delta".into()], &safe.plan_sha256)
        .unwrap();
    assert!(repo.manifest_exists("base"));
    assert!(!repo.manifest_exists("delta"));
}

#[test]
fn stale_token_cannot_delete_newly_committed_archive() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    add(&repo, "old", b"old");
    let token = repo.gc_preview(&["old".into()]).unwrap().plan_sha256;
    add(&repo, "new", b"new");
    assert!(repo.gc_confirm(&["old".into()], &token).is_err());
    assert!(repo.manifest_exists("old"));
    assert!(repo.manifest_exists("new"));
}

#[test]
fn unexpected_object_symlinks_fail_closed_without_deletion() {
    use std::os::unix::fs::symlink;
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    add(&repo, "original", b"known bytes");
    let prefix = temp.path().join("objects/aa");
    std::fs::create_dir_all(&prefix).unwrap();
    symlink(
        temp.path().join("manifests/original.json"),
        prefix.join(format!("{}.zst", "aa".repeat(32))),
    )
    .unwrap();
    assert!(repo.gc_preview(&["original".into()]).is_err());
    assert!(repo.manifest_exists("original"));
}

#[test]
fn exclusive_gc_waits_until_shared_restore_reader_releases_lease() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    add(&repo, "delete", b"test-bytes");
    let token = repo.gc_preview(&["delete".into()]).unwrap().plan_sha256;
    let lease = repo.read_lease().unwrap();
    let root = temp.path().to_path_buf();
    let (tx, rx) = mpsc::channel();
    let t = std::thread::spawn(move || {
        let repo = Repository::open(&root).unwrap();
        let result = repo.gc_confirm(&["delete".into()], &token);
        tx.send(result.is_ok()).unwrap();
    });
    assert!(rx.recv_timeout(Duration::from_millis(160)).is_err());
    assert!(repo.manifest_exists("delete"));
    drop(lease);
    assert!(rx.recv_timeout(Duration::from_secs(5)).unwrap());
    t.join().unwrap();
    assert!(!repo.manifest_exists("delete"));
}

#[test]
fn explicit_empty_selection_sweeps_only_orphans_after_aborted_ingest() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    add(&repo, "keep", b"good");
    let aborted = repo.ingest("failed", Cursor::new(b"orphan data"), || false);
    assert!(aborted.is_err());
    let plan = repo.gc_preview(&[]).unwrap();
    assert_eq!(plan.orphan_objects, 1);
    repo.gc_confirm(&[], &plan.plan_sha256).unwrap();
    repo.verify("keep").unwrap();
    assert_eq!(repo.gc_preview(&[]).unwrap().orphan_objects, 0);
}

#[test]
fn corrupted_retained_parent_provenance_fails_closed() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let first = Uuid::new_v4();
    let second = Uuid::new_v4();
    add_snap(&repo, "base", first, None);
    add_snap(&repo, "delta", second, Some((first, "base")));
    add(&repo, "disposable", b"unrelated");
    // Simulate externally corrupted historical metadata, never generated by
    // the protected ingest path. The existing manifest is still parseable.
    let path = temp.path().join("manifests/delta.json");
    let mut json: serde_json::Value =
        serde_json::from_slice(&std::fs::read(&path).unwrap()).unwrap();
    json["identity"]["parent_archive"] = serde_json::json!("missing-parent");
    std::fs::write(path, serde_json::to_vec(&json).unwrap()).unwrap();
    assert!(repo.gc_preview(&["disposable".into()]).is_err());
    assert!(repo.manifest_exists("disposable"));
}

#[test]
fn symlinked_repository_lock_is_rejected() {
    use std::os::unix::fs::symlink;
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    symlink(
        temp.path().join(".harbor-repo-id"),
        temp.path().join(".harbor-repo.lock"),
    )
    .unwrap();
    assert!(repo.gc_preview(&[]).is_err());
    assert!(repo.read_lease().is_err());
    assert!(temp.path().join(".harbor-repo-id").is_file());
}
