# evidence-control

A page that is known to change, so that pages which don't change mean something.

This is the control target for
[evidence-archive](https://github.com/petesherratt-collab/evidence-archive),
which collects UK government contract award notices on a schedule and records
every poll — including the polls where nothing moved.

## The problem it solves

Recording unchanged polls is the whole point of that archive: it is what lets
you say "this notice was checked every six hours for a year and never moved"
instead of merely failing to have evidence that it did. But a log of unchanged
polls is only worth as much as your confidence that the collector was actually
working. Consider a fortnight of silence across every target. Two readings:

1. Nothing in UK contract awards changed on those pages for two weeks.
2. The collector was resolving, or fetching, or decoding, or recording
   incorrectly for two weeks, and wrote "unchanged" fourteen days running.

The poll log alone cannot separate them, because both produce the same rows.
That is not a hypothetical failure: a fetcher serving from a stale cache, a
DNS answer pointing somewhere wrong, or a captive-portal login page returning
HTTP 200 all produce plausible, well-formed, *false* unchanged polls.

A control target separates them. This page changes every fifteen minutes, by a
mechanism that has nothing to do with the collector. If the collector polled it
and saw a change, the collector was working. Then the silence on the real
targets is a finding rather than an absence of data.

## How it works

`build.py` regenerates `index.html` with the current UTC time and a sequence
number. `.github/workflows/tick.yml` runs it every fifteen minutes and commits
the result; GitHub Pages serves it.

The sequence number is `git rev-list --count HEAD`, the number of commits
behind the page when it was built. That is deliberately not a counter this repo
keeps for itself: anyone who clones the repository can recompute it, so the
page cannot assert a tick that the history does not support.

### Signal inside `<main>`, noise outside it

A normalisation contract has two halves — select the thing that matters,
discard the churn around it — and a control that exercises only the first half
is half a control. So the page is built in two:

| where | what | a watcher selecting `main` should |
|---|---|---|
| inside `<main>` | ISO generation timestamp, sequence number | **see it move** |
| in `<footer>` | a random build nonce | **never see it** |

The nonce changes on every build whether or not anything inside `main` did.
That also makes the control structurally resemble the targets it vouches for:
three of those churn at the raw level on every single request — CSP nonces,
ASP.NET viewstate — while their selected region sits perfectly still. A control
whose raw bytes moved only when its signal moved would be a simpler shape than
anything it is standing in for, and would not exercise the distinction between
`raw chg` and `doc chg` that the whole archive turns on.

### Measuring observation lag

The generation time is machine-readable in the `datetime` attribute of a
`<time>` element inside `main`. Because the page states when it was built, and
the archive records when it was fetched, the difference between them is
measurable rather than assumed.

That matters beyond this page. Any claim of the form "this notice changed
between X and Y" rests on an observation resolution, and the configured poll
period is a floor for it, not the real figure — scheduler drift, retries and
fetch time all widen the bracket. The control is the only target whose true
change time is known, so it is the only place the real width can be measured.
`kibitzr archive calibration` in the collector reads it back out of the
retained responses.

## What this proves

A poll of this page that observed a change shows that, at that moment, the
collector:

- resolved a hostname and connected to it
- fetched content from the open internet, not from a cache
- decoded and hashed what came back
- wrote a poll row, and correctly judged it as changed

That is the liveness claim, and it is what makes a quiet fortnight on the real
targets readable.

## What this does not prove

Being clear about the bounds matters more than the claim itself.

- **It says nothing about extraction on other targets.** Each real target has
  its own CSS or jq selector, tuned to a page this repo does not resemble. A
  selector that silently stops matching — because the site was redesigned —
  produces empty or wrong normalised content while this control ticks happily.
  The control cannot see that. Transform fingerprints and the `status`
  selector warnings are what cover it.
- **It says nothing about the targets being reachable.** The collector can be
  perfectly healthy and still be blocked, rate-limited or 403'd by one
  specific host. That shows up as failed polls on that target, not here.
- **It is one host.** Everything here rides on GitHub — the schedule that
  builds the page and the CDN that serves it. A GitHub outage stops the ticks
  without the collector being at fault, so a control gap is a prompt to
  investigate, not a verdict. Moving the hosting to a different provider from
  the one running the cron would split that dependency; it has not been done,
  because the dependency that actually matters is on the collecting machine,
  and there is none.
- **A missed tick is not a missed poll.** GitHub's scheduler runs late and
  skips runs under load. The collector polls hourly against a fifteen-minute
  tick, so there is room for a couple of skips before a poll sees a stale page.
  Read a single stale poll as jitter and a run of them as a fault.

## Operational note

GitHub disables scheduled workflows in repositories with no activity for 60
days. The ticks themselves are commits, but they are made by the Actions token,
which does not always count as the activity that resets that timer. If the
control series stops, check whether the workflow was disabled before assuming
anything about the collector.

## Licence

Public domain (CC0). It is a page that prints the time.
