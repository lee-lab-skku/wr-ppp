# Setup and Updates

Use these Bash/Docker instructions on Linux/macOS or WSL.
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

Output directories must be absolute paths beginning with `/` or home-relative paths beginning with `~/`.
Other relative paths are not accepted.

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

## Automatic Release Updates

This Git updater applies to the Linux/macOS Bash workflow, including WSL.
Native Windows source checkouts and EXE installations are updated manually.

Automatic updates are optional and require Git and access to the installation's existing `origin` remote.
Enable them during setup or when changing an existing setup:

```bash
./scripts/setup.sh --auto-update
./scripts/setup.sh --auto-update=prerelease
./scripts/setup.sh --auto-update=off
```

`--auto-update` defaults to `stable`; `--auto-update=stable` is equivalent.
`stable` follows official releases, while `prerelease` includes beta and release-candidate tags as well as official releases.
`off` disables an existing setting.
Omitting the option preserves the saved channel, or leaves updates off on first installation.
Explicit values must follow `=`; no extra Python or Node.js packages are needed.
Setup saves the setting without contacting the remote or switching versions.

On a valid `report-build` invocation, an enabled installation checks for releases if its last successful check was at least 24 hours ago.
This is an elapsed-time check at build time, not a scheduled background job; independent terminals and agent commands share the same installation-local check record.
Changing channels or disabling and re-enabling updates makes the next build check again.
Remote lookup and fetch attempts each have a 30-second timeout with a short termination grace period.
Failures are reported, the existing checkout is used, and remote failures are retried no sooner than one hour later.
Help and invalid build requests do not check for updates.

Only origin tags named `vX.Y.Z`, `vX.Y.Z-beta`, or `vX.Y.Z-rc` are eligible, with no leading zeroes in numeric components except `0` itself.
Version components sort numerically, then `beta < rc < official release`; numbered prereleases such as `-beta.1`, other suffixes, and build metadata are excluded.
The selected release is checked out as detached HEAD, preserving existing branches, and the build restarts using the updated scripts and shared style.
Channel changes do not automatically downgrade the installation.

Use `--auto-update=off` for a development clone: automatic updates change the current checkout to a release.
Tracked edits or staged changes cause an update to be skipped, and a target must include the current commit in its history.
Thus a clone already ahead of the latest eligible release waits until a release includes its commits.
Updates never automatically stash work, force-reset a checkout, or overwrite an existing conflicting tag.
After resolving a skipped update, the normal check interval still applies; disabling and re-enabling updates requests a fresh check on the next build.

Enabled builds hold an installation lock through compilation so another automatic update cannot change the style mid-build.
A concurrent build waits up to 30 seconds, then asks you to retry if the installation is still busy.
Normal exits and handled interrupts release the lock; after a forced kill, inspect `.report-update/lock/owner` and verify that the recorded host and process no longer own a running build before removing the stale lock directory.
Local update records are stored under the Git-ignored `.report-update/` directory.
Installed skill links follow the updated files; an agent that already read the skill may need to read it again to use changed guidance.

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
