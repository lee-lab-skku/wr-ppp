# Automatic Release Updates

Configure release channels and use the automatic updater's checks, checkout safeguards, and lock recovery for an existing installation.
This Git updater applies to the Linux/macOS Bash workflow, including WSL.
Native Windows source checkouts and EXE installations are updated manually.

## Enable or Change a Channel

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

## Check Timing and Failures

On a valid `report-build` invocation, an enabled installation checks for releases if its last successful check was at least 24 hours ago.
This is an elapsed-time check at build time, not a scheduled background job; independent terminals and agent commands share the same installation-local check record.
Changing channels or disabling and re-enabling updates makes the next build check again.

Remote lookup and fetch attempts each have a 30-second timeout with a short termination grace period.
Failures are reported, the existing checkout is used, and remote failures are retried no sooner than one hour later.
Help and invalid build requests do not check for updates.

## Eligible Releases

Only origin tags named `vX.Y.Z`, `vX.Y.Z-beta`, or `vX.Y.Z-rc` are eligible, with no leading zeroes in numeric components except `0` itself.
Version components sort numerically, then `beta < rc < official release`; numbered prereleases such as `-beta.1`, other suffixes, and build metadata are excluded.
The selected release is checked out as detached HEAD, preserving existing branches, and the build restarts using the updated scripts and shared style.
Channel changes do not automatically downgrade the installation.

## Checkout Safeguards

Use `--auto-update=off` for a development clone: automatic updates change the current checkout to a release.
Tracked edits or staged changes cause an update to be skipped, and a target must include the current commit in its history.
Thus a clone already ahead of the latest eligible release waits until a release includes its commits.

Updates never automatically stash work, force-reset a checkout, or overwrite an existing conflicting tag.
After resolving a skipped update, the normal check interval still applies; disabling and re-enabling updates requests a fresh check on the next build.

## Build Locks and Recovery

Enabled builds hold an installation lock through compilation so another automatic update cannot change the style mid-build.
A concurrent build waits up to 30 seconds, then asks you to retry if the installation is still busy.

Normal exits and handled interrupts release the lock; after a forced kill, inspect `.report-update/lock/owner` and verify that the recorded host and process no longer own a running build before removing the stale lock directory.
Local update records are stored under the Git-ignored `.report-update/` directory.
Installed skill links follow the updated files; an agent that already read the skill may need to read it again to use changed guidance.
