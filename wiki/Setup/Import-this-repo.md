# Import this repo

One time. Done at setup; you should not need this again.

This page imports the tools repository into the Azure DevOps project that will own the private config repo.

## Steps

1. Open the Azure DevOps project that will own the private config repo.
2. Select **Repos → Files**.
3. Select the repository selector.
4. Select **Import repository**.
5. Type the clone URL of this tools repository in **Clone URL**.
6. Type `splunk-acs-config` in **Name**.
7. Select **Import**.

## Verify

1. Confirm `splunk-acs-config` appears in the repository selector.
2. Confirm `templates/acs-config.yml` exists on the default branch.
