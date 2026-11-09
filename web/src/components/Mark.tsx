// 記号はスジと同じ語彙で統一する: 三角 = LLM の指摘や失敗、四角 = 決定論的検証の警告、丸 = 問題なし。
export type MarkKind = "flag" | "warn" | "ok";

export function Mark({ kind }: { kind: MarkKind }) {
  return (
    <svg className={"mark " + kind} viewBox="0 0 10 10" width="10" height="10" aria-hidden="true">
      {kind === "flag" && <path d="M0.5 9.5 H9.5 L5 1 Z" />}
      {kind === "warn" && <rect x="1" y="1" width="8" height="8" />}
      {kind === "ok" && <circle cx="5" cy="5" r="4" />}
    </svg>
  );
}
