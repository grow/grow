---
$title: Content
$order: 5
---
## Strings

- All content strings should be managed such that non-developers can make changes.

## Data


## Branch names

Use the following naming conventions for branches.

`master`

- The single, main evergreen branch.
- `master` mirrors the live site.
- Most work should branch from `master`.

`feature/<id>`

- Used to develop a specific feature or enhancement.

`hotfix/<id>`

- Used for small fixes that need to be deployed immediately.

`localize/<id>`

- Used for long workstreams related to localization.

In all cases above, the `<id>` placeholder should either be the bug/issue
ID, or a plain, concise name that can identify the workstream.

## Merging

Move history forward and avoid merge commits. *Rebase* your branch with
`master` before merging and pushing to keep the Git history moving forward.

Larger launches and enhancements may be squashed into a single commit prior to
merging, so they can be easily undone later. In general, projects during the
pre-launch phase will receive many iterative commits. Post-launch maintenance,
and incremental launches may benefit from sqaushed commits.

```bash
# Create a new branch.
git checkout -b feature/123

...
# Make changes.
...

# When ready to merge, rebase with origin/master.
git fetch
git rebase origin/master

# Merge the changes to master.
git checkout master
git push origin master
```

## Remote names

Projects frequently have multiple remotes (for example, when working on an
internal Git host and an external Git host). Be consistent with your remote
names across projects to avoid confusion.

Avoid over-using `origin` as the meaning behind `origin` may change if you
frequently work with multiple remotes.Easy-to-remember remote names describe
the remote (e.g. `github` for GitHub, `gitlab` for Gitlab, or `google` for
Google Cloud Source Repositories).

## Commit messages

Use represent tense.

  - Good: Fix, Change, Add, Refactor, Update
  - Bad: Fixed, Changed, Added, Refactored, Updated, Fixing, Changing, Adding, Refactoring, Updating

Begin subject lines with an active verb describing the issue. Treat the subject
line of a Git commit like the subject line of an email, and avoid adding
terminating punctuation.

  - Good: Fix broken carousel component
  - Bad: A fix for the broken carousel component
  - Bad: Fixing broken carousel component
  - Bad: Fix broken carousel component.

Prefix the issue, task, or bug ID to the front of the commit message.

  - Good: b/1234 - Add hero module for device
  - Bad: Add hero module for device - b/1234
