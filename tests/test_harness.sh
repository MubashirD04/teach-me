#!/usr/bin/env bash
# Smoke tests for the guard hook and CLI. Run: bash tests/test_harness.sh
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export CLAUDE_PROJECT_DIR="$(mktemp -d)" TEACH_HOME="$(mktemp -d)"
T() { python3 "$ROOT/bin/teach.py" "$@"; }; G() { python3 "$ROOT/hooks/guard.py"; }
pass=0; fail=0
ok()  { pass=$((pass+1)); echo "ok   - $1"; }
bad() { fail=$((fail+1)); echo "FAIL - $1"; }
denied() { echo "$1" | G | grep -q '"deny"'; }

T mode learn >/dev/null
denied '{"tool_name":"Write","tool_input":{"file_path":"'$CLAUDE_PROJECT_DIR'/app.py"}}' && ok "learn blocks Write" || bad "learn blocks Write"
denied '{"tool_name":"Edit","tool_input":{"file_path":"app.py"}}' && ok "learn blocks relative Edit" || bad "learn blocks relative Edit"
denied '{"tool_name":"Write","tool_input":{"file_path":"'$CLAUDE_PROJECT_DIR'/.teach/scratch/demo.py"}}' && bad "scratch writable" || ok "scratch writable"
denied '{"tool_name":"Write","tool_input":{"file_path":"'$CLAUDE_PROJECT_DIR'/.teach/../app.py"}}' && ok "path traversal blocked" || bad "path traversal blocked"
denied '{"tool_name":"Bash","tool_input":{"command":"echo hi > app.py"}}' && ok "bash redirect blocked" || bad "bash redirect blocked"
denied '{"tool_name":"Bash","tool_input":{"command":"sed -i s/a/b/ app.py"}}' && ok "sed -i blocked" || bad "sed -i blocked"
denied '{"tool_name":"Bash","tool_input":{"command":"pytest -q 2>&1 | tail -5"}}' && bad "pytest allowed" || ok "pytest allowed"
denied '{"tool_name":"Bash","tool_input":{"command":"python3 app.py > /dev/null"}}' && bad "/dev/null allowed" || ok "/dev/null allowed"
denied '{"tool_name":"Bash","tool_input":{"command":"python3 /x/bin/teach.py hint"}}' && bad "teach cli allowed" || ok "teach cli allowed"
denied '{"tool_name":"Read","tool_input":{"file_path":"app.py"}}' && bad "Read allowed" || ok "Read allowed"
T mode pair >/dev/null
denied '{"tool_name":"Write","tool_input":{"file_path":"app.py"}}' && bad "pair allows Write" || ok "pair allows Write"
T mode learn >/dev/null

T task "fizzbuzz" >/dev/null
T hint | grep -q "LEVEL 1" && ok "hint -> 1" || bad "hint -> 1"
T hint >/dev/null; T hint | grep -q "LEVEL 3" && ok "hint -> 3" || bad "hint -> 3"
T hint | grep -q HOLD && ok "level 4 held without attempts" || bad "level 4 held"
T attempt >/dev/null; T attempt >/dev/null
T hint | grep -q "LEVEL 4" && ok "level 4 after 2 attempts" || bad "level 4 after attempts"
T hint | grep -q HOLD && ok "level 5 held" || bad "level 5 held"
T hint --force | grep -q "LEVEL 5" && ok "force allows 5" || bad "force allows 5"
T concept "loops" fail >/dev/null; T concept "loops" pass >/dev/null
T profile | grep -q '"loops"' && ok "concept recorded" || bad "concept recorded"
TEACH_HOME="$(mktemp -d)" python3 "$ROOT/hooks/session_start.py" | grep -q "use the .roadmap. skill directly" && ok "session start routes goal to roadmap" || bad "session start routes goal to roadmap"
python3 "$ROOT/hooks/session_start.py" | grep -q "TEACHING HARNESS" && ok "session_start context" || bad "session_start context"
T mode learn >/dev/null
P="$(T diagram "Fork and Exec")"; [ "$P" = ".teach/diagrams/fork-and-exec.html" ] && ok "diagram path" || bad "diagram path ($P)"
mkdir -p "$CLAUDE_PROJECT_DIR/.teach/diagrams"; : > "$CLAUDE_PROJECT_DIR/$P"
P2="$(T diagram "Fork and Exec")"; [ "$P2" = ".teach/diagrams/fork-and-exec.html" ] && bad "diagram uniqueness" || ok "diagram uniqueness"
denied '{"tool_name":"Write","tool_input":{"file_path":"'$CLAUDE_PROJECT_DIR'/.teach/diagrams/fork-and-exec.html"}}' && bad "diagram path writable in learn" || ok "diagram path writable in learn"
T diagram '../../etc/x' | grep -q '^\.teach/diagrams/etc-x' && ok "diagram slug sanitised" || bad "diagram slug sanitised"
python3 "$ROOT/hooks/prompt_reminder.py" | grep -q "diagram" && ok "reminder mentions diagram" || bad "reminder mentions diagram"
[ -f "$ROOT/skills/diagram/template.html" ] && ok "template present" || bad "template present"
python3 "$ROOT/hooks/prompt_reminder.py" | grep -q "learn mode" && ok "prompt reminder (learn)" || bad "prompt reminder (learn)"
T mode off >/dev/null
[ -z "$(python3 "$ROOT/hooks/prompt_reminder.py")" ] && ok "no reminder when off" || bad "no reminder when off"
python3 -c "import json;json.load(open('$ROOT/hooks/hooks.json'));json.load(open('$ROOT/.claude-plugin/marketplace.json'))" && ok "json valid" || bad "json valid"
# ---- quiz
FRESH="$(mktemp -d)"; TEACH_HOME="$FRESH" python3 "$ROOT/bin/teach.py" quiz pick | grep -q "NO HISTORY" && ok "quiz pick: no history" || bad "quiz pick: no history"
T quiz pick | head -1 | grep -q "fizzbuzz" && ok "quiz pick ranks weakest first" || bad "quiz pick ranks weakest first"
T quiz start loops | grep -q "difficulty 2" && ok "quiz start difficulty 2" || bad "quiz start difficulty 2"
T quiz answer pass >/dev/null; T quiz answer pass | grep -q "difficulty 3" && ok "2 passes raise difficulty" || bad "2 passes raise difficulty"
T quiz answer fail | grep -q "difficulty 2" && ok "fail lowers difficulty" || bad "fail lowers difficulty"
T quiz answer partial "pointer arithmetic" | grep -q "pointer arithmetic" && ok "partial recorded w/ concept" || bad "partial recorded"
python3 "$ROOT/hooks/prompt_reminder.py" | grep -q "QUIZ ACTIVE" && ok "reminder: quiz active (even mode off)" || bad "reminder: quiz active"
T quiz end | grep -q "revisit" && ok "quiz end summary" || bad "quiz end summary"
T quiz status | grep -q "no active quiz" && ok "quiz cleared" || bad "quiz cleared"
T quiz answer pass | grep -q "no active quiz" && ok "answer without quiz rejected" || bad "answer without quiz rejected"
T profile | python3 -c "import sys,json;c=json.load(sys.stdin)['concepts']['loops'];sys.exit(0 if c['pass']>=3 else 1)" && ok "quiz results hit profile" || bad "quiz results hit profile"
T mode learn >/dev/null; python3 "$ROOT/hooks/prompt_reminder.py" | grep -q "quiz me" && ok "reminder: quiz trigger" || bad "reminder: quiz trigger"
T mode off >/dev/null
# ---- roadmap + guard CLI robustness
T roadmap status | grep -q "no roadmap yet" && ok "roadmap: none yet" || bad "roadmap: none yet"
T roadmap init "build a shell in C" | grep -q created && ok "roadmap init" || bad "roadmap init"
T profile | grep -q '"onboarded": true' && ok "roadmap init marks onboarded" || bad "roadmap init marks onboarded"
T profile | grep -q "build a shell" && ok "goal copied to profile" || bad "goal copied to profile"
T roadmap add --title "Prompt and echo" --outcome "your program shows a prompt and repeats a line back" --done-when "run it, see a dollar prompt, type hello, see you typed: hello" --concepts "stdin" --first-step "predict why a prompt without newline may not show" | grep -q "ERROR" && ok "rejects concept without description" || bad "rejects concept without description"
T roadmap add --title "Prompt and echo" --outcome "your program shows a prompt and repeats a line back" --done-when "run it, see a dollar prompt, type hello, see you typed: hello" --concepts "stdin | where keyboard input arrives; getline | reads a whole line of text" --first-step "think about how a prompt appears on screen and do some reading" | grep -q "bring something back" && ok "rejects first step with nothing to bring back" || bad "rejects first step with nothing to bring back"
T roadmap add --title "Prompt and echo" --outcome "your program shows a prompt and repeats a line back" --done-when "run it, see a dollar prompt, type hello, see you typed: hello" --concepts "stdin | where keyboard input arrives; getline | reads a whole line of text" --first-step "write getline(&l,&n,stdin); then run it" | grep -q "ERROR" && ok "rejects code in first step" || bad "rejects code in first step"
T roadmap add --title "Prompt and echo" --outcome "your program shows a prompt and repeats a line back" --done-when "run it, see a dollar prompt, type hello, see you typed: hello" --concepts "stdin | where keyboard input arrives; getline | reads a whole line of text" --look-up "man 3 getline" --first-step "predict whether a prompt without a newline shows at once, then test it and tell me what you saw" | grep -q "added milestone 1" && ok "add milestone 1" || bad "add milestone 1"
T roadmap add --title "Run one command" --outcome "type a program name and it runs" --done-when "type ls and see the listing, then the prompt returns" --concepts "process | a running program; exec | replaces the running program with another" --first-step "work out what would happen to your shell program if it ran ls inside itself. What do you expect to see?" | grep -q "added milestone 2" && ok "add milestone 2" || bad "add milestone 2"
[ -f "$CLAUDE_PROJECT_DIR/.teach/ROADMAP.md" ] && grep -q "Prompt and echo" "$CLAUDE_PROJECT_DIR/.teach/ROADMAP.md" && ok "ROADMAP.md rendered" || bad "ROADMAP.md rendered"
T roadmap start 1 | grep -q "milestone 1 active" && ok "start 1" || bad "start 1"
T status | grep -q "M1: Prompt and echo" && ok "start sets task" || bad "start sets task"
T roadmap done 1 | grep -q "NOT YET" && ok "done gated until checked" || bad "done gated until checked"
T quiz pick | grep -q "CURRENT MILESTONE 1" && ok "quiz pick prioritises milestone" || bad "quiz pick prioritises milestone"
T concept stdin pass >/dev/null; T roadmap done 1 | grep -q "milestone 1 done" && ok "done after 1 of 2 concepts passed" || bad "done after check"
T roadmap start 2 >/dev/null; T roadmap done 2 | grep -q "NOT YET" && ok "milestone 2 gated" || bad "milestone 2 gated"
T roadmap done 2 --force | grep -q "complete" && ok "force override" || bad "force override"
T roadmap park "add colours to the prompt" | grep -q parked && T roadmap parked | grep -q colours && ok "park idea" || bad "park idea"
T roadmap edit 2 --title "Run one external command" | grep -q edited && ok "edit milestone" || bad "edit milestone"
T roadmap remove 2 | grep -q removed && ok "remove milestone" || bad "remove milestone"
T roadmap start 1 >/dev/null; T mode learn >/dev/null
python3 "$ROOT/hooks/prompt_reminder.py" | grep -q "ROADMAP" && python3 "$ROOT/hooks/prompt_reminder.py" | grep -q "park" && ok "reminder carries roadmap + drift rule" || bad "reminder roadmap"
python3 "$ROOT/hooks/session_start.py" | grep -q "milestones done" && ok "session start shows progress" || bad "session start progress"
CLI='python3 "'$ROOT'/bin/teach.py"'
denied '{"tool_name":"Bash","tool_input":{"command":"'"python3 \\\"$ROOT/bin/teach.py\\\" roadmap park \\\"make install -> touch files\\\""'"}}' && bad "teach CLI w/ free text allowed" || ok "teach CLI w/ free text allowed"
denied '{"tool_name":"Bash","tool_input":{"command":"python3 teach.py status ; rm -rf x"}}' && ok "chained rm blocked" || bad "chained rm blocked"
denied '{"tool_name":"Bash","tool_input":{"command":"python3 teach.py status > app.c"}}' && ok "teach redirect blocked" || bad "teach redirect blocked"
denied '{"tool_name":"Bash","tool_input":{"command":"python3 other.py hello"}}' && bad "plain python not blocked by teach rule" || ok "plain python not blocked by teach rule"
T mode off >/dev/null
grep -q "^> \*\*First step" "$CLAUDE_PROJECT_DIR/.teach/ROADMAP.md" && ok "ROADMAP.md first step is its own callout" || bad "ROADMAP.md first step callout"
echo "---- $pass passed, $fail failed"; [ $fail -eq 0 ]
