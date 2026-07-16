---
name: github-publisher
description: "Use when the user asks to publish, push, upload, sync, commit and push, create a GitHub repository, update an existing GitHub repository, or put a local project or Skill on GitHub. Protect remotes, default branches, history, credentials, private files, and repository visibility."
---

# GitHub Publisher

Publish local work to GitHub while preserving history, privacy, and explicit authorization.

## Success Criteria

- The correct owner, repository, and visibility are selected.
- GitHub authentication is checked in the same OS identity that runs `git` and `gh`.
- Local work is committed on the intended branch.
- The intended branch is pushed and tracks the remote default branch.
- No unrelated private files, backups, secrets, or accidental extra branches are pushed.

## Workflow

1. Read the governing agent policy for the current environment.
2. Inspect local Git state:

   ```bash
   git status --short --branch
   git remote -v
   git branch -a -vv
   git log --oneline --decorate --graph --all -5
   ```

3. Check GitHub authentication in the same OS identity:

   ```bash
   gh auth status
   ```

4. Before creating a remote repository, explicitly confirm:

   - GitHub owner;
   - repository name;
   - `public` or `private` visibility.

   Making a repository public requires immediate explicit confirmation. Do not infer public visibility from a general request to "publish."

5. Identify the target repository:

   - If `origin` exists, inspect and use it unless the user requested another repository.
   - If no remote exists, run `gh repo view <owner>/<repo>` before creating anything.
   - If the name already exists, stop creating, inspect the existing repository, and preserve its history.

6. For an existing repository:

   - fetch before pushing;
   - read its default branch and visibility;
   - work on the remote default branch unless the user requested another;
   - do not create or push an accidental `master` branch when the default is `main`.

7. Stage only intended files:

   - inspect `git status --short` and `git diff --stat`;
   - exclude credentials, `.env`, cookies, recovery codes, backups, caches, reports, and tool state;
   - leave unrelated dirty files unstaged.

8. Commit with a concise message and push the intended branch:

   ```bash
   git push -u origin <default-branch>
   ```

9. Verify:

   ```bash
   git status --short --branch
   git ls-remote --heads origin
   gh repo view <owner>/<repo> --json defaultBranchRef,url,visibility,updatedAt
   ```

## High-Risk Actions

Obtain explicit confirmation immediately before:

- `git push --force` or `--force-with-lease`;
- deleting a remote branch;
- making a repository public or changing visibility;
- overwriting unrelated remote history;
- changing collaborators, settings, branch protection, or default branch.

Never place a personal access token in chat or a command line. Authenticate through the supported GitHub CLI or credential manager in the same environment that performs the push.

Credentials, cookies, recovery codes, private account files, and unredacted secrets must never be staged, committed, or pushed. User confirmation cannot override this prohibition. If any are detected, stop, unstage them, and inspect local history before continuing. If they are already committed, do not push until the history is remediated safely.

## Existing Remote With No Local Clone

When a same-name repository already exists but the current folder is a new local repository:

1. Fetch the existing remote.
2. Inspect its default branch, history, and files.
3. Move local changes onto that branch with a normal commit.
4. Push the default branch.
5. Treat any accidental extra branch as cleanup that requires confirmation before deletion.

## Final Report

```markdown
Done:
- Repo: <url>
- Visibility: <public|private>
- Branch: <branch>
- Commit: <sha message>
- Verified: <tracking/default branch/status>
- Not pushed / risks: <only when relevant>
```
