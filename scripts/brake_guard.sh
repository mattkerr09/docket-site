# Sourced first by scripts/deploy.sh. Refuses a deploy while the update brake holds Docket.
#
# The brake (~/ops/bin/update-brake.py hold docket --yes) sets the live updater.json on gh-pages back to the previous
# release and records the hold in ~/ops/brake/docket.json. A deploy force-pushes this repo's site/ folder, updater.json
# included, to gh-pages, so any deploy during a hold silently puts the release the brake held back to customers again
# (CEO, 2026-11-08, writing ~/ops/RUNBOOK.md). The roll-forward deploy, the one that publishes the fixed higher version,
# is the only deploy that may pass, and it says so: DOCKET_DEPLOY_PAST_BRAKE=1.
#
# DOCKET_BRAKE_FILE exists for the guard's own test; nothing else sets it.
docket_brake_guard() {
  local hold="${DOCKET_BRAKE_FILE:-$HOME/ops/brake/docket.json}"
  if [ -e "$hold" ] && [ "${DOCKET_DEPLOY_PAST_BRAKE:-0}" != "1" ]; then
    echo "REFUSED: the update brake is holding Docket ($hold)."
    echo "  A deploy now would put the held-back updater.json back on gh-pages, and customers would update to it again."
    echo "  See ~/ops/RUNBOOK.md section 3, \"A bad update reached customers\"."
    echo "  For the roll-forward deploy that publishes the fixed version, and only that one:"
    echo "    DOCKET_DEPLOY_PAST_BRAKE=1 bash scripts/deploy.sh \"site: <fixed version>\""
    echo "  then release the brake: python3 ~/ops/bin/update-brake.py release docket --yes"
    return 1
  fi
  if [ -e "$hold" ]; then
    echo "==> brake guard: passing a held brake on purpose (DOCKET_DEPLOY_PAST_BRAKE=1), for the roll-forward deploy"
  fi
  return 0
}
