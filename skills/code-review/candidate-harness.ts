import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

export type CandidateAxis = "standards" | "spec" | "structural_quality";

export type CandidateRequest = {
	mode: "candidate";
	protocolVersion: "candidate.v1";
	axis: CandidateAxis;
	candidate: {
		schemaVersion: 4;
		id: string;
		runId: string;
		reviewUnitId: string;
		repositoryFingerprint: string;
		base: {
			headHash: string;
			treeHash: string;
		};
		aggregate: {
			treeHash: string;
			diffHash: string;
			patchHash: string;
			patchPath: string;
			changedPaths: Array<{
				path: string;
				status: string;
				oldPath?: string;
				mode?: number;
				contentHash?: string;
			}>;
			changedPathInventoryHash: string;
		};
		memberCandidates: Array<{
			candidateId: string;
			candidateHash: string;
			workOrderId: string;
			assignmentId: string;
			patchHash: string;
			evidenceManifestId: string;
			evidenceManifestHash: string;
			validationSnapshotId: string;
			validationSnapshotHash: string;
			authorityManifestHash: string;
			dependencyOrder: number;
			changedFiles?: string[];
		}>;
		authorityManifestHash: string;
		reviewRequirementDecisionId: string;
		reviewRequirementDecisionHash: string;
		interactionValidation: {
			id: string;
			snapshotHash: string;
			passed: true;
			evidence: string[];
		};
		skillProvenance: {
			repository: string;
			revision: string;
			packageHashes: Record<string, string>;
			referenceHashes: Record<string, string>;
		};
		workspacePath?: string;
		createdAt: string;
	};
	candidateHash: string;
	workspace: {
		root: string;
		repositoryFingerprint: string;
		expectedHeadHash: string;
		expectedTreeHash: string;
		expectedChangedPathsHash: string;
		clean: true;
	};
	context: {
		contextHash: string;
		documents: Array<{
			path: string;
			hash: string;
			content: unknown;
		}>;
		protocolSources: Array<{
			path: string;
			hash: string;
		}>;
		allowedPaths: string[];
	};
};

export type CandidateProtocolResult = {
	mode: "candidate";
	protocolVersion: "candidate.v1";
	axis: CandidateAxis;
	candidateId: string;
	candidateHash: string;
	patchPath: string;
	changedPaths: CandidateRequest["candidate"]["aggregate"]["changedPaths"];
};

export class CandidateProtocolError extends Error {
	readonly code:
		| "identity-mismatch"
		| "document-hash-mismatch"
		| "protocol-hash-mismatch"
		| "context-hash-mismatch"
		| "patch-hash-mismatch";

	constructor(
		code: CandidateProtocolError["code"],
		message: string,
		options?: ErrorOptions,
	) {
		super(message, options);
		this.name = "CandidateProtocolError";
		this.code = code;
	}
}

export function canonicalJson(value: unknown): string {
	if (Array.isArray(value)) return `[${value.map(canonicalJson).join(",")}]`;
	if (value && typeof value === "object") {
		return `{${Object.entries(value as Record<string, unknown>)
			.filter(([, entry]) => entry !== undefined)
			.sort(([left], [right]) => left.localeCompare(right))
			.map(([key, entry]) => `${JSON.stringify(key)}:${canonicalJson(entry)}`)
			.join(",")}}`;
	}
	return JSON.stringify(value) ?? "null";
}

export function sha256(value: string | Uint8Array): string {
	return `sha256:${createHash("sha256").update(value).digest("hex")}`;
}

export function sha256Canonical(value: unknown): string {
	return sha256(canonicalJson(value));
}

function sameJson(left: unknown, right: unknown): boolean {
	return canonicalJson(left) === canonicalJson(right);
}

function assertCandidateIdentity(
	request: CandidateRequest,
	expected: CandidateRequest,
): void {
	if (!sameJson(request, expected)) {
		throw new CandidateProtocolError(
			"identity-mismatch",
			"Candidate request does not match the controller's immutable binding",
		);
	}
}

function validateBoundContent(request: CandidateRequest): void {
	if (
		request.workspace.root !== request.candidate.workspacePath ||
		request.workspace.repositoryFingerprint !==
			request.candidate.repositoryFingerprint ||
		request.workspace.expectedHeadHash !== request.candidate.base.headHash ||
		request.workspace.expectedTreeHash !== request.candidate.aggregate.treeHash ||
		request.workspace.expectedChangedPathsHash !==
			request.candidate.aggregate.changedPathInventoryHash
	) {
		throw new CandidateProtocolError(
			"identity-mismatch",
			"Candidate workspace bindings do not match the candidate packet",
		);
	}

	if (
		sha256Canonical(request.candidate.aggregate.changedPaths) !==
		request.candidate.aggregate.changedPathInventoryHash
	) {
		throw new CandidateProtocolError(
			"identity-mismatch",
			"Candidate changed-path inventory hash mismatch",
		);
	}

	let patch: Buffer;
	try {
		patch = readFileSync(request.candidate.aggregate.patchPath);
	} catch (error) {
		throw new CandidateProtocolError(
			"patch-hash-mismatch",
			`Candidate patch is unavailable: ${request.candidate.aggregate.patchPath}`,
			{ cause: error },
		);
	}
	const patchHash = sha256(patch);
	if (
		patchHash !== request.candidate.aggregate.patchHash ||
		patchHash !== request.candidate.aggregate.diffHash
	) {
		throw new CandidateProtocolError(
			"patch-hash-mismatch",
			"Candidate patch hash mismatch",
		);
	}

	for (const document of request.context.documents) {
		if (sha256Canonical(document.content) !== document.hash) {
			throw new CandidateProtocolError(
				"document-hash-mismatch",
				`Candidate context document hash mismatch: ${document.path}`,
			);
		}
	}

	const contextPayload = {
		axis: request.axis,
		documents: request.context.documents,
		protocolSources: request.context.protocolSources,
		allowedPaths: request.context.allowedPaths,
	};
	if (sha256Canonical(contextPayload) !== request.context.contextHash) {
		throw new CandidateProtocolError(
			"context-hash-mismatch",
			"Candidate axis context hash mismatch",
		);
	}

	for (const source of request.context.protocolSources) {
		let content: Buffer;
		try {
			content = readFileSync(source.path);
		} catch (error) {
			throw new CandidateProtocolError(
				"protocol-hash-mismatch",
				`Candidate protocol source is unavailable: ${source.path}`,
				{ cause: error },
			);
		}
		if (sha256(content) !== source.hash) {
			throw new CandidateProtocolError(
				"protocol-hash-mismatch",
				`Candidate protocol source hash mismatch: ${source.path}`,
			);
		}
	}
}

/**
 * Execute the read-only candidate protocol against a controller-supplied
 * immutable request. Candidate mode reviews the supplied patch and context.
 * It deliberately has no Git runner and never creates a ref or touches the
 * workspace index.
 */
export function runCandidateProtocol(
	request: CandidateRequest,
	expected: CandidateRequest,
): CandidateProtocolResult {
	assertCandidateIdentity(request, expected);
	validateBoundContent(request);

	return {
		mode: request.mode,
		protocolVersion: request.protocolVersion,
		axis: request.axis,
		candidateId: request.candidate.id,
		candidateHash: request.candidateHash,
		patchPath: request.candidate.aggregate.patchPath,
		changedPaths: structuredClone(request.candidate.aggregate.changedPaths),
	};
}
