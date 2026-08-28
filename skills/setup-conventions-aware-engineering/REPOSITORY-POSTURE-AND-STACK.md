# Repository posture and stack

Classify the setup run from evidence. Repository posture selects workflow; it is not permanent project metadata. No single signal decides posture.

## Greenfield

Greenfield evidence points to a scaffold rather than an operating system:

- empty or starter source trees;
- placeholder tests and generated starter config;
- no released behavior, persisted migrations, deployed units, external consumers, or compatibility contracts;
- short history containing setup work only.

Use greenfield flow only when combined evidence shows little existing behavior to preserve. Propose minimal docs from confirmed choices, not hypothetical future needs.

## Brownfield

Brownfield evidence shows established behavior or knowledge that setup must preserve:

- functioning source and behavior tests;
- released APIs, schemas, migrations, generated contracts, or external consumers;
- deployment and operational procedures;
- existing architecture, standards, context, runbooks, or package-local instructions;
- history that records ongoing product or system changes.

A brownfield repository remains brownfield when one package is new. Give that package a local scope only when ownership warrants one.

## Ambiguous evidence

Starter config may coexist with real deployments, and imported history may be absent. Present evidence for both postures and ask the user to resolve ambiguity. Do not silently choose based on repository age, commit count, or file count.

Do not persist greenfield, brownfield, or ambiguous classification in project docs. It becomes stale as repository evolves.

## Stack inventory

Inspect environment rather than asking questions it can answer:

- package and language manifests;
- lockfiles and resolved versions;
- workspace definitions and application directories;
- framework, compiler, formatter, test, code-generation, database, mobile, and deployment config;
- scripts and CI workflows;
- installed skills and configuration they consume.

Use this inventory as evidence. A dependency is not a convention by itself.

## Group by concern

Translate stack evidence into smallest real ownership scopes:

| Evidence | Possible concern | Proposal boundary |
| --- | --- | --- |
| Workspace manifest and shared build graph | Workspace | Package boundaries, dependency direction, shared commands |
| HTTP framework or generated API client | API | Contract ownership, generation, compatibility, verification |
| Web framework and component system | Web and design | Rendering boundaries, UI rules, accessibility, tokens |
| Mobile application package | Mobile and design | Platform boundaries, interaction rules, device verification |
| Database toolkit and migrations | Data | Schema ownership, migration safety, generated artifacts |
| Test runner and CI config | Testing | Required seams, commands, environment expectations |
| Deployment manifests | Operations | Release constraints and runbook routing |
| Installed tracker-facing skills | Tracker | Backend, commands, and triage vocabulary |

Do not create one document per package. Merge shared rules at narrowest common concern; keep package-local rules near package only when they do not apply elsewhere.

## External sources

When package behavior matters to a proposed rule, identify detected version and consult current official documentation through available tooling. Explain source with proposal. Record accepted project policy, not copied package manuals or defaults.

`docs/agents/documentation-map.md` routes internal authority. Do not turn it into an external documentation index. Manifests and lockfiles remain source of truth for package versions.
