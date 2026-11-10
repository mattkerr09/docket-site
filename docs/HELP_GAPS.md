# Help questions without a supported answer

The help pages condense existing site pages. `data/help-answers.json` records
each answer and the source claims. The build fills prices, requirements and
licence counts from existing constants. The Help index chooses trying the app,
price and activation as its quick questions. The repo has no question-frequency
data to establish which questions are asked most often.

These questions need a source page before they can become help answers.

| Question | What an existing page would need to say |
| --- | --- |
| My receipt or key never arrived. What do I do? | `/download/` or `/contact/` needs a tested receipt and key recovery process. The current pages only say the key comes with the receipt. |
| My key is refused. What should I check? | `/download/` needs the actual error messages, their causes and tested recovery steps. The terms already cover releasing a place after a computer is lost or dies. |
| What should I send about a Windows crash? | `/contact/` needs a Windows bug-report checklist. It currently asks for the macOS version and what the user was doing. The support page keeps that request specific to Mac. |
| Where are logs, and how do I collect them? | `/contact/` needs tested log paths and safe collection steps for each platform. It does not currently ask users to send logs, screenshots or diagnostic bundles. |
| Windows blocks the installer. What do I click? | `/download/` needs the tested Windows warning and recovery steps. An installer link and a signing claim do not establish those steps. |
| How do I install, uninstall or repair the Windows app? | `/download/` needs a tested Windows walkthrough, including what is kept when the app is removed. |
| How do I back up or move audit history? | `/download/` or `/legal/privacy/` needs a supported export, backup and restore process for each platform. A storage path alone does not establish one. |
| Can I get an answer by a set time? | `/contact/` would need a real service promise. It currently says one person reads the inbox and tracker and gives no response-time promise. |
| What do I do if an audit appears stuck? | `/download/` needs tested signs of progress and recovery steps. It already explains crawl limits and Finish now, but does not give a fault diagnosis. |

## Release scope and the link graph

The job adds `/help/`, `/support/` and `/faq/`, plus the bundle sum on `/pricing/`.
The footer links change all pages made by the shared renderer. The default-brand
regression test permits only those additions, the new sitemap entries and the
resulting build ID changes when it compares existing output with main.

The offline link-graph gate finds stale counts after adding the pages and footer
links. Its dataset still describes 154 pages. The built site has 157 graph nodes.
Refreshing `data/link-equity.json` would also change the figures printed by
`/learn/internal-link-equity/`. This job limits existing page copy changes to
the pricing line and footer links, so that dataset refresh is left for Claude
to resolve with the copy limit. The command for that follow-up is
`python3 scripts/verify_link_graph.py --write --date 2026-11-09`, followed by a
rebuild in each brand and another graph check. That command has not been run
with `--write` in this job.
