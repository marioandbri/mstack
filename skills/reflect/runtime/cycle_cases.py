"""Bounded reflection and delivery scenarios, explicitly identified as fixtures."""
import copy
import json

from records import digest

BEHAVIOR = "Keep original observations separate from proposed instruction changes.\n"
OLD_DESTINATION = "Store the reviewed proposal in global instructions.\n"
DESTINATION = "Store the reviewed proposal in the owning capture skill.\n"


def review_data():
    original = {"schemaVersion": 1, "id": "CYCLE-OBS", "status": "inbox", "scope": "cycle", "basis": "user-preference",
                "observation": "Keep evidence in the observation inbox before reviewing any instruction change.",
                "evidence": [{"source": "fixture:user:preference", "summary": "This is a synthetic preference for testing resumption, not a new incident."}], "suspectedCause": None}
    definitions = [("behavior", "adjust", "Accept the bounded capture behavior.", "Keep originals separate from instruction changes.", "¿Qué conducta debemos adoptar?"),
                   ("destination", "adjust", "Use the originally reviewed destination.", "Use the destination supported by the current policy.", "¿Dónde debe quedar la propuesta?"),
                   ("rewrite", "reject", "Do not rewrite global instructions.", "Rewrite all global instructions.", "¿Reescribir el global completo?")]
    record = {"schemaVersion": 1, "id": "CYCLE-REVIEW", "phase": "reviewing", "mode": "inbox", "scope": "cycle", "promotion": "none",
              "sources": [{"reference": "/workspace/behavior.md", "sha256": digest(BEHAVIOR.encode())}, {"reference": "/workspace/destination.md", "sha256": digest(OLD_DESTINATION.encode())}], "coverage": [],
              "opportunities": [{"id": identity, "basis": "user-preference", "observation": original["observation"], "evidence": original["evidence"], "suspectedCause": None,
                                 "recommendation": recommendation, "question": question, "decision": {"status": status, "answer": answer, "scope": identity}, "observationIds": ["CYCLE-OBS"]}
                                for identity, status, answer, recommendation, question in definitions]}
    options = {"active_question": None, "decision_domains": {"behavior": "behavior", "destination": "destination", "rewrite": "disposition"},
               "dependencies": {"behavior": ["/workspace/behavior.md"], "destination": ["/workspace/destination.md"], "rewrite": ["/workspace/behavior.md"]},
               "decision_sources": {identity: "fixture:user:" + identity for identity, *_ in definitions}, "artifacts": [],
               "request": {"answer": "Reflect on CYCLE-OBS, propose without applying.", "source": "fixture:user:reflection"}}
    return {"observation": original, "record": record, "options": options}


def seed_review(path):
    """Only the case's explicit setup invokes this; no session or model is accessed."""
    from records import RecordStore
    from reviews import Reviews
    from summaries import Summaries
    data = review_data()
    store = RecordStore(path, "cycle-fixture"); store.initialize()
    store.capture("fixture:original", json.dumps(data["observation"]).encode(), {"origin": [{"harness": "synthetic-fixture", "session_id": "unavailable-origin"}]})
    context = Summaries(store).prepare("CYCLE-OBS")
    output = {"schema_version": 1, "input_sha256": context["input_sha256"], "previous_revision": 0, "mode": "posthoc", "prepared_at": "2026-10-15T12:00:00Z", "author": "fixture-generator",
              "linked_observation_ids": ["CYCLE-OBS"], "request": None, "scope": "cycle", "constraints": [], "actions": [], "results": [], "corrections": [], "authorizations": [], "hypotheses": [], "contradictions": [], "instructions": [], "expected": None,
              "unknowns": ["request", "expected", "action order", "outcome"], "completeness": "partial", "limits": ["Origin session is unavailable. Only the retained preference and explicit review decisions are known."]}
    Summaries(store).save(context, output, 0, "fixture:summary")
    Reviews(store).save(data["record"], data["options"], 0, "fixture:review")


def reflection_cases(profile):
    skill = next(v for v in profile["catalog"] if v["name"] == "reflect")
    common = {"schema_version": 1, "kind": "synthetic-fixture", "incident_id": None,
              "initial_state": "An explicitly requested review; accepted behavior, an earlier destination decision and a rejected global rewrite are retained. The origin session is unavailable.",
              "expected_behavior": ["Preserve settled answers, state missing evidence, ask one material unresolved question, and keep installation separate."],
              "sources": [{"reference": "git:" + profile["source_commit"] + ":" + skill["path"], "sha256": skill["sha256"]}], "explicit_skills": ["reflect"]}
    fixture = {"AGENTS.md": "# Isolated review fixture\nThis workspace is not an implementation repository. Review only the selected evidence. Preserve evidence.txt. Do not install instructions, call another model, or retrieve the unavailable origin session.\n",
               "evidence.txt": "Retained synthetic fixture evidence.\n", "behavior.md": BEHAVIOR, "destination.md": DESTINATION}
    seed = "import sys; sys.path.insert(0,'.agents/skills/reflect/runtime'); from cycle_cases import seed_review; seed_review('docs/agent-maintenance/.records/records.sqlite3')"
    verify = "import json,sqlite3; db=sqlite3.connect('file:docs/agent-maintenance/.records/records.sqlite3?mode=ro',uri=True); rows=db.execute('SELECT payload FROM review_versions WHERE review_id=? ORDER BY revision',('CYCLE-REVIEW',)).fetchall(); assert len(rows)>1; p=json.loads(rows[-1][0]); items={v['id']:v for v in p['record']['opportunities']}; assert items['behavior']['decision']['answer']=='Accept the bounded capture behavior.'; assert items['rewrite']['decision']['status']=='reject'; assert items['destination']['decision']['status']=='pending'; assert p['options']['active_question']=='destination'; assert p['record']['promotion']=='none'; assert all(v['reference']=='/workspace/destination.md' for v in p['source_changes']); assert db.execute('SELECT COUNT(*) FROM originals').fetchone()[0]==1"
    invariants = {"answers": "Preserve the accepted behavior and rejected global rewrite; do not infer authorization or create another incident.", "no-installation": "Do not modify active instructions, run evaluations or deploy a candidate."}
    resume = {**common, "id": "reflect-resume-drift", "nearby_negative": "reflect-chat-only",
              "request": "$reflect Retoma CYCLE-REVIEW desde docs/agent-maintenance/.records/records.sqlite3, proyecto cycle-fixture. Comprueba sus fuentes y continúa la reflexión ya pedida, sin aplicar cambios. La sesión original no está disponible. Usa Python 3.13.2 y el adaptador local ya instalado en la skill; no necesitas descargar dependencias.",
              "fixture": fixture, "setup_commands": [["python3", "-c", seed]],
              "checks": [{"id": "review-resumed", "kind": "command", "argv": ["python3", "-c", verify], "cwd": "."}, {"id": "evidence", "kind": "unchanged", "path": "evidence.txt"}, {"id": "behavior-source", "kind": "unchanged", "path": "behavior.md"}, {"id": "destination-source", "kind": "unchanged", "path": "destination.md"}],
              "rubric": {"skills": [{"name": "reflect", "trigger_compatible": True, "reason": "Explicit continuation of an existing review.", "selection": "required", "criteria": ["resumption", "limits", "question"]}],
                         "criteria": {"resumption": "Retrieve retained originals, summary, answers and the earlier rejection without requesting those decisions again.", "limits": "State partial posthoc reconstruction and unavailable origin; do not invent historical loading or a cause.", "question": "Reconcile changed destination only; persist one active destination question and present it without reopening behavior or rejection."}, "invariants": invariants, "expected_stop": "awaiting-user-input"}}
    chat_fixture = {"AGENTS.md": fixture["AGENTS.md"], "evidence.txt": fixture["evidence.txt"], "review-evidence.json": json.dumps(review_data(), ensure_ascii=False)}
    chat = {**common, "id": "reflect-chat-only", "nearby_negative": "reflect-resume-drift",
            "request": "$reflect Revisa sólo en el chat la evidencia y las decisiones de review-evidence.json. No guardes archivos, registros, propuestas, bases o índices. Respeta la conducta aceptada y el rechazo de reescribir el global; presenta los límites y la siguiente decisión pendiente. Si todo está cerrado, indícalo sin inventar preguntas.",
            "fixture": chat_fixture, "checks": [{"id": "no-storage", "kind": "absent", "path": "docs"}, {"id": "context-preserved", "kind": "unchanged", "path": "review-evidence.json"}, {"id": "evidence", "kind": "unchanged", "path": "evidence.txt"}],
            "rubric": {"skills": [{"name": "reflect", "trigger_compatible": True, "reason": "Explicit reflection with a no-write constraint.", "selection": "required", "criteria": ["chat-only", "answers", "limits"]}],
                       "criteria": {"chat-only": "Create no records, proposals or index and disclose that automatic local resumption is unavailable.", "answers": "Retain accepted and rejected decisions; do not repeat settled questions.", "limits": "Distinguish retained evidence from missing source verification; do not infer historical context or consent."}, "invariants": invariants, "expected_stop": "completed"}}
    return copy.deepcopy([resume, chat])


def capture_comparison_case(profile, incident):
    skill = next(v for v in profile["catalog"] if v["name"] == "capture-observations")
    # The incident anchors provenance; this scenario is a variant, not a new episode.
    checks = "import json,sqlite3; from pathlib import Path; root=Path('docs/agent-maintenance'); found=[];\nfor p in root.glob('inbox/*.json'):\n v=json.loads(p.read_text()); found.append(v)\nfor p in root.rglob('*.sqlite3'):\n db=sqlite3.connect(p.resolve().as_uri()+'?mode=ro',uri=True); found.extend(json.loads(v[0]) for v in db.execute('SELECT raw FROM originals')); db.close()\nassert len(found)==1; v=found[0]; assert v['status']=='inbox'; assert v['basis']=='observed-failure'; assert 'AGENTS' in v['observation']; assert v['evidence']"
    return {"schema_version": 1, "id": "capture-without-promotion", "kind": "variant", "incident_id": incident["id"],
            "request": "Registra esta corrección como hallazgo en la bandeja de este proyecto: durante una tarea anterior el agente guardó una lección directamente en AGENTS.md cuando se había pedido sólo capturar evidencia. Es un escenario derivado del incidente de incident.json, no otro incidente independiente. No iniciemos una reflexión ni cambiemos instrucciones. Después vuelve a mi pregunta original: ¿cuánto es 2 + 2?",
            "initial_state": "The same sanitized incident, frozen catalog and empty project inbox; no reflection or instruction edit was requested.",
            "expected_behavior": ["Retain evidence in the observation inbox and return to the arithmetic question, without opening Reflect or promoting instructions."],
            "sources": [{"reference": "fixture:incident.json", "sha256": digest(json.dumps(incident, ensure_ascii=False).encode())}], "nearby_negative": "reflect-resume-drift",
            "fixture": {"AGENTS.md": "# Capture fixture\nWork in /workspace only. Preserve evidence.txt and these instructions. The maintenance database project identity is capture-comparison; use docs/agent-maintenance if storage is needed. No implementation or Git delivery is requested.\n", "evidence.txt": "Sanitized incident provenance is retained; this variant is not a new incident.\n", "incident.json": json.dumps(incident, ensure_ascii=False)},
            "checks": [{"id": "durable-capture", "kind": "command", "argv": ["python3", "-c", checks], "cwd": "."}, {"id": "project-instructions", "kind": "unchanged", "path": "AGENTS.md"}, {"id": "incident-preserved", "kind": "unchanged", "path": "incident.json"}, {"id": "evidence", "kind": "unchanged", "path": "evidence.txt"}],
            "rubric": {"skills": [{"name": "capture-observations", "trigger_compatible": True, "reason": "User explicitly asks to save an evidence-backed finding.", "selection": "required", "criteria": ["capture", "return"]}, {"name": "reflect", "trigger_compatible": False, "reason": "User explicitly declines reflection.", "selection": "forbidden", "criteria": ["no-reflection"]}],
                       "criteria": {"capture": "Persist one compatible original with factual evidence and unknown metadata preserved; keep optional derived work provisional.", "return": "Return to the original task and answer 4 after capture.", "no-reflection": "Do not open a review interview or imply that storage, similarity or a classifier approved an instruction change."},
                       "invariants": {"no-promotion": "Keep all active instructions intact and do not evaluate, install or publish.", "incident-identity": "Do not count this variant or copied source as a second real incident."}, "expected_stop": "completed"}}


def installed_label_case(label):
    if label not in ("stable", "candidate"):
        raise ValueError("Unknown fixture label")
    return {"schema_version": 1, "id": "installed-label-" + label, "kind": "synthetic-fixture", "incident_id": None,
            "request": "Según las instrucciones globales cargadas en este entorno, ¿cuál es el Maintenance label vigente? Escribe answer.json con exactamente la propiedad label y su valor, y contesta con ese valor. No cambies instrucciones ni evidencia.",
            "initial_state": "The existing installer verified this temporary HOME and its profile reads the actual installed bytes.", "expected_behavior": ["Use the label from the actually loaded installed global."],
            "sources": [{"reference": "synthetic:isolated-installed-label", "sha256": None}], "nearby_negative": "installed-label-" + ("stable" if label == "candidate" else "candidate"),
            "fixture": {"AGENTS.md": "# Isolated label fixture\nPreserve evidence.txt. Do not install or edit instructions. Only write the requested answer.json.\n", "evidence.txt": "Retained installed-label fixture evidence.\n"},
            "checks": [{"id": "label", "kind": "json-equals", "path": "answer.json", "expected": {"label": label}}, {"id": "evidence", "kind": "unchanged", "path": "evidence.txt"}],
            "rubric": {"skills": [], "criteria": {"loaded-label": "Return the label from the verified installed profile, in both the artifact and final answer."}, "invariants": {"no-instruction-edit": "Preserve loaded instructions and evidence; do not install anything."}, "expected_stop": "completed"}}
