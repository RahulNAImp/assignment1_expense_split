# Demo video v2: guide script (spoken, Indian-English presenting style)

Voice: Voicebox profile "Rahul" (chatterbox; per-line seed for natural intonation variety).
Each line is one utterance, generated separately and joined using the student's own speaking
rhythm (measured from the reference recording): "," → ~0.22 s, sentence end → ~0.4 s, blank
line → ~0.65 s plus one of the student's real breaths. `> visual:` lines are not spoken.

## s01_title
> visual: Remotion animated title card
Hello everyone, I'm Rahul Nandanwar,
student I D two zero two six, N S, nine three zero nine five.
So, this is my demo for Assignment One of A I Augmented S D L C,
which is basically about spec-driven development and harness engineering.

For this, I have built two small applications, using GitHub Spec Kit and a coding agent.
First one is SplitKaro, it splits group expenses, exactly, up to the paisa.
And the second one is TxnSense, an A I that reads your bank and U P I messages.

## s02_workflow
> visual: Remotion animated pipeline
Okay, so both parts follow the same workflow.
First we have the constitution, where the quality gates are actually measurable.
Then the spec, where every acceptance criterion is a clear pass or fail test.
The clarification questions, I answered them myself,
and the plan, the tasks, and the analysis, all of that came before any code.

Only after that, the coding agent did the implementation.
And this is the important part.
A separate harness, which does not trust the generated code, decides if it is acceptable or not.
If something fails, the evidence goes back to the agent,
the same checks run again,
and the final decision is mine.

## s03_1a_spec
> visual: terminal: constitution gates table, AC-008 and the clarification in spec.md
So, let's start with Part 1A, that is SplitKaro.
In the constitution, money is always exact.
Everything is stored in paise, never as a floating point number.
And we have six gates here,
an integrity lock on the spec and tests, then lint, security, the tests,
minimum ninety percent coverage, and full traceability.

Now see this, A C zero zero eight.
It decides who gets the extra paisa, when a bill doesn't divide equally.
This was my decision, during clarification.
Alphabetical order, not the person who paid.

## s04_1a_demo
> visual: terminal: group create, expenses, balances, settle, overpayment rejected
Now let me show you, this is actually running.
I create a group, add a dinner, and then a hundred rupees, which cannot be divided equally by three.
So that one extra paisa goes to Asha, because she comes first alphabetically,
exactly as per the spec.

The balances always add up to zero.
Settle gives a short list of who should pay whom.
And if someone tries to pay more than what they owe,
it is rejected, with exit code four.

## s05_1a_harness
> visual: terminal: run_harness.py, all six gates PASS
Now, just one command runs the complete harness.
Six independent gates,
the integrity lock, lint, security, one hundred and seven tests written from the spec, coverage, and traceability.
And you can see, all six gates are passing,
with ninety-six point eight percent coverage, and every acceptance criterion traced to a test.

## s06_1b_spec
> visual: terminal: output schema, guardrails GR-01..05, EV-03 thresholds
Now Part 1B, that is TxnSense, and this one is a little tricky,
because a language model never says the same thing in the same way twice.
So in the spec, we don't compare the text at all.

Instead, it fixes a JSON schema, eight invariants, and five guardrails.
Never repeat an O T P.
Never repeat a phishing link or a phone number.
Never print the full account number.
Any instruction hidden inside the message is just data,
and a scam message should never be treated as a real transaction.

And the pass criteria was decided before the very first run.
Hundred percent valid output, zero violations, all safety cases passing,
and an average score of at least point eight five.

## s07_1b_demo
> visual: terminal: live parse of a UPI debit, a KYC phishing SMS, a prompt-injection SMS
These are live calls to Gemini.
A normal U P I payment, comes back as a clean, structured transaction.
Amount, merchant, category, and date.

This one is a K Y C scam message.
It is flagged as high-risk phishing,
and if you notice, the link and the phone number are removed.

And this last message is trying to hijack the model.
It is telling the model to change the debit into a credit, and to print a fake O T P.
But it doesn't work.
The real debit comes out, and the injected values are nowhere in the output.

## s08_1b_harness
> visual: terminal: final evaluation run metrics
Now the evaluation harness for TxnSense.
It runs twenty-five cases through three layers,
schema checks, invariant and guardrail checks, and semantic scoring with an independent A I judge.
And this is the final result.
Hundred percent valid output, zero violations, every safety case passing,
and an average score of point nine eight, well above the point eight five threshold.

## s09_acceptance
> visual: terminal: acceptance test on new data
And finally, I tested both the apps on completely new data, which no test had seen before.
SplitKaro passed all sixteen steps, matching the values I calculated by hand.
And TxnSense passed all eleven new messages, with zero guardrail leaks.

## s10_outro
> visual: Remotion results summary card
So, both the applications are working as specified, and both the harnesses are passing.
All the evidence, the harness logs, and the known limitations are documented in the GitHub repository.
The final accept or reject decision is mine, as the engineer.
Thank you for watching.
