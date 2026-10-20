# Step 7: Create environments

[Home](/Home) > [Getting started](/Getting-started) > Create environments

[[_TOC_]]

**Where:** **Pipelines → Environments**

**Do:**

1. Select **Pipelines → Environments**.
2. Select **New environment**.
3. Type `splunk-nonprod` in **Name**.
4. Select **None** as the resource.
5. Select **Create**.
6. Select **New environment**.
7. Type `splunk-prod` in **Name**.
8. Select **None** as the resource.
9. Select **Create**.
10. Open the `splunk-prod` environment.
11. Select the `...` menu.
12. Select **Approvals and checks**.
13. Select **+**.
14. Select **Approvals**.
15. Add the approver who must approve prod pushes.
16. Select **Create**.

**Verify:**

1. Confirm both `splunk-nonprod` and `splunk-prod` are listed.
2. Confirm `splunk-prod` lists an **Approvals** check.

## Related

- [Getting started](/Getting-started)
- [Commands](/Reference/Commands)

---

[< Previous: Build validation](/Getting-started/Add-build-validation) |
[Next: Pull environments >](/Getting-started/Pull-environments)
