# Setup and Updates

Set up and verify the Bash/Docker report workflow on Linux/macOS or WSL, including optional agent skills and administrator support.
This guide also covers configuration changes and links to automatic release update operations.
For native Windows installation and updates, use the [Windows guide](../windows/README.md).

## Requirements

Linux/macOS use Bash and Docker; macOS compatibility is a source-level design target rather than a tested-platform guarantee.
The optional local browser editor also needs Python 3.9 or newer on the host, using only its standard library.
The native Windows offline installer includes the tools needed to generate reports without separate dependency installation.
See the [Windows guide](../windows/README.md) for source prerequisites and installation.
For the Bash/Docker workflow, make sure that:

- Bash and Docker are installed.
- The Docker daemon is running and your account can run Docker containers.
- You can use `sudo` during setup to install `report-build` under
  `/usr/local/bin`.

The recommended image is `danteev/texlive:latest`.
Another compatible TeX Live Docker image may be supplied to `scripts/setup.sh` if preferred.
The image must provide XeLaTeX, `latexmk`, and `pdfinfo` (Poppler); these PDF tools are not required on the host.

## Install

Run the setup script from the cloned repository.
The following example stores finished PDFs in `~/report-output`:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest
```

This saves the selected image and output directory in the repository's local configuration and links the `report-build` command into `/usr/local/bin`.

Output directories must be absolute paths beginning with `/` or home-relative paths beginning with `~/`.
Other relative paths are not accepted.

## Optional Agent Skills

To also make the bundled report-writing skill available from any working directory, pass the supported services as a comma-separated `--skills` option:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest --skills=agents,claude
```

Each value links the repository's canonical skill into the following user-level directory:

| Value | Skill directory | Aliases |
| --- | --- | --- |
| `agents` | `~/.agents/skills` | `codex`, `gemini`, `copilot` |
| `claude` | `~/.claude/skills` | |
| `antigravity` | `~/.gemini/config/skills` | |

[Gemini CLI](https://geminicli.com/docs/cli/skills/) supports `~/.agents/skills` and gives it precedence over `~/.gemini/skills`, so `gemini` uses the shared `agents` destination.
[GitHub Copilot](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills) also supports `~/.agents/skills` for personal skills, so `copilot` is another alias for `agents`.
The previous `codex` alias remains supported.
The `antigravity` destination follows the current [Antigravity global skill directory](https://antigravity.google/docs/skills).

For example, `--skills=gemini,antigravity` installs links in both the shared and Antigravity directories.
Repeated service names and aliases for the same destination are automatically deduplicated, preserving the first occurrence.
For example, `--skills=agents,codex,gemini,copilot,claude,claude` installs each skill once into `~/.agents/skills` and once into `~/.claude/skills`.

When setup runs in WSL, these paths are under the WSL home directory; this does not install skills into a Windows-native agent's separate home directory.
Omitting `--skills` leaves user-level skill directories unchanged.

## Existing Destinations

Setup applies the same destination policy to `/usr/local/bin/report-build` and each requested skill link.
A missing destination is linked, and a link that already resolves to the same repository source is accepted without change.
By default, any other file, link, or directory is preserved and reported as an error.

All requested destinations are checked before the configuration or any links are changed.
Checks include destination parent paths, and unsupported options are rejected before setup changes anything.
Setup saves configuration atomically after installing the requested links; if installation fails, it preserves the previous configuration and attempts to restore links changed by that run.
Any incomplete rollback reports the preserved backup locations.

Use `--replace-existing` to replace conflicting files or links explicitly:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest \
    --skills=agents,claude --replace-existing
```

Each replaced entry is moved to an adjacent backup such as `report-build.backup` or `wr-wr.backup.1`, and setup prints a warning containing the backup path.
Existing backup names are not overwritten.
Directories are never replaced, even with `--replace-existing`.
This option also provides the migration path for a regular `report-build` file installed by an older setup version.

## Administrator Mode

Administrator operating procedures and formats are defined in the [rollup workflow](../skills/admin-wr/references/rollup-workflow.md) and [manager manifest](../skills/admin-wr/references/manager-manifest.md).
Install it with `--admin`; use optional `--admin-output` for final PDFs and `--admin-data` for the manager manifest and execution history:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest \
    --skills=agents,claude \
    --admin \
    --admin-output=/absolute/path/to/admin-bundles \
    --admin-data=/absolute/path/to/admin-data
```

`--admin` requires `--skills`; `--admin-output` may be omitted until final bundle output is needed.
Administrator paths must not contain tabs, newlines, carriage returns, or `.` / `..` path components; setup and administrator commands apply the same rules.

`--admin-data` stores `manager-manifest.toml` and `manifests/<week>.manifest.tsv` beneath the chosen directory.
The manifest can be stored on a NAS that manages permissions on the server; setup does not require changing its permissions after creation.
Omitting it with `--admin` selects the existing repository-local `.manager-manifest.toml` and `.admin-wr/manifests/` locations.
When reading a missing configured file, the workflow falls back to its local counterpart; writes still use the configured destination.

For discovery, draft review, publication, and lock recovery, follow the [rollup workflow](../skills/admin-wr/references/rollup-workflow.md).
Optional Slack notices require Python 3 and approval of each complete message; see the canonical [Slack guide](../skills/admin-wr/references/slack-notifications.md).

## Verify the Setup

Compile the included template:

```bash
./scripts/test.sh
```

A successful test writes `template.pdf` in the repository.
Use the same command after changing `weekly-report.sty` to check that the example still builds.

## Change the Setup

Run `scripts/setup.sh` again whenever the output directory or Docker image needs to change:

```bash
./scripts/setup.sh ~/report-output danteev/texlive:latest
```

After the initial setup, either value can be updated independently.
With no arguments, both saved values are reused.
A single argument beginning with `/` or `~/` updates the output directory; any other single argument updates the Docker image.
The omitted value is read from `.local-config`:

```bash
./scripts/setup.sh
./scripts/setup.sh /mnt/reports
./scripts/setup.sh danteev/texlive:latest
./scripts/setup.sh --replace-existing
```

The new values replace the previous local configuration and are used by both `scripts/test.sh` and `report-build`.
The `--skills` and `--replace-existing` options may be combined with any of these forms.
The [automatic update option](#automatic-release-updates) may also be combined with them; omitting it preserves the saved channel.

## Automatic Release Updates

Automatic updates are optional for Bash/Docker installations; development clones should use `--auto-update=off`.
[Automatic Release Updates](setup/updates.md) covers channel selection, release checks, checkout safeguards, and recovery from skipped updates or stale build locks.
Native Windows updates remain manual.
