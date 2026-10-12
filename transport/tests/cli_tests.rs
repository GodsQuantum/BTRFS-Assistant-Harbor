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
