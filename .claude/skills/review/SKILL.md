# PR Review Skill

<!-- configured: false -->

> **NOTE: This is a placeholder skill.** It has not been configured for this repository.
> On first invocation, it will offer to detect the project's stack and interactively build
> a tailored review checklist.

---

## Phase 1: Bootstrap Check

Read this file and check for `<!-- configured: false -->`.

If found:
- Tell the user: "This review skill hasn't been configured for this repo yet. Would you like to initialize it now? (It will ask you a few questions based on what it finds.)"
- If the user says no: proceed to **Review** using the generic checklist below and stop.
- If the user says yes: proceed to **Interactive Initialization**.

If `<!-- configured: true -->` is found, skip to **Review**.

---

## Interactive Initialization

Work through these steps, pausing to ask the user at each detection:

### 1. Detect Languages
Scan for file extensions (`*.py`, `*.go`, `*.ts`, `*.js`, `*.rs`, `*.java`, `*.rb`, etc.) in the repo root and `src/`.

For each language detected, say:
> "I found [language] code. Should I add [language]-specific rules? For example: [list 2–3 sensible defaults for that language, e.g. type hints for Python, error wrapping for Go]"

Let the user confirm, modify, or skip each one before adding it to the checklist.

### 2. Detect Test Framework
Look for `pytest.ini`, `go.mod`, `jest.config.*`, `vitest.config.*`, `package.json` test scripts, `Makefile` test targets, etc.

Ask:
> "It looks like you're using [framework] for tests. Should I require test coverage checks using that framework's conventions?"

### 3. Detect Infrastructure
Look for `*.tf`, `helm/`, `charts/`, `k8s/`, `Dockerfile`, `.github/workflows/`, `.circleci/`.

For each found, ask:
> "I found [terraform files / Helm charts / Dockerfiles / CI workflows]. Should I add a rule to flag PRs that modify these?"

### 4. Detect Auth/Security Patterns
Look for directories or files named `auth/`, `permissions/`, `rbac/`, `middleware/`, `authz/`.

Ask:
> "I found what looks like auth/permission code. Should I add a rule to always flag changes in these paths as requiring extra scrutiny?"

### 5. Write the Checklist
After all confirmations, replace the content between `<!-- project-checklist-start -->` and `<!-- project-checklist-end -->` below with the agreed rules using the Edit tool.

Then replace `<!-- configured: false -->` with `<!-- configured: true -->` and remove the placeholder notice block.

Tell the user: "Review skill configured. You can re-run initialization by changing `configured: true` back to `configured: false` in this file."

Then proceed to **Review**.

---

## Review

Review the PR critically. For each finding assign: `[BLOCKER]`, `[MAJOR]`, `[MINOR]`, or `[INFO]`.

### Universal Checks (always apply)
- Hardcoded secrets or credentials
- Auth/authorization changes (any edits to permissions, roles, middleware)
- Silent error handling or missing input validation at system boundaries
- Breaking changes: API contracts, DB schema, config key renames
- Test coverage for new or modified logic

### Project-Specific Checklist
<!-- project-checklist-start -->
(not yet configured — initialize the skill to populate this)
<!-- project-checklist-end -->

### Output Format

```
## PR Review

### Summary
<one paragraph overview>

### Issues
- [SEVERITY] <file>:<line> — <description>

### Recommendations
<optional non-blocking suggestions>
```
