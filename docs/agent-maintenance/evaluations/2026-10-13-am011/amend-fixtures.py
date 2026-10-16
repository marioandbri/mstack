import datetime, hashlib, json, pathlib, shutil
r=pathlib.Path('/Users/mario.brito/.local/share/mstack-evals/agents/20261013T131918Z-am011')
ids=[f'{case}-{profile}' for case in ['04-interview-gap','05-interview-closed'] for profile in ['A','B']]
assert all(not (r/ident).exists() for ident in ids), 'Never amend an exposed case'
manifest=json.loads((r/'manifest.json').read_text())
shutil.copy2(r/'manifest.json',r/'manifest-before-amendment.json')
# Remove contradictory pre-approved spec from both checkout copies and their Git baseline.
# Rebuild only these unexposed fixtures using the same runner setup, then remove the spec
# through a local baseline commit. Both profiles get identical task contents.
import subprocess
for ident in ids:
 ws=r/'workspaces'/ident
 subprocess.run(['docker','run','--rm','--platform','linux/amd64','--network','none','--mount',f'type=bind,src={ws},dst=/workspace',manifest['image'],'sh','-c','cd /workspace/repo && git rm docs/spec.md && git commit -m "Fixture: interview has no approved spec" && cd /workspace/task && git merge --ff-only main && cd /workspace/other && git merge --ff-only main'],check=True,stdout=subprocess.DEVNULL)
 manifest['fixtureHashes'][ident]={str(p.relative_to(ws)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ws.rglob('*')) if p.is_file() and not p.is_symlink()}
amendment={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reason':'Shared fixture wrongly included approved spec for interviews whose route is unresolved. Removed before any exposure to these four sessions. No model calls or retries.','cases':ids,'scriptHash':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()}
manifest['preExposureAmendment']=amendment
(r/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(r/'fixture-amendment.json').write_text(json.dumps(amendment,ensure_ascii=False,indent=2)+'\n')
shutil.copy2(__file__,r/'amend-fixtures.py')
print('Amended 4 unexposed fixtures identically; original manifest retained.')
