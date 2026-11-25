# Command Metadata

Read this before adding or changing commands in `bin/`.

Commands in `bin/` can declare CLI metadata in comments near the top of the
file. `bin/nixos` scans the first 80 lines, and tests expect command metadata
to remain valid.

Supported metadata keys:

- `# nixos:group=...` - override the command group inferred from the filename
- `# nixos:name=...` - override the command name inferred from the filename
- `# nixos:summary=...` - short help text
- `# nixos:args=...` - usage arguments
- `# nixos:examples=...` - examples separated with ` | `
- `# nixos:alias=...` / `# nixos:aliases=...` - alternate routes
- `# nixos:hidden=true` - hide from default command listings
- `# nixos:requires-sudo=true` - mark commands that require sudo

Only use `nixos:examples` where there are args that need explaining.

Prefer explicit metadata for user-facing commands. Keep routes consistent with
the filename unless there is a deliberate alias or compatibility route.

Example:

```bash
# nixos:summary=Take a screenshot
# nixos:args=[smart|region|windows|fullscreen] [slurp|copy]
# nixos:examples=nixos screenshot | nixos capture screenshot region
```
