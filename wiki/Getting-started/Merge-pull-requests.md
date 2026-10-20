# Step 9: Merge the pull requests

[Home](/Home) > [Getting started](/Getting-started) > Merge pull requests

[[_TOC_]]

**Where:** **Repos → Pull requests**

**Do:**

1. Select **Repos → Pull requests**.
2. Open the pull request whose source branch starts with `acs-pull/nonprod-`.
3. Select **Files**.
4. Review the changed files.
5. Confirm no changed file contains a token value.
6. Wait for the Build validation run on the pull request to succeed.
7. Select **Complete**.
8. Select **Complete merge**.
9. Run [Pull environments](/Getting-started/Pull-environments) again with
   `prod` as **Environment**.
10. Repeat steps 2 to 8 for the pull request whose source branch starts with
    `acs-pull/prod-`.

**Verify:**

1. Confirm both pull requests show **Completed**.
2. Confirm `main` contains the files under `objects/` from both environments.

## Related

- [Getting started](/Getting-started)
- [Object types](/Reference/Object-types)

---

[< Previous: Pull environments](/Getting-started/Pull-environments) |
[Next: Check the plan >](/Getting-started/Check-plan)
