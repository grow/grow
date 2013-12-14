---
$title: Git usage
$category: Reference
---
# Git + Grow = ♡

Grow pods are backed by Git to bring joy to content management and launch workflow. Yes, thanks to Git and a branching model that integrates with Grow's SDK, Grow attempts to make everything from massive redesigns to quick hotfixes joyful and predictable. You'll be able to stop guessing about the state of your web site, and take control back of your workflow.

Read on to learn how to properly use Git with Grow pods to ensure compatibility with the Grow SDK.

## One pod == one repo

Each pod lives within its own Git repository.

## Branches and development

In Grow, the names of Git branches carry meaning. When a user makes a change to a site, she must first decide whether the change is a "dev" change, a "feature" change, or a "hotfix".

The following branches contain __pod files__:

- `master` – The master branch is "sacred" and pod files committed here should be production-ready. Every release candidate must be commited to master.
- `dev` – For incremental development. Typical site development should take place in the dev branch.
- `feature/<name>` – For major site changes, such as redesigns. When features are complete, they should be integrated into the dev branch.
- `hotfix/<name>` – For hot fixes made to the production site. Hot fixes branch from master, and must merge back into both master and dev.

The "build" branch contains __generated files__, not pod files:

- `build` – When commits are made to the master branch, the Grow SDK can build a static version of the site using the state from master, and commit it to the "build" branch. Build branches should only be generated using the "grow build" command, and should never be edited manually.

## Launches and tags

When the state of the build branch is ready to become a real launch, both the build branch, and the master branch used to *make* the build branch, are tagged with the same version number.

In the below example, the branches are tagged for the 12th launch. The `<name>` component is optional, and can be used to help you identify the launch.

- `launch-12-build-<name>` 
- `launch-12-master-<name>`

Therefore, the tagged build branch should represent **exactly** what's on the production server, and the tagged master branch represents **exactly** what was used to make the build branch.

Thanks to master branches, build branches, and tags, you'll be able to precisely know the state of your site (and your launch history) at any time.
