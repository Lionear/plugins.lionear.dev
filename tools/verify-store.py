#!/usr/bin/env python3
"""Verify that every plugin this store advertises is actually installable.

The DataTray rename (SE-203) renamed every plugin assembly, which made all fifteen published plugins
unloadable at once. Nothing noticed for four days: the host refuses the assembly on the user's machine,
after the download, so the failure never reaches CI or anyone here. This check closes that gap (SE-224).

It deliberately runs against the *live* index over HTTP rather than the working copy, because the thing
being tested is what a user's app actually fetches — a correct index.json that failed to deploy, or a
release asset that was deleted or replaced, is exactly as broken as bad JSON.

For every plugin's newest version it checks:

  1. the download URL resolves,
  2. sha256 and size match what the index promises,
  3. the archive contains a plugin.json,
  4. that manifest's id and version match the store entry,
  5. the assembly the manifest names as its entry point is present in the archive, and
  6. that assembly binds to the current SDK and not a pre-rename one.

Step 6 is the one that catches the rename, and steps 3-5 are not enough on their own: the packages
broken by SE-203 were internally consistent. redis 1.2.0 shipped a manifest naming
SqlExplorer.Providers.Redis.dll and that file was right there beside it. What made it unloadable was
one level down — the assembly referenced SqlExplorer.Sdk, which no current host provides.

Step 6 is a byte scan of the entry assembly for the SDK name rather than a real AssemblyRef parse.
That is a proxy, and worth knowing as one: it would miss a plugin that binds the old SDK purely
through reflection. It does catch every ordinary compile-time reference, which is the failure that
actually happened, and it needs no IL reader.

Usage:  verify-store.py [--index URL] [--all-versions]
        The index may be an http(s) URL or a file:// URL, which is how the negative test runs it
        against a known-broken package.
Exit code 0 when everything passes, 1 otherwise.
"""

import argparse
import hashlib
import io
import json
import sys
import urllib.error
import urllib.request
import zipfile

DEFAULT_INDEX = "https://plugins.lionear.dev/sql-explorer/index.json"
TIMEOUT = 120


class Failure(Exception):
    """A check that failed for one version, with a message worth printing verbatim."""


def fetch(url: str) -> bytes:
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise Failure(f"{url} → HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise Failure(f"{url} → {exc}") from exc


def check_version(entry: dict, version: dict) -> None:
    blob = fetch(version["downloadUrl"])

    actual_sha = hashlib.sha256(blob).hexdigest()
    if actual_sha != version["sha256"]:
        raise Failure(f"sha256 mismatch: index says {version['sha256']}, asset is {actual_sha}")

    if "size" in version and len(blob) != version["size"]:
        raise Failure(f"size mismatch: index says {version['size']}, asset is {len(blob)}")

    try:
        archive = zipfile.ZipFile(io.BytesIO(blob))
    except zipfile.BadZipFile as exc:
        raise Failure(f"not a readable zip: {exc}") from exc

    names = archive.namelist()
    if "plugin.json" not in names:
        raise Failure("no plugin.json at the root of the archive")

    try:
        manifest = json.loads(archive.read("plugin.json"))
    except json.JSONDecodeError as exc:
        raise Failure(f"plugin.json is not valid JSON: {exc}") from exc

    if manifest.get("id") != entry["id"]:
        raise Failure(f"manifest id is '{manifest.get('id')}', store entry is '{entry['id']}'")

    if manifest.get("version") != version["version"]:
        raise Failure(
            f"manifest version is '{manifest.get('version')}', store entry is '{version['version']}' — "
            "the app compares these to decide whether an update is available, so they must agree")

    entry_assembly = manifest.get("entryAssembly")
    if not entry_assembly:
        raise Failure("manifest declares no entryAssembly")

    if entry_assembly not in names:
        raise Failure(
            f"entryAssembly '{entry_assembly}' is not in the archive — the host cannot load this plugin. "
            f"Archive holds: {', '.join(sorted(n for n in names if n.endswith('.dll'))[:6])}")

    check_sdk_binding(archive, entry_assembly)


# The contract assembly every plugin compiles against, and the name it had before SE-203. A package
# referencing the old one is what a pre-rename build looks like from the outside.
CURRENT_SDK = b"DataTray.Sdk"
LEGACY_SDKS = (b"SqlExplorer.Sdk", b"Provider.Sdk")


def check_sdk_binding(archive: zipfile.ZipFile, entry_assembly: str) -> None:
    """Reject an entry assembly that binds a pre-rename SDK, or names no SDK at all."""
    blob = archive.read(entry_assembly)

    stale = [name.decode() for name in LEGACY_SDKS if name in blob]
    if stale:
        raise Failure(
            f"{entry_assembly} references {', '.join(stale)} — a pre-rename build. No current host "
            "provides that assembly, so this package fails to load after download. Rebuild and republish.")

    if CURRENT_SDK not in blob:
        raise Failure(
            f"{entry_assembly} names no {CURRENT_SDK.decode()} reference at all — either it is not a "
            "plugin assembly or it was built against something unexpected.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", default=DEFAULT_INDEX, help="index.json to verify (default: live store)")
    parser.add_argument("--all-versions", action="store_true",
                        help="check every published version, not only the newest per plugin")
    args = parser.parse_args()

    print(f"Verifying {args.index}\n")
    index = json.loads(fetch(args.index))
    plugins = index.get("plugins", [])
    if not plugins:
        print("FAIL: the index lists no plugins at all")
        return 1

    failures = 0
    checked = 0
    for entry in plugins:
        versions = entry.get("versions") or []
        if not versions:
            print(f"FAIL {entry['id']}: entry has no versions")
            failures += 1
            continue

        targets = versions if args.all_versions else [versions[-1]]
        for version in targets:
            label = f"{entry['id']} {version['version']}"
            checked += 1
            try:
                check_version(entry, version)
            except Failure as exc:
                print(f"FAIL {label}: {exc}")
                failures += 1
            else:
                print(f"  ok {label}")

    print(f"\n{checked} version(s) checked, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
