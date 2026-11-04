# What to run

Pick the row for your task. Follow [Start a run](#start-a-run) with the row's values. Then open the task's page.

| Task | `action` | `write` | `types` | `names` | Also set | Page |
| --- | --- | --- | --- | --- | --- | --- |
| See differences | Any | Cleared | Any | Any | `check`, to fail on differences | [Plan](/What-to-run/Plan) |
| Read live into a pull request | `pull` | Selected | Any | Any | | [Pull](/What-to-run/Pull) |
| Push one object | `push` | Selected | One type name | One name or a `;` list | | [Push](/What-to-run/Push) |
| Push a type | `push` | Selected | One type name or a `;` list | `all` | | [Push](/What-to-run/Push) |
| Delete live-only objects | `push` | Selected | The objects to check | The objects to check | `delete` | [Delete](/What-to-run/Delete-live-only-objects) |

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
5. Set `write`.
6. Set `environment`.
7. Set `types`.
8. Set `names`.
9. Set `check` if your task needs it.
10. Set `delete` if your task needs it.
11. Select **Run**.

| Parameter | Values | Default | Effect |
| --- | --- | --- | --- |
| `action` | `pull`, `push` | `push` | With `write` selected, `pull` reads live into a pull request and `push` writes files to the stack. |
| `write` | Selected, cleared | Cleared | After the plan, opens the pull request or adds the Push stages. |
| `environment` | `all`, or one name from `environments.toml` | `all` | Environments to read or write. |
| `types` | `all`, or type names separated by `;` | `all` | Types from [Object types](/Reference/Object-types). |
| `names` | `all`, or stanza names separated by `;` | `all` | Objects within those types. |
| `check` | `false`, `true` | `false` | Fails the plan when differences exist. A pull ignores it. |
| `delete` | `false`, `true` | `false` | Adds stages that remove objects only in the stack. A pull ignores it. |
