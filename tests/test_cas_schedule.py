import json
import unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
from backend import cas_schedule as cas

class CasScheduleTests(unittest.TestCase):
    def setUp(self):
        self.profile=SimpleNamespace(config="root",target="/mnt/backup",
                                     allow_local=False,owner_uid=1000)
        self.snapper={'root':[
            {'number':0,'subvolume':'/','read-only':False},
            {'number':11,'subvolume':'/','read-only':True},
            {'number':12,'subvolume':'/','read-only':True},
            {'number':13,'subvolume':'/','read-only':False},
        ]}
    def test_parses_config_scope_and_excludes_rw(self):
        paths=cas.eligible_snapshots(cas.snapper_rows(self.snapper,'root'))
        self.assertEqual([num for num,_ in paths],[12,11])
        self.assertEqual(str(paths[0][1]),'/.snapshots/12/snapshot')
        with self.assertRaises(ValueError):
            cas.snapper_rows({'not-root':[]},'root')
    def test_source_selection_without_shell_and_with_verified_parent(self):
        def fake(cmd,**kwargs):
            if cmd[0]=='snapper':
                return SimpleNamespace(stdout=json.dumps(self.snapper),returncode=0)
            if cmd[1]=='list':
                return SimpleNamespace(stdout=json.dumps([{'name':'snap-root-11'}]),returncode=0)
            if cmd[1]=='verify-stream':
                return SimpleNamespace(returncode=0)
            raise AssertionError(cmd)
        with patch.object(cas.subprocess,'run',side_effect=fake),patch.object(cas,'is_readonly_snapshot',return_value=True):
            argv=cas.build_send(self.profile)
        self.assertEqual(argv[:3],['harbor-transport','send','--repo'])
        self.assertIn('/.snapshots/12/snapshot',argv)
        self.assertIn('--parent',argv)
        self.assertIn('snap-root-11',argv)
        self.assertNotIn('--allow-local',argv)
    def test_existing_incremental_parent_is_verified_first(self):
        commands=[]
        def fake(cmd,**kwargs):
            commands.append(cmd)
            if cmd[0]=='snapper':
                return SimpleNamespace(stdout=json.dumps(self.snapper),returncode=0)
            if cmd[1]=='list':
                return SimpleNamespace(stdout=json.dumps([{'name':'snap-root-11'}]),returncode=0)
            if cmd[1]=='verify-stream':
                return SimpleNamespace(stdout='',returncode=0)
            raise AssertionError(cmd)
        with patch.object(cas.subprocess,'run',side_effect=fake),patch.object(cas,'is_readonly_snapshot',return_value=True):
            argv=cas.build_send(self.profile)
        self.assertIn('--parent-archive',argv)
        self.assertEqual([cmd[1] for cmd in commands if cmd[0]=='harbor-transport'],
                         ['list','verify-stream'])
        self.assertEqual(commands[-1][-1],'snap-root-11')

    def test_idempotent_completed_backup_must_verify(self):
        def fake(cmd,**kwargs):
            if cmd[0]=='snapper':
                return SimpleNamespace(stdout=json.dumps(self.snapper))
            if cmd[1]=='list':
                return SimpleNamespace(stdout=json.dumps([{'name':'snap-root-12'}]))
            if cmd[1]=='verify-stream':
                return SimpleNamespace(returncode=0)
            raise AssertionError(cmd)
        with patch.object(cas.subprocess,'run',side_effect=fake) as runner,patch.object(cas,'is_readonly_snapshot',return_value=True):
            self.assertIsNone(cas.build_send(self.profile))
        self.assertTrue(any('verify-stream' in call.args[0] for call in runner.call_args_list))
    def test_no_shell_no_ro_snapshot_refused(self):
        with patch.object(cas.subprocess,'run',return_value=SimpleNamespace(stdout=json.dumps(self.snapper))),patch.object(cas,'is_readonly_snapshot',return_value=False):
            with self.assertRaises(RuntimeError):
                cas.build_send(self.profile)
    def test_multi_hour_cas_transfers_are_not_killed_by_python_timeout(self):
        # systemd owns stopping/cancelling jobs, not an arbitrary 7200s
        # Python deadline that makes large first backups impossible.
        with (patch.object(cas, 'build_send',
                           return_value=['harbor-transport', 'send']),
              patch.object(cas.subprocess, 'run',
                           return_value=SimpleNamespace(returncode=0)) as runner):
            self.assertEqual(cas.run_cas_profile(self.profile), 0)
        self.assertNotIn('timeout', runner.call_args.kwargs)

    def test_long_archive_verification_is_not_killed_after_180_seconds(self):
        calls = []
        def fake(command, **kwargs):
            calls.append((command, kwargs))
            if command[0] == 'snapper':
                return SimpleNamespace(stdout=json.dumps(self.snapper), returncode=0)
            if command[1] == 'list':
                return SimpleNamespace(stdout=json.dumps([{'name': 'snap-root-12'}]), returncode=0)
            if command[1] == 'verify-stream':
                return SimpleNamespace(returncode=0)
            raise AssertionError(command)
        with patch.object(cas.subprocess, 'run', side_effect=fake), patch.object(
                cas, 'is_readonly_snapshot', return_value=True):
            self.assertIsNone(cas.build_send(self.profile))
        verified = [kwargs for args, kwargs in calls if 'verify-stream' in args]
        self.assertTrue(verified)
        self.assertTrue(all('timeout' not in kwargs for kwargs in verified))

    def test_run_inherits_authenticated_uid(self):
        with patch.object(cas,'build_send',return_value=['harbor-transport','send','--repo','/mnt/backup']),patch.object(cas.subprocess,'run',return_value=SimpleNamespace(returncode=0)) as run:
            self.assertEqual(cas.run_cas_profile(self.profile),0)
            self.assertEqual(run.call_args.kwargs['env']['PKEXEC_UID'],'1000')
        self.profile.owner_uid=0
        with self.assertRaises(ValueError):
            cas.run_cas_profile(self.profile)
if __name__=='__main__':
    unittest.main()
