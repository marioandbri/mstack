import { describe, expect, test } from "bun:test";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";
import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import Ajv2020 from "ajv/dist/2020.js";
import addFormats from "ajv-formats";
import {
	runCandidateProtocol,
	sha256Canonical,
	type CandidateRequest,
} from "../skills/code-review/candidate-harness";
import { createRealCandidateFixture } from "./code-review-candidate-fixture";

const repository = join(import.meta.dir, "..");
const skillPath = join(repository, "skills", "code-review", "SKILL.md");
const schemaPath = join(
	repository,
	"skills",
	"code-review",
	"candidate-review.schema.json",
);
const sha = (character: string) => `sha256:${character.repeat(64)}`;
const gitObject = (character: string) => character.repeat(40);

type JsonSchema = {
	oneOf?: Array<{
		$ref?: string;
		properties?: Record<string, { const?: string; enum?: string[] }>;
	}>;
	$defs?: Record<
		string,
		{
			required?: string[];
			pattern?: string;
			properties?: Record<
				string,
				{
					const?: string;
					enum?: string[];
					required?: string[];
					$ref?: string;
					minItems?: number;
					pattern?: string;
					content?: unknown;
				}
			>;
			not?: { required?: string[]; anyOf?: Array<{ required?: string[] }> };
		}
	>;
};

function readContract(): { skill: string; schema: JsonSchema } {
	return {
		skill: readFileSync(skillPath, "utf8"),
		schema: JSON.parse(readFileSync(schemaPath, "utf8")) as JsonSchema,
	};
}

function candidateValidator() {
	const schema = JSON.parse(readFileSync(schemaPath, "utf8"));
	const ajv = new Ajv2020({
		allErrors: true,
		strict: true,
		strictRequired: false,
	});
	addFormats(ajv);
	return ajv.compile(schema);
}

function git(repository: string, ...arguments_: string[]): string {
	return execFileSync("git", arguments_, {
		cwd: repository,
		encoding: "utf8",
	}).trim();
}

function gitRaw(repository: string, ...arguments_: string[]): Buffer {
	return execFileSync("git", arguments_, {
		cwd: repository,
		encoding: "buffer",
	}) as Buffer;
}

function firstMember(value: CandidateRequest) {
	const member = value.candidate.memberCandidates[0];
	if (!member) throw new Error("Candidate fixture is missing its member");
	return member;
}

function firstDocument(value: CandidateRequest) {
	const document = value.context.documents[0];
	if (!document) throw new Error("Candidate fixture is missing its document");
	return document;
}

function firstProtocolSource(
	value: CandidateRequest,
) {
	const source = value.context.protocolSources[0];
	if (!source)
		throw new Error("Candidate fixture is missing its protocol source");
	return source;
}

type PathSegment = string | number;

function deleteAtPath(value: unknown, path: readonly PathSegment[]): void {
	let current: unknown = value;
	for (const [index, segment] of path.entries()) {
		if (!current || typeof current !== "object") {
			throw new Error(`Cannot delete ${path.join(".")}`);
		}
		if (index === path.length - 1) {
			delete (current as Record<string, unknown>)[String(segment)];
			return;
		}
		current = (current as Record<string, unknown>)[String(segment)];
	}
}

const requiredCandidateFields: Array<{
	label: string;
	path: readonly PathSegment[];
}> = [
	{ label: "request.mode", path: ["mode"] },
	{ label: "request.protocolVersion", path: ["protocolVersion"] },
	{ label: "request.axis", path: ["axis"] },
	{ label: "request.candidate", path: ["candidate"] },
	{ label: "request.candidateHash", path: ["candidateHash"] },
	{ label: "request.workspace", path: ["workspace"] },
	{ label: "request.context", path: ["context"] },
	{ label: "candidate.schemaVersion", path: ["candidate", "schemaVersion"] },
	{ label: "candidate.id", path: ["candidate", "id"] },
	{ label: "candidate.runId", path: ["candidate", "runId"] },
	{ label: "candidate.reviewUnitId", path: ["candidate", "reviewUnitId"] },
	{
		label: "candidate.repositoryFingerprint",
		path: ["candidate", "repositoryFingerprint"],
	},
	{ label: "candidate.base", path: ["candidate", "base"] },
	{ label: "candidate.base.headHash", path: ["candidate", "base", "headHash"] },
	{ label: "candidate.base.treeHash", path: ["candidate", "base", "treeHash"] },
	{ label: "candidate.aggregate", path: ["candidate", "aggregate"] },
	{
		label: "candidate.aggregate.treeHash",
		path: ["candidate", "aggregate", "treeHash"],
	},
	{
		label: "candidate.aggregate.diffHash",
		path: ["candidate", "aggregate", "diffHash"],
	},
	{
		label: "candidate.aggregate.patchHash",
		path: ["candidate", "aggregate", "patchHash"],
	},
	{
		label: "candidate.aggregate.patchPath",
		path: ["candidate", "aggregate", "patchPath"],
	},
	{
		label: "candidate.aggregate.changedPaths",
		path: ["candidate", "aggregate", "changedPaths"],
	},
	{
		label: "candidate.aggregate.changedPaths[0].path",
		path: ["candidate", "aggregate", "changedPaths", 0, "path"],
	},
	{
		label: "candidate.aggregate.changedPaths[0].status",
		path: ["candidate", "aggregate", "changedPaths", 0, "status"],
	},
	{
		label: "candidate.aggregate.changedPathInventoryHash",
		path: ["candidate", "aggregate", "changedPathInventoryHash"],
	},
	{
		label: "candidate.memberCandidates",
		path: ["candidate", "memberCandidates"],
	},
	{
		label: "member.candidateId",
		path: ["candidate", "memberCandidates", 0, "candidateId"],
	},
	{
		label: "member.candidateHash",
		path: ["candidate", "memberCandidates", 0, "candidateHash"],
	},
	{
		label: "member.workOrderId",
		path: ["candidate", "memberCandidates", 0, "workOrderId"],
	},
	{
		label: "member.assignmentId",
		path: ["candidate", "memberCandidates", 0, "assignmentId"],
	},
	{
		label: "member.patchHash",
		path: ["candidate", "memberCandidates", 0, "patchHash"],
	},
	{
		label: "member.evidenceManifestId",
		path: ["candidate", "memberCandidates", 0, "evidenceManifestId"],
	},
	{
		label: "member.evidenceManifestHash",
		path: ["candidate", "memberCandidates", 0, "evidenceManifestHash"],
	},
	{
		label: "member.validationSnapshotId",
		path: ["candidate", "memberCandidates", 0, "validationSnapshotId"],
	},
	{
		label: "member.validationSnapshotHash",
		path: ["candidate", "memberCandidates", 0, "validationSnapshotHash"],
	},
	{
		label: "member.authorityManifestHash",
		path: ["candidate", "memberCandidates", 0, "authorityManifestHash"],
	},
	{
		label: "member.dependencyOrder",
		path: ["candidate", "memberCandidates", 0, "dependencyOrder"],
	},
	{
		label: "candidate.authorityManifestHash",
		path: ["candidate", "authorityManifestHash"],
	},
	{
		label: "candidate.reviewRequirementDecisionId",
		path: ["candidate", "reviewRequirementDecisionId"],
	},
	{
		label: "candidate.reviewRequirementDecisionHash",
		path: ["candidate", "reviewRequirementDecisionHash"],
	},
	{
		label: "candidate.interactionValidation",
		path: ["candidate", "interactionValidation"],
	},
	{
		label: "interaction.id",
		path: ["candidate", "interactionValidation", "id"],
	},
	{
		label: "interaction.snapshotHash",
		path: ["candidate", "interactionValidation", "snapshotHash"],
	},
	{
		label: "interaction.passed",
		path: ["candidate", "interactionValidation", "passed"],
	},
	{
		label: "interaction.evidence",
		path: ["candidate", "interactionValidation", "evidence"],
	},
	{
		label: "candidate.skillProvenance",
		path: ["candidate", "skillProvenance"],
	},
	{
		label: "skillProvenance.repository",
		path: ["candidate", "skillProvenance", "repository"],
	},
	{
		label: "skillProvenance.revision",
		path: ["candidate", "skillProvenance", "revision"],
	},
	{
		label: "skillProvenance.packageHashes",
		path: ["candidate", "skillProvenance", "packageHashes"],
	},
	{
		label: "skillProvenance.referenceHashes",
		path: ["candidate", "skillProvenance", "referenceHashes"],
	},
	{
		label: "skillProvenance.referenceHashes.SMELL-BASELINE",
		path: [
			"candidate",
			"skillProvenance",
			"referenceHashes",
			"skills/code-review/SMELL-BASELINE.md",
		],
	},
	{
		label: "skillProvenance.referenceHashes.schema",
		path: [
			"candidate",
			"skillProvenance",
			"referenceHashes",
			"skills/code-review/candidate-review.schema.json",
		],
	},
	{
		label: "skillProvenance.referenceHashes.thermo",
		path: [
			"candidate",
			"skillProvenance",
			"referenceHashes",
			"skills/thermo-nuclear-code-quality-review/thermo-nuclear-code-quality-reviewer.md",
		],
	},
	{ label: "candidate.createdAt", path: ["candidate", "createdAt"] },
	{ label: "workspace.root", path: ["workspace", "root"] },
	{
		label: "workspace.repositoryFingerprint",
		path: ["workspace", "repositoryFingerprint"],
	},
	{
		label: "workspace.expectedHeadHash",
		path: ["workspace", "expectedHeadHash"],
	},
	{
		label: "workspace.expectedTreeHash",
		path: ["workspace", "expectedTreeHash"],
	},
	{
		label: "workspace.expectedChangedPathsHash",
		path: ["workspace", "expectedChangedPathsHash"],
	},
	{ label: "workspace.clean", path: ["workspace", "clean"] },
	{ label: "context.contextHash", path: ["context", "contextHash"] },
	{ label: "context.documents", path: ["context", "documents"] },
	{ label: "document.path", path: ["context", "documents", 0, "path"] },
	{ label: "document.hash", path: ["context", "documents", 0, "hash"] },
	{ label: "document.content", path: ["context", "documents", 0, "content"] },
	{ label: "context.protocolSources", path: ["context", "protocolSources"] },
	{
		label: "protocolSource.path",
		path: ["context", "protocolSources", 0, "path"],
	},
	{
		label: "protocolSource.hash",
		path: ["context", "protocolSources", 0, "hash"],
	},
	{ label: "context.allowedPaths", path: ["context", "allowedPaths"] },
];

function executeFixedPointMode(
	fixedPoint: string,
	gitRunner: (...arguments_: string[]) => string,
): {
	fixedPointHash: string;
	headHash: string;
	mergeBaseHash: string;
	diff: string;
	log: string;
} {
	const fixedPointHash = gitRunner("rev-parse", fixedPoint);
	const headHash = gitRunner("rev-parse", "HEAD");
	const mergeBaseHash = gitRunner("merge-base", fixedPointHash, headHash);
	const diff = gitRunner("diff", "--name-only", `${fixedPointHash}...${headHash}`);
	const log = gitRunner("log", `${fixedPointHash}..${headHash}`, "--format=%s");
	if (!diff) throw new Error("Fixed-point review has an empty diff");
	return { fixedPointHash, headHash, mergeBaseHash, diff, log };
}

describe("code-review candidate protocol", () => {
	test("discriminates candidate from the existing fixed-point request", () => {
		const { schema } = readContract();
		const modes = (schema.oneOf ?? [])
			.map((branch) => branch.$ref?.split("/").pop())
			.map(
				(definition) =>
					schema.$defs?.[definition ?? ""]?.properties?.mode?.const,
			)
			.filter((mode): mode is string => typeof mode === "string");

		expect(modes).toEqual(["fixed-point", "candidate"]);
	});

	test("requires one isolated review axis and immutable candidate bindings", () => {
		const { schema } = readContract();
		const candidate = schema.$defs?.candidateRequest;

		expect(candidate?.required).toEqual([
			"mode",
			"protocolVersion",
			"axis",
			"candidate",
			"candidateHash",
			"workspace",
			"context",
		]);
		expect(candidate?.properties?.axis?.enum).toEqual([
			"standards",
			"spec",
			"structural_quality",
		]);
		expect(schema.$defs?.reviewUnitCandidate?.required).toEqual([
			"schemaVersion",
			"id",
			"runId",
			"reviewUnitId",
			"repositoryFingerprint",
			"base",
			"aggregate",
			"memberCandidates",
			"authorityManifestHash",
			"reviewRequirementDecisionId",
			"reviewRequirementDecisionHash",
			"interactionValidation",
			"skillProvenance",
			"createdAt",
		]);
		expect(schema.$defs?.gitObjectId?.pattern).toBe(
			"^(?:[0-9a-f]{40}|[0-9a-f]{64})$",
		);
		expect(schema.$defs?.sha256?.pattern).toBe("^sha256:[0-9a-f]{64}$");
		expect(schema.$defs?.skillProvenance?.properties?.revision?.$ref).toBe(
			"#/$defs/gitObjectId",
		);
		expect(
			schema.$defs?.skillProvenance?.properties?.referenceHashes,
		).toBeDefined();
		expect(schema.$defs?.skillProvenance?.required).toContain(
			"referenceHashes",
		);
		expect(schema.$defs?.aggregateBinding?.required).toContain(
			"changedPathInventoryHash",
		);
		expect(schema.$defs?.baseBinding?.required).toEqual([
			"headHash",
			"treeHash",
		]);
		expect(schema.$defs?.baseBinding?.properties?.head).toBeUndefined();
		expect(schema.$defs?.aggregateBinding?.required).toContain("treeHash");
		expect(
			schema.$defs?.aggregateBinding?.properties?.changedPaths?.minItems,
		).toBe(1);
		expect(schema.$defs?.axisContext?.required).toEqual([
			"contextHash",
			"documents",
			"protocolSources",
			"allowedPaths",
		]);
		expect(schema.$defs?.protocolSource?.properties?.path?.pattern).toBe("^/");
		expect(schema.$defs?.hashedDocument?.properties?.content).toBeDefined();
		expect(candidate?.not?.anyOf?.map((branch) => branch.required)).toEqual([
			["fixedPoint"],
			["thermo"],
		]);
	});

	test("rejects every missing required field in fixed-point and candidate packets", async () => {
		const validate = candidateValidator();
		const fixedPoint = { mode: "fixed-point", fixedPoint: "HEAD~1" };
		expect(validate(fixedPoint), JSON.stringify(validate.errors)).toBe(true);
		expect(validate({ fixedPoint: "HEAD~1" })).toBe(true);
		const missingFixedPoint = { mode: "fixed-point" };
		expect(validate(missingFixedPoint)).toBe(false);

		const fixture = await createRealCandidateFixture(
			repository,
			skillPath,
			schemaPath,
		);
		try {
			for (const { label, path } of requiredCandidateFields) {
				const missing = structuredClone(fixture.request);
				deleteAtPath(missing, path);
				expect(validate(missing), label).toBe(false);
			}
		} finally {
			await rm(fixture.patchPath, { force: true });
			await rm(fixture.repository, { recursive: true, force: true });
		}
	});

	test("documents read-only isolation and provenance/hash checks", () => {
		const { skill } = readContract();

		expect(skill).toContain("Candidate mode");
		expect(skill).toContain("never resolves `HEAD`");
		expect(skill).toContain("ambient staged or unstaged changes");
		expect(skill).toContain("Standards, Spec, and Structural Quality");
		expect(skill).toContain("engineering-skills revision");
		expect(skill).toContain("exact hashes");
		expect(skill).toContain("sibling reports");
		expect(skill).toContain("protocolSources");
		expect(skill).toContain("allowedPaths");
		expect(skill).toContain("candidate-harness.ts");
		expect(skill).toContain("at least one complete structured finding");
	});

	test("accepts a real candidate packet and rejects identity corruption", async () => {
		const fixture = await createRealCandidateFixture(
			repository,
			skillPath,
			schemaPath,
		);
		try {
			const validate = candidateValidator();
			const expected = fixture.request;
			const request = structuredClone(expected);
			expect(validate(request), JSON.stringify(validate.errors)).toBe(true);
			expect(request.candidateHash).toBe(sha256Canonical(request.candidate));
			expect(request.candidateHash).not.toBe(request.candidate.aggregate.patchHash);
			expect(runCandidateProtocol(request, expected).candidateHash).toBe(
				request.candidateHash,
			);

			const corruptions: Array<{
				label: string;
				mutate: (value: CandidateRequest) => void;
			}> = [
				{ label: "review axis", mutate: (value) => (value.axis = "spec") },
				{
					label: "candidate identity",
					mutate: (value) => (value.candidate.id = "candidate-2"),
				},
				{
					label: "candidate hash",
					mutate: (value) => (value.candidateHash = sha("f")),
				},
				{
					label: "run binding",
					mutate: (value) => (value.candidate.runId = "run-2"),
				},
				{
					label: "Review Unit binding",
					mutate: (value) => (value.candidate.reviewUnitId = "unit-2"),
				},
				{
					label: "repository fingerprint",
					mutate: (value) => (value.candidate.repositoryFingerprint = sha("f")),
				},
				{
					label: "base head",
					mutate: (value) => (value.candidate.base.headHash = gitObject("f")),
				},
				{
					label: "aggregate tree",
					mutate: (value) => (value.candidate.aggregate.treeHash = gitObject("f")),
				},
				{
					label: "workspace root",
					mutate: (value) => (value.workspace.root = "/state/other"),
				},
				{
					label: "workspace expected head",
					mutate: (value) => (value.workspace.expectedHeadHash = gitObject("f")),
				},
				{
					label: "workspace expected tree",
					mutate: (value) => (value.workspace.expectedTreeHash = gitObject("f")),
				},
				{
					label: "changed path inventory",
					mutate: (value) =>
						(value.workspace.expectedChangedPathsHash = sha("f")),
				},
				{
					label: "aggregate patch hash",
					mutate: (value) => (value.candidate.aggregate.patchHash = sha("f")),
				},
				{
					label: "aggregate changed path",
					mutate: (value) =>
						(value.candidate.aggregate.changedPaths[0]!.path = "src/other.ts"),
				},
				{
					label: "member assignment",
					mutate: (value) => (firstMember(value).assignmentId = "assignment-2"),
				},
				{
					label: "review requirement decision",
					mutate: (value) =>
						(value.candidate.reviewRequirementDecisionHash = sha("f")),
				},
				{
					label: "skill provenance",
					mutate: (value) =>
						(value.candidate.skillProvenance.revision = gitObject("f")),
				},
				{
					label: "document content",
					mutate: (value) => (firstDocument(value).content = { rules: ["changed"] }),
				},
				{
					label: "protocol hash",
					mutate: (value) => (firstProtocolSource(value).hash = sha("f")),
				},
				{
					label: "context hash",
					mutate: (value) => (value.context.contextHash = sha("f")),
				},
			];
			for (const { label, mutate } of corruptions) {
				const candidate = structuredClone(request);
				mutate(candidate);
				expect(() => runCandidateProtocol(candidate, expected), label).toThrow();
			}
		} finally {
			await rm(fixture.patchPath, { force: true });
			await rm(fixture.repository, { recursive: true, force: true });
		}
	});

	test("candidate mode reads the supplied packet without touching real Git state", async () => {
		const fixture = await createRealCandidateFixture(
			repository,
			skillPath,
			schemaPath,
		);
		try {
			const { repository: workspace, request } = fixture;
			const expected = structuredClone(request);
			await Bun.write(join(workspace, "staged.ts"), "export const staged = true;\n");
			git(workspace, "add", "staged.ts");
			await Bun.write(join(workspace, "feature.ts"), "export const value = 99;\n");
			await Bun.write(join(workspace, "ambient.ts"), "export const ambient = true;\n");

			const indexPath = join(workspace, git(workspace, "rev-parse", "--git-path", "index"));
			const before = {
				head: git(workspace, "rev-parse", "HEAD"),
				refs: git(workspace, "show-ref"),
				reflog: gitRaw(workspace, "reflog", "--all"),
				index: readFileSync(indexPath),
				staged: gitRaw(workspace, "diff", "--cached", "--binary"),
				unstaged: gitRaw(workspace, "diff", "--binary"),
				status: gitRaw(workspace, "status", "--porcelain=v1", "-z"),
				objects: gitRaw(workspace, "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)"),
			};
			expect(before.status.toString("utf8")).toContain("A  staged.ts");
			expect(before.status.toString("utf8")).toContain(" M feature.ts");
			expect(before.status.toString("utf8")).toContain("?? ambient.ts");

			const result = runCandidateProtocol(request, expected);
			const after = {
				head: git(workspace, "rev-parse", "HEAD"),
				refs: git(workspace, "show-ref"),
				reflog: gitRaw(workspace, "reflog", "--all"),
				index: readFileSync(indexPath),
				staged: gitRaw(workspace, "diff", "--cached", "--binary"),
				unstaged: gitRaw(workspace, "diff", "--binary"),
				status: gitRaw(workspace, "status", "--porcelain=v1", "-z"),
				objects: gitRaw(workspace, "cat-file", "--batch-all-objects", "--batch-check=%(objectname) %(objecttype)"),
			};

			expect(result).toEqual({
				mode: "candidate",
				protocolVersion: "candidate.v1",
				axis: "standards",
				candidateId: request.candidate.id,
				candidateHash: request.candidateHash,
				patchPath: request.candidate.aggregate.patchPath,
				changedPaths: request.candidate.aggregate.changedPaths,
			});
			expect(after.head).toBe(before.head);
			expect(after.refs).toBe(before.refs);
			expect(after.reflog.equals(before.reflog)).toBe(true);
			expect(after.index.equals(before.index)).toBe(true);
			expect(after.staged.equals(before.staged)).toBe(true);
			expect(after.unstaged.equals(before.unstaged)).toBe(true);
			expect(after.status.equals(before.status)).toBe(true);
			expect(after.objects.equals(before.objects)).toBe(true);

			await Bun.write(fixture.patchPath, "tampered candidate patch\n");
			expect(() => runCandidateProtocol(request, expected)).toThrow(
				"Candidate patch hash mismatch",
			);
		} finally {
			await rm(fixture.patchPath, { force: true });
			await rm(fixture.repository, { recursive: true, force: true });
		}
	});

	test("freezes fixed point, HEAD, and merge base without consuming ambient Git state", async () => {
		const repository = await mkdtemp(
			join(tmpdir(), "code-review-fixed-point-"),
		);
		try {
			git(repository, "init", "-q");
			git(repository, "config", "user.email", "fixture@example.com");
			git(repository, "config", "user.name", "Fixture");
			await Bun.write(
				join(repository, "feature.ts"),
				"export const value = 1;\n",
			);
			git(repository, "add", "feature.ts");
			git(repository, "commit", "-qm", "baseline");
			const fixedPoint = git(repository, "rev-parse", "HEAD");

			await Bun.write(
				join(repository, "feature.ts"),
				"export const value = 2;\n",
			);
			git(repository, "add", "feature.ts");
			git(repository, "commit", "-qm", "candidate");
			const gitCalls: string[][] = [];
			const review = executeFixedPointMode(fixedPoint, (...arguments_: string[]) => {
				gitCalls.push(arguments_);
				return git(repository, ...arguments_);
			});
			const refsBeforeAmbientChanges = git(repository, "show-ref");

			expect(review.fixedPointHash).toBe(fixedPoint);
			expect(review.mergeBaseHash).toBe(fixedPoint);
			expect(review.diff).toBe("feature.ts");
			expect(review.log).toBe("candidate");
			expect(gitCalls).toEqual([
				["rev-parse", fixedPoint],
				["rev-parse", "HEAD"],
				["merge-base", fixedPoint, review.headHash],
				["diff", "--name-only", `${fixedPoint}...${review.headHash}`],
				["log", `${fixedPoint}..${review.headHash}`, "--format=%s"],
			]);

			await Bun.write(
				join(repository, "feature.ts"),
				"export const value = 3;\n",
			);
			git(repository, "add", "feature.ts");
			git(repository, "commit", "-qm", "later", "--", "feature.ts");
			expect(git(repository, "rev-parse", "HEAD")).not.toBe(review.headHash);

			await Bun.write(
				join(repository, "staged.ts"),
				"export const staged = true;\n",
			);
			git(repository, "add", "staged.ts");
			await Bun.write(
				join(repository, "ambient.ts"),
				"export const ambient = true;\n",
			);

			expect(review.headHash).not.toBe(git(repository, "rev-parse", "HEAD"));
			expect(git(repository, "show-ref")).not.toBe(refsBeforeAmbientChanges);
			expect(
				git(repository, "status", "--porcelain").split("\n").sort(),
			).toEqual(["?? ambient.ts", "A  staged.ts"]);
		} finally {
			await rm(repository, { recursive: true, force: true });
		}
	});
});
