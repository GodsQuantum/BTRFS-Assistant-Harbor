use harbor_transport::mount_probe::filesystem_for_path;
use std::path::Path;

const MOUNTS: &str = "25 1 0:25 / / rw - ext4 /dev/sda1 rw\n26 25 0:26 / /mnt/Cloud\\040Backup rw - nfs4 cloud:/backup rw\n27 25 0:27 / /mnt/data rw - btrfs /dev/vdb rw\n";

#[test]
fn probe_resolves_escaped_paths_and_nested_mounts() {
    assert_eq!(
        filesystem_for_path(Path::new("/mnt/Cloud Backup/user"), MOUNTS).unwrap(),
        "nfs4"
    );
    assert_eq!(
        filesystem_for_path(Path::new("/mnt/data/staging"), MOUNTS).unwrap(),
        "btrfs"
    );
    assert_eq!(
        filesystem_for_path(Path::new("/mnt/data-old"), MOUNTS).unwrap(),
        "ext4"
    );
}

#[test]
fn probe_rejects_ambiguous_or_malformed_mountinfo() {
    assert!(filesystem_for_path(Path::new("/tmp"), "").is_err());
    assert!(filesystem_for_path(Path::new("/tmp"), "invalid\n").is_err());
    assert!(filesystem_for_path(Path::new("relative"), MOUNTS).is_err());
}

#[test]
fn probe_selects_deepest_mountpoint_not_first_matching() {
    let mounts = format!("{MOUNTS}28 27 0:28 / /mnt/data/staging rw - nfs4 cloud:/staging rw\n");
    assert_eq!(
        filesystem_for_path(Path::new("/mnt/data/staging/data"), &mounts).unwrap(),
        "nfs4"
    );
}
