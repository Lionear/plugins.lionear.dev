# SQL Explorer Plugins — release procedure

This repo hosts `https://plugins.lionear.dev/sql-explorer/discovery.json` and
`.../index.json` for the SQL Explorer Store (GitHub Pages, custom domain via
`CNAME`). It is intentionally just static JSON + release assets — no build
step of its own.

The plugin *source* lives in the main app repo,
`~/dev/Lionear.SqlExplorer` (`Lionear/SqlExplorer` on GitHub), under
`plugins/<ProjectName>/`. This repo only publishes built versions.

When Rick asks to "release a version of plugin X" (or similar), do the
following, in this repo unless noted:

## 1. Gather facts from the source repo

In `~/dev/Lionear.SqlExplorer`:

- Find the plugin project under `plugins/<ProjectName>/`.
- Read `plugin.json` for: `id`, `type` (`provider`/`tool`), `entryAssembly`,
  and the `hostApiVersion` it was built against.
- Decide the new `version` (semver) — ask Rick if it's not obvious from a
  changelog/commit message.
- Note the plugin's display metadata for the store listing: name,
  description, author ("Lionear"), homepage
  (`https://github.com/Lionear/SqlExplorer`), icon if any.
- `hostApiVersion` maps to `minHostApiVersion`/`maxHostApiVersion` in the
  store entry — see `src/SqlExplorer.Core/Store/HostApiVersions.cs` and
  `src/SqlExplorer.Sdk/ProviderHostApi.cs` /
  `src/SqlExplorer.Sdk/Tools/ToolHostApi.cs` for the current contract
  version and whether older builds are still compatible. Default to
  `minHostApiVersion = maxHostApiVersion = <that build's hostApiVersion>`
  unless Rick says the build is compatible across a range.

## 2. Build and package

- Build the plugin project in Release config so it produces its full output
  folder (assembly + `.deps.json` + `plugin.json` + any driver DLLs) — the
  same shape described in `docs/PLUGINS.md` under "Ship it".
- Zip that output folder's *contents* (not the folder itself) into
  `<id>-<version>.zip`.
- Compute `sha256sum <id>-<version>.zip` and the file size in bytes.

## 3. Publish the artifact

Attach the zip to a GitHub Release in **this** repo (`sql-explorer-plugins`),
not the source repo:

```
gh release create <id>-v<version> <id>-<version>.zip \
  --repo Lionear/sql-explorer-plugins \
  --title "<display name> <version>" \
  --notes "<short changelog line>"
```

The resulting download URL is:
`https://github.com/Lionear/sql-explorer-plugins/releases/download/<id>-v<version>/<id>-<version>.zip`

## 4. Update `sql-explorer/index.json`

Add a new `StoreVersion` to the plugin's `versions` array (create the
`StoreEntry` if this is the plugin's first release). Keep older versions in
the array — `HighestCompatibleVersion` in the app picks the best match per
host, so removing old entries can strand users on an old host build.

```json
{
  "id": "<id>",
  "type": "<provider|tool>",
  "name": "<display name>",
  "description": "<one line>",
  "author": "Lionear",
  "homepage": "https://github.com/Lionear/SqlExplorer",
  "iconUrl": null,
  "capabilities": [],
  "versions": [
    {
      "version": "<version>",
      "minHostApiVersion": <n>,
      "maxHostApiVersion": <n or null>,
      "downloadUrl": "https://github.com/Lionear/sql-explorer-plugins/releases/download/<id>-v<version>/<id>-<version>.zip",
      "sha256": "<lowercase hex>",
      "size": <bytes>
    }
  ]
}
```

## 5. Commit and push

```
git add sql-explorer/index.json
git commit -m "Release <id> <version>"
git push
```

GitHub Pages redeploys automatically. Verify with:

```
curl -s https://plugins.lionear.dev/sql-explorer/index.json | jq '.plugins[] | select(.id=="<id>")'
```

## 6. Confirm with Rick before pushing

Building/zipping/computing hashes is safe to do freely. **Always show Rick
the diff of `index.json` and ask before pushing to this repo or creating the
GitHub Release** — both are publicly visible and immediately live for every
installed copy of SQL Explorer.
