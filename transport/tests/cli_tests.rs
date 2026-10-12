use std::process::Command;
use tempfile::TempDir;
fn call(args: &[&str]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_harbor-transport"))
        .args(args)
        .output()
        .unwrap()
}
#[test]
fn cli_synthetic_archive_roundtrip_and_no_overwrite() {
    let tmp = TempDir::new().unwrap();
    let repo = tmp.path().join("repo");
    std::fs::create_dir(&repo).unwrap();
    let input = tmp.path().join("input.send");
    let output = tmp.path().join("restored.send");
    std::fs::write(&input, b"pretend sample of Btrfs send data").unwrap();
    let r = repo.to_str().unwrap();
    let i = input.to_str().unwrap();
    let o = output.to_str().unwrap();
    assert!(
        call(&["init", "--repo", r, "--allow-local"])
            .status
            .success()
    );
    assert!(
        call(&[
            "ingest-file",
            "--repo",
            r,
            "--name",
            "snap-1",
            "--file",
            i,
            "--experimental",
            "--allow-local"
        ])
        .status
        .success()
    );
    assert!(
        call(&["verify", "--repo", r, "--name", "snap-1"])
            .status
            .success()
    );
    assert!(
        call(&[
            "recover-file",
            "--repo",
            r,
            "--name",
            "snap-1",
            "--output",
            o
        ])
        .status
        .success()
    );
    assert_eq!(
        std::fs::read(&input).unwrap(),
        std::fs::read(&output).unwrap()
    );
    assert!(
        !call(&[
            "recover-file",
            "--repo",
            r,
            "--name",
            "snap-1",
            "--output",
            o
        ])
        .status
        .success()
    );
}
#[test]
fn cli_never_sends_live_non_btrfs_dir_as_snapshot() {
    let tmp = TempDir::new().unwrap();
    let repo = tmp.path().join("repo");
    std::fs::create_dir(&repo).unwrap();
    let r = repo.to_str().unwrap();
    assert!(
        call(&["init", "--repo", r, "--allow-local"])
            .status
            .success()
    );
    let bad = call(&[
        "send",
        "--repo",
        r,
        "--name",
        "snap-live",
        "--snapshot",
        tmp.path().to_str().unwrap(),
        "--experimental",
        "--allow-local",
        "--retries",
        "0",
    ]);
    assert!(!bad.status.success());
    assert!(!repo.join("manifests/snap-live.json").exists());
}
#[test]
fn cli_refuses_missing_repository_and_invalid_names() {
    let tmp = TempDir::new().unwrap();
    let r = tmp.path().to_str().unwrap();
    assert!(
        !call(&["verify", "--repo", r, "--name", "../unsafe"])
            .status
            .success()
    );
    assert!(
        !call(&["verify", "--repo", r, "--name", "missing"])
            .status
            .success()
    );
}

#[test]
fn incremental_send_requires_parent_archive_reference_before_source_checks() {
    let temp = TempDir::new().unwrap();
    let root = temp.path().join("repo");
    std::fs::create_dir(&root).unwrap();
    let r = root.to_str().unwrap();
    assert!(
        call(&["init", "--repo", r, "--allow-local"])
            .status
            .success()
    );
    let attempt = call(&[
        "send",
        "--repo",
        r,
        "--name",
        "child",
        "--snapshot",
        r,
        "--parent",
        r,
        "--experimental",
        "--allow-local",
        "--retries",
        "0",
    ]);
    assert!(!attempt.status.success());
    assert!(
        String::from_utf8_lossy(&attempt.stderr).contains("parent-archive"),
        "expected explicit parent archive error, got {}",
        String::from_utf8_lossy(&attempt.stderr)
    );
}

#[test]
fn receive_preview_reports_verified_chain_without_writing_staging() {
    use harbor_transport::cas::{Repository, SnapshotIdentity};
    use std::io::Cursor;
    use uuid::Uuid;
    let temp = TempDir::new().unwrap();
    let repo_path = temp.path().join("repo");
    let staging = temp.path().join("staging");
    std::fs::create_dir(&repo_path).unwrap();
    std::fs::create_dir(&staging).unwrap();
    let repo = Repository::initialize(&repo_path).unwrap();
    let base_uuid = Uuid::new_v4();
    repo.ingest_snapshot(
        "base",
        Cursor::new(b"base"),
        || true,
        SnapshotIdentity {
            source_uuid: base_uuid,
            parent_uuid: None,
            parent_archive: None,
            protocol: 2,
        },
    )
    .unwrap();
    repo.ingest_snapshot(
        "child",
        Cursor::new(b"incremental"),
        || true,
        SnapshotIdentity {
            source_uuid: Uuid::new_v4(),
            parent_uuid: Some(base_uuid),
            parent_archive: Some("base".to_string()),
            protocol: 2,
        },
    )
    .unwrap();
    let output = call(&[
        "receive",
        "--repo",
        repo_path.to_str().unwrap(),
        "--name",
        "child",
        "--staging",
        staging.to_str().unwrap(),
        "--preview",
    ]);
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let data: serde_json::Value = serde_json::from_slice(&output.stdout).unwrap();
    assert_eq!(data["chain"], serde_json::json!(["base", "child"]));
    assert!(staging.read_dir().unwrap().next().is_none());
    let invalid = call(&[
        "receive",
        "--repo",
        repo_path.to_str().unwrap(),
        "--name",
        "child",
        "--staging",
        staging.to_str().unwrap(),
        "--confirm",
    ]);
    assert!(
        !invalid.status.success(),
        "non-Btrfs recovery destination should be refused"
    );
    assert!(staging.read_dir().unwrap().next().is_none());
}

#[test]
fn native_btrfs_stream_validation_refuses_synthetic_bytes() {
    let tmp = TempDir::new().unwrap();
    let root = tmp.path().join("repo");
    std::fs::create_dir(&root).unwrap();
    let source = tmp.path().join("fake");
    std::fs::write(&source, b"not-a-btrfs-send-stream").unwrap();
    let r = root.to_str().unwrap();
    assert!(
        call(&["init", "--repo", r, "--allow-local"])
            .status
            .success()
    );
    assert!(
        call(&[
            "ingest-file",
            "--repo",
            r,
            "--name",
            "fake",
            "--file",
            source.to_str().unwrap(),
            "--experimental",
            "--allow-local"
        ])
        .status
        .success()
    );
    assert!(
        call(&["verify", "--repo", r, "--name", "fake"])
            .status
            .success()
    );
    let native = call(&["verify-stream", "--repo", r, "--name", "fake"]);
    assert!(!native.status.success());
    let error = String::from_utf8_lossy(&native.stderr);
    assert!(
        error.contains("Btrfs stream is invalid"),
        "unexpected error: {error}"
    );
}

#[test]
fn list_cas_archives_is_json_and_does_not_modify_repository() {
    let tmp = TempDir::new().unwrap();
    let root = tmp.path().join("repo");
    std::fs::create_dir(&root).unwrap();
    let archive = tmp.path().join("payload.send");
    std::fs::write(&archive, b"synthetic").unwrap();
    let r = root.to_str().unwrap();
    assert!(
        call(&["init", "--repo", r, "--allow-local"])
            .status
            .success()
    );
    assert!(
        call(&[
            "ingest-file",
            "--repo",
            r,
            "--name",
            "snap-home-2",
            "--file",
            archive.to_str().unwrap(),
            "--experimental",
            "--allow-local"
        ])
        .status
        .success()
    );
    let listed = call(&["list", "--repo", r]);
    assert!(
        listed.status.success(),
        "{}",
        String::from_utf8_lossy(&listed.stderr)
    );
    let data: serde_json::Value = serde_json::from_slice(&listed.stdout).unwrap();
    assert_eq!(data.as_array().unwrap().len(), 1);
    assert_eq!(data[0]["name"], "snap-home-2");
    assert_eq!(data[0]["raw_size"], 9);
    assert_eq!(data[0]["source_uuid"], serde_json::Value::Null);
    assert!(!root.join("manifests/.tmp").exists());
}
