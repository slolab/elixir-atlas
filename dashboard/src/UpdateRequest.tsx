import { createContext, useContext, useState, type FormEvent } from "react";

export const UpdateRequestsEnabled = createContext<boolean | undefined>(undefined);

export function UpdateRequest({ entityType, entityId, context = "" }: { entityType?: string; entityId?: string; context?: string }) {
  const enabled = useContext(UpdateRequestsEnabled);
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

  return <details className="update-request">
    <summary>Request update</summary>
    {enabled === undefined ? <p className="note">Checking availability…</p> : !enabled ? <p className="note">Update requests are unavailable in this deployment.</p> : receipt ? <div role="status">
      <p>Request saved as pending. The Atlas data has not changed.</p>
      <p className="note">Request ID: <code>{receipt}</code></p>
    </div> : <form onSubmit={submit}>
      <p className="note">Describe an incorrect fact, display, or name match. Your suggestion will be saved for future review.</p>
      <label>What needs correcting?
        <textarea required maxLength={5000} rows={3} value={message} onChange={(event) => setMessage(event.target.value)} />
      </label>
      <label>Suggested correction (optional)
        <textarea maxLength={5000} rows={2} value={proposedChange} onChange={(event) => setProposedChange(event.target.value)} />
      </label>
      <label>Supporting source or explanation (optional)
        <textarea maxLength={5000} rows={2} value={evidence} onChange={(event) => setEvidence(event.target.value)} />
      </label>
      {error ? <p role="alert">{error}</p> : null}
      <button type="submit" disabled={sending || !message.trim()}>{sending ? "Saving…" : "Submit request"}</button>
    </form>}
  </details>;
}
