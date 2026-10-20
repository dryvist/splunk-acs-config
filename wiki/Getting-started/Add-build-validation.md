# Step 6: Add Build validation

[Home](/Home) > [Getting started](/Getting-started) > Build validation

[[_TOC_]]

**Where:** **Repos → Branches**

**Do:**

1. Select **Repos → Branches**.
2. Select the `...` menu on the `main` row.
3. Select **Branch policies**.
4. Under **Build validation**, select **+ Add build policy**.
5. Select the config repo's pipeline in **Build pipeline**.
6. Select **Automatic** as the trigger.
7. Select **Required** as the policy requirement.
8. Select **Save**.

**Verify:**

1. Confirm the Build validation list shows the pipeline with **Required**.
2. Open a test pull request to `main`. Confirm the pipeline queues and runs
   a plan for each environment.

## Related

- [Getting started](/Getting-started)
- [Create the pipeline](/Getting-started/Create-pipeline)

---

[< Previous](/Getting-started/Grant-repository-permissions) |
[Next: Create environments >](/Getting-started/Create-environments)
