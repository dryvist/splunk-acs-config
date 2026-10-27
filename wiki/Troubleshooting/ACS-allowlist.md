# ACS allowlist

This page fixes ACS requests that cannot connect, or that ACS denies by agent address.

## Symptom

The ACS request cannot connect, or ACS denies the agent address.

## Check

Confirm the ACS allowlist feature `acs` includes the current pipeline agent IP. Hosted agent addresses can change, so use
an approved stable agent network or update the allowlist when the agent address changes. To add a subnet, see
[Access and tokens](/Setup/Access-and-tokens).

## Verify

Rerun [Plan](/What-to-run/Plan) and confirm the request reaches ACS.
