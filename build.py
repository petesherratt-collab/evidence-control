#!/usr/bin/env python3
"""Regenerate index.html with the current time, a sequence number and a nonce.

Run by .github/workflows/tick.yml on a schedule.

The page is deliberately built in two halves, because a normalisation contract
has two halves and a control that tests only one of them is half a control:

  inside <main>   the signal — an ISO generation timestamp and a counter.
                  A watcher selecting `main` must see this move.
  outside <main>  the noise — a random build nonce in the footer. A watcher
                  selecting `main` must NOT see this, and the raw response
                  must.

The nonce also makes the control structurally match the real targets it exists
to vouch for. Three of those churn at the raw level on every request (CSP
nonces, ASP.NET viewstate) while their selected region sits still. A control
whose raw bytes only moved when its signal moved would be a simpler shape than
anything it is standing in for.

The sequence number is `git rev-list --count HEAD` — the number of commits in
this repository's history when the page was built. It is not a counter this
script keeps, which matters: anyone who clones the repo can recompute it, so
the page cannot claim a tick that is not in the history behind it.
"""
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).parent

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Evidence archive — control target</title>
<style>
  body {{ font: 16px/1.6 system-ui, sans-serif; max-width: 42rem;
         margin: 3rem auto; padding: 0 1.2rem; }}
  #tick {{ font-family: ui-monospace, monospace; font-size: 1.05rem;
          background: #f4f4f5; border: 1px solid #d4d4d8; border-radius: 6px;
          padding: 1rem; margin: 1.5rem 0; }}
  #tick span {{ display: block; }}
  .k {{ color: #52525b; font-size: .85rem; letter-spacing: .04em;
       text-transform: uppercase; }}
  h1 {{ font-size: 1.4rem; }}
  footer {{ margin-top: 2.5rem; padding-top: 1rem; font-size: .9rem;
           color: #52525b; border-top: 1px solid #d4d4d8; }}
  code {{ font-family: ui-monospace, monospace; }}
  @media (prefers-color-scheme: dark) {{
    body {{ background: #18181b; color: #e4e4e7; }}
    #tick {{ background: #27272a; border-color: #3f3f46; }}
    .k, footer {{ color: #a1a1aa; }}
    footer {{ border-color: #3f3f46; }}
  }}
</style>
</head>
<body>

<main>

<h1>Evidence archive — control target</h1>

<p>This page exists to be watched. It is rewritten on a schedule by a GitHub
Action, so it is <em>known</em> to change, and a monitor that fails to observe
a change here has told you something about the monitor rather than about the
world.</p>

<p id="tick">
<span class="k">generated</span>
<span id="generated"><time datetime="{stamp}">{stamp}</time></span>
<span class="k">sequence</span>
<span id="seq">{seq}</span>
</p>

<p>It is the control for
<a href="https://github.com/petesherratt-collab/evidence-archive">evidence-archive</a>,
which collects UK government contract award notices. Those targets can sit
unchanged for weeks, and an archive of unchanged observations is only worth
something if you can tell it apart from an archive that stopped collecting.
Polling this page alongside them is what makes that difference visible: if the
quiet targets are quiet and this one is still ticking, the quiet is real.</p>

<p>Everything above that moves between builds is inside
<code>&lt;main&gt;</code>. The build nonce in the footer is outside it, and is
there to be <em>rejected</em> — a watcher selecting <code>main</code> should
see the timestamp move and never see the nonce. The generation timestamp is
machine-readable in the <code>datetime</code> attribute, so the lag between
when this page was built and when an archive observed it can be measured
rather than assumed.</p>

<p>What a tick observed here does and does not show is set out in
<a href="https://github.com/petesherratt-collab/evidence-control#what-this-proves">the
README</a>. In short: it evidences that the collector fetched fresh content
from the open internet and recorded it. It says nothing about whether the
extraction rules for any other target were still selecting the right thing.</p>

</main>

<footer>
<p>Build nonce <code id="nonce">{nonce}</code> — deliberate noise, outside
<code>&lt;main&gt;</code>. It changes on every build whether or not anything
above it did.</p>
<p>No tracking, no cookies, nothing dynamic — a static file rebuilt in CI.
Crawl it freely; that is what it is for.
<a href="https://github.com/petesherratt-collab/evidence-control">Source</a>.</p>
</footer>

</body>
</html>
"""


def main():
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    seq = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=HERE, capture_output=True, text=True, check=True,
    ).stdout.strip()
    (HERE / "index.html").write_text(
        TEMPLATE.format(stamp=stamp, seq=seq, nonce=secrets.token_hex(8)),
        encoding="utf-8",
    )
    print("built {} seq {}".format(stamp, seq))


if __name__ == "__main__":
    main()
