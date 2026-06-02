# Wendell CI Milestones

## What must be true

Wendell CI works only if these contracts are real:

1. Worlds and scenario packs are versioned.
2. Every scenario has a stable id, rubric, expected outcome, and critical failure definitions.
3. The runner can invoke an agent through a stable adapter contract.
4. The runner can capture a trace containing messages, tool calls, observations, metrics, and scoring evidence.
5. Scores are deterministic enough for CI use, or variability is handled through retries and confidence bands.
6. Advisory mode never blocks CI, but still produces useful reports and uploaded traces.
7. Blocking mode is opt-in and based on explicit gates.
8. Secrets and sensitive trace fields can be redacted before upload.
9. Wendell can compare a run against prior runs by world version, scenario pack, agent version, and commit SHA.
10. Failures are explainable: developers can see which scenario failed, why it failed, and which trace events support that result.
11. Agent execution stays local to the developer machine or CI worker; Wendell supplies evaluation data and stores traces/results.

## Milestone 0: Local package skeleton

Goal: establish the standalone Python package.

Deliverables:

- `wendell-ci` package
- CLI entrypoint
- config model
- result/gate model
- trace upload placeholder
- tests for advisory vs blocking exit behavior

Done when:

- `pip install -e ".[dev]"` works
- `wendell --help` works
- tests pass locally

## Milestone 1: Local advisory runner

Goal: run a scenario pack from disk without requiring Wendell Cloud.

Deliverables:

- `wendell.toml` discovery
- local scenario pack loader
- command-based agent adapter
- JSONL trace artifact writer
- summary output
- advisory mode that always exits `0`

Done when:

- A repo can add Wendell CI without network access
- Developers can inspect local trace artifacts
- Failed gates are visible but non-blocking

## Milestone 2: Gate semantics

Goal: make pass/fail semantics explicit and trustworthy.

Deliverables:

- suite minimum score
- per-scenario minimum score
- critical failure cap
- required step status checks
- optional regression delta checks
- blocking mode with nonzero exit on gate failure

Done when:

- The same run result can be interpreted as advisory or blocking
- Critical failures cannot be hidden by high average scores

## Milestone 3: Wendell trace capture

Goal: make Wendell the system of record for traces and reports.

Deliverables:

- authenticated upload client
- run creation API contract
- trace upload API contract
- final report upload
- redaction hooks
- retry/backoff behavior

Done when:

- CI output links to a Wendell run URL
- Wendell stores scenario traces, scores, metadata, and failure evidence

## Milestone 3.5: Remote data, local execution

Goal: keep customer agent execution local while Wendell remains the source of truth.

Deliverables:

- fetch pinned scenario pack from Wendell
- execute `agent_command` locally
- upload redacted traces to Wendell
- never send local source code or agent secrets to Wendell
- include commit SHA, agent adapter metadata, model metadata, and runner version in run metadata

Done when:

- `wendell run` can evaluate a local agent using only remote Wendell public scenario data and tool schemas
- Wendell can show the trace/report without having executed the agent itself

## Milestone 4: Wendell-managed worlds

Goal: keep world creation in Wendell, not the customer repo.

Deliverables:

- fetch pinned world/scenario pack by id and version
- cache packs locally for repeatable CI
- verify world/scenario checksum
- support `latest` only for advisory mode
- require pinned versions for blocking mode

Done when:

- Customers do not author worlds locally
- Blocking CI cannot silently change because a remote scenario pack changed

## Milestone 5: CI integrations

Goal: make adoption easy.

Deliverables:

- GitHub Actions example
- GitLab CI example
- CircleCI example
- PR comment summary format
- artifact upload instructions

Done when:

- First advisory run takes under 10 minutes to install
- CI logs clearly show score, failures, and Wendell report URL

## Milestone 6: Regression intelligence

Goal: move beyond one-off scoring.

Deliverables:

- compare against main branch baseline
- compare against previous model/prompt/tool version
- score deltas by scenario and dimension
- flaky scenario detection
- nightly deep suite support

Done when:

- Wendell can answer what changed and where behavior regressed
