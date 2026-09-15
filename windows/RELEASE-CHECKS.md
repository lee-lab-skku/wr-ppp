# Windows release checks

The records below describe the earlier Windows implementation and its distribution.
For the current PowerShell refactor, see [VALIDATION.md](VALIDATION.md); previous installer checks do not certify a newly built installer.
Before publishing, prepare TinyTeX, build the offline bundle and installer, rerun the portable and installation checks, and attach the installer and SHA256 as release assets.

## Privacy and Git contents (2026-09-15)

- Reviewed tracked files and new source files for developer profile names, personal email addresses, private keys, common access-token formats and Slack webhook URLs. No real credentials or personal profile data were detected in the source candidate set. Webhook URLs in tests are explicit dummy values.
- Local configuration, Python environments, report output, temporary files, build tools, executables and signing keys are excluded from Git.
- Removed generated TinyTeX logs, font caches and unused non-XeTeX format dumps. Removed developer paths from generated comments and made font directories relative to the bundled font configuration.
- Scanned the distribution, including decompressed gzip format data, for the developer profile/email and common credential patterns. No remaining matches were detected after cleanup. This is a targeted privacy check, not a guarantee against every possible secret or third-party binary issue.
- Use a GitHub noreply author/committer email for the release commit.

## Validation

- Windows native tests: 46 passed.
- Common tests: 8 passed; 26 POSIX-only tests skipped on Windows.
- The Slack manifest fixture explicitly uses UTF-8 so tests work with the Windows locale.
- The sanitized distribution generated a Korean PDF successfully with development Python/TeX excluded from PATH.
- Installer and shortcuts were tested on the development Windows PC. A separate clean PC, Windows ARM and uninstallation remain untested; the installer is unsigned.
- Publish installer EXE and SHA256 only as GitHub Release assets. They must not be committed to the source branch.
