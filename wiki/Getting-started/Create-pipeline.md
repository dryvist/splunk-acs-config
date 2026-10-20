# Step 4: Create the pipeline

[Home](/Home) > [Getting started](/Getting-started) > Create pipeline

[[_TOC_]]

**Where:** **Pipelines → New pipeline**

**Do:**

1. Select **Pipelines → New pipeline**.
2. Select **Azure Repos Git**.
3. Select the `<config-repo>` repository.
4. Select **Existing Azure Pipelines YAML file**.
5. Select the `main` branch.
6. Select `/azure-pipelines.yml` as the path.
7. Select **Continue**.
8. Select the arrow next to **Run**.
9. Select **Save**.
10. When the pipeline asks to permit the `tools` repository resource, select
   **Permit**.

**Verify:**

1. Confirm the pipeline is listed under **Pipelines**.
2. Confirm the pipeline's YAML path is `/azure-pipelines.yml`.
3. Confirm the pipeline has no pending prompt to permit a resource.

## Related

- [Getting started](/Getting-started)
- [Repository permissions](/Getting-started/Grant-repository-permissions)

---

[< Previous: Configure access](/Getting-started/Configure-access) |
[Next: Grant repository permissions >](/Getting-started/Grant-repository-permissions)
