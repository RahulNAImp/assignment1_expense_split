import React from "react";
import { C, MONO } from "../theme";
import { Card, Pill, Reveal, Slide, Tick, useBeat } from "./kit";

const PEOPLE = [
  { n: "Josh", c: C.peach },
  { n: "Kimberly", c: C.mauve },
  { n: "Mike", c: C.green },
];

const Avatar: React.FC<{ n: string; c: string }> = ({ n, c }) => (
  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 14 }}>
    <div style={{ width: 150, height: 150, borderRadius: 75, background: c, color: C.base, fontSize: 70, fontWeight: 900, display: "flex", alignItems: "center", justifyContent: "center" }}>{n[0]}</div>
    <div style={{ fontSize: 40, fontWeight: 700 }}>{n}</div>
  </div>
);

export const SplitIdea: React.FC = () => (
  <Slide kicker="PART 1A · SPLITKARO" title="A simple example: three friends on a trip" color={C.green}>
    <Reveal at={0}>
      <div style={{ display: "flex", gap: 90, marginLeft: 20 }}>
        {PEOPLE.map((p) => <Avatar key={p.n} {...p} />)}
      </div>
    </Reveal>
    <div style={{ display: "flex", gap: 40, marginTop: 70 }}>
      <Reveal at={1}><Card color={C.green}><div style={{ fontSize: 34, color: C.subtext }}>Mike paid</div><div style={{ fontSize: 64, fontWeight: 850 }}>₹900 <span style={{ fontSize: 38, color: C.subtext }}>Dinner</span></div></Card></Reveal>
      <Reveal at={1} delay={1.6}><Card color={C.peach}><div style={{ fontSize: 34, color: C.subtext }}>Josh paid</div><div style={{ fontSize: 64, fontWeight: 850 }}>₹100 <span style={{ fontSize: 38, color: C.subtext }}>Snacks</span></div></Card></Reveal>
      <Reveal at={1} delay={3.2}><Card color={C.yellow}><div style={{ fontSize: 34, color: C.subtext }}>Total spent</div><div style={{ fontSize: 64, fontWeight: 850 }}>₹1000</div></Card></Reveal>
    </div>
  </Slide>
);

const cell: React.CSSProperties = { padding: "18px 28px", fontSize: 42, fontFamily: MONO, textAlign: "right" };
const head: React.CSSProperties = { ...cell, fontFamily: undefined, fontSize: 32, color: C.subtext, fontWeight: 700 };

export const SplitShares: React.FC = () => {
  const { idx } = useBeat();
  const show = (b: number) => ({ opacity: idx >= Math.min(b, 1) ? 1 : 0, transition: "none" });
  return (
    <Slide kicker="STEP 1 · SHARES" title="Each expense is split equally" color={C.green}>
      <table style={{ borderCollapse: "collapse", background: C.surface, borderRadius: 20, overflow: "hidden" }}>
        <thead>
          <tr style={{ background: C.mantle }}>
            <th style={{ ...head, textAlign: "left" }}>Friend</th>
            <th style={head}>Dinner ₹900 ÷ 3</th>
            <th style={{ ...head, ...show(1) }}>Snacks ₹100 ÷ 3</th>
            <th style={{ ...head, ...show(2) }}>Total share</th>
          </tr>
        </thead>
        <tbody>
          {[["Josh", "33.34", "333.34"], ["Kimberly", "33.33", "333.33"], ["Mike", "33.33", "333.33"]].map(([n, s, t]) => (
            <tr key={n} style={{ borderTop: `2px solid ${C.base}` }}>
              <td style={{ ...cell, textAlign: "left", fontFamily: undefined, fontWeight: 700 }}>{n}</td>
              <td style={cell}>300.00</td>
              <td style={{ ...cell, ...show(1), color: n === "Josh" ? C.yellow : C.text, fontWeight: n === "Josh" ? 900 : 400 }}>{s}</td>
              <td style={{ ...cell, ...show(2), fontWeight: 800 }}>{t}</td>
            </tr>
          ))}
          <tr style={{ borderTop: `3px solid ${C.overlay}`, ...show(2) }}>
            <td style={{ ...cell, textAlign: "left", fontFamily: undefined, fontWeight: 800 }}>Total</td>
            <td style={cell}>900.00</td>
            <td style={cell}>100.00</td>
            <td style={{ ...cell, color: C.green, fontWeight: 900 }}>1000.00 ✔</td>
          </tr>
        </tbody>
      </table>
      <Reveal at={1} delay={0.5}>
        <div style={{ marginTop: 34, fontSize: 36, color: C.subtext }}>
          ₹100 ÷ 3 leaves <b style={{ color: C.yellow }}>1 extra paisa</b> → it goes to the first name alphabetically: <b style={{ color: C.yellow }}>Josh</b> (rule from my spec)
        </div>
      </Reveal>
    </Slide>
  );
};

export const SplitBalance: React.FC = () => {
  const rows: [string, string, string, string, string][] = [
    ["Mike", "900.00", "333.33", "+566.67", C.green],
    ["Josh", "100.00", "333.34", "−233.34", C.red],
    ["Kimberly", "0.00", "333.33", "−333.33", C.red],
  ];
  return (
    <Slide kicker="STEP 2 · BALANCE" title="Balance = what you paid − your share" color={C.green}>
      <div style={{ display: "flex", gap: 60, alignItems: "flex-start" }}>
        <Reveal at={1}>
          <table style={{ borderCollapse: "collapse", background: C.surface, borderRadius: 20, overflow: "hidden" }}>
            <thead><tr style={{ background: C.mantle }}>
              <th style={{ ...head, textAlign: "left" }}>Friend</th><th style={head}>Paid</th><th style={head}>Share</th><th style={head}>Balance</th>
            </tr></thead>
            <tbody>
              {rows.map(([n, p, s, b, c], i) => (
                <tr key={n} style={{ borderTop: `2px solid ${C.base}` }}>
                  <td style={{ ...cell, textAlign: "left", fontFamily: undefined, fontWeight: 700 }}>{n}</td>
                  <td style={cell}>{p}</td>
                  <td style={cell}>{s}</td>
                  <td style={{ ...cell, color: c, fontWeight: 900 }}><Reveal at={1} delay={1.2 + i * 0.7}>{b}</Reveal></td>
                </tr>
              ))}
              <tr style={{ borderTop: `3px solid ${C.overlay}` }}>
                <td style={{ ...cell, textAlign: "left", fontFamily: undefined, fontWeight: 800 }}>Total</td>
                <td style={cell}>1000.00</td><td style={cell}>1000.00</td>
                <td style={{ ...cell, fontWeight: 900 }}><Reveal at={2} delay={0.6}><span style={{ color: C.green }}>0.00 ✔</span></Reveal></td>
              </tr>
            </tbody>
          </table>
        </Reveal>
        <Reveal at={1} delay={2}>
          <div style={{ display: "flex", flexDirection: "column", gap: 24, width: 560 }}>
            <Card color={C.red}><div style={{ fontSize: 38 }}><b style={{ color: C.red }}>−</b> minus = you <b>owe</b> money</div></Card>
            <Card color={C.green}><div style={{ fontSize: 38 }}><b style={{ color: C.green }}>+</b> plus = you <b>get money back</b></div></Card>
            <Card color={C.yellow}><div style={{ fontSize: 34 }}>Add with the sign: <span style={{ fontFamily: MONO }}>566.67 − 233.34 − 333.33 = 0</span> → no money lost</div></Card>
          </div>
        </Reveal>
      </div>
    </Slide>
  );
};

const Arrow: React.FC<{ from: string; amount: string; delay: number }> = ({ from, amount, delay }) => (
  <Reveal at={0} delay={delay}>
    <div style={{ display: "flex", alignItems: "center", gap: 30, fontSize: 50, fontWeight: 800 }}>
      <Pill color={C.red} big>{from}</Pill>
      <span style={{ color: C.overlay }}>── pays ₹{amount} ──▶</span>
      <Pill color={C.green} big>Mike</Pill>
    </div>
  </Reveal>
);

export const SplitSettle: React.FC = () => (
  <Slide kicker="STEP 3 · SETTLE UP" title="Who pays whom" color={C.green}>
    <div style={{ display: "flex", flexDirection: "column", gap: 50, marginTop: 30 }}>
      <Arrow from="Kimberly" amount="333.33" delay={0.2} />
      <Arrow from="Josh" amount="233.34" delay={1.2} />
      <Reveal at={0} delay={2.2}><div style={{ fontSize: 48, fontWeight: 800 }}>Everyone is at zero <Tick /></div></Reveal>
    </div>
  </Slide>
);
