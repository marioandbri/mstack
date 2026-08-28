import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
	sha256,
	sha256Canonical,
	type CandidateRequest,
} from "../skills/code-review/candidate-harness";

type RealCandidateFixture = {
	repository: string;
	patchPath: string;
	request: CandidateRequest;
};

function git(repository: string, ...arguments_: string[]): string {
	return execFileSync("git", arguments_, {
		cwd: repository,
		encoding: "utf8",
	}).trim();
}

function gitWithEnv(
	repository: string,
	env: Record<string, string>,
	...arguments_: string[]
): string {
	return execFileSync("git", arguments_, {
		cwd: repository,
		env: { ...process.env, ...env },
		encoding: "utf8",
	}).trim();
}

function fileHash(path: string): string {
	return `sha256:${createHash("sha256").update(readFileSync(path)).digest("hex")}`;
}

export async function createRealCandidateFixture(
	skillsRepository: string,
	skillPath: string,
	schemaPath: string,
): Promise<RealCandidateFixture> {
	const workspace = await mkdtemp(join(tmpdir(), "code-review-candidate-"));
	const patchPath = `${workspace}.patch`;
	const alternateIndex = join(workspace, "candidate-index");
	try {
		git(workspace, "init", "-q");
		git(workspace, "config", "user.email", "fixture@example.com");
		git(workspace, "config", "user.name", "Fixture");
		await Bun.write(
			join(workspace, "feature.ts"),
			"export const value = 1;\n",
		);
		git(workspace, "add", "feature.ts");
		git(workspace, "commit", "-qm", "baseline");

		const baseHeadHash = git(workspace, "rev-parse", "HEAD");
		const baseTreeHash = git(workspace, "rev-parse", "HEAD^{tree}");
		const candidateContent = Buffer.from("export const value = 2;\n");
		const candidateBlobHash = execFileSync(
			"git",
			["hash-object", "-w", "--stdin"],
			{ cwd: workspace, input: candidateContent, encoding: "utf8" },
		).trim();

		gitWithEnv(workspace, { GIT_INDEX_FILE: alternateIndex }, "read-tree", baseHeadHash);
		gitWithEnv(
			workspace,
			{ GIT_INDEX_FILE: alternateIndex },
			"update-index",
			"--add",
			"--cacheinfo",
			`100644,${candidateBlobHash},feature.ts`,
		);
		const aggregateTreeHash = gitWithEnv(
			workspace,
			{ GIT_INDEX_FILE: alternateIndex },
			"write-tree",
		);
		await rm(alternateIndex, { force: true });

		const patch = execFileSync(
			"git",
			["diff", "--binary", baseHeadHash, aggregateTreeHash],
			{ cwd: workspace, encoding: "buffer" },
		) as Buffer;
		await Bun.write(patchPath, patch);
		const changedPathRecords = (
			execFileSync(
				"git",
				["diff", "--name-status", "-z", baseHeadHash, aggregateTreeHash],
				{ cwd: workspace, encoding: "buffer" },
			) as Buffer
		)
			.toString("utf8")
			.split("\0")
			.filter(Boolean);
		const changedPaths = changedPathRecords.reduce<
			CandidateRequest["candidate"]["aggregate"]["changedPaths"]
		>((records, field, index) => {
			if (index % 2 !== 0) return records;
			const status = field?.[0];
			const path = changedPathRecords[index + 1];
			if (!status || !path) throw new Error("Malformed Git changed-path output");
			const statusMap: Record<string, string> = {
				A: "added",
				C: "copied",
				D: "deleted",
				M: "modified",
				R: "renamed",
				T: "type_changed",
			};
			records.push({ path, status: statusMap[status] ?? "modified" });
			return records;
		}, []);
		if (changedPaths.length === 0) throw new Error("Candidate patch is empty");

		const repositoryFingerprint = sha256Canonical({
			gitDirectory: git(workspace, "rev-parse", "--git-dir"),
			topLevel: git(workspace, "rev-parse", "--show-toplevel"),
			objectFormat: git(workspace, "rev-parse", "--show-object-format"),
		});
		const patchHash = sha256(patch);
		const authorityContent = {
			axis: "standards",
			rules: ["review supplied candidate only", "do not mutate Git state"],
		};
		const documents = [
			{
				path: "agent-pilot/authority",
				hash: sha256Canonical(authorityContent),
				content: authorityContent,
			},
		];
		const changedFiles = changedPaths.map(({ path }) => path);
		const memberWithoutHash = {
			candidateId: "member-1",
			workOrderId: "work-1",
			assignmentId: "assignment-1",
			patchHash,
			evidenceManifestId: "evidence-1",
			evidenceManifestHash: sha256Canonical({ evidence: ["patch captured"] }),
			validationSnapshotId: "validation-1",
			validationSnapshotHash: sha256Canonical({ validation: "passed" }),
			authorityManifestHash: sha256Canonical(authorityContent),
			dependencyOrder: 0,
			changedFiles,
		};
		const member = {
			candidateId: memberWithoutHash.candidateId,
			candidateHash: sha256Canonical(memberWithoutHash),
			...memberWithoutHash,
		};
		const interactionValidation = {
			id: "interaction-1",
			snapshotHash: sha256Canonical({
				status: "passed",
				evidence: ["candidate patch captured"],
			}),
			passed: true as const,
			evidence: ["candidate patch captured"],
		};
		const decision = {
			id: "decision-1",
			category: "implementation-review",
		};
		const referencePaths = {
			"skills/code-review/SMELL-BASELINE.md": join(
				skillsRepository,
				"skills",
				"code-review",
				"SMELL-BASELINE.md",
			),
			"skills/code-review/candidate-review.schema.json": schemaPath,
			"skills/thermo-nuclear-code-quality-review/thermo-nuclear-code-quality-reviewer.md": join(
				skillsRepository,
				"skills",
				"thermo-nuclear-code-quality-review",
				"thermo-nuclear-code-quality-reviewer.md",
			),
		};
		const candidate: CandidateRequest["candidate"] = {
			schemaVersion: 4,
			id: "candidate-1",
			runId: "run-1",
			reviewUnitId: "unit-1",
			repositoryFingerprint,
			base: { headHash: baseHeadHash, treeHash: baseTreeHash },
			aggregate: {
				treeHash: aggregateTreeHash,
				diffHash: patchHash,
				patchHash,
				patchPath,
				changedPaths,
				changedPathInventoryHash: sha256Canonical(changedPaths),
			},
			memberCandidates: [member],
			authorityManifestHash: sha256Canonical(authorityContent),
			reviewRequirementDecisionId: decision.id,
			reviewRequirementDecisionHash: sha256Canonical(decision),
			interactionValidation,
			skillProvenance: {
				repository: skillsRepository,
				revision: git(skillsRepository, "rev-parse", "HEAD"),
				packageHashes: { "code-review": fileHash(skillPath) },
				referenceHashes: Object.fromEntries(
					Object.entries(referencePaths).map(([path, source]) => [path, fileHash(source)]),
				),
			},
			workspacePath: workspace,
			createdAt: "2026-08-21T00:00:00.000Z",
		};
		const context = {
			contextHash: "",
			documents,
			protocolSources: [
				{ path: skillPath, hash: fileHash(skillPath) },
				{ path: schemaPath, hash: fileHash(schemaPath) },
			],
			allowedPaths: changedFiles,
		};
		context.contextHash = sha256Canonical({
			axis: "standards",
			documents: context.documents,
			protocolSources: context.protocolSources,
			allowedPaths: context.allowedPaths,
		});
		const request: CandidateRequest = {
			mode: "candidate",
			protocolVersion: "candidate.v1",
			axis: "standards",
			candidate,
			candidateHash: sha256Canonical(candidate),
			workspace: {
				root: workspace,
				repositoryFingerprint,
				expectedHeadHash: baseHeadHash,
				expectedTreeHash: aggregateTreeHash,
				expectedChangedPathsHash: candidate.aggregate.changedPathInventoryHash,
				clean: true,
			},
			context,
		};
		return { repository: workspace, patchPath, request };
	} catch (error) {
		await rm(alternateIndex, { force: true });
		await rm(patchPath, { force: true });
		await rm(workspace, { recursive: true, force: true });
		throw error;
	}
}
