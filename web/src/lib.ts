// 画面用の純粋関数。API の生データを表示しやすい形に整える。テストはここだけ。
import type { QueueItem, ShadowReport, ShadowSummary, Step } from "./api";

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

export function fmtMs(ms?: number | null): string {
  if (ms == null) return "";
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
}

// ---- スジ（段の線）。design.md D2-1, 2, 4, 8, 9 -------------------------------------------------
// 駅は 4 つ。LLM か人が関わり、失敗や警告が出うる点だけ。FAQ 表引きは担当の駅の注記。
export const STATIONS = ["分類", "担当", "検査", "キュー"] as const;
export type Urgency3 = "high" | "normal" | "low";

export interface Track {
  /** 線が届く最後の駅の添字（0〜3） */
  to: number;
  /** 失敗の記号を付ける駅。null なら無し */
  failedAt: number | null;
  /** 線がそこで止まり、終端記号が付く（返信案なしでキューに載る件、影の担当の失敗） */
  terminal: boolean;
  /** 駅ごとの所要時間（ms）。追跡画面だけ */
  elapsed: (number | null)[] | null;
  /** 検査の駅に立てる警告の印。det = 決定論的検証の警告あり（四角）、flag = レビューの指摘あり（三角） */
  marks: { det: boolean; flag: boolean };
}

export interface Suji {
  urgency: Urgency3;
  /** 本番。実線。分類から */
  main: Track;
  /** 影。破線。担当（添字 1）から。影が無ければ null */
  shadow: Track | null;
  /** 担当の駅の注記（渡した記事 ID）。無ければ空 */
  articles: string[];
  /** 人が判断済み（accepted / rejected / edited）。キューの駅に終端記号 */
  decided: boolean;
}

const NO_MARKS = { det: false, flag: false };
/** 決定論的検証の警告か。レビュー由来と「人が直接対応」の案内は除く */
const isDetWarning = (w: string) => !w.startsWith("レビュー") && !w.startsWith("分類失敗") && !w.startsWith("返信案の生成失敗") && !w.startsWith("カテゴリ ") && w !== "人が直接対応";

export function urgency3(u: string): Urgency3 {
  return u === "high" || u === "normal" || u === "low" ? u : "low";
}

const noElapsed = (): (number | null)[] | null => null;

/** キュー項目だけから導く（一覧用）。失敗は warnings の文言で読む。 */
export function sujiFromItem(item: QueueItem): Suji {
  const w = item.warnings;
  let main: Track;
  if (!item.specialist) {
    // 分類の失敗、またはカテゴリ other（人が直接対応）。線は分類で止まる
    main = { to: 0, failedAt: w.some((x) => x.startsWith("分類失敗")) ? 0 : null, terminal: true, elapsed: noElapsed(), marks: NO_MARKS };
  } else if (!item.draft) {
    main = { to: 1, failedAt: 1, terminal: true, elapsed: noElapsed(), marks: NO_MARKS };
  } else {
    main = {
      to: 3,
      failedAt: w.some((x) => x.startsWith("レビュー失敗")) ? 2 : null,
      terminal: false,
      elapsed: noElapsed(),
      marks: { det: w.some(isDetWarning), flag: w.some((x) => x.startsWith("レビュー指摘")) },
    };
  }
  return {
    urgency: urgency3(item.urgency),
    main,
    shadow: shadowTrack(item.shadow, null),
    articles: item.candidate_ids ?? [],
    decided: item.status === "accepted" || item.status === "rejected" || item.status === "edited",
  };
}

function shadowTrack(sh: ShadowSummary | null | undefined, elapsed: (number | null)[] | null): Track | null {
  if (!sh) return null;
  if (sh.failed) return { to: 1, failedAt: 1, terminal: true, elapsed, marks: NO_MARKS };
  const reviewFailed = typeof sh.verdict === "string" && sh.verdict.startsWith("失敗");
  return { to: 3, failedAt: reviewFailed ? 2 : null, terminal: false, elapsed, marks: { det: (sh.warnings ?? 0) > 0, flag: sh.verdict === "flag" } };
}

/** steps.jsonl から導く（追跡画面用）。失敗は段の status で読み、所要時間を添える。 */
export function sujiFromSteps(steps: Step[], item: QueueItem): Suji {
  const by = (name: string) => steps.find((s) => s.step === name);
  const ms = (s?: Step) => (s?.elapsed_ms == null ? null : s.elapsed_ms);
  // 検査はレビュー（LLM）と検証（コード）が並列。駅の数字は遅い方
  const checkMs = (a?: Step, b?: Step) => {
    const xs = [ms(a), ms(b)].filter((x): x is number => x != null);
    return xs.length ? Math.max(...xs) : null;
  };
  const route = by("route"), draft = by("draft"), review = by("review"), verify = by("verify");
  const base = sujiFromItem(item);
  const main: Track = { ...base.main, elapsed: [ms(route), ms(draft), checkMs(review, verify), null] };
  if (route?.status === "failed") Object.assign(main, { to: 0, failedAt: 0, terminal: true });
  else if (draft?.status === "failed") Object.assign(main, { to: 1, failedAt: 1, terminal: true });
  else if (draft && review?.status === "failed") main.failedAt = 2;
  const sd = by("shadow_draft");
  let shadow: Track | null = null;
  if (sd) {
    const sr = by("shadow_review"), sv = by("shadow_verify");
    const elapsed = [null, ms(sd), checkMs(sr, sv), null];
    const verdict = sr?.status === "ok" && sr.output && !Array.isArray(sr.output) ? (sr.output as { verdict?: string }).verdict : undefined;
    const det = Array.isArray(sv?.output) && sv.output.length > 0;
    shadow =
      sd.status === "failed"
        ? { to: 1, failedAt: 1, terminal: true, elapsed, marks: NO_MARKS }
        : { to: 3, failedAt: sr?.status === "failed" ? 2 : null, terminal: false, elapsed, marks: { det, flag: verdict === "flag" } };
  }
  return { ...base, main, shadow };
}
