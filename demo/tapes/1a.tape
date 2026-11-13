# Part 1A demo - SplitKaro (real commands, recorded with charmbracelet/vhs)
Output demo/build/1a.mp4
Set Shell "bash"
Set FontSize 20
Set Width 1600
Set Height 900
Set Padding 30
Set Theme "Catppuccin Mocha"
Set TypingSpeed 25ms

Hide
Type "cd Part-1A && source .venv/bin/activate && export PYTHONPATH=src SPLITKARO_DATA=/tmp/splitkaro-demo.json PS1='$ ' && rm -f /tmp/splitkaro-demo.json && clear" Enter
Sleep 1s
Show

Type "# Part 1A - SplitKaro: spec-driven expense splitter. Acceptance criteria from the spec:" Enter
Type "grep -n 'AC-008\|AC-025' -A3 specs/001-group-expense-splitter/spec.md | head -14" Enter
Sleep 5s
Type "clear" Enter
Type "splitkaro group create goa --members ravi,asha,meera" Enter
Sleep 1.5s
Type "splitkaro expense add goa --paid-by ravi --amount 900 --desc Dinner" Enter
Sleep 1.2s
Type "splitkaro expense add goa --paid-by asha --amount 100.00 --desc Snacks" Enter
Sleep 1.2s
Type "splitkaro expense list goa" Enter
Sleep 2s
Type "splitkaro balances goa" Enter
Sleep 2.5s
Type "splitkaro settle goa" Enter
Sleep 2.5s
Type "splitkaro pay goa --from meera --to ravi --amount 999" Enter
Sleep 2s
Type "echo exit code: $?" Enter
Sleep 2s
Type "clear" Enter
Type "# The harness: 6 independent gates, one command" Enter
Type "python .harness/run_harness.py --label 'demo run (video)'" Enter
Sleep 25s
Type "clear" Enter
Type "# Genuine failure from the first run, fed back to the coding agent:" Enter
Type "head -24 evidence/harness-results/run-001-feedback.md" Enter
Sleep 7s
Type "clear" Enter
Type "git log --oneline -- . | head -14" Enter
Sleep 6s
