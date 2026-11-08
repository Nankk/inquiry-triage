// API の JSON の形。Python 側（views.py / approval.py / server.py）と対応させる。

export type Urgency = "high" | "normal" | "low";
export type Status = "pending" | "accepted" | "rejected" | "edited";

export interface Draft {
  body: string;
  cited: string[];
  ask_customer: string[];
  confidence: "high" | "medium" | "low";
}

export interface ShadowSummary {
  agent: string;
  verdict: string | null;
  warnings: number | null;
  failed: string | null;
}

export interface QueueItem {
  inquiry_id: string;
  customer: string;
  subject: string;
  urgency: Urgency | string;
  category: string;
  specialist: string | null;
  candidate_ids: string[];
  draft: Draft | null;
  warnings: string[];
  status: Status | string;
  shadow: ShadowSummary | null;
}

export interface Step {
  ts: string;
  step: string;
  agent: string;
  inquiry_id: string;
  input: Record<string, unknown>;
  output: Record<string, unknown> | string[] | null;
  elapsed_ms?: number;
  status: "ok" | "failed";
  reason?: string;
}

export interface Decision {
  ts: string;
  inquiry_id: string;
  action: Status;
  reason: string;
  body: string | null;
}

export interface InquiryView {
  item: QueueItem;
  steps: Step[];
  decisions: Decision[];
}

export interface ReportSide {
  agent: string | null;
  verdict: string | null;
  warnings: number | null;
  failed?: string | null;
}

export interface ShadowReport {
  run_id: string;
  rows: { inquiry_id: string; category: string; main: ReportSide; shadow: ReportSide }[];
  totals: {
    count: number;
    main_pass: number;
    main_warnings: number;
    shadow_pass: number;
    shadow_warnings: number;
    shadow_failed: number;
  };
}

export interface Config {
  categories: string[];
  agents: Record<string, string>;
  defaults: Record<string, string>;
  routing: Record<string, string>;
  routing_override: Record<string, string>;
  shadow: Record<string, string>;
  files: { routing: string; shadow: string };
}

export interface RunInfo {
  run_id: string;
  items: number;
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const r = await fetch(path, { headers: { "Content-Type": "application/json" }, ...init });
  const data = await r.json();
  if (!r.ok) throw new Error((data as { error?: string }).error ?? `${r.status}`);
  return data as T;
}

export const api = {
  runs: () => req<RunInfo[]>("/api/runs"),
  queue: (run: string) => req<{ run_id: string; items: QueueItem[] }>(`/api/runs/${run}/queue`),
  inquiry: (run: string, id: string) => req<InquiryView>(`/api/runs/${run}/inquiries/${id}`),
  shadowReport: (run: string) => req<ShadowReport>(`/api/runs/${run}/shadow-report`),
  config: () => req<Config>("/api/config"),
  decide: (run: string, body: { inquiry_id: string; action: Status; reason: string; body?: string }) =>
    req<Decision & { outbox: string | null }>(`/api/runs/${run}/decisions`, { method: "POST", body: JSON.stringify(body) }),
  promote: (category: string, agent: string) =>
    req<{ routing: Record<string, string>; shadow: Record<string, string> }>("/api/routing", {
      method: "POST",
      body: JSON.stringify({ category, agent }),
    }),
};
