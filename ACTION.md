# Docket SEO audit: GitHub Action

Crawl a site and fail the build on SEO regressions. Wraps the CLI that ships
inside [Docket](https://docketseo.app), so the shell you would otherwise
maintain lives here instead.

**For Linux runners, use [mattkerr09/docket-audit-action](https://github.com/mattkerr09/docket-audit-action).**
It installs Docket's Linux build on `ubuntu-latest`, or the macOS build on a
macOS runner, runs the free version, which needs no key, and fails the job at
the severity you set.

This action installs the Apple silicon macOS build, so it needs
`runs-on: macos-latest` and stops on any other runner with a sentence saying
so. It can also write SARIF or JUnit, which needs a licence key in
`DOCKET_LICENCE_KEY`. A licence activates on up to 3 computers at a time and a
fresh hosted runner counts as a new one, so use the key on a self-hosted runner.

`--render` does not work on Linux: the renderer is a WebKit helper that exists
only on macOS. There is no Windows build of the command line yet.

macOS runner minutes cost about ten times Linux ones. See
[the cost arithmetic](https://docketseo.app/for/developers/).

## Use it

```yaml
name: SEO gate
on: [pull_request]

jobs:
  seo:
    runs-on: macos-latest
    steps:
      - uses: mattkerr09/docket-site@v1.3.147
        with:
          url: https://staging.example.com
          fail-on: critical
```

### Findings on the Security tab

```yaml
      - uses: mattkerr09/docket-site@v1.3.147
        env:
          DOCKET_LICENCE_KEY: ${{ secrets.DOCKET_LICENCE_KEY }}   # SARIF needs a licence
        with:
          url: https://staging.example.com
          format: sarif
          fail-on: never          # let the upload run, then gate elsewhere
      - uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: docket-report.sarif
```

SARIF alerts land on the Security tab. They do **not** annotate the pull
request diff: SARIF locations are files and lines, an SEO finding is about a
URL, and there is no general way to map one to the other.

### Findings in the test-report panel

```yaml
      - uses: mattkerr09/docket-site@v1.3.147
        env:
          DOCKET_LICENCE_KEY: ${{ secrets.DOCKET_LICENCE_KEY }}   # JUNIT needs a licence
        with:
          url: https://staging.example.com
          format: junit
          fail-on: never
      - uses: mikepenz/action-junit-report@v4
        if: always()
        with:
          report_paths: docket-report.xml
```

One testcase per check, so the panel reads "93 tests, 4 failed". A check that
ran and found nothing passes; a check that could not run is **skipped**, never
passed. If the crawl reached no pages at all, every check is skipped and none
is green: a passing test report is read as a guarantee, and an audit that
read nothing has not earned one.

## Inputs

| Input | Default | What it does |
|---|---|---|
| `url` | *required* | Site to audit. `https://` is assumed if omitted. |
| `fail-on` | `critical` | `critical`, `high`, `medium`, `low`, `notice` or `never`. |
| `pages` | `100` | Maximum pages to crawl. |
| `format` | `text` | `text`, `sarif` or `junit`. |
| `output-file` | `docket-report` | Base name for the `sarif`/`junit` file. |
| `render` | `0` | Pages to run through WebKit first. Much slower. |
| `version` | the latest release when this file was published | Docket release tag to install. |

`fail-on` defaults to `critical` deliberately. Almost every real site carries
HIGH findings, and a gate that fails on ordinary work gets wrapped in
`|| true` within a month.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Ran, found nothing at or above the threshold |
| `1` | Docket could not run: a tool failure, not a finding about your site |
| `2` | Ran, found something at or above the threshold |

`1` and `2` are deliberately distinct. "Your site is broken" and "the tool is
broken" need opposite responses from whoever reads the log. A staging URL that
does not answer is `2`, not `1`: Docket ran fine, the site was not there, and
that should stop a deploy.

## Gating on what this deploy broke

An absolute threshold is the wrong question for a pipeline: every real site
carries standing findings, so a bar tight enough to catch a regression fails
every build and one loose enough to pass catches nothing. `docket diff` compares
two audits and fails only on what is new or worse. It is not wired into this
action yet; run it directly for now:

```yaml
      - run: docket diff https://example.com https://staging.example.com --fail-on medium
```

## What this action deliberately does not do

It does not cache the download between runs, does not post a PR comment, and
does not upload anything anywhere. It installs, audits, and exits with a code.
It is not published to the GitHub Marketplace; reference it by repository as
shown above.
