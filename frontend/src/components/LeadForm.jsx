import { useState } from "react";
import Modal from "./Modal";
import { STATUSES } from "../constants";

const EMPTY = { name: "", company: "", email: "", event: "", notes: "", status: "not_contacted" };
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validate(values) {
  const errors = {};
  if (!values.name.trim()) errors.name = "Name is required";
  if (!values.company.trim()) errors.company = "Company is required";
  if (!values.email.trim()) errors.email = "Email is required";
  else if (!EMAIL_RE.test(values.email.trim())) errors.email = "Enter a valid email address";
  if (!values.event.trim()) errors.event = "Event is required";
  return errors;
}

export default function LeadForm({ lead, eventSuggestions, onSave, onClose }) {
  const isEdit = Boolean(lead);
  const [values, setValues] = useState(
    lead
      ? {
          name: lead.name,
          company: lead.company,
          email: lead.email,
          event: lead.event,
          notes: lead.notes,
          status: lead.status,
        }
      : EMPTY
  );
  const [errors, setErrors] = useState({});
  const [saving, setSaving] = useState(false);
  const [serverError, setServerError] = useState("");

  const set = (field) => (e) => setValues((v) => ({ ...v, [field]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    const found = validate(values);
    setErrors(found);
    if (Object.keys(found).length) return;

    setSaving(true);
    setServerError("");
    try {
      await onSave({
        ...values,
        name: values.name.trim(),
        company: values.company.trim(),
        email: values.email.trim(),
        event: values.event.trim(),
      });
    } catch (err) {
      setServerError(err.message);
      setSaving(false);
    }
  }

  return (
    <Modal title={isEdit ? "Edit lead" : "Add lead"} onClose={onClose}>
      <form onSubmit={handleSubmit} noValidate className="form">
        <div className="field-row">
          <label className="field">
            <span>Name *</span>
            <input value={values.name} onChange={set("name")} autoFocus placeholder="Asha Rao" />
            {errors.name && <small className="error">{errors.name}</small>}
          </label>
          <label className="field">
            <span>Company *</span>
            <input value={values.company} onChange={set("company")} placeholder="Acme Corp" />
            {errors.company && <small className="error">{errors.company}</small>}
          </label>
        </div>

        <label className="field">
          <span>Email *</span>
          <input type="email" value={values.email} onChange={set("email")} placeholder="asha@acme.com" />
          {errors.email && <small className="error">{errors.email}</small>}
        </label>

        <div className="field-row">
          <label className="field">
            <span>Event *</span>
            <input
              value={values.event}
              onChange={set("event")}
              list="event-suggestions"
              placeholder="SaaStr Annual 2026"
            />
            <datalist id="event-suggestions">
              {eventSuggestions.map((name) => (
                <option key={name} value={name} />
              ))}
            </datalist>
            {errors.event && <small className="error">{errors.event}</small>}
          </label>
          <label className="field">
            <span>Follow-up status</span>
            <select value={values.status} onChange={set("status")}>
              {STATUSES.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label className="field">
          <span>Notes</span>
          <textarea
            rows={5}
            value={values.notes}
            onChange={set("notes")}
            placeholder="What did you talk about? Pain points, next steps, deadlines…"
          />
        </label>

        {serverError && <div className="alert alert-error">{serverError}</div>}

        <footer className="form-actions">
          <button type="button" className="btn" onClick={onClose} disabled={saving}>
            Cancel
          </button>
          <button type="submit" className="btn btn-primary" disabled={saving}>
            {saving ? "Saving…" : isEdit ? "Save changes" : "Add lead"}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
