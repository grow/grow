---
$title: Git + Grow = ♡
$category: Workflow
$order: 5
---
[TOC]

Grow pods are backed by Git to bring joy to content management and launch workflow. Yes, thanks to Git and a branching model that integrates with Grow's SDK, Grow attempts to make everything from massive redesigns to quick hotfixes joyful and predictable. You'll be able to stop guessing about the state of your web site, and take control back of your workflow.

Read on to learn how to properly use Git with Grow pods to ensure compatibility with Grow.

## One pod == one repo

Each pod lives within its own Git repository.

## Branches and development

In Grow, the names of Git branches carry meaning. When a user makes a change to a site, she must first decide whether the change is a "dev" change, a "feature" change, or a "hotfix".

The following branch naming conventions are used for consistency:

- `master` – The master branch is "sacred" and pod files committed here should be production-ready. Every release candidate must be commited to master.
- `dev` – For incremental development. Typical site development should take place in the dev branch.
- `feature/<name>` – For major site changes, such as redesigns. When features are complete, they should be integrated into the dev branch.
- `hotfix/<name>` – For hotfixes made to the production site. Hotfixes branch from master, and must merge back into both master and dev.
- `translation/<name>` – Strictly for translation work. Just like hotfixes, translations branch from master, and must merge back into both master and dev.

This branching model is based on [@nvie's Git branchind model](http://nvie.com/posts/a-successful-git-branching-model/).
