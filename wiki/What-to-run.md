# What to run

Pick the row for your task. Follow [Start a run](#start-a-run) with the row's values. Then open the task's page.

| Task | `action` | `write` | `types` | `names` | Also set | Page |
| --- | --- | --- | --- | --- | --- | --- |
| See differences | Any | Cleared | Any | Any | `check`, to fail on differences | [Plan](/What-to-run/Plan) |
| Read live into a pull request | `pull` | Selected | Any | Any | | [Pull](/What-to-run/Pull) |
| Push one object | `push` | Not used | One type name | One name or a `;` list | | [Push](/What-to-run/Push) |
| Push a type | `push` | Not used | One type name or a `;` list | `all` | | [Push](/What-to-run/Push) |
| Delete live-only objects | `push` | Not used | The objects to check | The objects to check | `delete` | [Delete](/What-to-run/Delete-live-only-objects) |

These tasks do not start from the run form:

- The nightly drift check runs from a schedule. See [Nightly drift check](/What-to-run/Plan#nightly-drift-check).
- To set prod values, edit the prod tables in the type files, open a pull request, and review the plan before you
  [push](/What-to-run/Push).
- To regenerate the README and apps.csv, run `doc` on your machine. See
  [Regenerate the README and apps.csv](/What-to-run/Regenerate-docs).

## Start a run

1. Select **Pipelines**.
2. Open the config pipeline.
3. Select **Run pipeline**.
4. Set `action`.
5. Set `write` if your task needs it.
6. Set `environment`.
7. Set `types`.
8. Set `names`.
9. Set `check` if your task needs it.
10. Set `delete` if your task needs it.
11. Select **Run**.

The run name shows the options it started with, such as `20261105.3 push prod, types indexes, names 2`. A pull run
without `write` shows `plan`.

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `action` | `pull`, `push` | `push` | `pull` with `write` reads live into a pull request. `push` adds optional Push stages that write files to the stack. |
| `write` | Selected, cleared | Cleared | After the plan, opens the pull request. A push ignores it. |
| `environment` | `all`, or one name from `environments.toml` | `all` | Environments to read or write. |
| `types` | `all`, or type names separated by `;` | `all` | Types from [Object types](/Reference/Object-types). |
| `names` | `all`, or stanza names separated by `;` | `all` | Objects within those types. |
| `check` | `false`, `true` | `false` | Fails the plan when differences exist. A pull ignores it. |
| `delete` | `false`, `true` | `false` | Adds stages that remove objects only in the stack. A pull ignores it. |
