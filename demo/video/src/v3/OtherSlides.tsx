import React from "react";
import { AbsoluteFill } from "remotion";
import { C, FONT, MONO } from "../theme";
import { Card, Reveal, Slide, Tick } from "./kit";

export const Intro: React.FC = () => (
  <AbsoluteFill style={{ background: `radial-gradient(circle at 20% 10%, ${C.surface}, ${C.base} 55%, ${C.crust})`, fontFamily: FONT, color: C.text, padding: "110px 130px" }}>
    <Reveal at={0}>
      <div style={{ fontFamily: MONO, fontSize: 32, color: C.mauve, letterSpacing: 3 }}>AI-AUGMENTED SDLC · SE ZG534 · ASSIGNMENT 1</div>
      <div style={{ fontSize: 100, fontWeight: 900, lineHeight: 1.05, marginTop: 22 }}>Spec-Driven Development<br /><span style={{ color: C.blue }}>&amp; Harness Engineering</span></div>
      <div style={{ fontSize: 44, color: C.subtext, marginTop: 30 }}>Rahul Rangnath Nandanwar · 2026NS93095 · BITS Pilani WILP</div>
    </Reveal>
    <Reveal at={1}><div style={{ fontSize: 40, marginTop: 60, color: C.subtext }}>Two small applications:</div></Reveal>
    <div style={{ display: "flex", gap: 48, marginTop: 24 }}>
      <Reveal at={1} delay={0.8} style={{ flex: 1 }}><Card color={C.green}><div style={{ fontSize: 66, fontWeight: 850 }}>SplitKaro</div><div style={{ fontSize: 36, color: C.subtext }}>splits shared expenses between friends</div></Card></Reveal>
      <Reveal at={2} style={{ flex: 1 }}><Card color={C.peach}><div style={{ fontSize: 66, fontWeight: 850 }}>TxnSense</div><div style={{ fontSize: 36, color: C.subtext }}>reads bank &amp; UPI SMS using AI</div></Card></Reveal>
    </div>
  </AbsoluteFill>
);

const CHECKS = [
  "Spec and tests were not changed",
  "Code style is clean (Ruff)",
  "No security issues (Bandit)",
  "All 107 tests pass",
  "At least 90 % of the code is tested",
  "Every requirement has a test",
];

export const HarnessSlide: React.FC = () => (
  <Slide kicker="PART 1A · HOW DO I KNOW IT'S CORRECT?" title="The harness checks 6 things automatically" color={C.green}>
    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 26 }}>
      {CHECKS.map((c, i) => (
        <Reveal key={c} at={1} delay={0.4 + i * 0.45}>
          <Card color={C.green}><div style={{ fontSize: 40 }}><Tick /> &nbsp;{c}</div></Card>
        </Reveal>
      ))}
    </div>
  </Slide>
);

export const TxnIdea: React.FC = () => (
  <Slide kicker="PART 1B · TXNSENSE" title="A bank SMS in → clean details out" color={C.peach}>
    <div style={{ display: "flex", alignItems: "center", gap: 40 }}>
      <Reveal at={0} style={{ width: 640 }}>
        <div style={{ background: C.surface, borderRadius: "28px 28px 28px 6px", padding: "28px 34px", fontSize: 36, lineHeight: 1.35 }}>
          Rs.450.00 debited from A/c XX1234 on 12-11-26 to VPA swiggy@icici UPI Ref 4321…
        </div>
      </Reveal>
      <Reveal at={0} delay={1.2}><div style={{ fontSize: 80, color: C.overlay }}>→</div></Reveal>
      <Reveal at={0} delay={2}>
        <div style={{ background: C.surface, borderRadius: 24, padding: "24px 34px", fontFamily: MONO, fontSize: 34, lineHeight: 1.5 }}>
          amount&nbsp;&nbsp;&nbsp;<b style={{ color: C.green }}>450.00</b><br />type&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b style={{ color: C.green }}>debit</b><br />merchant <b style={{ color: C.green }}>Swiggy</b><br />category <b style={{ color: C.green }}>food</b><br />date&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b style={{ color: C.green }}>2026-11-12</b>
        </div>
      </Reveal>
    </div>
    <div style={{ display: "flex", gap: 30, marginTop: 50 }}>
      <Reveal at={1} style={{ flex: 1 }}><Card color={C.red}><div style={{ fontSize: 34 }}>Scam message → <b>flagged</b>, link &amp; phone number <b>never repeated</b></div></Card></Reveal>
      <Reveal at={1} delay={1.5} style={{ flex: 1 }}><Card color={C.yellow}><div style={{ fontSize: 34 }}>Hidden trick instruction inside the SMS → <b>ignored</b></div></Card></Reveal>
    </div>
  </Slide>
);

const LAYERS = [
  ["1", "Is the format correct?", "JSON schema"],
  ["2", "Are the safety rules followed?", "no OTP / link leaks, no scam as payment"],
  ["3", "Are the details correct?", "amount, type, merchant… + AI judge"],
];

export const EvalSlide: React.FC = () => (
  <Slide kicker="PART 1B · TESTING THE AI" title="25 test messages, 3 checks each" color={C.peach}>
    <Reveal at={0}>
      <div style={{ display: "flex", gap: 22, fontSize: 34 }}>
        {["normal", "tricky", "scam", "missing info", "garbage"].map((t) => (
          <span key={t} style={{ background: C.surface, borderRadius: 14, padding: "10px 22px" }}>{t}</span>
        ))}
      </div>
    </Reveal>
    <div style={{ display: "flex", flexDirection: "column", gap: 24, marginTop: 44 }}>
      {LAYERS.map(([n, q, d], i) => (
        <Reveal key={n} at={0} delay={1.5 + i * 0.9}>
          <Card color={C.peach}><div style={{ fontSize: 42 }}><b style={{ color: C.peach }}>{n}.</b> {q} <span style={{ color: C.subtext, fontSize: 32 }}>· {d}</span></div></Card>
        </Reveal>
      ))}
    </div>
  </Slide>
);

export const Outro: React.FC = () => (
  <Slide kicker="RESULT" title="Both apps work as specified" color={C.mauve}>
    <div style={{ display: "flex", gap: 36 }}>
      {[
        ["SplitKaro", "16 / 16", "steps on new data", C.green],
        ["TxnSense", "11 / 11", "new messages, 0 leaks", C.peach],
        ["Harness", "6 / 6", "gates · 25 / 25 AI cases", C.blue],
      ].map(([a, b, c, col], i) => (
        <Reveal key={a} at={0} delay={i * 0.6} style={{ flex: 1 }}>
          <Card color={col}><div style={{ fontSize: 36, color: C.subtext }}>{a}</div><div style={{ fontSize: 84, fontWeight: 900, color: col }}>{b}</div><div style={{ fontSize: 32, color: C.subtext }}>{c}</div></Card>
        </Reveal>
      ))}
    </div>
    <Reveal at={1}>
      <div style={{ marginTop: 70, fontSize: 40 }}>Code, tests and harness logs:</div>
      <div style={{ fontFamily: MONO, fontSize: 40, color: C.blue, marginTop: 10 }}>github.com/RahulNAImp/assignment1_expense_split</div>
      <div style={{ fontSize: 60, fontWeight: 850, marginTop: 50 }}>Thank you!</div>
    </Reveal>
  </Slide>
);
