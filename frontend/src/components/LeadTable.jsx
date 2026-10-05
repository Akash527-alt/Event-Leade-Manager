import StatusBadge from "./StatusBadge";

function formatDate(iso) {
  // SQLite returns timestamps without a timezone; they are stored as UTC.
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/.test(iso);
  return new Date(hasZone ? iso : `${iso}Z`).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export default function LeadTable({ leads, onEdit, onDelete, onAi }) {
  return (
    <table className="leads">
      <thead>
        <tr>
          <th>Lead</th>
          <th>Event</th>
          <th>Status</th>
          <th>Notes</th>
          <th aria-label="Actions" />
        </tr>
      </thead>
      <tbody>
        {leads.map((lead) => (
          <tr key={lead.id}>
            <td data-label="Lead">
              <div className="lead-name">{lead.name}</div>
              <div className="muted">{lead.company}</div>
              <a className="lead-email" href={`mailto:${lead.email}`}>
                {lead.email}
              </a>
            </td>
            <td data-label="Event">
              <div>{lead.event}</div>
              <div className="muted small">Added {formatDate(lead.created_at)}</div>
            </td>
            <td data-label="Status">
              <StatusBadge status={lead.status} />
            </td>
            <td data-label="Notes" className="notes-cell">
              {lead.notes ? <p className="notes">{lead.notes}</p> : <span className="muted">—</span>}
            </td>
            <td className="actions">
              <button className="btn btn-ai btn-sm" onClick={() => onAi(lead)}>
                ✨ AI
              </button>
              <button className="btn btn-sm" onClick={() => onEdit(lead)}>
                Edit
              </button>
              <button className="btn btn-danger btn-sm" onClick={() => onDelete(lead)}>
                Delete
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
