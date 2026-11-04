# Administrator Manifest

The manager manifest is human-managed configuration that defines the administrator's roster, reporting timezone, and authorized storage boundaries.
This reference covers its location, required fields, and incomplete-configuration handling.

## Resolve the Manifest Location

With the platform's `--admin-data` setup option, its write location is `<directory>/manager-manifest.toml`; otherwise it is the repository-local `.manager-manifest.toml`.
On Windows, configuration uses `.windows-config.json` for a source checkout or `%LOCALAPPDATA%/WeeklyReport/config.json` for a packaged installation.
Resolve the active manifest path with the launcher's `admin-paths` subcommand; do not read `.local-config` or invoke a POSIX helper.
On Linux/macOS, setup saves the optional base directory as `ADMIN_DATA_DIR` in `.local-config`.

Setup creates a commented skeleton when absent and never guesses members or replaces an existing manifest.
For reads, use the `manager-manifest` path returned by the platform's `admin-paths` command; a missing configured file falls back to the repository-local file.
An existing but invalid or incomplete configured manifest must be diagnosed rather than bypassed.

## Schema

```toml
schema = 1
storage_root = "/absolute/path/to/report-storage"
timezone = "Asia/Seoul"

[[members]]
id = "member-a"
display_name = "구성원 가"
order = 10
required = true
search_roots = ["member-a"]

[[members]]
id = "member-b"
display_name = "구성원 나"
order = 20
required = true
search_roots = ["member-b/current-period"]
```

Every top-level field is required:

| Field | Value or constraint |
| --- | --- |
| `schema` | Integer `1` |
| `storage_root` | Absolute directory containing all authorized member roots |
| `timezone` | IANA timezone used to interpret the target date and filesystem times |
| `members` | One or more member tables |

Every member requires these fields:

| Field | Value or constraint |
| --- | --- |
| `id` | Unique ASCII value matching `[A-Za-z0-9][A-Za-z0-9._-]*` |
| `display_name` | Nonempty value |
| `order` | Unique positive integer |
| `required` | Boolean |
| `search_roots` | One or more paths relative to `storage_root` |

## Authorized Search Roots

Each search root is relative to `storage_root`.
Reject absolute roots, `..` path components, missing directories, directory-symlink components, and paths whose physical resolution escapes the storage root.
Do not follow directory symlinks while searching.
The configured administrator output directory must not be inside a member search root.

Do not add filename patterns, expected internal week labels, or template requirements.
Narrow a member to a stable subdirectory such as `member-b/current-period` when that is the intended administrative boundary.
Multiple roots are allowed only when the administrator actually wants all of them searched.

## Incomplete Configuration

If `storage_root` or members are absent, explain which values are missing and stop before discovery.
If the active platform configuration has no administrator output directory, discovery and a temporary draft remain possible, but final promotion must wait until setup is rerun with an absolute `--admin-output` directory.
