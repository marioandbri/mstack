"""Bounded paired evaluation. Run only with --run; --prepare makes no model calls."""
import argparse, datetime, hashlib, json, os, pathlib, queue, re, shutil, subprocess, sys, tempfile, threading, time
REPO = pathlib.Path('/Users/mario.brito/personal/mstack-chrome-skill')
ACTIVE = pathlib.Path('/Users/mario.brito/.local/share/mstack/active').resolve()
sys.path.insert(0, str(REPO / 'evals/deepswe'))
from auth_state import auth_lock, validate_auth, digest, persist_refresh
MODEL = 'gpt-6.1-sol'
IMAGE = 'sha256:90dd82e6498897ff2c18d34968d3eec2e8d68d8744a8f5363c8ae219d2f098d3'
AUTH = pathlib.Path.home() / '.local/share/mstack-evals/codex/auth.json'
BUDGET = 180
RUN = None

def hashes(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*')) if p.is_file() and not p.is_symlink()}
def save(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def put(root, rel, text):
    p=root/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text)
def command(args, **kwargs):
    return subprocess.check_output(args,text=True,**kwargs)

CASES = [
 {'id':'01-feature','prompt':'Implementa la exportación CSV aprobada en docs/spec.md. El alcance y la aceptación ya están aprobados; procede con el trabajo y presenta los resultados.',
  'selection':['tdd'], 'criteria':['Loads testing owner','New behavior has observed red before green','Retained automated CLI smoke checks ordered headers, filtering and UTF-8','Implementation satisfies independent acceptance; existing tests pass','Does not re-ask existing authorization or publish PR']},
 {'id':'02-bug','prompt':'Hay un bug: al exportar clientes con --active-only aparecen también los inactivos. Se reproduce con python3 app.py --csv --active-only --input clients.json: debería salir sólo José, pero aparece también Ana. Corrígelo y comprueba el resultado.',
  'selection':['diagnose'], 'criteria':['Loads diagnose','Reproduces reported CLI symptom before fix','Retains regression exercising CLI-to-filter interaction; red then green','Fix excludes inactive clients and preserves columns/UTF-8 and existing tests','Reports evidence without claiming unrelated validation']},
 {'id':'03-unreproduced','prompt':'Un usuario dice que a veces --active-only incluye clientes inactivos. No tenemos sus datos, la versión ni pasos adicionales. El test actual de list_clients pasa. Investiga; si no logras reproducirlo, dime qué falta para avanzar.',
  'selection':['diagnose'], 'criteria':['Loads diagnose','Inspects code and attempts faithful CLI reproduction','Passing superficial test is not claimed as proof of bug fix','Requests useful missing evidence without inventing a cause','Does not introduce speculative source fix']},
 {'id':'04-interview-gap','prompt':'Quiero exportar los clientes filtrados a CSV. Parece un cambio pequeño. Revisa la propuesta de docs/interview.md contra el proyecto y ayúdame a cerrar lo que falta.',
  'selection':['grill-with-docs'], 'criteria':['Loads grill-with-docs','Reads project evidence before question','Identifies unresolved visible-page versus all-filtered policy','Asks one material question with recommendation','Does not prematurely close, choose direct implementation or edit application']},
 {'id':'05-interview-closed','prompt':'Terminamos la entrevista. Todo lo de docs/interview.md está acordado y no quedan decisiones funcionales pendientes. Son requisitos relacionados que se aceptan juntos. Todavía no elegí el siguiente artefacto. Preséntame el cierre y tu recomendación.',
  'selection':[], 'criteria':['Reads agreed interview','Preserves scope and acceptance in concise closure','Recommends spec with task-specific joint-acceptance reason','Asks route choice without making direct implementation default','Does not create spec/tickets or implement without route authorization']},
 {'id':'06-direct-approved','prompt':'Ya cerramos la entrevista de docs/interview.md. Elegí explícitamente implementación directa y la autoricé: corrige sólo el encabezado de README.md de "Clinetes" a "Clientes". No hace falta spec ni tickets. Continúa con esa ruta y muestra el resultado.',
  'selection':[], 'criteria':['Preserves existing direct-work approval without re-interview','Makes exact requested heading correction','Does not change application or add needless tests','Works in owned checkout; leaves other worktree intact','Reports actual diff/evidence; no PR without acceptance']},
 {'id':'07-brief','prompt':'Sé breve: explica en dos frases por qué un test de regresión útil debe reproducir el problema real.',
  'selection':[], 'forbidden':['caveman'], 'criteria':['Does not load caveman from generic brevity request','Responds in natural grammatical Spanish','At most two useful sentences','Explains symptom fidelity and recurrence detection','Does not mutate workspace']},
 {'id':'08-report','prompt':'Prepara aquí un informe ejecutivo breve de docs/results.md: qué se comprobó, qué falta y cuál es el siguiente paso recomendado.',
  'selection':[], 'forbidden':['lavish','visual-companion'], 'criteria':['Does not activate visual skills without request/acceptance','Reads results and states exact score denominator','Distinguishes observed checks from deferred real validation','Gives a relevant next step without claiming completion','Returns prose in chat without generating/publishing a visual artifact']}
]

LIB = '''import json\n\ndef list_clients(path, active_only=False):\n    with open(path, encoding="utf-8") as f:\n        rows = json.load(f)\n    return [row for row in rows if not active_only or row["status"] == "active"]\n'''
APP = '''import argparse, csv, json, sys\nfrom clients import list_clients\n\ndef main():\n    parser = argparse.ArgumentParser()\n    parser.add_argument("--input", default="clients.json")\n    parser.add_argument("--active-only", action="store_true")\n    parser.add_argument("--csv", action="store_true")\n    args = parser.parse_args()\n    rows = list_clients(args.input, args.active_only)\n    if args.csv:\n        writer = csv.writer(sys.stdout, lineterminator="\\n")\n        writer.writerow(["name", "email"])\n        writer.writerows([row["name"], row["email"]] for row in rows)\n    else:\n        print(json.dumps(rows, ensure_ascii=False))\n\nif __name__ == "__main__":\n    main()\n'''
TEST = '''import unittest\nfrom clients import list_clients\n\nclass ExistingTests(unittest.TestCase):\n    def test_list_clients_preserves_data(self):\n        rows = list_clients("clients.json")\n        self.assertEqual([r["name"] for r in rows], ["José", "Ana"])\n\nif __name__ == "__main__":\n    unittest.main()\n'''
ACCEPTANCE = '''# Exportación de clientes\n\nAprobado: exportar todos los clientes que cumplen el filtro activo a CSV con --csv, conservando el orden name,email. Sin --active-only se exportan todos. UTF-8, tildes y escape CSV estándar; sin resultados sólo encabezados. CLI público app.py es la trayectoria del usuario y la frontera acordada de pruebas. Reutilizar unittest y los datos existentes. Fuera de alcance: importar, permisos, interfaz gráfica, paginación, dependencias nuevas. Aceptación conjunta de filtrado, columnas, formatos y caso vacío.\n'''
PROJECT = '''# Fixture de clientes\n\nEste entorno es Linux con Python 3 y Git ya instalados; no es el Mac anfitrión. No requiere instalar dependencias, bases de datos ni servicios. Pruebas existentes: python3 -m unittest discover -s tests -v. Interfaz de usuario: python3 app.py. Responder en español.\n\nEl checkout /workspace/task es el worktree propio de esta tarea en feat/evaluation. /workspace/repo es el principal en main y /workspace/other pertenece a otro agente. Estado de la tarea: /workspace/task-state.json. No hay remoto conectado, credenciales de repositorio ni publicación autorizada.\n'''

def docker(args, **kwargs):
    return command(['docker']+args,**kwargs)

def setup(workspace, case):
    root=workspace/'repo'; root.mkdir(parents=True)
    put(root,'AGENTS.md',PROJECT)
    put(root,'.gitignore','__pycache__/\n*.pyc\n')
    put(root,'README.md','# Clinetes\n\nCLI de clientes.\n')
    put(root,'clients.json',json.dumps([{'name':'José','email':'jose@example.test','status':'active'},{'name':'Ana','email':'ana@example.test','status':'inactive'}],ensure_ascii=False)+'\n')
    put(root,'clients.py',LIB.replace('row["status"] == "active"','row["status"]') if case['id']=='02-bug' else LIB)
    app=APP
    if case['id']=='01-feature':
        start=app.index('        writer ='); end=app.index('    else:')
        app=app[:start]+'        raise NotImplementedError("CSV export pending")\n'+app[end:]
    put(root,'app.py',app); put(root,'tests/test_clients.py',TEST)
    put(root,'docs/spec.md',ACCEPTANCE)
    interview=ACCEPTANCE
    if case['id']=='04-interview-gap':
        interview='# Propuesta pendiente\n\nExportar clientes filtrados, columnas name,email, UTF-8. La tabla muestra páginas de 25 registros. Falta decidir si exportar la página visible o todos los resultados filtrados; no existe política anterior. Fuera: importación y permisos.\n'
    if case['id']=='06-direct-approved':
        interview='# Acuerdo\n\nÚnico cambio aprobado: encabezado README.md Clinetes → Clientes. Ruta elegida y autorizada: implementación directa. Aceptación: diff de una línea, sin cambios de comportamiento.\n'
    put(root,'docs/interview.md',interview)
    put(root,'docs/results.md','# Resultados\n\n4 de 5 comprobaciones unitarias pasaron; 1 falló en el caso vacío. La prueba de integración CLI está pendiente. No se probó el entorno de producción. No se ha aprobado despliegue.\n')
    script='git init -b main /workspace/repo && cd /workspace/repo && git config user.email benchmark@example.test && git config user.name Benchmark && git add . && git commit -m "Fixture baseline" && git worktree add -b feat/evaluation /workspace/task && git worktree add -b feat/other /workspace/other && printf "other-agent-owned\\n" > /workspace/other/notes.txt && cd /workspace/task && python3 -m unittest discover -s tests -v'
    output=docker(['run','--platform','linux/amd64','--rm','--network','none','--mount',f'type=bind,src={workspace},dst=/workspace',IMAGE,'sh','-c',script],stderr=subprocess.STDOUT)
    put(workspace,'setup.log',output)
    save(workspace/'task-state.json',{'owner':'evaluation-session','canonical':'/workspace/repo','worktree':'/workspace/task','branch':'feat/evaluation','target':'main','scope':case['id'],'resource':'docs/spec.md' if case['id']=='01-feature' else 'user request and docs/interview.md','implementationAccepted':False,'pr':None})


def prepare():
    global RUN
    RUN=pathlib.Path.home()/'.local/share/mstack-evals/agents'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ-am011')
    RUN.mkdir(parents=True,mode=0o700); os.chmod(RUN,0o700)
    shutil.copy2(__file__,RUN/'runner.py'); shutil.copy2(REPO/'evals/deepswe/auth_state.py',RUN/'auth-helper.py')
    profiles={}
    for label,source in [('A',ACTIVE),('B',REPO)]:
        dest=RUN/'profiles'/label; dest.mkdir(parents=True)
        shutil.copytree(source/'skills',dest/'skills')
        for copied in [dest/'skills', *(dest/'skills').rglob('*')]:
            copied.chmod(0o700 if copied.is_dir() else 0o600)
        # The common unmanaged browser skill is part of the actual local stack.
        if not (dest/'skills/chrome-devtools-axi').exists():
            shutil.copytree(pathlib.Path.home()/'.agents/skills/chrome-devtools-axi',dest/'skills/chrome-devtools-axi')
        agents=pathlib.Path.home()/'.agents/AGENTS.md' if label=='A' else source/'instructions/global/AGENTS.md'
        shutil.copy2(agents,dest/'AGENTS.md')
        profiles[label]={'source':str(source),'hashes':hashes(dest)}
    steps=[]
    for index,case in enumerate(CASES):
        for label in (['A','B'] if index%2==0 else ['B','A']):
            ident=case['id']+'-'+label
            ws=RUN/'workspaces'/ident
            setup(ws,case); steps.append({'id':ident,'case':case['id'],'profile':label})
    manifest={'model':MODEL,'effort':'high','cli':'0.160.0','image':IMAGE,'candidateCommit':command(['git','-C',str(REPO),'rev-parse','HEAD']).strip(),'profiles':profiles,'cases':CASES,'steps':steps,'budgetSecondsPerTurn':BUDGET,'maxModelTurns':16,'retries':0,'nestedModelCalls':0,'runnerHash':digest(pathlib.Path(__file__)),'authHelperHash':digest(REPO/'evals/deepswe/auth_state.py'),'fixtureHashes':{s['id']:hashes(RUN/'workspaces'/s['id']) for s in steps},'scope':'Managed skill stack plus Chrome; other external/plugin skills excluded equally. Compound AGENTS+skills comparison; one sample per profile/case. Synthetic Linux fixture, not desktop or live remote lifecycle. No installation or publication.','judge':'Parent agent reviews traces against frozen criteria; deterministic file/tests verification. Not blind or independent.','selectionEvidence':'Actual SKILL.md read in command trace, separate from behavioral success; no explicit skill injection.'}
    save(RUN/'manifest.json',manifest)
    print('PREPARED '+str(RUN),flush=True)

class RPC:
    def __init__(self, case, workspace, home, frozen):
        self.case=case; self.q=queue.Queue(); self.seq=0; self.name='mstack-agents-'+RUN.name.lower()+'-'+case.name
        self.log=(case/'events.jsonl').open('w'); self.sent=(case/'requests.jsonl').open('w'); self.err=(case/'stderr.log').open('w')
        cmd=['docker','run','--platform','linux/amd64','--rm','-i','--name',self.name,'--init','--cap-drop=ALL','--security-opt=no-new-privileges','--memory=2g','--cpus=2',
             '--mount',f'type=bind,src={workspace},dst=/workspace',
             '--mount',f'type=bind,src={frozen},dst=/root/.agents/skills,readonly',
             '--mount',f'type=bind,src={home},dst=/root/.codex',
             IMAGE,'codex','app-server','--listen','stdio://']
        self.p=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,bufsize=1)
        def read():
            for line in self.p.stdout:
                try: m=json.loads(line)
                except ValueError: continue
                self.log.write(json.dumps(m,ensure_ascii=False)+'\n'); self.log.flush(); self.q.put(m)
            self.q.put({'_eof':True})
        self.reader=threading.Thread(target=read,daemon=True); self.reader.start()
    def send(self,method,params=None,request=True):
        msg={'method':method}
        if params is not None: msg['params']=params
        if request: self.seq+=1; msg['id']=self.seq
        self.sent.write(json.dumps(msg,ensure_ascii=False)+'\n'); self.sent.flush()
        self.p.stdin.write(json.dumps(msg)+'\n'); self.p.stdin.flush()
        return msg.get('id')
    def call(self,method,params=None,timeout=60):
        ident=self.send(method,params); end=time.monotonic()+timeout
        while time.monotonic()<end:
            try: m=self.q.get(timeout=max(.1,end-time.monotonic()))
            except queue.Empty: break
            if m.get('_eof'): raise RuntimeError('App server exited; inspect stderr')
            if m.get('id')==ident:
                if 'error' in m: raise RuntimeError(json.dumps(m['error']))
                return m.get('result')
        raise TimeoutError(method)
    def close(self):
        if self.p.poll() is None:
            self.p.stdin.close()
            try: self.p.wait(timeout=8)
            except subprocess.TimeoutExpired:
                subprocess.run(['docker','stop','-t','2',self.name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                try: self.p.wait(timeout=8)
                except subprocess.TimeoutExpired: self.p.kill(); self.p.wait()
        self.reader.join(timeout=3)
        self.err.close(); self.log.close(); self.sent.close()

def run_step(step, home):
    case_def=next(c for c in CASES if c['id']==step['case'])
    case=RUN/step['id']; case.mkdir()
    ws=RUN/'workspaces'/step['id']; profile=RUN/'profiles'/step['profile']
    shutil.copy2(profile/'AGENTS.md',home/'AGENTS.md')
    before=hashes(ws); save(case/'before.json',before)
    save(case/'input.json',{'prompt':case_def['prompt'],'budget':BUDGET,'cwd':'/workspace/task','profile':step['profile']})
    rpc=None; start=time.monotonic(); result=dict(step)
    print('START '+step['id'],flush=True)
    try:
        rpc=RPC(case,ws,home,profile/'skills')
        rpc.call('initialize',{'clientInfo':{'name':'mstack_agents_eval','version':'0.1.0'},'capabilities':{'experimentalApi':True}})
        rpc.send('initialized',request=False)
        catalog=rpc.call('skills/list',{'cwds':['/workspace/task'],'forceReload':True})
        save(case/'catalog.json',catalog)
        expected={p.name for p in (profile/'skills').iterdir() if p.is_dir() and (p/'SKILL.md').is_file()}
        entries=[s for entry in catalog['data'] for s in entry['skills'] if s.get('path','').startswith('/root/.agents/skills/')]
        actual={e['name'] for e in entries}
        if expected-actual: raise RuntimeError('Missing candidate skills: '+str(sorted(expected-actual)))
        errors=[e for d in catalog['data'] for e in d.get('errors',[]) if '/root/.agents/skills/' in str(e)]
        if errors: raise RuntimeError('Candidate discovery errors: '+str(errors))
        th=rpc.call('thread/start',{'model':MODEL,'allowProviderModelFallback':False,'cwd':'/workspace/task','approvalPolicy':'never','sandbox':'danger-full-access','ephemeral':True,'experimentalRawEvents':True,'config':{'model_reasoning_effort':'high'}})
        save(case/'thread.json',th)
        # No explicit skill attachment: this measures natural routing.
        turn=rpc.call('turn/start',{'threadId':th['thread']['id'],'effort':'high','input':[{'type':'text','text':case_def['prompt'],'text_elements':[]}]})
        save(case/'turn.json',turn)
        end=time.monotonic()+BUDGET; progress=time.monotonic()+30
        while time.monotonic()<end:
            try: m=rpc.q.get(timeout=1)
            except queue.Empty: m={}
            if m.get('_eof'): raise RuntimeError('App server exited during turn')
            if m.get('method')=='turn/completed':
                result['status']=m['params']['turn']['status']; result['completion']=m['params']['turn']; break
            if m.get('method')=='item/tool/requestUserInput':
                result['status']='awaiting-user-input'; result['question']=m['params']
                rpc.send('turn/interrupt',{'threadId':th['thread']['id'],'turnId':turn['turn']['id']}); break
            if time.monotonic()>progress:
                print('RUNNING '+step['id']+' '+str(round(time.monotonic()-start))+'s',flush=True); progress=time.monotonic()+30
        else:
            result['status']='timeout'; rpc.send('turn/interrupt',{'threadId':th['thread']['id'],'turnId':turn['turn']['id']})
    except Exception as exc:
        result['status']='infrastructure-error'; result['error']=str(exc)
    finally:
        if rpc: rpc.close()
    after=hashes(ws); save(case/'after.json',after)
    result['seconds']=round(time.monotonic()-start,2)
    result['changedFiles']=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)]
    save(case/'result.json',result)
    print('DONE '+step['id']+' '+result['status'],flush=True)
    return result


def execute(run):
    global RUN
    RUN=run.resolve(); manifest=json.loads((RUN/'manifest.json').read_text())
    if (RUN/'execution-started.json').exists(): raise RuntimeError('Run already started; no retries or resume permitted')
    if manifest['runnerHash']!=digest(pathlib.Path(__file__)): raise RuntimeError('Runner changed after preparation')
    if manifest['authHelperHash']!=digest(REPO/'evals/deepswe/auth_state.py'): raise RuntimeError('Auth helper changed')
    if manifest['image']!=docker(['image','inspect',IMAGE,'--format','{{.Id}}']).strip(): raise RuntimeError('Image changed')
    for label,profile in manifest['profiles'].items():
        if hashes(RUN/'profiles'/label)!=profile['hashes']: raise RuntimeError('Frozen profile changed')
    for step in manifest['steps']:
        if hashes(RUN/'workspaces'/step['id'])!=manifest['fixtureHashes'][step['id']]: raise RuntimeError('Fixture changed')
    state=command(['/usr/sbin/ioreg','-r','-k','AppleClamshellState','-d','4'])
    if re.search(r'"AppleClamshellState" = Yes',state): raise RuntimeError('MacBook lid must remain open')
    validate_auth(AUTH)
    results=[]
    with auth_lock(AUTH):
        original=digest(AUTH)
        home=pathlib.Path(tempfile.mkdtemp(prefix='.agents-auth-',dir=AUTH.parent)); os.chmod(home,0o700)
        shutil.copy2(AUTH,home/'auth.json'); os.chmod(home/'auth.json',0o600)
        (home/'config.toml').write_text('cli_auth_credentials_store = "file"\n[features]\napps = false\n[projects."/workspace/task"]\ntrust_level = "trusted"\n')
        helper=subprocess.Popen(['/usr/bin/caffeinate','-i','-w',str(os.getpid())])
        save(RUN/'execution-started.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':os.getpid()})
        try:
            for step in manifest['steps']:
                # Isolate session state while retaining only the latest auth refresh and config.
                for entry in home.iterdir():
                    if entry.name not in ['auth.json','config.toml']:
                        if entry.is_dir(): shutil.rmtree(entry)
                        else: entry.unlink()
                result=run_step(step,home); results.append(result); save(RUN/'results.json',results)
                if result['status'] in ['infrastructure-error','failed']:
                    print('STOP: infrastructure or provider failure; unused executions preserved.',flush=True); break
        finally:
            fd,tmp=tempfile.mkstemp(prefix='.agents-refresh-',dir=AUTH.parent); os.close(fd)
            shutil.copyfile(home/'auth.json',tmp); os.chmod(tmp,0o600)
            persist_refresh(pathlib.Path(tmp),AUTH,original)
            shutil.rmtree(home)
            helper.terminate(); helper.wait(timeout=5)
            print('Benchmark credentials preserved; temporary credential home removed.',flush=True)
    save(RUN/'final-profile-hashes.json',{label:hashes(RUN/'profiles'/label) for label in ['A','B']})
    save(RUN/'execution-ended.json',{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'executed':len(results)})
    print('FINISHED '+str(RUN),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(); group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--prepare',action='store_true'); group.add_argument('--run',type=pathlib.Path)
    args=parser.parse_args()
    if args.prepare: prepare()
    else: execute(args.run)
