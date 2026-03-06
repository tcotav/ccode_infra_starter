# Git Ship Skill

End-to-end workflow: verify branch, stage changes, commit, and optionally open a PR.

---

## Step 1: Branch Check

Run `git branch --show-current` and `git rev-parse --abbrev-ref HEAD` to determine the current branch.

**If on `main` or `master`:**

Check whether all changed files are documentation-only. Documentation-only means files whose sole purpose is human-readable docs: `README.md`, `CHANGELOG*`, `LICENSE`, `*.txt`, `*.rst`, or files under a `docs/` directory. This does NOT include skill definitions (`SKILL.md`, `skills/**`), configuration files, or any file that affects runtime behavior.

- Run `git diff --name-only HEAD` and `git status --short` to get the full list of changed files.
- If **all** changes are documentation files: inform the user and ask if they want to continue committing directly to `main`. If they say no, stop here and prompt them to create a branch first.
- If **any** non-documentation files are changed: tell the user they are on `main`/`master` with non-doc changes and **require** them to provide a branch name before continuing. Create and check out the branch with `git checkout -b <branch-name>`.

---

## Step 2: Review Changes

Run the following in parallel to give the user a clear picture of what will be staged:

- `git status --short`
- `git diff` (unstaged changes)
- `git diff --cached` (already staged changes)

Summarize what will be included in the commit. If there are untracked files that look relevant (source files, configs), list them and ask the user if they should be included.

---

## Step 3: Stage Files

Ask the user how they want to stage:

> "Stage all changed/tracked files, or specific ones? (I'll list them if you want to choose)"

- **All**: run `git add` on each modified tracked file individually (never `git add -A` or `git add .` — avoids accidentally staging secrets or build artifacts).
- **Specific**: list the files and let the user select which to include.

Do not stage files matching: `.env`, `*.env`, `*secret*`, `*credential*`, `*.key`, `*.pem`.
If any such files appear in the diff, warn the user explicitly before proceeding.

---

## Step 4: Commit

Draft a commit message based on the staged diff:

- First line: concise summary under 72 characters, imperative mood (e.g., "Add retry logic to API client")
- Body (if changes are non-trivial): brief explanation of *why*, not *what*
- Append: `Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>`

Show the draft message to the user and ask for confirmation or edits before committing.

Run the commit using a heredoc to preserve formatting:

```
git commit -m "$(cat <<'EOF'
<message>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

If the commit fails due to a pre-commit hook, report the hook output, fix the underlying issue, re-stage, and create a **new** commit (never `--amend`).

---

## Step 5: Offer to Create a PR

Ask the user:

> "Would you like to open a pull request for this branch?"

If yes:

1. Check if the branch has a remote tracking branch: `git status -sb`
2. If not pushed yet, push with `git push -u origin <branch-name>`
3. Run `git log main..HEAD --oneline` to summarize commits in this branch
4. Draft a PR title (under 70 chars) and body:

```
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
- <bullet points from commits>

## Test plan
- [ ] <relevant checks>

🤖 Generated with [Claude Code](https://claude.ai/code)
EOF
)"
```

5. Return the PR URL to the user.

If no, confirm the commit was successful and stop.

---

## Safety

- **NEVER** use `git add -A` or `git add .`
- **NEVER** force-push (`--force`, `-f`) unless the user explicitly requests it, and never to `main`/`master`
- **NEVER** skip hooks (`--no-verify`)
- **NEVER** stage files that look like secrets (`.env`, `*.key`, `*.pem`, `*credential*`)
- **NEVER** amend a commit that has already been pushed to a remote
