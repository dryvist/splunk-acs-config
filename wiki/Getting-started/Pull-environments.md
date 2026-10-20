# Step 8: Pull environments

[Home](/Home) > [Getting started](/Getting-started) > Pull environments

[[_TOC_]]

**Where:** **Pipelines → the config pipeline → Run pipeline**

**Do:**

1. Select **Run pipeline**.
2. Keep **Environment** as `all`.
3. Select `pull` as **Action**.
4. Keep **Object types** as `all`.
5. Keep **Object names** as `all`.
6. Keep **Delete live-only objects** unchecked.
7. Select **Run**.
8. Wait for the run to finish.

With `all`, the run pulls environments in reverse name order, so `prod` runs
before `nonprod`. Every environment commits to one branch,
`acs-pull/<build id>`, with one pull request. The first environment pulled
sets each object's base values; later environments add only their
differences as overrides.

**Verify:**

1. Confirm the `pull prod live into repo` job finished before the
   `pull nonprod live into repo` job started.
2. Confirm the last step prints a pull request link, or `Pull request for
   acs-pull/<build id> is already open`.
3. Confirm a run with no changes prints `NO DIFFERENCES` and opens no pull
   request.
4. Confirm no step in the run is a push step.

## Related

- [Getting started](/Getting-started)
- [Merge pull requests](/Getting-started/Merge-pull-requests)
- [Commands](/Reference/Commands)

---

[< Previous: Create environments](/Getting-started/Create-environments) |
[Next: Merge pull requests >](/Getting-started/Merge-pull-requests)
