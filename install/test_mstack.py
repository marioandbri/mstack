"""Exercise the real installer against independent Git sources and temporary homes."""
import importlib.metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import mstack
from mstack_fs import InstallError, signature, lock

ROOT = Path(__file__).resolve().parent.parent


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='mstack-install-test-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.repo = self.base / 'source'
        self.home = self.base / 'home'
        self.repo.mkdir()
        self.home.mkdir()
        self.state = self.home / '.local/share/mstack'
        self.roots = {'agents': str(self.home/'.agents'), 'claude': str(self.home/'.claude'),
                      'codex': str(self.home/'.codex'), 'pi': str(self.home/'.pi/agent')}
        self.manifest = json.loads((ROOT/'mstack.json').read_text())
        self.manifest['runtime'] = {'python': sys.version.split()[0], 'tomlkit': importlib.metadata.version('tomlkit')}
        self.write('mstack.json', json.dumps(self.manifest))
        self.write('skills.json', json.dumps({'targets': list(self.roots), 'skills': [{'name': 'code-review'}, {'name': 'unslop'}]}))
        self.write('instructions/global/AGENTS.md', 'Frozen fixture instructions.\n')
        self.write('config/codex/defaults.toml', 'model = "after"\nmodel_reasoning_effort = "high"\n')
        self.write('config/pi/defaults.json', json.dumps({'defaultProvider':'openai-codex', 'defaultModel':'after', 'defaultThinkingLevel':'high'}))
        self.write('config/claude/CLAUDE.md.template', '# Claude instructions\n\nRead global agent instructions at {{globalAgentsPath}}\n')
        for name in ['code-review', 'unslop']:
            self.write('skills/'+name+'/SKILL.md', f'---\nname: {name}\ndescription: Fixture.\n---\nFrozen {name}.\n')
        helper = self.write('skills/code-review/scripts/check.py', 'print("fixture")\n')
        helper.chmod(0o755)
        self.git('init', '-q', '-b', 'main')
        self.commit()
        self.put('.agents/AGENTS.md', 'Original global memory.\n')
        self.put('.claude/CLAUDE.md', 'Original Claude wrapper.\n')
        self.put('.codex/config.toml', '# Keep this comment\nmodel = "before" # Inline comment\nunowned = true\n[profiles.private]\napi_key = "fixture-secret-never-logged"\n')
        self.put('.pi/agent/settings.json', json.dumps({'defaultModel':'before', 'packages':['external-fixture'], 'private':'fixture-secret-never-logged'}))
        for label in ['codex', 'pi']:
            p = Path(self.roots[label])/'AGENTS.md'
            p.symlink_to(self.home/'.agents/AGENTS.md')
        self.put('.agents/skills/code-review/marker.txt', 'preserve directory')
        wrong = self.home/'.claude/skills/unslop'
        wrong.parent.mkdir(parents=True)
        wrong.symlink_to('../missing')
        legacy = self.home/'.codex/skills/code-review'
        legacy.parent.mkdir(parents=True)
        legacy.symlink_to(self.repo/'skills/code-review')

    def write(self, name, text):
        p = self.repo/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def put(self, name, text):
        p = self.home/name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
        return p

    def git(self, *args):
        return subprocess.check_output(['git','-C',str(self.repo),*args], stderr=subprocess.PIPE).decode().strip()

    def commit(self):
        self.git('add', '.')
        self.git('-c','user.name=Fixture','-c','user.email=fixture@example.invalid','-c','commit.gpgsign=false','-c','core.hooksPath=/dev/null','commit','-qm','fixture')
        return self.git('rev-parse','HEAD')

    def run_cli(self, command, *args):
        return subprocess.run([sys.executable,str(ROOT/'install/mstack.py'),command,'--home',str(self.home),'--repo',str(self.repo),*args],cwd=ROOT,capture_output=True,text=True)

    def apply(self):
        result = self.run_cli('setup', '--apply')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('fixture-secret-never-logged', result.stdout+result.stderr)
        return json.loads((self.state/'current.json').read_text())

    def test_fish_dry_run_leaves_home_unchanged(self):
        before = signature(self.home)
        result = subprocess.run(['fish',str(ROOT/'install/setup.fish'),'--home',str(self.home),'--repo',str(self.repo)],capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('MODE dry-run', result.stdout)
        self.assertIn('no files changed', result.stdout)
        self.assertEqual(signature(self.home), before)

    def test_install_is_frozen_and_idempotent_across_all_harnesses(self):
        receipt = self.apply()
        for label, root in self.roots.items():
            for name in ['code-review','unslop']:
                p = Path(root)/'skills'/name
                self.assertTrue(p.is_symlink())
                self.assertEqual(p.resolve(),self.state/'versions'/receipt['commit']/'skills'/name)
        self.assertEqual((self.home/'.agents/AGENTS.md').read_text(), 'Frozen fixture instructions.\n')
        self.assertFalse((self.home/'.agents/AGENTS.md').is_symlink())
        wrapper = (self.home/'.claude/CLAUDE.md').read_text()
        self.assertIn(str(self.home/'.agents/AGENTS.md'), wrapper)
        helper=self.state/'active/skills/code-review/scripts/check.py'
        self.assertEqual(helper.stat().st_mode & 0o777,0o555)
        before = signature(self.home)
        second = self.run_cli('setup','--apply')
        self.assertEqual(second.returncode,0,second.stderr)
        self.assertIn('unchanged',second.stdout)
        self.assertEqual(signature(self.home),before)
        self.write('skills/code-review/SKILL.md','Uncommitted development edit.\n')
        self.assertIn('Frozen code-review.', (self.home/'.codex/skills/code-review/SKILL.md').read_text())
        self.assertEqual(self.run_cli('verify').returncode,0)

    def test_backup_parent_and_generation_are_private(self):
        receipt = self.apply()
        for directory in (self.state, self.state/'backups', self.state/'receipts',
                          self.state/'backups'/receipt['generation']):
            self.assertEqual(directory.stat().st_mode & 0o777, 0o700, directory.name)
        self.assertEqual((self.state/'current.json').stat().st_mode & 0o777, 0o600)

    def test_shared_configuration_keeps_unowned_values_and_toml_comments(self):
        self.apply()
        text=(self.home/'.codex/config.toml').read_text()
        self.assertIn('# Keep this comment',text)
        self.assertIn('# Inline comment',text)
        self.assertIn('fixture-secret-never-logged',text)
        self.assertIn('unowned = true',text)
        doc=json.loads((self.home/'.pi/agent/settings.json').read_text())
        self.assertEqual(doc['packages'],['external-fixture'])
        self.assertEqual(doc['private'],'fixture-secret-never-logged')
        self.assertEqual(doc['defaultModel'],'after')

    def test_upgrade_and_rollback_use_commits_not_the_working_tree(self):
        original=self.apply()
        self.write('instructions/global/AGENTS.md','Second approved fixture.\n')
        self.write('skills/unslop/SKILL.md','Second skill version.\n')
        second_commit=self.commit()
        self.assertEqual(self.run_cli('verify').returncode,0)
        self.assertIn('Frozen unslop.', (self.home/'.pi/agent/skills/unslop/SKILL.md').read_text())
        self.assertEqual(self.apply()['commit'],second_commit)
        self.assertEqual((self.home/'.agents/AGENTS.md').read_text(),'Second approved fixture.\n')
        dry=self.run_cli('rollback')
        self.assertEqual(dry.returncode,0,dry.stderr)
        result=self.run_cli('rollback','--apply')
        self.assertEqual(result.returncode,0,result.stderr)
        restored=json.loads((self.state/'current.json').read_text())
        self.assertEqual(restored['generation'],original['generation'])
        self.assertEqual((self.home/'.agents/AGENTS.md').read_text(),'Frozen fixture instructions.\n')
        self.assertIn('Frozen unslop.', (self.home/'.pi/agent/skills/unslop/SKILL.md').read_text())
        self.assertEqual(self.run_cli('verify').returncode,0)

    def test_rollback_preserves_later_unowned_configuration_changes(self):
        self.apply()
        config=self.home/'.pi/agent/settings.json'
        doc=json.loads(config.read_text());doc['packages'].append('added-later');config.write_text(json.dumps(doc))
        codex=self.home/'.codex/config.toml'
        codex.write_text(codex.read_text()+'\n[profiles.new]\nvalue = "retain me"\n')
        self.assertEqual(self.run_cli('verify').returncode,0)
        result=self.run_cli('rollback','--apply')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.home/'.agents/AGENTS.md').read_text(),'Original global memory.\n')
        self.assertEqual((self.home/'.agents/skills/code-review/marker.txt').read_text(),'preserve directory')
        self.assertEqual(os.readlink(self.home/'.claude/skills/unslop'),'../missing')
        restored=json.loads(config.read_text())
        self.assertEqual(restored['defaultModel'],'before')
        self.assertNotIn('defaultProvider',restored)
        self.assertEqual(restored['packages'],['external-fixture','added-later'])
        self.assertIn('retain me',codex.read_text())
        self.assertIn('model = "before"',codex.read_text())

    def test_local_global_memory_edits_block_updates_and_rollback(self):
        self.apply()
        path=self.home/'.agents/AGENTS.md';path.write_text('Local curated memory.\n')
        for command,args in [('verify',()),('setup',('--apply',)),('rollback',('--apply',))]:
            result=self.run_cli(command,*args)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('drift',result.stderr)
            self.assertEqual(path.read_text(),'Local curated memory.\n')

    def test_snapshot_tampering_blocks_verification_and_rollback(self):
        self.apply()
        p=self.state/'active/skills/unslop/SKILL.md'
        p.chmod(0o644);p.write_text('tampered')
        for command,args in [('verify',()),('rollback',('--apply',))]:
            result=self.run_cli(command,*args)
            self.assertNotEqual(result.returncode,0)
            self.assertIn('Snapshot content drift',result.stderr)

    def test_duplicate_and_upstream_ownership_are_detected(self):
        self.apply()
        self.put('.agents/skills/legacy/skills/unslop/SKILL.md','duplicate')
        result=self.run_cli('verify');self.assertNotEqual(result.returncode,0);self.assertIn('Duplicate managed skill',result.stderr)
        shutil.rmtree(self.home/'.agents/skills/legacy')
        self.put('.agents/.skill-lock.json',json.dumps({'skills':{'unslop':{'source':'upstream'}}}))
        result=self.run_cli('verify');self.assertNotEqual(result.returncode,0);self.assertIn('upstream',result.stderr)

    def test_invalid_private_configuration_is_not_echoed_or_modified(self):
        bad=self.put('.codex/config.toml','model = "fixture-secret-never-logged\n')
        before=signature(self.home)
        result=self.run_cli('setup','--apply')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Invalid configuration',result.stderr)
        self.assertNotIn('fixture-secret-never-logged',result.stdout+result.stderr)
        self.assertEqual(signature(self.home),before)
        self.assertTrue(bad.exists())

    def test_tampered_backup_blocks_rollback_before_any_target_changes(self):
        receipt=self.apply()
        a=next(a for a in receipt['actions'] if a['method']=='copy')
        Path(a['backup']).write_text('backup changed')
        pointer=os.readlink(self.state/'active')
        before=(self.home/'.agents/AGENTS.md').read_bytes()
        result=self.run_cli('rollback','--apply')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('backup changed',result.stderr)
        self.assertEqual(os.readlink(self.state/'active'),pointer)
        self.assertEqual((self.home/'.agents/AGENTS.md').read_bytes(),before)

    def test_failed_transaction_restores_original_targets(self):
        original=(self.home/'.agents/AGENTS.md').read_bytes()
        real=mstack.replace_target
        count=0
        def fail(action):
            nonlocal count
            count+=1
            if count==2:
                raise InstallError('Injected operation failure')
            real(action)
        with patch.object(mstack,'replace_target',fail):
            with self.assertRaises(InstallError):
                mstack.setup(self.repo,'HEAD',self.roots,self.state,True)
        self.assertEqual((self.home/'.agents/AGENTS.md').read_bytes(),original)
        self.assertFalse((self.state/'current.json').exists())
        self.assertFalse((self.state/'journal.json').exists())

    def test_recover_finishes_a_crash_after_current_record_was_written(self):
        receipt=self.apply()
        (self.state/'journal.json').write_bytes((self.state/'current.json').read_bytes())
        self.assertNotEqual(self.run_cli('verify').returncode,0)
        result=self.run_cli('recover','--apply')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertFalse((self.state/'journal.json').exists())
        self.assertFalse((self.state/'current.json').exists())
        self.assertEqual((self.home/'.agents/AGENTS.md').read_text(),'Original global memory.\n')

    def test_override_is_detected_without_home_changes(self):
        self.put('.codex/AGENTS.override.md','User override')
        before=signature(self.home)
        result=self.run_cli('setup','--apply')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('override',result.stderr)
        self.assertEqual(signature(self.home),before)

    def test_explicit_home_ignores_ambient_agent_directories(self):
        elsewhere=self.base/'untouched';elsewhere.mkdir()
        env=dict(os.environ,CODEX_HOME=str(elsewhere),PI_CODING_AGENT_DIR=str(elsewhere),CLAUDE_CONFIG_DIR=str(elsewhere))
        result=subprocess.run([sys.executable,str(ROOT/'install/mstack.py'),'setup','--home',str(self.home),'--repo',str(self.repo),'--apply'],cwd=ROOT,capture_output=True,text=True,env=env)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(list(elsewhere.iterdir()),[])


    def test_concurrent_install_is_rejected_without_target_changes(self):
        original=(self.home/'.agents/AGENTS.md').read_bytes()
        with lock(self.state):
            result=self.run_cli('setup','--apply')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('Another mstack operation',result.stderr)
        self.assertEqual((self.home/'.agents/AGENTS.md').read_bytes(),original)
        self.assertFalse((self.state/'current.json').exists())

    def test_commit_with_managed_symlink_is_rejected(self):
        path=self.repo/'skills/unslop/SKILL.md'
        path.unlink();path.symlink_to('/private/unknown-reference')
        self.commit()
        before=signature(self.home)
        result=self.run_cli('setup','--apply')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('regular files',result.stderr)
        self.assertEqual(signature(self.home),before)

    def test_traversal_in_target_manifest_is_rejected(self):
        self.manifest['managed'][0]['target']='agents/../../escape'
        self.write('mstack.json',json.dumps(self.manifest));self.commit()
        before=signature(self.home)
        result=self.run_cli('setup','--apply')
        self.assertNotEqual(result.returncode,0)
        self.assertEqual(signature(self.home),before)

    def test_changed_legacy_source_stops_initial_rollback(self):
        self.apply()
        self.write('skills/code-review/SKILL.md','New uncommitted candidate.\n')
        before=(self.home/'.agents/AGENTS.md').read_bytes()
        result=self.run_cli('rollback','--apply')
        self.assertNotEqual(result.returncode,0)
        self.assertIn('original mutable skill source changed',result.stderr)
        self.assertEqual((self.home/'.agents/AGENTS.md').read_bytes(),before)


    def test_candidate_snapshot_does_not_activate_or_modify_targets(self):
        receipt=self.apply()
        self.write('skills/unslop/SKILL.md','Candidate only.\n')
        commit=self.commit()
        before=(self.home/'.pi/agent/skills/unslop/SKILL.md').read_text()
        result=self.run_cli('snapshot','--apply')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((self.state/'versions'/commit/'skills/unslop/SKILL.md').read_text(),'Candidate only.\n')
        self.assertEqual((self.home/'.pi/agent/skills/unslop/SKILL.md').read_text(),before)
        self.assertEqual(json.loads((self.state/'current.json').read_text())['generation'],receipt['generation'])
        self.assertEqual(self.run_cli('verify').returncode,0)

    def test_repository_defaults_contain_only_supported_owned_keys(self):
        from mstack_config import OWNED_KEYS, owned_defaults
        manifest=json.loads((ROOT/'mstack.json').read_text())
        for entry in manifest['managed']:
            if entry['method'].endswith('-keys'):
                self.assertEqual(tuple(entry['keys']),OWNED_KEYS[entry['target']])
                values=owned_defaults((ROOT/entry['source']).read_bytes(),entry['keys'],entry['method'])
                self.assertEqual(set(values),set(OWNED_KEYS[entry['target']]))


if __name__=='__main__':
    unittest.main()
