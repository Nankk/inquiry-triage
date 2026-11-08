import { describe, expect, it } from "vitest";
import { orderSteps, pairSides, reportLine, summarize } from "./lib";
import type { Step } from "./api";

const step = (p: Partial<Step>): Step => ({ ts: "2026-11-09T00:00:00Z", step: "x", agent: "a", inquiry_id: "INQ-001", input: {}, output: null, status: "ok", ...p });

describe("pairSides", () => {
  it("本番と影を 2 列にまとめ、失敗は理由を残す", () => {
    const steps: Step[] = [
      step({ step: "draft", agent: "billing_specialist", output: { body: "本文", cited: ["KB-B01"], confidence: "high" } }),
      step({ step: "review", agent: "reviewer", output: { verdict: "flag", reasons: ["確約"] } }),
      step({ step: "verify", agent: "verifier", output: ["禁止表現: 返金の確約"] }),
      step({ step: "shadow_draft", agent: "billing_specialist_v2", output: { body: "影の本文", cited: ["KB-B01"], confidence: "medium" } }),
      step({ step: "shadow_review", agent: "reviewer", status: "failed", reason: "fixture missing" }),
      step({ step: "shadow_verify", agent: "verifier", output: [] }),
    ];
    const { main, shadow } = pairSides(steps);
    expect(main.body).toBe("本文");
    expect(main.verdict).toBe("flag");
    expect(main.warnings).toEqual(["禁止表現: 返金の確約"]);
    expect(shadow?.agent).toBe("billing_specialist_v2");
    expect(shadow?.verdict).toBe("失敗");
    expect(shadow?.reasons).toEqual(["fixture missing"]);
    expect(shadow?.warnings).toEqual([]);
  });
  it("影が無ければ null", () => {
    expect(pairSides([step({ step: "draft", output: { body: "b" } })]).shadow).toBeNull();
  });
});

describe("orderSteps", () => {
  it("並列で入れ替わった段を本番 → 影の順に整える", () => {
    const names = orderSteps([
      step({ step: "shadow_verify" }),
      step({ step: "verify" }),
      step({ step: "enqueue" }),
      step({ step: "shadow_draft" }),
      step({ step: "draft" }),
      step({ step: "route" }),
    ]).map((s) => s.step);
    expect(names).toEqual(["route", "draft", "shadow_draft", "verify", "shadow_verify", "enqueue"]);
  });
});

describe("reportLine / summarize", () => {
  it("影が pass で警告が少なければ shadow が良い", () => {
    const line = reportLine({ inquiry_id: "INQ-001", category: "billing", main: { agent: "a", verdict: "flag", warnings: 1 }, shadow: { agent: "b", verdict: "pass", warnings: 0, failed: null } });
    expect(line.better).toBe("shadow");
  });
  it("影の失敗は unknown", () => {
    const line = reportLine({ inquiry_id: "INQ-004", category: "billing", main: { agent: "a", verdict: null, warnings: 5 }, shadow: { agent: "b", verdict: null, warnings: null, failed: "fixture missing" } });
    expect(line).toEqual({ verdict: "失敗", warnings: "-", better: "unknown" });
  });
  it("合計の文", () => {
    expect(summarize({ count: 2, main_pass: 0, main_warnings: 6, shadow_pass: 1, shadow_warnings: 0, shadow_failed: 1 })).toBe("2 件: 本番 pass 0 / 警告 6、影 pass 1 / 警告 0、影の失敗 1");
    expect(summarize({ count: 0, main_pass: 0, main_warnings: 0, shadow_pass: 0, shadow_warnings: 0, shadow_failed: 0 })).toBe("影は走っていません");
  });
});
