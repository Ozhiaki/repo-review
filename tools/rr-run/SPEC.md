> Historical: draft 2 of the design, written in the gashki project before the first live run. The script has changed since (folder trust, bypass mode, 1M context, scratch cleanup, turn-cursor waits). See README.md for current behavior.

# gashki runs repo-review: short spec (draft 2)

## 1. Goal

One command runs the repo-review passes on one target repo, one pass at a time, in one Claude session. gashki sends each pass prompt, waits for the turn to end, and checks the output. After the last pass, the script stops and the human talks with the same agent in the same pane.

This is the first productive gashki experiment. It uses one agent, no critic and no Esc. It tests `spawn --here`, `send` and `wait` over long turns.

## 2. First run

- Target repo: `/Users/dave/p/farm/tmuxwatch/tmuxwatch` (github.com/steipete/tmuxwatch, commit d87d2a5 of 2026-09-14, 79 tracked files, 1 MB, clean).
- Artifact folder: `/Users/dave/p/farm/tmuxwatch` (empty except for the repo).
- Agent: Claude. The human does these reviews with Claude today.
- Passes: 01, 02, 02.5, 03, 04, 05.
- Folder trust: `/Users/dave/p` is trusted in Claude, and the L1 test found that a trusted parent covers child folders. So no trust screen is expected, and the script does not pass `--trust-folder`.

## 3. The command

From a pane inside tmux:

```sh
~/p/repo-review/rr-run.sh /Users/dave/p/farm/tmuxwatch/tmuxwatch
```

The script is `~/p/repo-review/rr-run.sh`, outside the repo-review git repo. It is about 60 lines of bash.

## 4. Prompts

The human's prompts, verbatim. The only change: `[name of target]` becomes the absolute repo path. The script fills in `{REPO}`. The prompts live in `~/p/repo-review/rr-prompts/`, one file per pass, so the script holds no prompt text.

1. `01.txt`: I want you to read the instructions here: /Users/dave/p/repo-review/repo-review/01-first-read.md
   Please apply the instructions in this file to the {REPO} repo. Place your analysis in the folder above the repo.
2. `02.txt`: Please read the instructions at /Users/dave/p/repo-review/repo-review/02-discounted-artifact.md and apply them to this repo. As last time, place your analysis above the repo.
3. `02.5.txt`: Your next set of instructions are here: /Users/dave/p/repo-review/repo-review/02.5-synthesis.md. Please write your output to the folder above the repo.
4. `03.txt`: For the next pass your instructions are here: /Users/dave/p/repo-review/repo-review/03-trace.md
5. `04.txt`: Read your next instructions here: /Users/dave/p/repo-review/repo-review/04-twin.md. For this pass you need a tool to compare to. I don't have quite a twin. But you can search for a twin at Github or elsewhere.
6. `05.txt`: One pass left: /Users/dave/p/repo-review/repo-review/05-lift.md.

The prompts name the repo-review folder, so the agent can open later passes early. The human accepts this; it is the same in a normal chat.

## 5. Script steps

1. Check: inside tmux; the repo exists; its parent is not `~/p/farm` itself.
2. `gashki spawn rr-<repo>/analyst --agent=claude --here --cwd=<artifact folder> --agent-args=<A>`. The agent starts in the artifact folder, so the repo and the outputs are both inside its working folder.
3. For each pass:
   1. Record the `.md` files in the artifact folder.
   2. `gashki send rr-<repo>/analyst --from-stdin --idempotency-key=rr-<repo>:<pass>` with the prompt.
   3. `gashki wait rr-<repo>/analyst --until=idle --wait-timeout=2h`, in a loop:
      - Exit 0: the turn ended. Go to step 4.
      - `APPROVAL_REQUIRED`: print "approve in the analyst pane", ring the bell, `wait --until=change`, then wait again.
      - `WAIT_TIMEOUT`: stop and hand over.
      - `TURN_FAILED`, or any other error: stop and hand over.
   4. Find the new or changed `.md` files. None: stop and hand over.
   5. Run `lint_pass_outputs.py` on them. A failure is recorded, not fatal: the output is still useful to the human.
   6. Append one line to `rr-run.log` in the artifact folder: pass, start time, end time, output files, lint result, approvals, the number of `PreCompact` hook events for the pane so far (from gashki's `events.jsonl`).
4. Print "your turn: rr-<repo>/analyst" and exit. The pane stays open. gashki does not kill it.

"Stop and hand over" means: print the reason and the log path, then exit. The pane stays open, so the human can see what happened and continue by hand.

## 6. Agent start options (A)

`--agent-args='["--add-dir","/Users/dave/p/repo-review/repo-review","--allowedTools","WebSearch","WebFetch","Bash(git log:*)","Bash(git show:*)","Bash(find:*)","Bash(rg:*)","Bash(ls:*)","Bash(wc:*)"]'`

- `acceptEdits`: gashki already starts Claude with `--permission-mode acceptEdits` (spawn.go:436), so the agent writes its outputs with no prompt.
- `--add-dir`: the agent reads the pass files with no prompt.
- `--allowedTools`: read-only commands and pass 04's web search.

Unverified: whether this set removes all prompts. Any other command gives an approval prompt, which the loop hands to the human. The log counts the approvals, so the next run can widen the list. No mode that skips all permissions: the agent reads third-party content.

## 7. Risks

- **Context size.** tmuxwatch is small (79 files), so the repo itself is not the risk. Six deep passes in one session can still fill the context. After a compaction, the detail for the human's discussion is summarized. The outputs on disk stay complete. The log records `compacting`, so the effect is visible.
- **Long turns.** One pass can take much more than gashki's 10 min wait default. The script passes 2 h.
- **Turn-state errors.** A false idle (rule 5) during a long silent tool call would make the script send the next prompt early. Check: step 4 finds no new output, so the script stops and does not send.
- **Output naming.** The pass prompts do not fix file names. The script finds outputs by change, not by name.

## 8. Checks

- R1. Dry run on the stub agent: six passes, each stub turn writes one `.md`. The script ends with "your turn", the pane is alive, and the log has six lines.
- R2. Stub turn that writes nothing: the script stops after that pass and does not send the next prompt.
- R3. Stub approval prompt: the script prints, waits, and continues after the approval.
- R4. Live run on tmuxwatch, only with the human's go. Pass: six outputs in `/Users/dave/p/farm/tmuxwatch`, the pane is open for discussion, and the human window is unchanged (same check as P5 in the human-rung spec).

## 9. Not in scope

- Pass 06 (Delta Review).
- Codex. A second run can compare it.
- Fixing the window-resize defect. It fires only on the Codex hooks screen, so this Claude run does not reach it.
- Steering between passes. The human can type in the pane at any time; the script only reacts to the turn state.
