#!/usr/bin/env bash
# Keeps one GitHub issue, labelled "ai-check", open while figures await an AI check (econpulse/attention.py):
# opens it when something starts waiting, rewrites it and comments when the list changes, and closes it when
# nothing is waiting. Run by .github/workflows/update.yml after each build, with GH_TOKEN and GH_REPO set and
# MENTION the login to tag; needs the gh CLI.
set -euo pipefail

label="ai-check"
title="Figures await an AI check"
body="$(mktemp)"
python -m econpulse pending --mention "${MENTION:-}" > "$body"
gh label create "$label" --color FBCA04 --description "Figures awaiting an AI check" --force > /dev/null
open="$(gh issue list --label "$label" --state open --json number --jq '.[0].number // empty')"

if [ -s "$body" ]; then
  key="$(head -n 1 "$body")"
  if [ -z "$open" ]; then
    gh issue create --title "$title" --label "$label" --body-file "$body"
  elif grep -qF -- "$key" <<< "$(gh issue view "$open" --json body --jq .body)"; then
    echo "Issue #$open already lists what is waiting."
  else
    gh issue edit "$open" --body-file "$body" > /dev/null
    gh issue comment "$open" --body "What awaits an AI check has changed: the description above has the new list."
  fi
elif [ -n "$open" ]; then
  gh issue close "$open" --comment "Nothing awaits an AI check now: every figure on the site has been checked."
else
  echo "Nothing awaits an AI check."
fi
