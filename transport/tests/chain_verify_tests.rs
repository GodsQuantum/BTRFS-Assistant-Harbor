use harbor_transport::cas::{Repository, SnapshotIdentity};
use std::io::Cursor;
use std::os::unix::fs::PermissionsExt;
use std::process::Command;
use tempfile::TempDir;
use uuid::Uuid;

fn fixture() -> TempDir {
    let temp = TempDir::new().unwrap();
    let target = temp.path().join("repository");
    std::fs::create_dir(&target).unwrap();
    let repo = Repository::initialize(&target).unwrap();
    let base = Uuid::new_v4();
    repo.ingest_snapshot(
        "base",
        Cursor::new(b"base-stream"),
        || true,
        SnapshotIdentity {
            source_uuid: base,
            parent_uuid: None,
            parent_archive: None,
            protocol: 2,
        },
    )
    .unwrap();
    repo.ingest_snapshot(
        "child",
        Cursor::new(b"child-stream"),
        || true,
        SnapshotIdentity {
            source_uuid: Uuid::new_v4(),
            parent_uuid: Some(base),
            parent_archive: Some("base".into()),
            protocol: 2,
        },
    )
    .unwrap();
    let bin = temp.path().join("bin");
    std::fs::create_dir(&bin).unwrap();
    let script = bin.join("btrfs");
    std::fs::write(&script, "#!/bin/sh\n[ \"$1\" = receive ] && [ \"$2\" = --dump ] || exit 23\ncat >> \"$HARBOR_TEST_DUMP_LOG\"\nprintf '\\n' >> \"$HARBOR_TEST_DUMP_LOG\"\n").unwrap();
    std::fs::set_permissions(&script, std::fs::Permissions::from_mode(0o755)).unwrap();
    temp
}

fn check(temp: &TempDir) -> std::process::Output {
    let path = format!(
        "{}:{}",
        temp.path().join("bin").display(),
        std::env::var("PATH").unwrap_or_default()
    );
    Command::new(env!("CARGO_BIN_EXE_harbor-transport"))
        .args([
            "verify-stream",
            "--repo",
            temp.path().join("repository").to_str().unwrap(),
            "--name",
            "child",
        ])
        .env("PATH", path)
        .env("HARBOR_TEST_DUMP_LOG", temp.path().join("dump.log"))
        .output()
        .unwrap()
}

#[test]
fn native_stream_check_validates_base_and_child_not_just_child() {
    let temp = fixture();
    let result = check(&temp);
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    assert_eq!(
        std::fs::read(temp.path().join("dump.log")).unwrap(),
        b"base-stream\nchild-stream\n"
    );
}

#[test]
fn native_stream_check_rejects_missing_incremental_parent() {
    let temp = fixture();
    let target = temp.path().join("repository");
    let repo = Repository::open(&target).unwrap();
    assert_eq!(repo.verify("child").unwrap(), 12);
    std::fs::remove_file(target.join("manifests/base.json")).unwrap();
    let result = check(&temp);
    assert!(
        !result.status.success(),
        "verify-stream improperly accepted a broken parent chain"
    );
    assert!(
        !temp.path().join("dump.log").exists(),
        "invalid chain must fail before spawning a native verifier"
    );
}

#[test]
fn native_stream_check_rejects_corrupted_parent_even_if_child_hash_is_valid() {
    let temp = fixture();
    let target = temp.path().join("repository");
    let repo = Repository::open(&target).unwrap();
    assert_eq!(repo.verify("child").unwrap(), 12);
    let objects = target.join("objects");
    let base = serde_json::from_slice::<serde_json::Value>(
        &std::fs::read(target.join("manifests/base.json")).unwrap(),
    )
    .unwrap();
    let hash = base["objects"][0]["hash"].as_str().unwrap();
    let path = objects.join(&hash[..2]).join(format!("{hash}.zst"));
    std::fs::write(path, b"corrupted parent object").unwrap();
    let result = check(&temp);
    assert!(
        !result.status.success(),
        "verify-stream accepted a damaged ancestor"
    );
    assert!(!temp.path().join("dump.log").exists());
}
