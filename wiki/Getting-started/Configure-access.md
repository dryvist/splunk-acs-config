# Step 3: Configure access

[Home](/Home) > [Getting started](/Getting-started) > Configure access

[[_TOC_]]

**Where:** **Pipelines → Library**

**Do:**

1. Select **Pipelines → Library**.
2. If the `splunk-nonprod` group does not exist, select **+ Variable group**.
3. If the group is new, type `splunk-nonprod` in **Name**.
4. If the group is new, select **Save**.
5. Select the `splunk-nonprod` variable group.
6. Confirm `SPLUNK_STACK` holds the nonprod stack name, the `<stack>` part of
   `https://<stack>.splunkcloud.com`.
7. Confirm `ACS_TOKEN` holds the nonprod ACS token, and its lock icon is on.
8. If the nonprod stack uses a search head, add `SPLUNK_SEARCH_HEAD` with the
   search head name, the part before `.<stack>`.
9. Select **Save**.
10. If the `splunk-prod` group does not exist, select **+ Variable group**.
11. If the group is new, type `splunk-prod` in **Name**.
12. If the group is new, select **Save**.
13. Select the `splunk-prod` variable group.
14. Confirm `SPLUNK_STACK` holds the prod stack name.
15. Confirm `ACS_TOKEN` holds the prod ACS token, and its lock icon is on.
16. If the prod stack uses a search head, add `SPLUNK_SEARCH_HEAD`.
17. Select **Save**.
18. Sign in to Splunk Web on the nonprod stack as an administrator.
19. Select **Settings**.
20. Select **Users**.
21. Open the user that owns the nonprod `ACS_TOKEN`.
22. Confirm the user has the `sc_admin` role.
23. Repeat steps 18 to 22 for the prod stack.
24. From an address the allowlist permits, send `POST
    https://admin.splunk.com/<stack>/adminconfig/v2/access/acs/ipallowlists`
    with the body `{"subnets": ["<agent-subnet>"]}` and the header
    `Authorization: Bearer <acs-token>`.

For a variable group that can push Splunkbase apps, add
`SPLUNKBASE_USERNAME` and `SPLUNKBASE_PASSWORD` as secret variables.

**Verify:**

1. Confirm both variable groups list `SPLUNK_STACK` and `ACS_TOKEN`.
2. Confirm the nonprod and prod token users have the `sc_admin` role.
3. Send `GET https://admin.splunk.com/<stack>/adminconfig/v2/access/acs/ipallowlists`
   with the same token. Confirm the response lists `<agent-subnet>`.

## Related

- [Getting started](/Getting-started)
- [Authentication troubleshooting](/Troubleshooting/Authentication)
- [ACS allowlist troubleshooting](/Troubleshooting/ACS-allowlist)

---

[< Previous: Create config repo](/Getting-started/Create-config-repo) |
[Next: Create the pipeline >](/Getting-started/Create-pipeline)
