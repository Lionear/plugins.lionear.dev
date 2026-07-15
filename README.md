# SQL Explorer Plugins

Hosts the plugin Discovery feed and the official plugin store index for
[Lionear SQL Explorer](https://github.com/Lionear/SqlExplorer).

Served at `https://plugins.lionear.dev/` via GitHub Pages + a custom domain
(this repo's `CNAME` file). The app has this Discovery URL hardcoded
(`HttpDiscoveryService.DefaultDiscoveryUrl`) — it is not user-configurable.

## Layout

```
CNAME                        # plugins.lionear.dev
sql-explorer/
  discovery.json              # the fixed Discovery feed: registry of stores
  index.json                  # the "official" store's index: plugins + versions
```

`discovery.json` is a registry of *stores* — each entry just points at a
store's own `index.json`. Today there is one store ("official"), this repo's
own `sql-explorer/index.json`. Sibling products (if any) would get their own
`plugins.lionear.dev/<product>/` space, hence the `sql-explorer/` prefix.

`index.json` lists every published plugin with its available versions
(download URL, sha256, size, host-API compatibility range).

## Releasing a new plugin version

Not documented in this repo — the release procedure lives in Rick's private
notes (`Memory/Lionear/SQL Explorer/Plans/Plugin-Release-Procedure.md`),
since this repo is just the published output, not a place for operating
instructions.
