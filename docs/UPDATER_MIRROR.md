# Updater mirror

Installed copies read `https://docketseo.app/updater.json`. Each platform URL
uses the legacy host and this layout.

```
https://docketseo.app/updates/<version>/<file>
```

The version folder matters. Both Mac updater filenames stay the same between
releases. The Windows filename includes its version.

## Local cache and Pages

`.updates-cache/<version>/` holds each updater file and a matching
`<file>.sha256` record. Files must be nonempty and smaller than 100,000,000
bytes. The cache is gitignored. Tracking these files on main would grow its
history with each release and copy those bytes into every worktree.

Staging prunes the cache to the two highest numeric versions. For example,
1.3.100 sorts above 1.3.99. The previous version stays available for an app
that read the manifest just before a release.

Deploy checks the manifest and cache before any push. After the existing
`site/` subtree split, it opens a temporary git worktree on `gh-pages-tmp`,
copies the two cached versions to `updates/`, and commits them there. It
removes the worktree with `git worktree remove --force`. The existing force
push publishes that branch. Each deploy starts from a new subtree split,
so binary commits stay off main and do not become ancestors of later
publish commits. Old objects may remain on GitHub until its storage cleanup.

## Stage a release

Run the normal collector after the build. It reads signatures from the `.sig`
files, stages the artifacts it cites, and writes the mirror URLs.

```
python3 scripts/collect_updater.py --version <version> --notes <notes-file>
```

The standalone staging command requires all three updater files.

```
python3 scripts/stage_updates_mirror.py --add <version> --from-dir <build-dist>
```

The host can also download the three assets from a published release.
This needs `gh` and network access. When release metadata includes a digest,
the downloaded bytes must match it before staging.

```
python3 scripts/stage_updates_mirror.py --add <version> --from-release v<version>
python3 scripts/stage_updates_mirror.py --prune
python3 scripts/stage_updates_mirror.py --plan
python3 scripts/verify_updates_mirror.py --offline
```

Staging validates all files before adding a version. A repeat with the same
bytes is safe. It refuses changed bytes at an existing version URL. To repair
a damaged cached version, remove that version's local cache folder and stage
it again from the release. The collector keeps its existing support for
releases with fewer platforms, including `--no-intel`.

## Roll back to release asset URLs

Run the collector with the same version, release tag and notes, adding
`--source github`, then use the normal reviewed deploy process.

```
python3 scripts/collect_updater.py --version <version> --notes <notes-file> --source github
```

When every manifest URL points to GitHub, deploy adds no mirror commit.
Installed copies keep reading the same manifest and checking signatures.

## Check the live bytes

Deploy runs this after the Pages push. It retries for up to ten minutes and
fails loudly if the manifest or bytes stay stale. It does not roll back.

```
python3 scripts/verify_updates_mirror.py --live
```

The live manifest must match the local one. Each cited mirror URL must serve
bytes with the recorded sha256 and size. A Range request must return a valid
206 response when the server advertises Range support. A server that ignores
Range without advertising support is reported. Content type is reported.
The checker uses GET requests and makes no HEAD requests.

The offline tests use fake artifacts, a local bare git origin, and local HTTP
servers. The host must check real Pages Range support, content types and
propagation after the first reviewed deploy.
