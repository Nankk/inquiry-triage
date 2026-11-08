// 画面用の純粋関数。API の生データを表示しやすい形に整える。テストはここだけ。
import type { Step, ShadowReport } from "./api";

export const STEP_ORDER = ["route", "retrieve", "draft", "review", "verify", "enqueue"] as const;

export const STEP_LABEL: Record<string, string> = {
  route: "分類",
  retrieve: "FAQ 表引き",
  draft: "返信案",
  review: "レビュー",
  verify: "決定論的検証",
  enqueue: "キューへ",
  shadow_draft: "返信案（影）",
  shadow_review: "レビュー（影）",
  shadow_verify: "決定論的検証（影）",
};

export const STATUS_LABEL: Record<string, string> = {
  pending: "未決",
  accepted: "採用",
  rejected: "却下",
  edited: "修正して採用",
};

export const URGENCY_LABEL: Record<string, string> = { high: "高", normal: "中", low: "低" };

export interface Side {
  agent: string | null;
  body: string | null;
  cited: string[];
  confidence: string | null;
  verdict: string | null;
  reasons: string[];
  warnings: string[];
  failed: string | null;
}

function draftOf(step: Step | undefined): Pick<Side, "agent" | "body" | "cited" | "confidence" | "failed"> {
  if (!step) return { agent: null, body: null, cited: [], confidence: null, failed: null };
  if (step.status !== "ok" || !step.output || Array.isArray(step.output))
    return { agent: step.agent, body: null, cited: [], confidence: null, failed: step.reason ?? "失敗" };
  const o = step.output as { body?: string; cited?: string[]; confidence?: string };
  return { agent: step.agent, body: o.body ?? null, cited: o.cited ?? [], confidence: o.confidence ?? null, failed: null };
}

function reviewOf(step: Step | undefined): Pick<Side, "verdict" | "reasons"> {
  if (!step) return { verdict: null, reasons: [] };
  if (step.status !== "ok" || !step.output || Array.isArray(step.output)) return { verdict: "失敗", reasons: [step.reason ?? ""] };
  const o = step.output as { verdict?: string; reasons?: string[] };
  return { verdict: o.verdict ?? null, reasons: o.reasons ?? [] };
}

function verifyOf(step: Step | undefined): string[] {
  if (!step || step.status !== "ok" || !Array.isArray(step.output)) return [];
  return step.output as string[];
}

/** steps を「本番」「影」の 2 列にまとめる。影が無ければ shadow は null。 */
export function pairSides(steps: Step[]): { main: Side; shadow: Side | null } {
  const by = (name: string) => steps.find((s) => s.step === name);
  const main: Side = { ...draftOf(by("draft")), ...reviewOf(by("review")), warnings: verifyOf(by("verify")) };
  const sd = by("shadow_draft");
  if (!sd) return { main, shadow: null };
  const shadow: Side = { ...draftOf(sd), ...reviewOf(by("shadow_review")), warnings: verifyOf(by("shadow_verify")) };
  return { main, shadow };
}

/** 時系列の表示順。並列に走った段は記録順が入れ替わるので、段の順で整える。 */
export function orderSteps(steps: Step[]): Step[] {
  const rank = (s: Step) => {
    const base = s.step.replace(/^shadow_/, "");
    const i = STEP_ORDER.indexOf(base as (typeof STEP_ORDER)[number]);
    return (i < 0 ? 99 : i) * 2 + (s.step.startsWith("shadow_") ? 1 : 0);
  };
  return [...steps].sort((a, b) => rank(a) - rank(b) || a.ts.localeCompare(b.ts));
}

/** 比較表の 1 行を人が読む形に。 */
export function reportLine(row: ShadowReport["rows"][number]): { verdict: string; warnings: string; better: "shadow" | "main" | "even" | "unknown" } {
  const sh = row.shadow;
  if (sh.failed) return { verdict: "失敗", warnings: "-", better: "unknown" };
  const mainScore = (row.main.verdict === "pass" ? 0 : 1) + (row.main.warnings ?? 0);
  const shadowScore = (sh.verdict === "pass" ? 0 : 1) + (sh.warnings ?? 0);
  return {
    verdict: sh.verdict ?? "-",
    warnings: String(sh.warnings ?? "-"),
    better: shadowScore < mainScore ? "shadow" : shadowScore > mainScore ? "main" : "even",
  };
}

/** 比較表の合計を 1 文に。 */
export function summarize(t: ShadowReport["totals"]): string {
  if (t.count === 0) return "影は走っていません";
  return `${t.count} 件: 本番 pass ${t.main_pass} / 警告 ${t.main_warnings}、影 pass ${t.shadow_pass} / 警告 ${t.shadow_warnings}` + (t.shadow_failed ? `、影の失敗 ${t.shadow_failed}` : "");
}

export function fmtMs(ms?: number): string {
  if (ms == null) return "";
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
}
