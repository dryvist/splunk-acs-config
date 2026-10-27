# Access and tokens

One time. Done at setup; you should not need this again.

This page sets the variable group for each environment, the values the pipeline reads from it, and the agent subnet in ACS.

The pipeline reads the variable group `splunk-<env>` for each environment in the `environments` list of `azure-pipelines.yml`.

| Environment | Variable group | `SPLUNK_STACK` | `SPLUNK_SEARCH_HEAD` |
| --- | --- | --- | --- |
| nonprod | `splunk-nonprod` | `<nonprod-stack>` | `<nonprod-search-head>` or blank |
| prod | `splunk-prod` | `<prod-stack>` | `<prod-search-head>` or blank |

## Steps

1. Select **Pipelines → Library**.
2. Select **+ Variable group** if the group does not exist.
3. Enter the group name from the table in **Name**.
4. Select **Save**.
5. Open the variable group.
6. Add `SPLUNK_STACK` with the value from the table.
7. Add `ACS_TOKEN` as a secret variable.
8. Add `SPLUNK_SEARCH_HEAD` when the environment targets a search head.
9. Select **Save**.
10. Repeat steps 2 to 9 for each table row.
11. Sign in to each stack as the user whose token is in its variable group.
12. Select **Settings**.
13. Select **Users**.
14. Open the token user's record.
15. Confirm the user has the `sc_admin` role.
16. From an allowed address, send `POST <ACS base URL>/access/acs/ipallowlists` with the body `{"subnets": ["<agent-subnet>"]}`.
17. Set the request header `Authorization: Bearer <acs-token>`.
18. Add `SPLUNKBASE_USERNAME` as a secret variable in groups that push apps.
19. Add `SPLUNKBASE_PASSWORD` as a secret variable in those groups.
20. Select **Save** for each updated group.

## Rules

Do not put a token value in a config file, a pipeline log, or a pull request.

For what the tool reads from these variables, see [Commands](/Reference/Commands). For access errors, see
[Authentication](/Troubleshooting/Authentication) and [ACS allowlist](/Troubleshooting/ACS-allowlist).
