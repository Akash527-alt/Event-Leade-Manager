import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { STATUSES } from "./constants";
import LeadTable from "./components/LeadTable";
import LeadForm from "./components/LeadForm";
import AiPanel from "./components/AiPanel";
import Modal from "./components/Modal";

function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

export default function App() {
  const [leads, setLeads] = useState([]);
  const [total, setTotal] = useState(0);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [eventFilter, setEventFilter] = useState("");
  const debouncedSearch = useDebounced(search);

  // null = closed, "new" = add form, lead object = edit form
  const [formTarget, setFormTarget] = useState(null);
  const [aiLead, setAiLead] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [toast, setToast] = useState("");
  const toastTimer = useRef();

  const showToast = useCallback((message) => {
    setToast(message);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), 2500);
  }, []);

  const loadEvents = useCallback(async () => {
    try {
      setEvents(await api.listEvents());
    } catch {
      /* the event filter is optional; the main list shows any real error */
    }
  }, []);

  // Ignore responses from outdated requests (fast typing in the search box).
  const requestId = useRef(0);
  const loadLeads = useCallback(async () => {
    const id = ++requestId.current;
    setLoading(true);
    try {
      const data = await api.listLeads({ search: debouncedSearch, status, event: eventFilter });
      if (id !== requestId.current) return;
      setLeads(data.items);
      setTotal(data.total);
      setError("");
    } catch (err) {
      if (id !== requestId.current) return;
      setError(err.message);
    } finally {
      if (id === requestId.current) setLoading(false);
    }
  }, [debouncedSearch, status, eventFilter]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  // If the selected event no longer exists (e.g. its last lead was deleted), clear the filter.
  useEffect(() => {
    if (eventFilter && events.length && !events.includes(eventFilter)) setEventFilter("");
  }, [events, eventFilter]);

  async function handleSave(values) {
    if (formTarget && formTarget !== "new") {
      await api.updateLead(formTarget.id, values);
      showToast("Lead updated");
    } else {
      await api.createLead(values);
      showToast("Lead added");
    }
    setFormTarget(null);
    await Promise.all([loadLeads(), loadEvents()]);
  }

  async function confirmDelete() {
    setDeleting(true);
    try {
      await api.deleteLead(deleteTarget.id);
      setDeleteTarget(null);
      showToast("Lead deleted");
      await Promise.all([loadLeads(), loadEvents()]);
    } catch (err) {
      setError(err.message);
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  }

  const filtersActive = Boolean(search || status || eventFilter);
  const clearFilters = () => {
    setSearch("");
    setStatus("");
    setEventFilter("");
  };

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <h1>Event Lead Manager</h1>
          <p className="muted">Capture the people you meet at events and follow up while it's fresh.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setFormTarget("new")}>
          + Add lead
        </button>
      </header>

      <section className="toolbar" aria-label="Search and filters">
        <input
          className="search"
          type="search"
          placeholder="Search name, company, email, event or notes…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search leads"
        />
        <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Filter by status">
          <option value="">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s.value} value={s.value}>
              {s.label}
            </option>
          ))}
        </select>
        <select value={eventFilter} onChange={(e) => setEventFilter(e.target.value)} aria-label="Filter by event">
          <option value="">All events</option>
          {events.map((name) => (
            <option key={name} value={name}>
              {name}
            </option>
          ))}
        </select>
        {filtersActive && (
          <button className="btn" onClick={clearFilters}>
            Clear
          </button>
        )}
      </section>

      {error && (
        <div className="alert alert-error" role="alert">
          {error}{" "}
          <button className="link-btn" onClick={loadLeads}>
            Retry
          </button>
        </div>
      )}

      <main className="card">
        <div className="card-head muted">
          {loading ? "Loading…" : `${total} lead${total === 1 ? "" : "s"}${filtersActive ? " match your filters" : ""}`}
        </div>

        {!loading && !error && leads.length === 0 ? (
          <div className="empty">
            {filtersActive ? (
              <>
                <h3>No leads match</h3>
                <p className="muted">Try a different search or clear the filters.</p>
                <button className="btn" onClick={clearFilters}>
                  Clear filters
                </button>
              </>
            ) : (
              <>
                <h3>No leads yet</h3>
                <p className="muted">Add the first person you met to get started.</p>
                <button className="btn btn-primary" onClick={() => setFormTarget("new")}>
                  + Add lead
                </button>
              </>
            )}
          </div>
        ) : (
          leads.length > 0 && (
            <div className={loading ? "is-loading" : ""}>
              <LeadTable leads={leads} onEdit={setFormTarget} onDelete={setDeleteTarget} onAi={setAiLead} />
            </div>
          )
        )}
      </main>

      {formTarget && (
        <LeadForm
          lead={formTarget === "new" ? null : formTarget}
          eventSuggestions={events}
          onSave={handleSave}
          onClose={() => setFormTarget(null)}
        />
      )}

      {aiLead && <AiPanel lead={aiLead} onClose={() => setAiLead(null)} />}

      {deleteTarget && (
        <Modal title="Delete lead?" onClose={() => !deleting && setDeleteTarget(null)}>
          <p>
            This will permanently delete <strong>{deleteTarget.name}</strong> from {deleteTarget.company}. This can't be
            undone.
          </p>
          <footer className="form-actions">
            <button className="btn" onClick={() => setDeleteTarget(null)} disabled={deleting}>
              Cancel
            </button>
            <button className="btn btn-danger-solid" onClick={confirmDelete} disabled={deleting}>
              {deleting ? "Deleting…" : "Delete"}
            </button>
          </footer>
        </Modal>
      )}

      {toast && (
        <div className="toast" role="status">
          {toast}
        </div>
      )}
    </div>
  );
}
