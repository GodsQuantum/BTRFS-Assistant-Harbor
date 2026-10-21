use harbor_transport::cas::{Repository, SnapshotIdentity};
use std::io::Cursor;
use tempfile::TempDir;
use uuid::Uuid;

fn machine(machine: &str, archive: &str) -> String {
    Repository::machine_archive_id(machine, archive).unwrap()
}

fn fixture() -> Vec<u8> {
    let mut x = 0xC0FFEE123456789_u64;
    (0..6 * 1024 * 1024)
        .map(|_| {
            x ^= x << 13;
            x ^= x >> 7;
            x ^= x << 17;
            (x >> 33) as u8
        })
        .collect()
}

fn full(uuid: Uuid) -> SnapshotIdentity {
    SnapshotIdentity {
        source_uuid: uuid,
        parent_uuid: None,
        parent_archive: None,
        protocol: 2,
    }
}

#[test]
fn two_machines_share_one_pool_and_prune_preserves_other_machine() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let input = fixture();
    let pegasus = machine("Pegasus", "root-snap42-20261021T020000Z");
    let galactica = machine("Galactica", "home-snap17-20261021T020001Z");
    let p = repo.ingest(&pegasus, Cursor::new(&input), || true).unwrap();
    let g = repo
        .ingest(&galactica, Cursor::new(&input), || true)
        .unwrap();
    assert!(p.new_objects > 0);
    assert_eq!(
        g.new_objects, 0,
        "identical remote bytes must not create another pool"
    );
    assert!(g.reused_objects > 0);
    assert!(
        temp.path()
            .join("machines/Pegasus/manifests/root-snap42-20261021T020000Z.json")
            .is_file()
    );
    assert!(
        temp.path()
            .join("machines/Galactica/manifests/home-snap17-20261021T020001Z.json")
            .is_file()
    );
    assert!(!temp.path().join("machines/Pegasus/objects").exists());
    assert!(!temp.path().join("machines/Galactica/objects").exists());
    assert_eq!(repo.list_archives().unwrap().len(), 2);
    let plan = repo.gc_preview(std::slice::from_ref(&pegasus)).unwrap();
    assert_eq!(
        plan.orphan_objects, 0,
        "Galactica must retain every shared chunk"
    );
    repo.gc_confirm(std::slice::from_ref(&pegasus), &plan.plan_sha256)
        .unwrap();
    assert!(!repo.manifest_exists(&pegasus));
    assert_eq!(repo.verify(&galactica).unwrap(), input.len() as u64);
    let mut restored = Vec::new();
    repo.recover_into(&galactica, &mut restored).unwrap();
    assert_eq!(restored, input);
    let empty = repo.gc_preview(&[galactica]).unwrap();
    assert!(empty.orphan_objects > 0);
}

#[test]
fn independently_versioned_incrementals_and_retention() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let input = fixture();
    let p0 = machine("Pegasus", "root-snap1-20261021T010000Z");
    let p1 = machine("Pegasus", "root-snap2-20261021T020000Z");
    let g0 = machine("Galactica", "home-snap1-20261021T010000Z");
    let u0 = Uuid::new_v4();
    let u1 = Uuid::new_v4();
    let gu = Uuid::new_v4();
    repo.ingest_snapshot(&p0, Cursor::new(&input), || true, full(u0))
        .unwrap();
    let mut delta = b"incremental change".repeat(100);
    delta.extend_from_slice(&input);
    repo.ingest_snapshot(
        &p1,
        Cursor::new(&delta),
        || true,
        SnapshotIdentity {
            source_uuid: u1,
            parent_uuid: Some(u0),
            parent_archive: Some(p0.clone()),
            protocol: 2,
        },
    )
    .unwrap();
    let g_stats = repo
        .ingest_snapshot(&g0, Cursor::new(&input), || true, full(gu))
        .unwrap();
    assert_eq!(g_stats.new_objects, 0);
    assert!(g_stats.reused_objects > 0);
    assert_eq!(
        repo.verified_restore_chain(&p1).unwrap(),
        vec![p0.clone(), p1.clone()]
    );
    assert!(
        repo.gc_preview(std::slice::from_ref(&p0)).is_err(),
        "retained incremental requires base"
    );
    let parent_cross = machine("Galactica", "wrong-snap2");
    assert!(
        repo.ingest_snapshot(
            &parent_cross,
            Cursor::new(b"x"),
            || true,
            SnapshotIdentity {
                source_uuid: Uuid::new_v4(),
                parent_uuid: Some(u0),
                parent_archive: Some(p0.clone()),
                protocol: 2
            }
        )
        .is_err(),
        "cross-machine incremental must be rejected"
    );
    let plan = repo.gc_preview(&[p0.clone(), p1.clone()]).unwrap();
    assert_eq!(plan.retain_archives, vec![g0.clone()]);
    repo.gc_confirm(&[p0.clone(), p1.clone()], &plan.plan_sha256)
        .unwrap();
    assert_eq!(repo.verify(&g0).unwrap(), input.len() as u64);
    let mut restored = Vec::new();
    repo.recover_into(&g0, &mut restored).unwrap();
    assert_eq!(restored, input);
}

#[test]
fn legacy_names_with_double_underscore_remain_unchanged() {
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let old_name = "Pegasus__snapshot";
    repo.ingest(old_name, Cursor::new(b"old stream"), || true)
        .unwrap();
    assert!(
        temp.path()
            .join("manifests/Pegasus__snapshot.json")
            .exists()
    );
    assert!(!temp.path().join("machines").exists());
    let reopen = Repository::open(temp.path()).unwrap();
    assert_eq!(reopen.verify(old_name).unwrap(), 10);
    assert_eq!(reopen.list_archives().unwrap()[0].name, old_name);
    assert!(Repository::machine_archive_id("a/b", "root").is_err());
    assert!(Repository::machine_archive_id("Pegasus", "../escape").is_err());
}

#[cfg(unix)]
#[test]
fn refuse_symlinked_machine_manifests_before_restore_or_gc() {
    use std::os::unix::fs::symlink;
    let temp = TempDir::new().unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let name = machine("Pegasus", "root-snap1");
    repo.ingest(&name, Cursor::new(b"safe data"), || true)
        .unwrap();
    let manifest = temp.path().join("machines/Pegasus/manifests");
    let original = temp.path().join("machines/Pegasus/original-manifests");
    std::fs::rename(&manifest, &original).unwrap();
    symlink(&original, &manifest).unwrap();
    assert!(
        repo.verify(&name).is_err(),
        "restore must not follow machine manifest symlinks"
    );
    assert!(
        repo.gc_preview(&[]).is_err(),
        "GC must fail closed for a symlinked machine"
    );
    assert!(repo.gc_preview(&[name]).is_err());
}

#[cfg(unix)]
#[test]
fn concurrent_machine_directory_symlink_swaps_never_escape_repository() {
    use std::os::unix::fs::symlink;
    use std::sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    };
    let temp = TempDir::new().unwrap();
    let outside = TempDir::new().unwrap();
    let bait = outside.path().join("outside.json");
    std::fs::write(&bait, b"OUTSIDE_SENTINEL_UNTOUCHED").unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let archive = machine("Pegasus", "root-42");
    let data = fixture();
    repo.ingest(&archive, Cursor::new(&data), || true).unwrap();
    let dir = temp.path().join("machines/Pegasus/manifests");
    let parked = temp.path().join("machines/Pegasus/parked-manifests");
    let running = Arc::new(AtomicBool::new(true));
    let signal = running.clone();
    let outside_path = outside.path().to_path_buf();
    let attacker = std::thread::spawn(move || {
        while signal.load(Ordering::Relaxed) {
            std::fs::rename(&dir, &parked).unwrap();
            symlink(&outside_path, &dir).unwrap();
            std::thread::yield_now();
            std::fs::remove_file(&dir).unwrap();
            std::fs::rename(&parked, &dir).unwrap();
            std::thread::yield_now();
        }
    });
    for _ in 0..100 {
        let _ = repo.verify(&archive); // missing/symlinked parent may fail closed
        let _ = repo.gc_preview(&[]); // never confirm a plan during this attack
        std::thread::yield_now();
    }
    running.store(false, Ordering::Relaxed);
    attacker.join().unwrap();
    assert_eq!(std::fs::read(&bait).unwrap(), b"OUTSIDE_SENTINEL_UNTOUCHED");
    assert_eq!(repo.verify(&archive).unwrap(), data.len() as u64);
    let mut restored = Vec::new();
    repo.recover_into(&archive, &mut restored).unwrap();
    assert_eq!(restored, data);
}

#[cfg(unix)]
#[test]
fn concurrent_object_prefix_symlink_swaps_do_not_escape_cas_pool() {
    use std::os::unix::fs::symlink;
    use std::sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
    };
    let temp = TempDir::new().unwrap();
    let outside = TempDir::new().unwrap();
    let bait = outside.path().join("outside.zst");
    std::fs::write(&bait, b"NO_CAS_DELETION_OUTSIDE_REPOSITORY").unwrap();
    let repo = Repository::initialize(temp.path()).unwrap();
    let name = machine("Pegasus", "protected");
    let data = fixture();
    repo.ingest(&name, Cursor::new(&data), || true).unwrap();
    let objects = temp.path().join("objects");
    let prefix = std::fs::read_dir(&objects)
        .unwrap()
        .next()
        .unwrap()
        .unwrap()
        .path();
    let parked = objects.join("parked-prefix");
    let running = Arc::new(AtomicBool::new(true));
    let signal = running.clone();
    let outside_path = outside.path().to_path_buf();
    let attacker = std::thread::spawn(move || {
        while signal.load(Ordering::Relaxed) {
            std::fs::rename(&prefix, &parked).unwrap();
            symlink(&outside_path, &prefix).unwrap();
            std::thread::yield_now();
            std::fs::remove_file(&prefix).unwrap();
            std::fs::rename(&parked, &prefix).unwrap();
        }
    });
    for _ in 0..100 {
        let _ = repo.gc_preview(&[]);
        let _ = repo.verify(&name);
        std::thread::yield_now();
    }
    running.store(false, Ordering::Relaxed);
    attacker.join().unwrap();
    assert_eq!(
        std::fs::read(&bait).unwrap(),
        b"NO_CAS_DELETION_OUTSIDE_REPOSITORY"
    );
    assert_eq!(repo.verify(&name).unwrap(), data.len() as u64);
    let mut recovered = Vec::new();
    repo.recover_into(&name, &mut recovered).unwrap();
    assert_eq!(recovered, data);
}
