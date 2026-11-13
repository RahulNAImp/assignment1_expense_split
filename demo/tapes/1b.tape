# Part 1B demo - TxnSense (real Gemini calls, recorded with charmbracelet/vhs)
Output demo/build/1b.mp4
Set Shell "bash"
Set FontSize 18
Set Width 1600
Set Height 900
Set Padding 30
Set Theme "Catppuccin Mocha"
Set TypingSpeed 20ms

Hide
Type "cd Part-1B && source .venv/bin/activate && export PYTHONPATH=src PS1='$ ' PYTHONWARNINGS=ignore && clear" Enter
Sleep 1s
Show

Type "# Part 1B - TxnSense. Output contract + guardrails from the spec:" Enter
Type "grep -n 'GR-01\|GR-02\|EV-03' specs/001-sms-transaction-extractor/spec.md | cut -c1-150" Enter
Sleep 6s
Type "clear" Enter
Type "python -m txnsense.cli parse 'Rs.450.00 debited from A/c XX1234 on 12-11-26 to VPA swiggy@icici UPI Ref 432112345678' --received-at 2026-11-13T09:00:00+05:30" Enter
Sleep 9s
Type "clear" Enter
Type "python -m txnsense.cli parse 'Dear SBI user, your KYC has expired and your account will be BLOCKED today. Update now: bit.ly/sbi-kyc-upd8 or call 9876543210' --received-at 2026-11-13T09:00:00+05:30" Enter
Sleep 9s
Type "clear" Enter
Type "# 25 eval cases: normal, boundary, missing info, malformed, adversarial" Enter
Type `python -c "import json;[print(c['id'],c['tags'],c['input']['text'][:70]) for c in json.load(open('evals/dataset.json'))['cases']]"` Enter
Sleep 7s
Type "clear" Enter
Type "# First evaluation (initial generation) vs re-evaluation after repair:" Enter
Type "python ../demo/show_eval.py run-001 run-003" Enter
Sleep 12s
Type "clear" Enter
Type "head -20 evidence/runs/run-001/feedback.md" Enter
Sleep 7s
Type "git log -1 --stat --format='%h %s' -- prompts/" Enter
Sleep 6s
