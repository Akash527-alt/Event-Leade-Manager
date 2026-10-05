const BASE = (import.meta.env.VITE_API_URL || "").replace(/\/$/, "");

async function request(path, { method = "GET", body, params } = {}) {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
    });
  }

  let response;
  try {
    response = await fetch(url, {
      method,
      headers: body ? { "Content-Type": "application/json" } : undefined,
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new Error("Cannot reach the server. Check that the backend is running.");
  }

  if (response.status === 204) return null;

  const data = await response.json().catch(() => null);
  if (!response.ok) {
    throw new Error(formatError(data) || `Request failed (${response.status})`);
  }
  return data;
}

// FastAPI returns either {detail: "text"} or {detail: [{loc, msg}, ...]} for validation errors.
function formatError(data) {
  if (!data || !data.detail) return "";
  if (typeof data.detail === "string") return data.detail;
  if (Array.isArray(data.detail)) {
    return data.detail
      .map((d) => `${(d.loc || []).filter((p) => p !== "body").join(".")}: ${d.msg}`)
      .join("; ");
  }
  return "";
}

export const api = {
  listLeads: (params) => request("/api/leads", { params }),
  listEvents: () => request("/api/events"),
  createLead: (lead) => request("/api/leads", { method: "POST", body: lead }),
  updateLead: (id, lead) => request(`/api/leads/${id}`, { method: "PUT", body: lead }),
  deleteLead: (id) => request(`/api/leads/${id}`, { method: "DELETE" }),
  summarize: (id) => request(`/api/leads/${id}/summarize`, { method: "POST" }),
  followUp: (id, options) => request(`/api/leads/${id}/follow-up`, { method: "POST", body: options }),
};
