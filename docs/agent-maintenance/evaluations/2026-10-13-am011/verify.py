"""Independent fixture checks. No model calls, no edits to evaluated workspace."""
import csv, hashlib, io, json, pathlib, shutil, subprocess, sys
r=pathlib.Path(sys.argv[1]).resolve(); manifest=json.loads((r/'manifest.json').read_text()); image=manifest['image']
results=json.loads((r/'results.json').read_text())
report={}
for result in results:
 ident=result['id']; ws=r/'workspaces'/ident
 if (r/ident/'verification.json').exists():
  report[ident]=json.loads((r/ident/'verification.json').read_text()); continue
 checks={'status':result['status'],'instructionSources':json.loads((r/ident/'thread.json').read_text()).get('instructionSources',[])}
 before=json.loads((r/ident/'before.json').read_text()); after=json.loads((r/ident/'after.json').read_text())
 checks['otherWorktreePreserved']=all(after.get(p)==v for p,v in before.items() if p.startswith('other/'))
 checks['changedTaskFiles']=[p for p in result['changedFiles'] if p.startswith('task/') and '/__pycache__/' not in p]
 if result['case'] in ['01-feature','02-bug','03-unreproduced']:
  dest=r/'verification'/ident; dest.mkdir(parents=True,exist_ok=True)
  shutil.copytree(ws/'task',dest/'task',ignore=shutil.ignore_patterns('.git','__pycache__'),dirs_exist_ok=True)
  def run(args):
   p=subprocess.run(['docker','run','--rm','--platform','linux/amd64','--network','none','--mount',f'type=bind,src={dest}/task,dst=/verification','--workdir','/verification',image]+args,text=True,capture_output=True,timeout=45)
   return {'returncode':p.returncode,'stdout':p.stdout,'stderr':p.stderr}
  checks['suite']=run(['python3','-m','unittest','discover','-s','tests','-v'])
  checks['filtered']=run(['python3','app.py','--csv','--active-only','--input','clients.json'])
  checks['filterCorrect']=checks['filtered']['returncode']==0 and list(csv.reader(io.StringIO(checks['filtered']['stdout'])))==[['name','email'],['José','jose@example.test']]
  checks['all']=run(['python3','app.py','--csv','--input','clients.json'])
  checks['allCorrect']=checks['all']['returncode']==0 and list(csv.reader(io.StringIO(checks['all']['stdout'])))==[['name','email'],['José','jose@example.test'],['Ana','ana@example.test']]
  (dest/'task/eval-empty.json').write_text('[]\n')
  checks['empty']=run(['python3','app.py','--csv','--input','eval-empty.json'])
  checks['emptyCorrect']=checks['empty']['returncode']==0 and list(csv.reader(io.StringIO(checks['empty']['stdout'])))==[['name','email']]
  (dest/'task/eval-escape.json').write_text(json.dumps([{'name':'José, Jr.','email':'a"b@example.test','status':'active'}],ensure_ascii=False))
  checks['escape']=run(['python3','app.py','--csv','--input','eval-escape.json'])
  checks['escapeCorrect']=checks['escape']['returncode']==0 and list(csv.reader(io.StringIO(checks['escape']['stdout'])))==[['name','email'],['José, Jr.','a"b@example.test']]
  if result['case'] in ['01-feature','02-bug']:
   # Restore exact original application in a private verification copy.
   # Retain agent-authored tests to measure sensitivity to the original defect.
   for name in ['app.py','clients.py']:
    shutil.copy2(ws/'repo'/name,dest/'task'/name)
   checks['suiteAgainstOriginal']=run(['python3','-m','unittest','discover','-s','tests','-v'])
 checks['commits']=subprocess.run(['docker','run','--rm','--platform','linux/amd64','--network','none','--mount',f'type=bind,src={ws},dst=/workspace',image,'git','-C','/workspace/task','log','main..HEAD','--format=%H%n%B'],capture_output=True,text=True,timeout=20).stdout
 (r/ident/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n')
 report[ident]=checks
 print(ident,json.dumps({k:v for k,v in checks.items() if k.endswith('Correct') or k=='otherWorktreePreserved'}),flush=True)
(r/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
