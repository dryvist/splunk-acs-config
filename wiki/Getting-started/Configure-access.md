# Step 3: Configure access

[Home](/Home) > [Getting started](/Getting-started) > Configure access

[[_TOC_]]

This page configures pipeline variables and access for each environment.

**Where:** **Pipelines → Library**

**Do:**

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
16. From an allowed address, send `POST <ACS base URL>/access/acs/ipallowlists`
    with body `{"subnets": ["<agent-subnet>"]}` and header
    `Authorization: Bearer <acs-token>`.
17. Add `SPLUNKBASE_USERNAME` as a secret variable in groups that push apps.
18. Add `SPLUNKBASE_PASSWORD` as a secret variable in those groups.
19. Select **Save** for each updated group.

| Environment | Variable group | `SPLUNK_STACK` | `SPLUNK_SEARCH_HEAD` |
| --- | --- | --- | --- |
| nonprod | `splunk-nonprod` | `<nonprod-stack>` | `<nonprod-search-head>` or blank |
| prod | `splunk-prod` | `<prod-stack>` | `<prod-search-head>` or blank |

See [Authentication](/Troubleshooting/Authentication) and
[ACS allowlist](/Troubleshooting/ACS-allowlist) for access errors.

---

[< Previous: Create config repo](/Getting-started/Create-config-repo) |
[Next: Create the pipeline >](/Getting-started/Create-pipeline)
