#!/usr/bin/env python3
"""Re-run the AI-crawler directives survey on the same ten thousand hosts.

    python3 scripts/collect_ai_directives.py --self-test
    python3 scripts/collect_ai_directives.py --fetch-reference
    python3 scripts/collect_ai_directives.py --max-hosts 400     # pilot
    python3 scripts/collect_ai_directives.py                     # the rest
    python3 scripts/collect_ai_directives.py --finalize
    python3 scripts/collect_ai_directives.py --recheck

WHY THIS FILE EXISTS. The August 2026 survey (data/ai-directives-survey-2026-08
.json.gz) was collected by a script that is in no repo and on no disk we could
find: build_directives.py says so ("the collector is not in this repo"), and the
improvement log records the same gap. Everything below is therefore RECONSTRUCTED
from what the August data and the published method statement fix:

  * the host list and the rank order       -> the August records themselves
  * one GET of https://<host>/robots.txt  -> method text on /index/ai-directives/
  * a second GET of /llms.txt only where robots.txt permitted our own agent,
    plus a control request for a path that cannot exist
  * a self-identifying user-agent with a contact address, 8 s timeout, no retries
  * state: ok (200, readable) / no_robots (any other status) / oversize /
    unreachable (the exception's class name, e.g. URLError, TimeoutError,
    RemoteDisconnected: the August errors are exactly urllib's, so urllib it is)
  * the parser: Docket's own RobotsTxt, as it stood on 2026-08-06 (see below)

What could NOT be recovered, and what this does about it:

  * The oversize threshold. The largest robots.txt the August run parsed was
    246,207 bytes; 116 hosts were dropped as oversize with no size recorded.
    256 KiB is used here, every oversize body is measured up to 1 MiB, and the
    size is recorded so the choice can be tested afterwards.
  * llms_present's exact rule. Rebuilt as: HTTP 200, a non-empty body, and a body
    that does not open like an HTML document. The August validation step
    (control request + opening-bytes test) is repeated on top of it, so the
    confirmed-llms.txt figure does not rest on this rule alone.
  * Whether the August run fell back to plain http. It must have: of 14 hosts
    that answered in August and fail over https now, 9 answer over http today.
    So https first, then http, and only when https could not connect at all.

THE PARSER, AND WHY THERE ARE TWO. robots.py in the app repo was changed three
times after the August survey and every change alters what a file means:

  a00abc8 (2026-08-10)  a comment or blank line no longer ends a group
  f28c655 / 0a4c14e     (sitemap and politeness fixes, no effect on access)
  2026-09-01            two `User-agent: *` groups are merged, not first-wins

A survey compared across those changes would measure the parser as much as the
web. scripts/robots_2026_08_06.py is robots.py as it stood at 07104ff, the last
commit before the August collection (2026-08-07T06:42Z), byte for byte. Every
access figure is computed with it, so August and October are read the same way.
The current parser reads the same October text too, and the bots whose answer
differs are recorded (`access_cur_diff`), so the size of the fix is visible
rather than assumed away.

CLOUDFLARE. Cloudflare's managed robots.txt is a block between two marker
comments, prepended to the site's own file. Its documented text was read from
developers.cloudflare.com/bots/additional-configurations/managed-robots-txt/
(page dated 2026-10-08). Per host this records whether the marker is present,
whether the block between the markers is the documented block, which crawlers it
disallows and which Content-signal it carries. The August data holds no
robots.txt text, so nothing here claims to know what August files said.

POLITENESS. One robots.txt request per host. llms.txt (and one control path)
only where our own agent was allowed. 16 workers across ten thousand different
hosts, a pause between a host's two requests, 8 s timeout, no retries. No vendor
crawler is impersonated: the agent names this survey and links /bot/.

Nothing is committed from here but the dataset. robots.txt bodies are kept in a
checkpoint outside the repo (--checkpoint) because the survey publishes
measurements, not other people's files.
"""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _Path
_sys.path.insert(0, str(_Path(__file__).resolve().parent))
import app_path  # noqa: E402

import argparse
import gzip
import hashlib
import importlib.util
import json
import random
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

AUGUST = DATA / "ai-directives-survey-2026-08.json.gz"
OUT_SURVEY = DATA / "ai-directives-survey-2026-10.json.gz"
OUT_VALIDATION = DATA / "ai-directives-llms-validation-2026-10.json.gz"
OUT_REFERENCE = DATA / "ai-robots-txt-reference-2026-10.json.gz"
REFERENCE_URL = ("https://raw.githubusercontent.com/ai-robots-txt/ai.robots.txt/"
                 "main/robots.json")

CONTACT = "support@docketseo.app"
UA = ("Docket-SEO-Audit-Survey/1.0 (+https://docketseo.app/bot/; research survey: "
      f"one robots.txt request per site, no crawling; contact {CONTACT})")
TIMEOUT = 8.0
OVERSIZE = 256 * 1024          # see the docstring: reconstructed, not recovered
READ_CAP = 1024 * 1024         # oversize bodies are measured up to here, not parsed
LLMS_CAP = 256 * 1024
HEAD_CHARS = 300
VALIDATION_BYTES = 8000
SEED = 20261019
WORKERS = 16
PAUSE_BETWEEN_REQUESTS = 0.25

#: robots.py at 07104ff, and the app's current one.
AUG_PARSER = Path(__file__).resolve().parent / "robots_2026_08_06.py"

# -- Cloudflare's managed block, from its documentation (page dated 2026-10-08) --

CF_AGENTS = ("Amazonbot", "Applebot-Extended", "Bytespider", "CCBot", "ClaudeBot",
             "Google-Extended", "GPTBot", "meta-externalagent")
#: The documented line is `Content-signal: search=yes, ai-train=no, use=reference`.
#: The page says `use=reference` was added to the managed content later, "in line
#: with the existing default of search=yes,ai-train=no", so both are accepted as
#: the documented block and the value found is recorded.
CF_SIGNALS = ("search=yes,ai-train=no,use=reference", "search=yes,ai-train=no")
CF_BEGIN = re.compile(r"^[ \t]*#[ \t]*BEGIN[ \t]+Cloudflare[ \t]+Managed[ \t]+content[ \t]*$",
                      re.I | re.M)
CF_END = re.compile(r"^[ \t]*#[ \t]*END[ \t]+Cloudflare[ \t]+Managed[ \t]+content[ \t]*$",
                    re.I | re.M)
CF_POLICY = ("as a condition of accessing this website, you agree to abide by the "
             "following content signals")
CONTENT_SIGNAL = re.compile(r"^[ \t]*content-signal[ \t]*:", re.I | re.M)


def _norm_line(line: str) -> str:
    key, sep, value = line.strip().partition(":")
    if not sep:
        return line.strip().lower()
    key = key.strip().lower()
    value = value.strip()
    if key == "content-signal":
        value = re.sub(r"\s+", "", value).lower()
    else:
        value = value.lower()
    return f"{key}: {value}"


def cloudflare(text: str) -> dict:
    """What the text says about Cloudflare's managed robots.txt.

    {"policy": bool}                       the Content Signals Policy comment only
    {"policy": bool, "marker": True, ...}  the BEGIN marker is present
    `exact` is True only when the lines between the markers are the documented
    block: the wildcard group with a Content-signal and Allow: /, then a
    Disallow: / for each of the eight crawlers, in the documented order.
    """
    flat = re.sub(r"\s+", " ", re.sub(r"(?m)^\s*#", " ", text)).lower()
    out: dict = {"policy": CF_POLICY in flat}
    begin = CF_BEGIN.search(text)
    if not begin:
        return out
    end = CF_END.search(text, begin.end())
    body = text[begin.end(): end.start() if end else len(text)]
    lines = [_norm_line(l) for l in body.splitlines() if l.strip()]
    agents, signal, group = [], None, None
    for l in lines:
        key, _, value = l.partition(": ")
        if key == "user-agent":
            group = value
        elif key == "content-signal" and signal is None:
            signal = value
        elif key == "disallow" and value == "/" and group not in (None, "*"):
            agents.append(group)
    expected = {
        sig: (["user-agent: *", f"content-signal: {sig}", "allow: /"]
              + [x for a in CF_AGENTS for x in (f"user-agent: {a.lower()}", "disallow: /")])
        for sig in CF_SIGNALS}
    out.update({
        "marker": True,
        "closed": bool(end),
        "signal": signal,
        "agents": sorted(agents),
        "exact": any(lines == exp for exp in expected.values()),
    })
    return out


# -- parsers ---------------------------------------------------------------

def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module        # dataclasses resolves annotations through this
    spec.loader.exec_module(module)
    return module


def load_parsers():
    aug = _load(AUG_PARSER, "robots_2026_08_06")
    cur = _load(app_path.backend() / "seo_engine" / "robots.py", "robots_current")
    return aug, cur


# -- probe lists -----------------------------------------------------------

_TOKEN = re.compile(r"^[A-Za-z0-9._-]+$")


def probe_lists(cur) -> tuple[list[str], list[str]]:
    """(the 40 August probes, the extra tokens on today's lists).

    Extra = ai.robots.txt as fetched for this run + the app's AI_USER_AGENTS +
    the vendor-documented tokens, minus the 40. Asking a parsed file about a
    token costs no request, so the whole current list is read from the same
    robots.txt that was already fetched.
    """
    aug = json.loads(gzip.decompress(AUGUST.read_bytes()))["probe_bots"]
    seen = {b.lower() for b in aug}
    extra: list[str] = []
    names = []
    if OUT_REFERENCE.exists():
        names += list(json.loads(gzip.decompress(OUT_REFERENCE.read_bytes())))
    names += list(cur.AI_USER_AGENTS)
    names += list(cur.DOCUMENTED_AI_TOKENS)
    for name in names:
        if _TOKEN.match(name) and name.lower() not in seen:
            seen.add(name.lower())
            extra.append(name)
    return aug, sorted(extra, key=str.lower)


# -- fetching --------------------------------------------------------------

def get(url: str, cap: int):
    """(status, content_type, body, error). Exactly one of status/error is set."""
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "text/plain,*/*;q=0.5"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read(cap + 1)
            ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
            return resp.status, ctype, body, None
    except urllib.error.HTTPError as exc:
        return exc.code, "", b"", None
    except Exception as exc:  # noqa: BLE001 — unreachable is data, not a crash
        return None, "", b"", type(exc).__name__


#: Errors after which a second attempt over plain http is not made: the host
#: answered slowly, and asking again would only wait another eight seconds.
_NO_FALLBACK = ("TimeoutError", "timeout")


def get_either(host: str, path: str, cap: int):
    """https first; plain http only when https could not be connected at all.

    Reconstructed, and the evidence is in the data: of 14 pilot hosts that
    answered in August and fail over https today, 9 answer over http. A
    collector that never tried http would have reported those 9 unreachable in
    August too. An HTTP error status (404, 403...) is an answer and ends it.
    Returns (scheme, status, content_type, body, error).
    """
    s, ct, b, err = get(f"https://{host}{path}", cap)
    if err is None or err in _NO_FALLBACK:
        return "https", s, ct, b, err
    s2, ct2, b2, err2 = get(f"http://{host}{path}", cap)
    if err2 is None:
        return "http", s2, ct2, b2, None
    return "https", None, "", b"", err2


def _head(body: bytes) -> str:
    return body[:VALIDATION_BYTES].decode("utf-8", "replace")[:HEAD_CHARS]


_NOT_A_DOCUMENT = ("<!doctype", "<html", "<head", "<body")


def llms_present(status, body: bytes) -> bool:
    if status != 200 or not body:
        return False
    return not body[:512].decode("utf-8", "replace").lstrip("﻿ \t\r\n").lower() \
        .startswith(_NOT_A_DOCUMENT)


def _is_h1(body: bytes) -> bool:
    return body[:512].decode("utf-8", "replace").lstrip("﻿ \t\r\n").startswith("# ")


# -- one host --------------------------------------------------------------

def classify(host: str, rank: int, status, ctype, body: bytes, error,
             aug, cur, probes: list[str], extra: list[str], scheme: str = "https"):
    """The survey record for one host, from a robots.txt response. No network."""
    rec: dict = {"rank": rank, "host": host, "robots_status": status}
    if scheme != "https":
        rec["scheme"] = scheme
    if error:
        rec.update(state="unreachable", error=error)
        return rec, None
    if status != 200:
        rec["state"] = "no_robots"
        return rec, None
    if len(body) > OVERSIZE:
        rec.update(state="oversize", robots_bytes=len(body),
                   robots_bytes_capped=len(body) > READ_CAP)
        return rec, None

    text = body.decode("utf-8", "replace")
    rt = aug.RobotsTxt(text, 200, f"https://{host}/robots.txt")
    now = cur.RobotsTxt(text, 200, f"https://{host}/robots.txt")
    access = {b: rt.allowed("/", b) for b in probes}
    differ = {b: now.allowed("/", b) for b in probes if now.allowed("/", b) != access[b]}

    named = {a for g in rt.groups for a in g.agents if a and a != "*"}
    ext_blocked = [t for t in extra
                   if not rt.allowed("/", t) and any(a in t.lower() for a in named)]
    ext_differ = {t: now.allowed("/", t) for t in extra
                  if now.allowed("/", t) != rt.allowed("/", t)}

    rec.update(
        state="ok", robots_bytes=len(body),
        robots_hash=hashlib.sha256(body).hexdigest()[:16],
        bom=body.startswith(b"\xef\xbb\xbf"),
        ua_tokens=[a for g in rt.groups for a in g.agents],
        has_sitemap=bool(rt.sitemaps),
        content_signal=bool(CONTENT_SIGNAL.search(text)),
        access=access,
        ext_blocked_by_name=ext_blocked,
    )
    if differ:
        rec["access_cur_diff"] = differ
    if ext_differ:
        rec["ext_cur_diff"] = sorted(ext_differ)
    cf = cloudflare(text)
    if cf.get("marker") or cf.get("policy"):
        rec["cf"] = cf
    return rec, text


def survey_host(host: str, rank: int, aug, cur, probes, extra):
    scheme, status, ctype, body, error = get_either(host, "/robots.txt", READ_CAP)
    rec, text = classify(host, rank, status, ctype, body, error, aug, cur, probes, extra,
                         scheme)
    val = None
    if rec["state"] == "ok":
        time.sleep(PAUSE_BETWEEN_REQUESTS)
        # "Permitted our own user-agent": the same rule a crawler would apply,
        # asked of the file we just read.
        aug_rt = aug.RobotsTxt(text, 200, f"https://{host}/robots.txt")
        allowed = aug_rt.allowed("/llms.txt", UA)
        rec["llms_allowed_for_us"] = allowed
        if allowed:
            s, ct, b, err = get(f"{scheme}://{host}/llms.txt", LLMS_CAP)
            rec.update(llms_status=s, llms_present=llms_present(s, b))
            if s == 200:
                rec.update(llms_bytes=len(b), llms_ctype=ct,
                           llms_is_markdown_h1=_is_h1(b))
            if rec["llms_present"]:
                time.sleep(PAUSE_BETWEEN_REQUESTS)
                token = hashlib.sha1(f"{host}{SEED}".encode()).hexdigest()[:12]
                cs, cct, cb, _ = get(
                    f"{scheme}://{host}/docket-survey-control-{token}.txt", VALIDATION_BYTES)
                val = {"host": host, "llms_status": s, "llms_ct": ct,
                       "llms_head": _head(b), "llms_len": min(len(b), VALIDATION_BYTES),
                       "ctrl_status": cs, "ctrl_ct": cct, "ctrl_head": _head(cb),
                       "ctrl_len": min(len(cb), VALIDATION_BYTES)}
    return rec, val, text


# -- driver ----------------------------------------------------------------

def august_hosts():
    d = json.loads(gzip.decompress(AUGUST.read_bytes()))
    return d, [(r["host"], r["rank"]) for r in d["records"]]


def read_checkpoint(path: Path) -> dict:
    done = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                row = json.loads(line)
                done[row["rec"]["host"]] = row
    return done


def run(args) -> int:
    aug, cur = load_parsers()
    probes, extra = probe_lists(cur)
    _, hosts = august_hosts()
    order = hosts[:]
    random.Random(SEED).shuffle(order)       # spreads load across networks; fixed, so resumable
    done = read_checkpoint(args.checkpoint)
    todo = [h for h in order if h[0] not in done]
    if args.max_hosts is not None:
        todo = todo[: max(0, args.max_hosts - len(done))]
    print(f"{len(hosts)} hosts, {len(done)} already done, {len(todo)} to fetch "
          f"({args.workers} workers, {TIMEOUT:.0f}s timeout)", flush=True)
    if not todo:
        return 0

    began = time.time()
    lock = threading.Lock()
    n = 0
    with args.checkpoint.open("a") as out, ThreadPoolExecutor(args.workers) as pool:
        futures = [pool.submit(survey_host, h, r, aug, cur, probes, extra) for h, r in todo]
        for fut in as_completed(futures):
            rec, val, text = fut.result()
            with lock:
                out.write(json.dumps({"rec": rec, "val": val, "text": text}) + "\n")
                n += 1
                if n % 250 == 0:
                    out.flush()
                    print(f"  {n}/{len(todo)}  {time.time() - began:.0f}s", flush=True)
    meta = args.checkpoint.with_suffix(".meta.json")
    prior = json.loads(meta.read_text()) if meta.exists() else {"started": None, "seconds": 0.0}
    prior["started"] = prior["started"] or time.strftime("%Y-%m-%dT%H:%M:%S+00:00",
                                                          time.gmtime(began))
    prior["seconds"] = round(prior["seconds"] + time.time() - began, 1)
    prior["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    meta.write_text(json.dumps(prior))
    print(f"fetched {n} in {time.time() - began:.0f}s", flush=True)
    return 0


def finalize(args) -> int:
    aug, cur = load_parsers()
    probes, extra = probe_lists(cur)
    august, hosts = august_hosts()
    done = read_checkpoint(args.checkpoint)
    missing = [h for h, _ in hosts if h not in done]
    if missing and not args.allow_partial:
        print(f"{len(missing)} hosts have no result; run again, or --allow-partial")
        return 1
    meta = json.loads(args.checkpoint.with_suffix(".meta.json").read_text())
    rows = sorted(done.values(), key=lambda r: r["rec"]["rank"])
    for row in rows:
        # Python 3.9 names a socket timeout `timeout`; 3.10 and later call it
        # TimeoutError, which is how the August records spell it.
        if row["rec"].get("error") == "timeout":
            row["rec"]["error"] = "TimeoutError"
    out = {
        "collected": meta["started"],
        "finished": meta["finished"],
        "population": august["population"],
        "population_source": ("the host list and rank order of the August 2026 survey "
                              "(data/ai-directives-survey-2026-08.json.gz), unchanged"),
        "duration_s": meta["seconds"],
        "probe_bots": probes,
        "ext_bots": extra,
        "method": {
            "user_agent": UA, "timeout_s": TIMEOUT, "scheme": "https, then plain http only if https could not connect; redirects followed",
            "oversize_bytes": OVERSIZE, "read_cap_bytes": READ_CAP, "seed": SEED,
            "parser": "scripts/robots_2026_08_06.py (robots.py at app commit 07104ff)",
            "cloudflare_agents": list(CF_AGENTS), "cloudflare_signals": list(CF_SIGNALS),
        },
        "records": [r["rec"] for r in rows],
    }
    if not args.allow_partial:
        args.out_survey.write_bytes(gzip.compress(
            json.dumps(out, separators=(",", ":")).encode(), mtime=0))
        vals = [r["val"] for r in rows if r["val"]]
        args.out_validation.write_bytes(gzip.compress(
            json.dumps(vals, separators=(",", ":")).encode(), mtime=0))
        print(f"wrote {args.out_survey} ({args.out_survey.stat().st_size // 1024} KB), "
              f"{args.out_validation} ({len(vals)} candidates)")
    else:
        scratch = args.checkpoint.with_suffix(".partial.json")
        scratch.write_text(json.dumps(out))
        print(f"partial: {len(rows)} records -> {scratch}")
    return 0


OUT_RECHECK = DATA / "ai-directives-recheck-2026-10.json"


def recheck() -> int:
    """Fetch a sample of hosts a second time and say whether the file was the same.

    The October finding that matters most is a robots.txt that CHANGED: the
    Cloudflare-looking block present in August and absent now. A file that
    differs between two fetches an hour apart would make that unsafe to state,
    so this asks. 40 hosts that showed the block in August and not in October,
    15 that showed it in both, drawn with a fixed seed, one request each, and
    the new body compared by hash with the one the survey stored. Only counts
    are written, no host.
    """
    august, _ = august_hosts()
    old = {r["host"]: r for r in august["records"]}
    new = {r["host"]: r for r in json.loads(gzip.decompress(OUT_SURVEY.read_bytes()))["records"]}

    def sig(r):
        return bool(r.get("content_signal")) and all(
            (r.get("access") or {}).get(b) is False for b in CF_AGENTS)

    both_ok = [h for h in old if old[h]["state"] == "ok" and new[h]["state"] == "ok"]
    gone = [h for h in both_ok if sig(old[h]) and not sig(new[h])]
    kept = [h for h in both_ok if sig(old[h]) and sig(new[h])]
    rnd = random.Random(7)
    picked = [("gone", h) for h in rnd.sample(gone, 40)] + \
             [("kept", h) for h in rnd.sample(kept, 15)]
    out = {"checked": time.strftime("%Y-%m-%d", time.gmtime()),
           "gone": {"asked": 0, "same_file": 0}, "kept": {"asked": 0, "same_file": 0},
           "of_gone_population": len(gone), "of_kept_population": len(kept)}
    for group, host in picked:
        _, status, _, body, _ = get_either(host, "/robots.txt", READ_CAP)
        out[group]["asked"] += 1
        if status == 200 and hashlib.sha256(body).hexdigest()[:16] == new[host]["robots_hash"]:
            out[group]["same_file"] += 1
        time.sleep(0.3)
    OUT_RECHECK.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps(out))
    return 0


def fetch_reference() -> int:
    status, _, body, error = get(REFERENCE_URL, 4 * 1024 * 1024)
    if status != 200:
        print(f"reference list: {status or error}")
        return 1
    data = json.loads(body)
    OUT_REFERENCE.write_bytes(gzip.compress(
        json.dumps(data, separators=(",", ":"), sort_keys=True).encode(), mtime=0))
    print(f"ai.robots.txt: {len(data)} tokens -> {OUT_REFERENCE}")
    return 0


# -- self-test -------------------------------------------------------------

def _managed(signal="search=yes, ai-train=no, use=reference", extra=""):
    lines = ["# As a condition of accessing this website, you agree to abide by the",
             "# following content signals:", "", "# BEGIN Cloudflare Managed content", "",
             "User-Agent: *", f"Content-signal: {signal}", "Allow: /", ""]
    for a in CF_AGENTS:
        lines += [f"User-agent: {a}", "Disallow: /", ""]
    lines += [extra, "# END Cloudflare Managed Content"] if extra else \
             ["# END Cloudflare Managed Content"]
    return "\n".join(lines) + "\n"


def self_test() -> int:
    aug, cur = load_parsers()
    probes, extra = probe_lists(cur)
    bad = []

    def check(label, ok):
        if not ok:
            bad.append(label)

    own = "User-agent: *\nDisallow: /lp\n\nSitemap: https://example.test/sitemap.xml\n"
    full = _managed() + own
    c = cloudflare(full)
    check("documented block is exact", c.get("exact") is True)
    check("agents read back", c["agents"] == sorted(a.lower() for a in CF_AGENTS))
    check("signal read back", c["signal"] == "search=yes,ai-train=no,use=reference")
    check("older signal still exact",
          cloudflare(_managed("search=yes,ai-train=no")).get("exact") is True)
    check("different signal is a marker, not exact",
          cloudflare(_managed("search=no,ai-train=no")).get("exact") is False)
    check("a missing crawler is not exact",
          cloudflare(full.replace("User-agent: CCBot\nDisallow: /\n\n", "")).get("exact") is False)
    check("an added crawler is not exact",
          cloudflare(full.replace("# END", "User-agent: PerplexityBot\nDisallow: /\n# END")
                     ).get("exact") is False)
    check("no marker, no cloudflare", "marker" not in cloudflare(own))
    check("policy comment alone",
          cloudflare("# As a condition of accessing this website, you agree to abide by the\n"
                     "# following content signals:\n").get("policy") is True)
    check("someone else's block named like ours", "marker" not in cloudflare(
        "# BEGIN Cloudflare Managed stuff\nUser-agent: GPTBot\nDisallow: /\n"))

    rec, _ = classify("x.test", 1, 200, "text/plain", full.encode(), None,
                      aug, cur, probes, extra)
    check("GPTBot blocked", rec["access"]["GPTBot"] is False)
    check("OAI-SearchBot not blocked", rec["access"]["OAI-SearchBot"] is True)
    check("signal seen", rec["content_signal"] is True)
    check("sitemap seen", rec["has_sitemap"] is True)
    check("cf recorded", rec["cf"]["exact"] is True)

    # The two parsers must disagree where the fix changed meaning, and only there.
    commented = "User-agent: GPTBot\n# no training\nDisallow: /\n"
    r2, _ = classify("y.test", 2, 200, "text/plain", commented.encode(), None,
                     aug, cur, probes, extra)
    check("august parser lost the rule after a comment", r2["access"]["GPTBot"] is True)
    check("current parser keeps it", r2["access_cur_diff"].get("GPTBot") is False)
    two = "User-agent: *\nAllow: /public\n\nUser-agent: *\nDisallow: /\n"
    r3, _ = classify("z.test", 3, 200, "text/plain", two.encode(), None, aug, cur, probes, extra)
    check("august parser read only the first * group", r3["access"]["OAI-SearchBot"] is True)
    check("current parser merges them", r3["access_cur_diff"].get("OAI-SearchBot") is False)

    states = [
        classify("a.test", 4, None, "", b"", "URLError", aug, cur, probes, extra)[0]["state"],
        classify("b.test", 5, 404, "", b"", None, aug, cur, probes, extra)[0]["state"],
        classify("c.test", 6, 200, "", b"x" * (OVERSIZE + 1), None, aug, cur, probes, extra)[0]["state"],
        classify("d.test", 7, 200, "", b"", None, aug, cur, probes, extra)[0]["state"],
    ]
    check("states", states == ["unreachable", "no_robots", "oversize", "ok"])
    check("llms: markdown is present", llms_present(200, b"# Name\n\n> text"))
    check("llms: html is not", not llms_present(200, b"\n<!DOCTYPE html><html>"))
    check("llms: 404 is not", not llms_present(404, b"# Name"))
    check("llms: empty is not", not llms_present(200, b""))
    check("the 40 August probes are all there", len(probes) == 40)

    if bad:
        print("SELF-TEST FAILED:")
        for b in bad:
            print("  -", b)
        return 1
    print(f"self-test ok ({len(probes)} probes, {len(extra)} extra tokens)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--fetch-reference", action="store_true")
    ap.add_argument("--finalize", action="store_true")
    ap.add_argument("--recheck", action="store_true")
    ap.add_argument("--allow-partial", action="store_true")
    ap.add_argument("--max-hosts", type=int, default=None)
    ap.add_argument("--workers", type=int, default=WORKERS)
    ap.add_argument("--checkpoint", type=Path, default=None,
                    help="JSONL kept OUTSIDE the repo: one line per host, with the robots.txt body")
    ap.add_argument("--out-survey", type=Path, default=OUT_SURVEY)
    ap.add_argument("--out-validation", type=Path, default=OUT_VALIDATION)
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.fetch_reference:
        return fetch_reference()
    if args.recheck:
        return recheck()
    if args.checkpoint is None:
        ap.error("--checkpoint is required (a path outside the repo)")
    if args.finalize:
        return finalize(args)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
