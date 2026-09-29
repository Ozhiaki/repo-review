#!/bin/bash
# rr-run.sh <repo>: run the repo-review passes on <repo> in one Claude pane
# beside this tmux pane, one pass at a time. The agent starts in <repo>.
# Outputs go to the folder above <repo>, which must have the same name
# (~/p/farm/<name>/<name>); clones for pass 04 go to .rr-scratch there. After the
# last pass the script deletes .rr-scratch; on a stop it keeps it. Either
# way the pane stays open for the human.
# Env: GASHKI (binary, default gashki), RR_PROMPTS (prompt dir),
# RR_WAIT (wait budget per try, default 2h), RR_MODEL (Claude model,
# default sonnet). The agent runs in bypassPermissions mode, with the
# 1M context window on (the user settings turn it off).
# Needs gashki with JSON contract 2 (github.com/Ozhiaki/gashki): spawn,
# send (for .data.turn_cursor) and wait --since. Prompts name the pass
# files as {RR}; the script fills in this repo's root.
set -uo pipefail
GASHKI=${GASHKI:-gashki}
MODEL=${RR_MODEL:-sonnet}
HERE=$(dirname "$(realpath "$0")")
RR_DIR=$(cd "$HERE/../.." && pwd)
PROMPTS=${RR_PROMPTS:-$HERE/prompts}
PASSES="01 02 02.5 03 04 05"
LINT=$RR_DIR/tools/lint_pass_outputs.py

die() { echo "rr: $*" >&2; exit 1; }
[[ $# -eq 1 ]] || die "usage: rr-run.sh <repo>"
[[ -n "${TMUX:-}" && -n "${TMUX_PANE:-}" ]] || die "run inside tmux"
REPO=$(cd "$1" 2>/dev/null && pwd) || die "no such folder: $1"
ART=$(dirname "$REPO")
[[ "$(basename "$ART")" == "$(basename "$REPO")" ]] || die "$REPO must sit in a folder of the same name, for example ~/p/farm/<name>/<name>"
NAME=$(basename "$REPO")
PANE="rr-$NAME/analyst"
LOG="$ART/rr-run.log"
MARK="$ART/.rr-mark"
SCRATCH="$ART/.rr-scratch"
for p in $PASSES; do [[ -f "$PROMPTS/$p.txt" ]] || die "missing prompt $PROMPTS/$p.txt"; done
[[ -f "$LINT" ]] || die "missing linter $LINT"
"$GASHKI" --version 2>/dev/null | grep -q '(contract 2,' || die "$GASHKI must speak JSON contract 2; got: $("$GASHKI" --version 2>&1 | head -1)"

log() { echo "$(date '+%F %T') $*" >>"$LOG"; }
code() { jq -r '.errors[0].code // empty' 2>/dev/null; }
handover() {
  echo "rr: stopped: $*"
  echo "rr: log: $LOG"
  echo "rr: the pane $PANE is open; talk with the agent there"
  log "stop: $*"
  rm -f "$MARK"
  exit 1
}

mkdir -p "$SCRATCH" || die "cannot make $SCRATCH"
ARGS='["--model","'"$MODEL"'","--permission-mode","bypassPermissions","--settings","{\"env\":{\"CLAUDE_CODE_DISABLE_1M_CONTEXT\":\"0\"}}","--add-dir","'"$RR_DIR"'","--add-dir","'"$ART"'"]'
out=$("$GASHKI" spawn "$PANE" --agent=claude --here --trust-folder --cwd="$REPO" --agent-args="$ARGS" --json)
rc=$?
[[ $rc -eq 0 ]] || die "spawn failed (exit $rc, $(code <<<"$out")): $(jq -r '.errors[0].message // empty' <<<"$out")"
[[ "$(jq -r '.data.existing' <<<"$out")" == true ]] && die "$PANE exists already; kill it or finish it by hand"
ID=$(jq -r '.data.id' <<<"$out")
EVENTS=${GASHKI_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/gashki}/events.jsonl
log "start: model $MODEL, repo $REPO, commit $(git -C "$REPO" rev-parse --short HEAD 2>/dev/null || echo unknown), pane $PANE"

for p in $PASSES; do
  touch "$MARK"
  sleep 1
  start=$(date +%T)
  out=$(sed -e "s|{REPO}|$REPO|g" -e "s|{ART}|$ART|g" -e "s|{SCRATCH}|$SCRATCH|g" -e "s|{RR}|$RR_DIR|g" "$PROMPTS/$p.txt" | "$GASHKI" send "$PANE" --from-stdin --idempotency-key="rr-$NAME:$ID:$p" --json) \
    || handover "pass $p: send failed"
  # Wait from the turn's own start event: with --since, only a Stop ends
  # the wait. With no --since, a still screen can read as idle at the
  # turn start (datasette pass 05).
  cur=$(jq -r '.data.turn_cursor // empty' <<<"$out")
  [[ -n "$cur" ]] || handover "pass $p: send gave no turn cursor"
  echo "rr: pass $p sent at $start"
  approvals=0
  while :; do
    out=$("$GASHKI" wait "$PANE" --until=idle --since="$cur" --wait-timeout="${RR_WAIT:-2h}" --json)
    rc=$?
    [[ $rc -eq 0 ]] && break
    c=$(code <<<"$out")
    if [[ "$c" == APPROVAL_REQUIRED ]]; then
      approvals=$((approvals + 1))
      cur=$(jq -r '.errors[0].evidence.cursor // empty' <<<"$out")
      [[ -n "$cur" ]] || handover "pass $p: approval gave no cursor"
      printf '\arr: pass %s: approve in the analyst pane\n' "$p"
      "$GASHKI" wait "$PANE" --until=change --wait-timeout="${RR_WAIT:-2h}" --json >/dev/null
      continue
    fi
    handover "pass $p: wait ended with ${c:-exit $rc}"
  done
  # The agent sometimes writes into its cwd, the repo. Move new untracked
  # .md files from there to $ART.
  for f in $(find "$REPO" -maxdepth 1 -name '*.md' -newer "$MARK"); do
    git -C "$REPO" ls-files --error-unmatch "$f" >/dev/null 2>&1 && continue
    mv "$f" "$ART/" && log "pass $p: moved $(basename "$f") from the repo to $ART"
  done
  outs=$(find "$ART" -maxdepth 1 -name '*.md' -newer "$MARK" | sort)
  [[ -n "$outs" ]] || handover "pass $p: the turn ended with no new .md file in $ART"
  lint=pass
  python3 "$LINT" $outs >/dev/null 2>&1 || lint=fail
  compact=$(jq -c --arg id "$ID" 'select(.pane == $id and .vendor_event == "PreCompact")' "$EVENTS" 2>/dev/null | wc -l | tr -d ' ')
  log "pass $p: $start-$(date +%T) outputs [$(echo $outs | xargs -n1 basename | tr '\n' ' ' | sed 's/ $//')] lint $lint approvals $approvals compactions-so-far $compact"
  echo "rr: pass $p done, lint $lint"
done
rm -f "$MARK"
rm -rf "$SCRATCH" && log "deleted $SCRATCH"
log "done"
echo "rr: all passes done; log: $LOG"
echo "rr: your turn: talk with the agent in $PANE"
