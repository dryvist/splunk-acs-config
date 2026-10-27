# Create the pipeline

One time. Done at setup; you should not need this again.

This page creates the config pipeline from the `azure-pipelines.yml` file in the config repo.

## Steps

1. Select **Pipelines → New pipeline**.
2. Select **Azure Repos Git**.
3. Select the `<config-repo>` repository.
4. Select **Existing Azure Pipelines YAML file**.
5. Select the `main` branch.
6. Select `/azure-pipelines.yml` as the path.
7. Select **Continue**.
8. Select the arrow next to **Run**.
9. Select **Save**.
10. When the pipeline asks to permit the `tools` repository resource, select **Permit**.

## Verify

1. Confirm the pipeline is listed under **Pipelines**.
2. Confirm the pipeline's YAML path is `/azure-pipelines.yml`.
3. Confirm the pipeline has no pending prompt to permit a resource.
4. Confirm the `environments` list in `azure-pipelines.yml` matches `environments.toml`.
