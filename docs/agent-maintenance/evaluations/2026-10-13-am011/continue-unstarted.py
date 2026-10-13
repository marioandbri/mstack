"""Continue unstarted slots only. Never retry any prior model turn."""
import datetime, importlib.util, json, os, pathlib, re, shutil, subprocess, sys, tempfile
run=pathlib.Path(sys.argv[1]).resolve()
spec=importlib.util.spec_from_file_location('frozen_runner',run/'runner.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); m.RUN=run
manifest=json.loads((run/'manifest.json').read_text())
results=json.loads((run/'results.json').read_text()); done={r['id'] for r in results}
assert len(done)==len(results) and len(manifest['steps'])==16
remaining=[s for s in manifest['steps'] if s['id'] not in done]
assert remaining and all(not (run/s['id']).exists() for s in remaining)
assert m.digest(run/'runner.py')==manifest['runnerHash']
assert m.digest(m.REPO/'evals/deepswe/auth_state.py')==manifest['authHelperHash']
assert m.docker(['image','inspect',m.IMAGE,'--format','{{.Id}}']).strip()==manifest['image']
for label,p in manifest['profiles'].items(): assert m.hashes(run/'profiles'/label)==p['hashes']
for s in remaining: assert m.hashes(run/'workspaces'/s['id'])==manifest['fixtureHashes'][s['id']]
state=m.command(['/usr/sbin/ioreg','-r','-k','AppleClamshellState','-d','4'])
assert not re.search(r'"AppleClamshellState" = Yes',state)
m.validate_auth(m.AUTH)
receipt=run/'continue-unstarted.json'
assert not receipt.exists(), 'No second continuation automatically'
m.save(receipt,{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'priorTurns':len(results),'remaining':[s['id'] for s in remaining],'reason':'Keep provider-overloaded 03-B inconclusive. Execute only unused authorized slots, same profile/model/budget; stop on another provider failure.','scriptHash':m.digest(pathlib.Path(__file__))})
shutil.copy2(__file__,run/'continue-unstarted.py')
with m.auth_lock(m.AUTH):
 original=m.digest(m.AUTH)
 home=pathlib.Path(tempfile.mkdtemp(prefix='.agents-auth-',dir=m.AUTH.parent)); os.chmod(home,0o700)
 shutil.copy2(m.AUTH,home/'auth.json'); os.chmod(home/'auth.json',0o600)
 (home/'config.toml').write_text('cli_auth_credentials_store = "file"\n[features]\napps = false\n[projects."/workspace/task"]\ntrust_level = "trusted"\n')
 helper=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())])
 try:
  for step in remaining:
   for entry in home.iterdir():
    if entry.name not in ['auth.json','config.toml']:
     if entry.is_dir(): shutil.rmtree(entry)
     else: entry.unlink()
   result=m.run_step(step,home); results.append(result); m.save(run/'results.json',results)
   if result['status'] in ['infrastructure-error','failed']: break
 finally:
  fd,tmp=tempfile.mkstemp(prefix='.agents-refresh-',dir=m.AUTH.parent); os.close(fd)
  shutil.copyfile(home/'auth.json',tmp); os.chmod(tmp,0o600)
  m.persist_refresh(pathlib.Path(tmp),m.AUTH,original); shutil.rmtree(home)
  helper.terminate(); helper.wait(timeout=5)
  print('Benchmark credentials preserved; temporary credential home removed.',flush=True)
m.save(run/'final-profile-hashes.json',{l:m.hashes(run/'profiles'/l) for l in ['A','B']})
m.save(run/'continuation-ended.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'totalTurns':len(results)})
print('FINISHED total='+str(len(results)),flush=True)
