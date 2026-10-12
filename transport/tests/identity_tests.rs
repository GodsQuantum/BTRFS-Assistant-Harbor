use harbor_transport::cas::{Repository, SnapshotIdentity};
use std::io::Cursor;
use tempfile::TempDir;
use uuid::Uuid;

fn identity(source: Uuid, parent: Option<Uuid>, archive: Option<&str>) -> SnapshotIdentity {
    SnapshotIdentity {
        source_uuid: source,
        parent_uuid: parent,
        parent_archive: archive.map(str::to_string),
        protocol: 2,
    }
}

#[test]
fn stores_source_provenance_and_parent_link() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let base = Uuid::new_v4();
    let child = Uuid::new_v4();
    repo.ingest_snapshot(
        "base",
        Cursor::new(b"base stream"),
        || true,
        identity(base, None, None),
    )
    .unwrap();
    repo.ingest_snapshot(
        "next",
        Cursor::new(b"delta"),
        || true,
        identity(child, Some(base), Some("base")),
    )
    .unwrap();
    assert_eq!(
        repo.snapshot_identity("next").unwrap(),
        Some(identity(child, Some(base), Some("base")))
    );
    let manifest = std::fs::read_to_string(temp.path().join("manifests/next.json")).unwrap();
    assert!(manifest.contains(&base.to_string()));
    assert!(manifest.contains("\"parent_archive\":\"base\""));
    assert_eq!(repo.verify("next").unwrap(), 5);
}

#[test]
fn rejects_child_when_parent_not_saved_or_wrong() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let base = Uuid::new_v4();
    let next = Uuid::new_v4();
    assert!(
        repo.ingest_snapshot(
            "child",
            Cursor::new(b"delta"),
            || true,
            identity(next, Some(base), Some("not-saved"))
        )
        .is_err()
    );
    assert!(!repo.manifest_exists("child"));
    repo.ingest_snapshot(
        "base",
        Cursor::new(b"full"),
        || true,
        identity(base, None, None),
    )
    .unwrap();
    assert!(
        repo.ingest_snapshot(
            "child",
            Cursor::new(b"delta"),
            || true,
            identity(next, Some(Uuid::new_v4()), Some("base"))
        )
        .is_err()
    );
    assert!(!repo.manifest_exists("child"));
}

#[test]
fn rejects_missing_parent_link_self_parent_and_bad_protocol() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let x = Uuid::new_v4();
    for bad in [
        identity(x, Some(Uuid::new_v4()), None),
        identity(x, None, Some("base")),
        identity(x, Some(x), Some("self")),
        SnapshotIdentity {
            source_uuid: x,
            parent_uuid: None,
            parent_archive: None,
            protocol: 0,
        },
    ] {
        assert!(
            repo.ingest_snapshot("bad", Cursor::new(b"bad"), || true, bad)
                .is_err()
        );
    }
    assert!(!repo.manifest_exists("bad"));
}

#[test]
fn rejects_identity_switch_even_if_stream_bytes_identical() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let a = Uuid::new_v4();
    repo.ingest_snapshot(
        "one",
        Cursor::new(b"same bytes"),
        || true,
        identity(a, None, None),
    )
    .unwrap();
    assert!(
        repo.ingest_snapshot(
            "one",
            Cursor::new(b"same bytes"),
            || true,
            identity(Uuid::new_v4(), None, None)
        )
        .is_err()
    );
    assert_eq!(
        repo.snapshot_identity("one").unwrap(),
        Some(identity(a, None, None))
    );
}

#[test]
fn incremental_restore_chain_is_ordered_and_refuses_missing_parent() {
    let tmp = TempDir::new().unwrap();
    let repo = Repository::initialize(tmp.path()).unwrap();
    let base = Uuid::new_v4();
    let newer = Uuid::new_v4();
    repo.ingest_snapshot(
        "base",
        Cursor::new(b"initial data"),
        || true,
        identity(base, None, None),
    )
    .unwrap();
    repo.ingest_snapshot(
        "delta",
        Cursor::new(b"delta commands"),
        || true,
        identity(newer, Some(base), Some("base")),
    )
    .unwrap();
    assert_eq!(
        repo.verified_restore_chain("delta").unwrap(),
        vec!["base".to_string(), "delta".to_string()]
    );
    std::fs::remove_file(tmp.path().join("manifests/base.json")).unwrap();
    assert!(repo.verified_restore_chain("delta").is_err());
}

#[test]
fn verify_does_not_recreate_missing_objects_directory() {
    let tmp = TempDir::new().unwrap();
    let repo = Repository::initialize(tmp.path()).unwrap();
    repo.ingest("one", Cursor::new(b"private data"), || true)
        .unwrap();
    std::fs::rename(
        tmp.path().join("objects"),
        tmp.path().join("objects-hidden"),
    )
    .unwrap();
    assert!(repo.verify("one").is_err());
    assert!(
        !tmp.path().join("objects").exists(),
        "read-only verification must not mutate repo"
    );
}
