# Step 8: Pull environments

[Home](/Home) > [Getting started](/Getting-started) > Pull environments

[[_TOC_]]

**Where:** **Pipelines → the config pipeline → Run pipeline**

**Do:**

1. Select **Run pipeline**.
2. Type `nonprod` as **Environment**.
3. Select `pull` as **Action**.
4. Keep **Object types** as `all`.
5. Keep **Object names** as `all`.
6. Keep **Delete live-only objects** unchecked.
7. Select **Run**.
8. Wait for the run to finish.

A pull run takes one environment at a time. Pull `prod` only after the
`nonprod` pull request is merged in the next step.

**Verify:**

1. Confirm the `pull nonprod live into repo` step succeeds.
2. Confirm the pull request's source branch starts with `acs-pull/nonprod-`.
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
