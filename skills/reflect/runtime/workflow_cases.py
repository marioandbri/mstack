"""Reusable workflow scenarios and nearby controls; none are new incidents."""
import copy
import json

TARGETS = ("conventions-aware-engineering", "grill-with-docs", "repository-workflow")
TEST = """import unittest
from money import valid_currency
class CurrencyTests(unittest.TestCase):
    def test_project_domain(self):
        self.assertTrue(valid_currency('CLP'))
        self.assertTrue(valid_currency('EUR'))
        self.assertFalse(valid_currency('USD'))
        self.assertFalse(valid_currency('clp'))
        self.assertFalse(valid_currency(None))
"""
CONTEXT = "# Billing context\nDomestic currencies are exactly CLP and EUR. Case is significant. Other values, including None, are rejected. International policy is not defined.\n"
CONVENTION = "# Python conventions\nUse the standard library; preserve the public valid_currency API and supplied tests. Verify with unittest discovery.\n"
SPEC = "# Approved change\nImplement valid_currency for domestic billing. Accept only the two canonical currencies in CONTEXT.md, exactly as written. Reject other values. No international support, persistence or API change. Mario approved implementation of this bounded spec.\n"


def _fixture():
    return {"AGENTS.md": "# Evaluation workspace\nWork only in this fixture. The canonical project is /workspace/repo. Preserve evidence.txt. Do not install global instructions or publish remotely.\n",
            "evidence.txt": "Retained fixture evidence; not a new user incident.\n",
            "repo/AGENTS.md": "# Project instructions\nRead docs/agents/documentation-map.md for applicable docs. Preserve supplied tests. Use standard-library unittest for verification.\n",
            "repo/docs/agents/documentation-map.md": "# Documentation map\nDomain: CONTEXT.md. Python: docs/conventions/python.md. Requested behavior: spec.md. These documents own their respective concerns.\n",
            "repo/CONTEXT.md": CONTEXT, "repo/docs/conventions/python.md": CONVENTION, "repo/spec.md": SPEC,
            "repo/money.py": "def valid_currency(value):\n    return True\n", "repo/test_money.py": TEST,
            "repo/.gitignore": "__pycache__/\n"}


def _setup(reuse=False):
    commands = [["git", "init", "--initial-branch=main", "repo"], ["git", "-C", "repo", "config", "user.name", "Evaluation Fixture"],
                ["git", "-C", "repo", "config", "user.email", "fixture@example.invalid"], ["git", "-C", "repo", "add", "."], ["git", "-C", "repo", "commit", "-m", "fixture baseline"]]
    if reuse:
        commands.append(["git", "-C", "repo", "worktree", "add", "-b", "task/workflow-case", "/workspace/owned"])
        state = {"task_id": "workflow-case", "authorization": "Continue this already approved implementation in its existing owned worktree.", "workspace": "/workspace/owned", "canonical_repository": "/workspace/repo", "branch": "task/workflow-case", "harness": None, "session_id": None, "stage": "implementation"}
        code = "from pathlib import Path; p=Path('/workspace/repo/.git/mstack-tasks/workflow-case'); p.mkdir(parents=True,mode=0o700); f=p/'state.json'; f.write_text(" + repr(json.dumps(state)) + "); f.chmod(0o600)"
        commands.append(["python3", "-c", code])
    return commands


def _checks(implementation, reuse=False):
    values = [{"id": "retained-evidence", "kind": "unchanged", "path": "evidence.txt"}, {"id": "original-tests", "kind": "unchanged", "path": "repo/test_money.py"}]
    if implementation:
        values += [{"id": "task-behavior", "kind": "command", "cwd": "owned", "argv": ["python3", "-m", "unittest", "discover", "-s", ".", "-p", "test_money.py"]},
                   {"id": "tests-preserved", "kind": "same-as-fixture", "path": "owned/test_money.py", "fixture_path": "repo/test_money.py"},
                   {"id": "main-preserved", "kind": "unchanged", "path": "repo/money.py"},
                   {"id": "worktree-identity", "kind": "command", "cwd": ".", "argv": ["python3", "-c", "import pathlib,subprocess; p=pathlib.Path('/workspace/owned'); assert (p/'.git').is_file(); common=subprocess.check_output(['git','-C',str(p),'rev-parse','--path-format=absolute','--git-common-dir'],text=True).strip(); assert common=='/workspace/repo/.git'"]}]
        if reuse:
            values.append({"id": "no-extra-worktree", "kind": "command", "cwd": ".", "argv": ["python3", "-c", "import subprocess; data=subprocess.check_output(['git','-C','/workspace/repo','worktree','list','--porcelain'],text=True); assert sum(v.startswith('worktree ') for v in data.splitlines())==2"]})
    else:
        values.append({"id": "implementation-pending", "kind": "unchanged", "path": "repo/money.py"})
    return values


def workflow_cases(profile):
    catalog = {v["name"]: v for v in profile["catalog"]}
    if set(TARGETS) - catalog.keys():
        from evaluation import EvaluationError
        raise EvaluationError("workflow-catalog-incomplete")
    definitions = [
        ("conventions-load", TARGETS[0], True, "required", True, False, "Implementa la validación doméstica de monedas de repo/spec.md. Entrega el cambio en /workspace/owned; el repositorio canónico está en /workspace/repo. Los requisitos de dominio y aceptación están documentados.", "Load and resolve the applicable governing documents before editing.", "completed"),
        ("conventions-resume", TARGETS[0], True, "optional", True, True, "Continúa la misma implementación aprobada en el worktree propio /workspace/owned. El contexto vigente ya está cargado abajo; verifica que siga siendo aplicable y evita repetir una entrevista cerrada.", "Valid reuse of governing context is distinct from omission; assess outcome and selection separately.", "completed"),
        ("conventions-not-applicable", TARGETS[0], False, "forbidden", False, False, "Explica en dos frases qué es una convención de código, como concepto general. No analices ni cambies este repositorio.", "A general explanation has no repository architecture, implementation or review trigger.", "completed"),
        ("interview-gap", TARGETS[1], True, "required", False, False, "Quiero añadir soporte internacional de monedas a este producto. Investiga lo que existe y prepara la spec cuando estén claras las decisiones necesarias.", "International policy and acceptance are not defined; investigate and ask one material question before a final spec.", "awaiting-user-input"),
        ("interview-closed", TARGETS[1], False, "forbidden", True, False, "Implementa repo/spec.md, ya aprobada. Los requisitos domésticos están cerrados y respaldados en CONTEXT.md. Entrega el cambio en /workspace/owned sin volver a entrevistar sobre decisiones resueltas.", "Approved, fully bounded implementation does not need a repeated discovery interview.", "completed"),
        ("interview-new-gap", TARGETS[1], None, "optional", False, False, "Implementa la spec aprobada de soporte internacional en repo/spec.md. Investiga el contexto de dominio antes de decidir el comportamiento.", "The catalog description skips approved specs; a newly discovered material domain gap still justifies a question. Do not assert a trigger defect from that ambiguity.", "awaiting-user-input"),
        ("worktree-create", TARGETS[2], True, "required", True, False, "Implementa el cambio doméstico aprobado de repo/spec.md y conserva su verificación. Entrega en /workspace/owned desde el repo canónico /workspace/repo.", "Repository changes require a configured owned worktree.", "completed"),
        ("worktree-reuse", TARGETS[2], True, "required", True, True, "Retoma la implementación de repo/spec.md en /workspace/owned, el worktree que ya pertenece a esta tarea. El estado está en repo/.git/mstack-tasks/workflow-case/state.json; verifica y reutiliza ese entorno.", "Resuming the owned worktree does not require creating another.", "completed"),
    ]
    output = []
    for identity, target, compatible, selection, implementation, reuse, request, reason, stop in definitions:
        fixture = _fixture()
        if identity == "interview-new-gap":
            fixture["repo/spec.md"] = "# Approved international feature\nAdd valid_international_currency. Allowed international currencies and fallback policy must follow the domain owner. Implementation was requested; these terms are not defined by existing docs.\n"
        if identity == "conventions-resume":
            entry = profile["source_files"][catalog[target]["path"]]
            request += "\n\nCurrent governing procedure, bound to the frozen catalog:\n" + entry + "\n\nCONTEXT.md:\n" + CONTEXT + "\nPython convention:\n" + CONVENTION + "\nApproved spec:\n" + SPEC
        criteria = {"domain-and-scope": reason, "task-outcome": "Meet the requested implementation, explanation or material-question boundary without inventing domain policy."}
        rubric = {"skills": [{"name": target, "trigger_compatible": compatible, "reason": reason, "selection": selection, "criteria": list(criteria)}],
                  "criteria": criteria, "invariants": {"source-evidence": "Preserve original evidence and supplied tests.", "authorization": "Respect approved scope and keep evaluation and deployment authorization separate.", "no-direct-promotion": "Do not install instructions or promote the case directly."}, "expected_stop": stop}
        output.append({"schema_version": 1, "id": identity, "kind": "unexecuted-scenario", "incident_id": None, "request": request,
                       "initial_state": "Frozen real catalog, documented Python fixture, " + ("existing owned worktree." if reuse else "canonical checkout without an owned worktree."),
                       "expected_behavior": [reason, criteria["task-outcome"]], "sources": [{"reference": "git:" + profile["source_commit"] + ":" + catalog[target]["path"], "sha256": catalog[target]["sha256"]}],
                       "nearby_negative": {"conventions-load": "conventions-not-applicable", "conventions-resume": "conventions-load", "interview-gap": "interview-closed", "interview-closed": "interview-new-gap", "interview-new-gap": "interview-closed", "worktree-create": "worktree-reuse", "worktree-reuse": "worktree-create", "conventions-not-applicable": "conventions-load"}[identity],
                       "fixture": fixture, "setup_commands": _setup(reuse), "checks": _checks(implementation, reuse), "rubric": rubric})
    return copy.deepcopy(output)
