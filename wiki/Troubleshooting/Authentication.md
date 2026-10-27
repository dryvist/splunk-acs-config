# ACS authentication

This page fixes ACS authentication and authorization errors.

## HTTP 401

1. Check that the ACS token is valid and intended for the ACS audience.
2. Confirm the variable group defines `ACS_TOKEN`. See [Access and tokens](/Setup/Access-and-tokens).

## HTTP 403

1. Confirm the token user has the `sc_admin` role. See [Access and tokens](/Setup/Access-and-tokens).
2. Check that the token belongs to the selected stack and that the stack name is correct.
