# Administrator Manifest

The manager manifest is human-managed configuration.
With setup option `--admin-data=<directory>`, its write location is `<directory>/manager-manifest.toml`; otherwise it is the repository-local `.manager-manifest.toml`.
Setup saves the optional base directory as `ADMIN_DATA_DIR` in `.local-config`, creates a commented skeleton when absent, and never guesses members or replaces an existing manifest.
For reads, use the `manager-manifest` path returned by `scripts/admin-paths`: a missing configured file falls back to the repository-local file.
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

The top-level fields are:

- `schema`: required integer `1`;
- `storage_root`: required absolute directory containing all authorized member roots;
- `timezone`: required IANA timezone used to interpret the target date and filesystem times;
- `members`: one or more member tables.

Each member requires:

- a unique ASCII `id` matching `[A-Za-z0-9][A-Za-z0-9._-]*`;
- a nonempty `display_name`;
- a unique positive integer `order`;
- a Boolean `required`;
- one or more `search_roots`.

Each search root is relative to `storage_root`. Reject absolute roots, `..` path components, missing directories, directory-symlink components, and paths whose physical resolution escapes the storage root. Do not follow directory symlinks while searching. The configured administrator output directory must not be inside a member search root.

Do not add filename patterns, expected internal week labels, or template requirements. Narrow a member to a stable subdirectory such as `member-b/current-period` when that is the intended administrative boundary. Multiple roots are allowed only when the administrator actually wants all of them searched.

## Incomplete Configuration

If `storage_root` or members are absent, explain which values are missing and stop before discovery. If `.local-config` has no `ADMIN_OUTPUT_DIR`, discovery and a temporary draft remain possible, but final promotion must wait until setup is rerun with `--admin-output=<absolute-directory>`.
