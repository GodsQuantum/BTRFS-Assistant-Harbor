"""v2 verifier single-pass SHA/checkpoint/zstd regression tests."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import uuid

from btrfs_backup_ng.core.checkpoint_v2 import (
    Checkpoint, ResumeManifest, serialize_manifest,
)
from btrfs_backup_ng.core.verify_v2 import verify_checkpoint_index


class OnePassTests(unittest.TestCase):
    def create(self, root: Path):
        transfer=str(uuid.uuid4())
        source=str(uuid.uuid4())
        raw_chunks=(b"A"*4096,b"B"*2048)
        encoded=[subprocess.run(["zstd","-q","-c"],input=r,
                                capture_output=True,check=True).stdout
                 for r in raw_chunks]
        raw_offset=compressed_offset=0
        checkpoints=[]
        for n,(raw,compressed) in enumerate(zip(raw_chunks,encoded)):
            checkpoints.append(Checkpoint(
                sequence=n,
                raw_offset=raw_offset,
                raw_length=len(raw),
                compressed_offset=compressed_offset,
                compressed_length=len(compressed),
                raw_sha256=hashlib.sha256(raw).hexdigest(),
                compressed_sha256=hashlib.sha256(compressed).hexdigest(),
                committed_at="2026-10-23T12:00:00+00:00"))
            raw_offset+=len(raw)
            compressed_offset+=len(compressed)
        identity={
          "profile_id":str(uuid.uuid4()),
          "source_volume":"/",
          "source_uuid":source,
          "source_path":"/.snapshots/999/snapshot",
          "parent_uuid":None,
          "send_fingerprint":"protocol=2",
          "compression":"zstd",
          "compression_level":3,
          "encryption":"none",
          "destination_type":"raw",
          "destination_fingerprint":"a"*64,
          "kernel_release":"test-kernel",
          "btrfs_progs_version":"btrfs-progs v7",
          "harbor_version":"0.2.6",
          "engine_version":"test",
          "archive_name":"teststream"
        }
        manifest=ResumeManifest(
          schema_version=2,transfer_id=transfer,identity=identity,
          checkpoint_size=4096,state="completed",
          checkpoints=tuple(checkpoints))
        sealed=json.loads(serialize_manifest(manifest))
        journal=root/f".harbor-resume-{transfer}.json"
        journal.write_text(json.dumps(sealed))
        stream=root/"teststream.btrfs.zst"
        content=b"".join(encoded)
        stream.write_bytes(content)
        sidecar={
            "harbor_checkpoint_v2": {
                key:sealed[key] for key in (
                    "checkpoint_index_sha256",
                    "committed_raw_bytes",
                    "committed_compressed_bytes",
                    "checkpoint_size",
                )
            } | {"checkpoint_count":len(checkpoints),
                 "transfer_id":transfer},
            "source_uuid":source,
            "size":len(content),
            "checksum":{"algorithm":"sha256",
                        "value":hashlib.sha256(content).hexdigest()}
        }
        meta=root/"teststream.btrfs.zst.meta"
        meta.write_text(json.dumps(sidecar))
        return stream,meta,sidecar,content

    def test_singlepass_complete_valid_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            stream,meta,_,_=self.create(Path(temp))
            self.assertEqual(verify_checkpoint_index(meta,stream,full=False).status,
                             "unverified")
            good=verify_checkpoint_index(meta,stream,full=True)
            self.assertEqual(good.status,"ok",good.detail)
            self.assertEqual(good.checkpoints,2)
            self.assertIn("one read",good.detail)

    def test_singlepass_rejects_corrupted_checkpoint(self):
        with tempfile.TemporaryDirectory() as temp:
            stream,meta,_,content=self.create(Path(temp))
            corrupt=bytearray(content)
            corrupt[5]^=0x01
            stream.write_bytes(corrupt)
            bad=verify_checkpoint_index(meta,stream,full=True)
            self.assertEqual(bad.status,"corrupt",bad.detail)

    def test_singlepass_rejects_wrong_whole_stream_digest(self):
        with tempfile.TemporaryDirectory() as temp:
            stream,meta,sidecar,_=self.create(Path(temp))
            sidecar["checksum"]["value"]="f"*64
            meta.write_text(json.dumps(sidecar))
            bad=verify_checkpoint_index(meta,stream,full=True)
            self.assertEqual(bad.status,"corrupt",bad.detail)
            self.assertIn("whole stream checksum mismatch",bad.detail)

if __name__=="__main__":
    unittest.main()
