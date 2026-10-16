"""One explicitly authorized supplemental turn; preserve the original trial."""
import datetime, importlib.util, json, os, pathlib, re, shutil, subprocess, tempfile
ORIGINAL=pathlib.Path('/Users/mario.brito/.local/share/mstack-evals/agents/20261013T131918Z-am011')
RUN=ORIGINAL/'supplement-03B'
spec=importlib.util.spec_from_file_location('frozen_runner',ORIGINAL/'runner.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
manifest=json.loads((ORIGINAL/'manifest.json').read_text()); ident='03-unreproduced-B'
assert not RUN.exists(), 'Only one additional attempt is authorized'
assert m.digest(ORIGINAL/'runner.py')==manifest['runnerHash']
assert m.digest(m.REPO/'evals/deepswe/auth_state.py')==manifest['authHelperHash']
assert m.hashes(ORIGINAL/'profiles/B')==manifest['profiles']['B']['hashes']
assert m.hashes(ORIGINAL/'workspaces'/ident)==manifest['fixtureHashes'][ident], 'Original fixture must still be pristine'
assert m.docker(['image','inspect',m.IMAGE,'--format','{{.Id}}']).strip()==manifest['image']
state=m.command(['/usr/sbin/ioreg','-r','-k','AppleClamshellState','-d','4'])
assert not re.search(r'"AppleClamshellState" = Yes',state), 'Keep lid open'
m.validate_auth(m.AUTH)
with m.auth_lock(m.AUTH):
 RUN.mkdir(mode=0o700)
 shutil.copy2(__file__,RUN/'supplement.py')
 shutil.copytree(ORIGINAL/'profiles/B',RUN/'profiles/B')
 shutil.copytree(ORIGINAL/'workspaces'/ident,RUN/'workspaces'/ident)
 assert m.hashes(RUN/'workspaces'/ident)==manifest['fixtureHashes'][ident]
 case=next(c for c in manifest['cases'] if c['id']=='03-unreproduced')
 supplemental={'model':m.MODEL,'effort':'high','cli':manifest['cli'],'image':m.IMAGE,'candidateCommit':manifest['candidateCommit'],'profiles':{'B':manifest['profiles']['B']},'cases':[case],'steps':[{'id':ident,'case':'03-unreproduced','profile':'B'}],'budgetSecondsPerTurn':180,'maxModelTurns':1,'retries':0,'originalRun':str(ORIGINAL),'originalOutcome':'serverOverloaded','authorization':'Mario: si, ejecuta el adicional faltante','scriptHash':m.digest(pathlib.Path(__file__)),'frozenRunnerHash':manifest['runnerHash'],'fixtureHashes':{ident:manifest['fixtureHashes'][ident]}}
 m.save(RUN/'manifest.json',supplemental); m.RUN=RUN
 original=m.digest(m.AUTH)
 home=pathlib.Path(tempfile.mkdtemp(prefix='.agents-auth-',dir=m.AUTH.parent));os.chmod(home,0o700)
 shutil.copy2(m.AUTH,home/'auth.json');os.chmod(home/'auth.json',0o600)
 (home/'config.toml').write_text('cli_auth_credentials_store = "file"\n[features]\napps = false\n[projects."/workspace/task"]\ntrust_level = "trusted"\n')
 helper=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())])
 try:
  result=m.run_step(supplemental['steps'][0],home)
  m.save(RUN/'results.json',[result])
  if (home/'AGENTS.md').exists():
   shutil.copy2(home/'AGENTS.md',RUN/'temporary-global-after.md')
   m.save(RUN/'global-integrity.json',{'expected':m.digest(RUN/'profiles/B/AGENTS.md'),'after':m.digest(home/'AGENTS.md')})
 finally:
  fd,tmp=tempfile.mkstemp(prefix='.agents-refresh-',dir=m.AUTH.parent);os.close(fd)
  shutil.copyfile(home/'auth.json',tmp);os.chmod(tmp,0o600)
  m.persist_refresh(pathlib.Path(tmp),m.AUTH,original);shutil.rmtree(home)
  helper.terminate();helper.wait(timeout=5)
  print('Benchmark credentials preserved; temporary credential home removed.',flush=True)
 m.save(RUN/'final-profile-hashes.json',{'B':m.hashes(RUN/'profiles/B')})
 m.save(RUN/'execution-ended.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executed':1})
 print('FINISHED '+str(RUN),flush=True)
