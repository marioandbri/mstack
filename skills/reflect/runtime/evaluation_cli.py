"""Explicit preparation, execution, reporting and recovery for maintenance cases."""
import argparse
import json
from pathlib import Path
import sys
import uuid

from collector import create_workspace
from evaluation import Runner, EvaluationError


def read(path):
    return json.loads(Path(path).read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare")
    prepare.add_argument("--case", required=True); prepare.add_argument("--profile", required=True)
    git = commands.add_parser("prepare-git")
    for key in ("case", "repository", "ref", "environment", "profile-id", "model", "reasoning"):
        git.add_argument("--" + key, required=True)
    git.add_argument("--seconds", type=int, required=True)
    library = commands.add_parser("prepare-workflows")
    for key in ("repository", "ref", "environment", "profile-id", "model", "reasoning"):
        library.add_argument("--" + key, required=True)
    library.add_argument("--seconds", type=int, required=True)
    execute = commands.add_parser("execute")
    for key in ("protocol", "attempt", "grant"):
        execute.add_argument("--" + key, required=True)
    execute.add_argument("--transport", choices=("fixture", "codex"), required=True)
    execute.add_argument("--auth")
    preflight = commands.add_parser("preflight")
    preflight.add_argument("--protocol", required=True); preflight.add_argument("--auth", required=True)
    recover = commands.add_parser("recover")
    for key in ("attempt", "recovery", "termination-evidence"):
        recover.add_argument("--" + key, required=True)
    commands.add_parser("report")
    assessment = commands.add_parser("assess")
    for key in ("attempt", "id", "judgment"):
        assessment.add_argument("--" + key, required=True)
    commands.add_parser("selection-report")
    args = parser.parse_args()
    runner = Runner(args.root)
    try:
        if args.command == "prepare":
            result = runner.prepare(read(args.case), read(args.profile))
        elif args.command in ("prepare-git", "prepare-workflows"):
            from evaluation_source import git_profile
            profile = git_profile(args.repository, args.ref, read(args.environment), identity=args.profile_id, model=args.model, reasoning=args.reasoning, seconds=args.seconds)
            if args.command == "prepare-workflows":
                from workflow_cases import workflow_cases
                result = {"stage": "prepared", "cases": [runner.prepare(case, profile) for case in workflow_cases(profile)], "agent_turns_started": 0}
            else:
                result = runner.prepare(read(args.case), profile)
        elif args.command in ("execute", "preflight"):
            if args.command == "preflight" or args.transport == "codex":
                if not args.auth:
                    raise EvaluationError("benchmark-auth-path-required")
                from codex_evaluation import CodexDocker
                transport = CodexDocker(Path(args.root) / "control", args.auth)
            else:
                from fixture_evaluation import FixtureProcess
                transport = FixtureProcess()
            if args.command == "execute":
                result = runner.execute(args.protocol, args.attempt, read(args.grant), transport)
            else:
                protocol = runner.load(args.protocol)
                identity = "preflight-" + uuid.uuid4().hex
                workspace = create_workspace(Path(args.root) / "preflights" / identity, identity)
                runner._populate(workspace, protocol)
                result = transport.preflight(workspace, protocol)
        elif args.command == "recover":
            result = runner.recover(args.attempt, args.recovery, args.termination_evidence)
        elif args.command == "assess":
            from selection import save_assessment
            result = save_assessment(runner, args.attempt, args.id, read(args.judgment))
        elif args.command == "selection-report":
            from selection import assessment_report
            result = assessment_report(runner)
        else:
            result = runner.report()
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except EvaluationError as error:
        print(json.dumps({"error": str(error), "execution": "unconfirmed", "next": "Inspect attempt receipts before retrying."}), file=sys.stderr)
    except Exception:
        print(json.dumps({"error": "evaluation-input-or-infrastructure-unavailable", "execution": "unconfirmed", "next": "Inspect attempt receipts before retrying."}), file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
