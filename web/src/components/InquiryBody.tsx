/** 問い合わせ本文。この列が無い古い run の queue.json では「本文なし」を出す。 */
export const NO_BODY = "本文なし（記録に含まれていません）";

export function InquiryBody({ body }: { body?: string | null }) {
  return <div className={"draft inquiry" + (body == null ? " empty" : "")}>{body ?? NO_BODY}</div>;
}
