# GitHub Actions outlook

This page maps the Azure DevOps pipeline to GitHub Actions, with `acs_config.py` unchanged.

| Azure DevOps | GitHub Actions |
| --- | --- |
| Pipeline with parameters `environment`, `action`, `types`, `check`, `names` and `delete` | A workflow with `on: workflow_dispatch` and inputs of the same names. `action` is a `choice`, `environment`, `types` and `names` are `string`, and `check` and `delete` are `boolean`. |
| `schedules` block | `on: schedule` with `cron`. Cron runs in UTC, the shortest interval is 5 minutes, and only the default branch runs the schedule. |
| Variable group `splunk-<env>` | An environment `splunk-<env>` with environment secrets for `ACS_TOKEN`, `SPLUNKBASE_USERNAME` and `SPLUNKBASE_PASSWORD`, and environment variables for `SPLUNK_STACK` and `SPLUNK_SEARCH_HEAD`. Jobs read them only when they reference the environment with `environment:`. |
| Environment `splunk-prod` with an Approvals check | An environment `splunk-prod` with required reviewers. The job waits until a reviewer approves it. |
| Pull request creation with the build identity | `GITHUB_TOKEN` with `permissions: pull-requests: write`. |
| `acs_config.py` | Unchanged. |

- The repository setting "Allow GitHub Actions to create and approve pull requests" must allow the token to create pull
  requests. It is under **Settings → Actions → General → Workflow permissions**. Personal repositories do not allow it by
  default. Organization repositories inherit the organization setting.
- A secret that is not defined expands to an empty string, not an error.

## Sources

- [Events that trigger workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows)
- [Workflow syntax](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax)
- [Manage environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)
- [Use secrets](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- [Automatic token authentication](https://docs.github.com/en/actions/security-guides/automatic-token-authentication)
- [Managing GitHub Actions settings](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository)
