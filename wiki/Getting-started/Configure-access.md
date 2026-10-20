# Step 3: Configure access

[Home](/Home) > [Getting started](/Getting-started) > Configure access

[[_TOC_]]

**Where:** **Pipelines → Library**

**Do:**

1. Select **Pipelines → Library**.
2. Select the `splunk-nonprod` variable group. Reuse the group from the app
   repositories. If it does not exist, select **+ Variable group** and
   create it with the name `splunk-nonprod`.
3. Confirm `SPLUNK_STACK` holds the nonprod stack name, the `<stack>` part of
   `https://<stack>.splunkcloud.com`.
4. Confirm `ACS_TOKEN` holds the nonprod ACS token, and its lock icon is on.
5. If the nonprod stack uses a search head, add `SPLUNK_SEARCH_HEAD` with the
   search head name, the part before `.<stack>`.
6. Select **Save**.
7. Select the `splunk-prod` variable group.
8. Confirm `SPLUNK_STACK` and `ACS_TOKEN` hold the prod values, with the lock
   icon on for `ACS_TOKEN`.
9. If the prod stack uses a search head, add `SPLUNK_SEARCH_HEAD`.
10. Select **Save**.
11. Sign in to Splunk Web on the nonprod stack as an administrator.
12. Select **Settings → Users**.
13. Open the user that owns the nonprod `ACS_TOKEN`.
14. Confirm the user has the `sc_admin` role.
15. Repeat steps 11 to 14 for the prod stack.
16. Add the pipeline agent subnet to the ACS allowlist feature `acs`. Send
    `POST https://admin.splunk.com/<stack>/adminconfig/v2/access/acs/ipallowlists`
    with the body `{"subnets": ["<agent-subnet>"]}` and the header
    `Authorization: Bearer <acs-token>`, from an address the allowlist already
    permits.

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
