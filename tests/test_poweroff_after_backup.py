import json
from pathlib import Path
import tempfile
import unittest
from backend.post_backup import validate_machine_set, EXPECTED

SET_ID="e3a0da68-bc1a-46f8-8ed8-46dd20c1c43c"
class PoweroffValidationTests(unittest.TestCase):
    def test_fails_closed_without_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertFalse(validate_machine_set(Path(tmp), SET_ID)[0])

    def test_rejects_partial_or_wrong_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            p=root/(".harbor-machine-set-"+SET_ID+".json")
            p.write_text(json.dumps({"set_id":SET_ID,"status":"pending","members":[]}))
            self.assertFalse(validate_machine_set(root,SET_ID)[0])
            p.write_text(json.dumps({"set_id":SET_ID,"status":"completed_btrfs_and_boot_files",
                                     "members":[{"original_mount":mount,"status":"completed"}
                                                for mount in EXPECTED]}))
            self.assertFalse(validate_machine_set(root,SET_ID)[0])

    def test_complete_small_fixture(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            members=[]
            for i,mount in enumerate(EXPECTED):
                name="machine20261023T121604-"+SET_ID[:8]+f"-{i:03d}"
                data=f"Btrfs stream {i}".encode()
                (root/(name+".btrfs.zst")).write_bytes(data)
                (root/(name+".btrfs.zst.meta")).write_text(json.dumps({
                  "size":len(data),"checksum":{"algorithm":"sha256",
                  "value":hashlib.sha256(data).hexdigest()}}))
                members.append({"original_mount":mount,"archive":name,
                                "transfer_id":"dummy","status":"completed"})
            boot=b"FAKE BOOT FILE"
            (root/"boot.tar.gz").write_bytes(boot)
            record={"set_id":SET_ID,"status":"completed_btrfs_and_boot_files",
                   "members":members,"boot_members":[{"archive":"boot.tar.gz",
                   "status":"completed","mount_point":"/boot","bytes":len(boot),
                   "sha256":hashlib.sha256(boot).hexdigest()}]}
            (root/(".harbor-machine-set-"+SET_ID+".json")).write_text(json.dumps(record))
            good,_=validate_machine_set(root,SET_ID,verify_boot=True)
            self.assertTrue(good)
            with (root/"boot.tar.gz").open("ab") as f:f.write(b"X")
            self.assertFalse(validate_machine_set(root,SET_ID,verify_boot=True)[0])

if __name__=="__main__":unittest.main()
