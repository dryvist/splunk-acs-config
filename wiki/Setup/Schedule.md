# Schedule the nightly plan

One time. Done at setup; you should not need this again.

This page confirms the nightly schedule in `azure-pipelines.yml` and that the pipeline defines no schedule of its own.

The `schedules` block runs the pipeline at midnight UTC every night on `main`, even when no code changed. Each scheduled
run is a plan with `check` on. See [Plan](/What-to-run/Plan).

## Steps

1. Open `azure-pipelines.yml` on the `main` branch of the config repo.
2. Confirm the `schedules` block has `cron: '0 0 * * *'`.
3. Confirm the `schedules` block includes `main` under `branches` and sets `always: true`.
4. Open the config pipeline's details page.
5. Select the `...` menu, then select **Scheduled runs**.
6. Confirm the list shows a run at 00:00 UTC on `main`. The list shows runs for the next seven days only, in your local
   time zone.
7. Open the pipeline editor and select **Triggers**.
8. Confirm no scheduled trigger is defined there. A schedule defined in this view takes precedence over the YAML schedule.

## Verify

1. After the first scheduled run, open it and confirm both plan steps ran and no push step ran.

## Change the time

Edit the `cron` value in `azure-pipelines.yml` on `main`. Cron times are in UTC, not local time.
