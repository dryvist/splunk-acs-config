# Step 10: Check the plan

[Home](/Home) > [Getting started](/Getting-started) > Check plan

[[_TOC_]]

This page checks a plan for each environment.

**Where:** **Pipelines → the config pipeline → Run pipeline**

**Do:**

1. Select **Run pipeline**.
2. Select `plan` as **Action**.
3. Keep **Object types** as `all`.
4. Keep **Object names** as `all`.
5. Select **Run**.
6. Wait for the run to finish.
7. Open the `Plan nonprod (repo vs live)` step.
8. Open the `Plan prod (repo vs live)` step.

**Verify:**

1. Confirm both plan steps succeed.
2. Confirm each plan step prints `NO DIFFERENCES`.
3. Confirm the run has no push step.

## Related

- [Getting started](/Getting-started)
- [Commands](/Reference/Commands)
- [Only live objects troubleshooting](/Troubleshooting/Only-live-objects)

---

[< Previous: Merge pull requests](/Getting-started/Merge-pull-requests) |
[Next: File format >](/Reference/File-format)
