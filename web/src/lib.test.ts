import { describe, expect, it } from "vitest";
import { orderSteps, pairSides, reportLine, sujiFromItem, sujiFromSteps, summarize } from "./lib";
import type { QueueItem, Step } from "./api";

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

describe("sujiFromItem / sujiFromSteps（design.md D2-8, 9）", () => {
  const item = (p: Partial<QueueItem>): QueueItem => ({
    inquiry_id: "INQ-001", customer: "c", subject: "s", body: "b", urgency: "high", category: "billing",
    specialist: "billing_specialist", candidate_ids: ["KB-B01"], draft: { body: "x", cited: [], ask_customer: [], confidence: "high" },
    warnings: [], status: "pending", shadow: null, ...p,
  });
  it("INQ-001: 本番は 4 駅、影は担当から破線で 4 駅まで", () => {
    const s = sujiFromItem(item({ shadow: { agent: "billing_specialist_v2", verdict: "pass", warnings: 0, failed: null } }));
    expect(s.urgency).toBe("high");
    expect(s.main).toMatchObject({ to: 3, failedAt: null, terminal: false });
    expect(s.shadow).toMatchObject({ to: 3, failedAt: null, terminal: false });
    expect(s.articles).toEqual(["KB-B01"]);
    expect(s.decided).toBe(false);
  });
  it("警告の印: 検証の警告は四角、レビュー指摘は三角。判断済みはキューの駅に終端記号", () => {
    const s = sujiFromItem(item({ status: "rejected", warnings: ["禁止表現: 期日の約束", "レビュー指摘: 規程 2 に反する"], shadow: { agent: "v2", verdict: "flag", warnings: 0, failed: null } }));
    expect(s.main.marks).toEqual({ det: true, flag: true });
    expect(s.shadow?.marks).toEqual({ det: false, flag: true });
    expect(s.decided).toBe(true);
    expect(sujiFromItem(item({ warnings: ["人が直接対応"] })).main.marks).toEqual({ det: false, flag: false });
  });
  it("INQ-004: レビュー失敗は本番の線を止めず検査に記号、影の担当の失敗は破線が担当で止まる", () => {
    const s = sujiFromItem(item({
      inquiry_id: "INQ-004", urgency: "normal",
      warnings: ["引用記事が候補に無い: KB-B09", "レビュー失敗: LLMError: fixture missing: reviewer/INQ-004.json"],
      shadow: { agent: "billing_specialist_v2", verdict: null, warnings: null, failed: "LLMError: fixture missing" },
    }));
    expect(s.urgency).toBe("normal");
    expect(s.main).toMatchObject({ to: 3, failedAt: 2, terminal: false });
    expect(s.shadow).toMatchObject({ to: 1, failedAt: 1, terminal: true });
  });
  it("INQ-005: other は分類で止まって終端記号、失敗の記号は無し", () => {
    const s = sujiFromItem(item({ inquiry_id: "INQ-005", urgency: "low", category: "other", specialist: null, draft: null, candidate_ids: [], warnings: ["カテゴリ other の担当なし", "人が直接対応"] }));
    expect(s.main).toMatchObject({ to: 0, failedAt: null, terminal: true });
    expect(s.shadow).toBeNull();
  });
  it("分類の失敗は分類に記号、担当の失敗は担当で止まる。未知の緊急度は低", () => {
    expect(sujiFromItem(item({ urgency: "??", specialist: null, draft: null, warnings: ["分類失敗: x", "人が直接対応"] }))).toMatchObject({ urgency: "low", main: { to: 0, failedAt: 0, terminal: true } });
    expect(sujiFromItem(item({ draft: null, warnings: ["返信案の生成失敗: x", "人が直接対応"] })).main).toMatchObject({ to: 1, failedAt: 1, terminal: true });
  });
  it("steps から: 失敗は段の status で読み、検査の数字はレビューと検証の遅い方、キューは無し", () => {
    const steps: Step[] = [
      step({ step: "route", elapsed_ms: 0.5 }),
      step({ step: "retrieve", elapsed_ms: 0 }),
      step({ step: "shadow_draft", agent: "billing_specialist_v2", status: "failed", reason: "fixture missing", elapsed_ms: 0.1 }),
      step({ step: "draft", elapsed_ms: 1300 }),
      step({ step: "review", status: "failed", reason: "fixture missing", elapsed_ms: 0.1 }),
      step({ step: "verify", output: [], elapsed_ms: 0.7 }),
      step({ step: "enqueue" }),
    ];
    const s = sujiFromSteps(steps, item({ inquiry_id: "INQ-004", urgency: "normal", shadow: { agent: "billing_specialist_v2", verdict: null, warnings: null, failed: "fixture missing" } }));
    expect(s.main).toEqual({ to: 3, failedAt: 2, terminal: false, elapsed: [0.5, 1300, 0.7, null], marks: { det: false, flag: false } });
    expect(s.shadow).toEqual({ to: 1, failedAt: 1, terminal: true, elapsed: [null, 0.1, null, null], marks: { det: false, flag: false } });
  });
});
