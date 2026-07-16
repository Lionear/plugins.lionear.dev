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
  assets/
    icon.png                  # store icon shown for the "official" source
```

`discovery.json` is a registry of *stores* — each entry just points at a
store's own `index.json`. Today there is one store ("official"), this repo's
own `sql-explorer/index.json`. Sibling products (if any) would get their own
`plugins.lionear.dev/<product>/` space, hence the `sql-explorer/` prefix.

`index.json` lists every published plugin with its available versions
(download URL, sha256, size, host-API compatibility range).
