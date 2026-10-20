# Step 9: Merge the pull requests

[Home](/Home) > [Getting started](/Getting-started) > Merge pull requests

[[_TOC_]]

**Where:** **Repos → Pull requests**

**Do:**

1. Select **Repos → Pull requests**.
2. Open the pull request whose source branch starts with `acs-pull/`.
3. Select **Files**.
4. Review the changed files.
5. Confirm no changed file contains a token value.
6. Wait for the Build validation run on the pull request to succeed.
7. Select **Complete**.
8. Select **Complete merge**.

**Verify:**

1. Confirm the pull request shows **Completed**.
2. Confirm `main` contains one file per object type under `objects/`, with
   each pulled environment's values in its stanzas.

## Related

- [Getting started](/Getting-started)
- [Object types](/Reference/Object-types)

---

[< Previous: Pull environments](/Getting-started/Pull-environments) |
[Next: Check the plan >](/Getting-started/Check-plan)
