# Demo video v2: guide script (spoken style)

Voice: Voicebox profile "Rahul" (chatterbox, fixed seed). Each line is one utterance, generated
separately and joined with natural pauses: a line ending in "," gets a short breath (~0.3 s), a
sentence end gets ~0.55 s, and a blank line gets a longer beat (~1 s), with slight random
variation. `> visual:` lines are not spoken.

## s01_title
> visual: Remotion animated title card
Hi, I'm Rahul Nandanwar,
student I D two zero two six, N S, nine three zero nine five.
This is my demo for Assignment One of A I Augmented S D L C,
on spec-driven development and harness engineering.

I built two small apps, using GitHub Spec Kit and a coding agent.
SplitKaro, which splits group expenses down to the exact paisa,
and TxnSense, an A I that reads bank and U P I text messages.

## s02_workflow
> visual: Remotion animated pipeline
Both parts follow the same workflow.
First, a constitution, with quality gates you can actually measure.
Then a spec, where every acceptance criterion is precise enough to become a pass or fail test.
I answered the clarifying questions myself,
and the plan, the tasks, and the consistency check all came before a single line of code.

Only then did the coding agent implement it.
And here's the important part.
A separate harness, that doesn't trust the generated code, decides if it's acceptable.
When something fails, the evidence goes back to the agent,
the exact same checks run again,
and the final call is mine.

## s03_1a_spec
> visual: terminal: constitution gates table, AC-008 and the clarification in spec.md
So, Part 1A. SplitKaro.
The constitution makes money exact.
Everything's stored in paise, never as a floating point number.
It also sets six gates,
an integrity lock on the spec and tests, lint, security, the tests themselves,
at least ninety percent coverage, and full traceability.

Now look at A C zero zero eight.
It decides who gets a leftover paisa when a bill doesn't split evenly.
That was my call during clarification.
Alphabetical order. Not the person who paid.

## s04_1a_demo
> visual: terminal: group create, expenses, balances, settle, overpayment rejected
Here it is, running for real.
I create a group, add a dinner, and then a hundred rupees, which can't be split evenly by three.
That extra paisa goes to Asha, first alphabetically,
exactly like the spec says.

The balances always add up to zero.
Settle gives a short list of who pays whom.
And if someone tries to pay more than they owe,
it's rejected, with exit code four.

## s05_1a_harness
> visual: terminal: run_harness.py all gates PASS; run-001 feedback; repair commit
One command runs the whole harness.
Six gates, and a hundred and seven tests written from the spec,
including property tests over hundreds of random inputs.
Everything passes.

But honestly, the first run didn't.
macOS had hidden the virtual environment's path files,
so the package couldn't even be imported.
And Ruff flagged the import order in three test files.

That feedback went straight back to the coding agent.
It fixed the root cause, without touching a single assertion,
re-locked the tests with a recorded reason,
and the same six gates passed.

## s06_1b_spec
> visual: terminal: output schema, guardrails GR-01..05, EV-03 thresholds
Part 1B is TxnSense, and this one's trickier,
because a language model never says things the same way twice.
So the spec doesn't compare text at all.

It fixes a JSON schema, eight invariants, and five guardrails.
Never repeat an O T P.
Never echo a phishing link or phone number.
Never print a full account number.
Treat instructions hidden in the message as data,
and never, ever, treat a scam as a real transaction.

And the pass mark was set before the first run.
A hundred percent valid output, zero violations, every safety case passing,
and an average score of at least point eight five.

## s07_1b_demo
> visual: terminal: live parse of a UPI debit, a KYC phishing SMS, a prompt-injection SMS
These are live calls to Gemini.
A normal U P I payment comes back as a clean, structured transaction.
Amount, merchant, category, date.

This one's a K Y C scam.
It's flagged as high-risk phishing,
and notice, the link and the phone number are gone.

And this last message tries to hijack the model.
It tells it to flip the debit to a credit, and print a fake O T P.
It doesn't work.
The real debit comes out, and the injected values never show up.

## s08_1b_harness
> visual: terminal: show_eval run-001 vs final run; S02 feedback; prompt fix
The evaluation harness runs twenty-five cases through three layers.
Schema checks, invariant and guardrail checks,
and then semantic scoring, with field accuracy and an independent A I judge.

The first run failed.
A message with an O T P, an amount, and a merchant came back as just an O T P,
but my clarified spec says that's a transaction.
So the safety score dropped below a hundred percent, and the run failed.

The agent added a clear precedence rule to the prompt,
and the identical harness passed.
The harness had its own weak spots too, and I logged those.
The first judge model ran out of free quota,
so I switched judges, documented why, and added retries.

## s09_acceptance
> visual: terminal: acceptance results run 1 vs run 2; parser fix commit
Last, I tested both apps once, on brand-new data that no test had ever seen.
SplitKaro passed all sixteen steps, against numbers I worked out by hand.
TxnSense passed ten out of eleven.

And that one miss was actually useful.
For a card alert with no amount,
the model gave the right answer, in the wrong shape,
and the app threw it away.
So the parser now cleans that up before validating.
A new unit test reproduces it,
and the re-run passed eleven out of eleven, with zero leaks.

## s10_outro
> visual: Remotion results summary card
So, both harnesses pass,
and every failure, every repair, and every limitation is written down in the harness logs.

But a green tick isn't the end.
Accepting or rejecting this, and owning the risks that are left,
that's my job as the engineer.
Thanks for watching.
