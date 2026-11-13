import { useState, type FormEvent } from "react";
import { apiUrl, useApi } from "./db";
import { RequestState } from "./components";
import { href, recordHref } from "./route";

export function UpdateRequestPage({ value }: { value: string }) {
  const params = new URLSearchParams(value);
  const entityType = params.get("type") || undefined;
  const entityId = params.get("id") || undefined;
  const context = params.get("context") || "";
  const from = params.get("from") || "#/";
  const back = from.startsWith("#/") && !from.startsWith("#/request-update") ? from : "#/";
  const { data, error: availabilityError } = useApi<{ mode?: string; api: { update_requests: boolean } }>(apiUrl("release"));
  const [message, setMessage] = useState("");
  const [proposedChange, setProposedChange] = useState("");
  const [evidence, setEvidence] = useState("");
  const [sending, setSending] = useState(false);
  const [receipt, setReceipt] = useState("");
  const [error, setError] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (sending || receipt) return;
    setSending(true);
    setError("");
    try {
      const response = await fetch("/api/update-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ origin: "dashboard", entity_type: entityType, entity_id: entityId, message: message.trim(), proposed_change: proposedChange.trim(), evidence: evidence.trim(), context }),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "The request could not be saved. Check your entries and try again.");
      setReceipt(body.id);
    } catch (error) {
      setError(error instanceof Error ? error.message : "The request could not be saved. Please try again.");
    } finally {
      setSending(false);
    }
  }

  return <div className="request-page">
    <a className="back-link" href={back}>Back to previous page</a>
    <h1 className="page-title">Request update</h1>
    <p className="lede">Describe an incorrect fact, display, or name match. Your suggestion will be saved for future review.</p>
    {entityType && entityId ? <RequestContext entityType={entityType} entityId={entityId} context={context} /> : null}
    {!data ? <RequestState error={availabilityError} /> : !data.api.update_requests ? <div className="request-status">
      {data.mode === "sqlite" ? <>
        <p>This local preview cannot save update requests. You can submit your request in the live Atlas.</p>
        <a className="request-link" href={`https://atlas-production-d392fb6d.up.railway.app/${href("request-update", value)}`}>Open live request form</a>
      </> : <p>Update requests are temporarily unavailable. Please try again later.</p>}
    </div> : receipt ? <div className="request-status" role="status">
      <h2>Request saved</h2>
      <p>Request saved as pending. The Atlas data has not changed.</p>
      <p className="note">Request ID: <code>{receipt}</code></p>
      <a className="request-link" href={back}>Return to Atlas</a>
    </div> : <form className="request-form" onSubmit={submit}>
      <label>What needs correcting?
        <textarea required maxLength={5000} rows={5} value={message} onChange={(event) => setMessage(event.target.value)} />
      </label>
      <label>Suggested correction (optional)
        <textarea maxLength={5000} rows={3} value={proposedChange} onChange={(event) => setProposedChange(event.target.value)} />
      </label>
      <label>Supporting source or explanation (optional)
        <textarea maxLength={5000} rows={3} value={evidence} onChange={(event) => setEvidence(event.target.value)} />
      </label>
      {error ? <p role="alert">{error}</p> : null}
      <button type="submit" disabled={sending || !message.trim()}>{sending ? "Saving…" : "Submit request"}</button>
    </form>}
  </div>;
}

function RequestContext({ entityType, entityId, context }: { entityType: string; entityId: string; context: string }) {
  const { data, error } = useApi<{ title: string }>(apiUrl("record", { type: entityType, id: entityId }));
  return <section className="request-context" aria-label="Request subject">
    <h2>About this record</h2>
    {data ? <a href={recordHref(entityType, entityId)}>{data.title}</a> : <RequestState error={error} />}
    {context && !context.startsWith("#/") && context !== data?.title ? <p className="note">{context}</p> : null}
  </section>;
}
