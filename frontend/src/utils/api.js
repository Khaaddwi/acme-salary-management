const BASE = "/api";

async function get(path, params = {}) {
  const qs = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== "" && v != null)
  ).toString();
  const url = qs ? `${BASE}${path}?${qs}` : `${BASE}${path}`;
  const resp = await fetch(url);
  if (!resp.ok) throw new Error(`${resp.status} ${resp.statusText}`);
  return resp.json();
}

async function put(path, body) {
  const resp = await fetch(`${BASE}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.error || `${resp.status} ${resp.statusText}`);
  }
  return resp.json();
}

async function post(path, body) {
  const resp = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.error || `${resp.status} ${resp.statusText}`);
  }
  return resp.json();
}

export const api = {
  employees: {
    list:   (params) => get("/employees", params),
    get:    (id)     => get(`/employees/${id}`),
    updateSalary: (id, body) => put(`/employees/${id}/salary`, body),
    exportUrl: (params) => {
      const qs = new URLSearchParams(
        Object.entries(params).filter(([, v]) => v !== "" && v != null)
      ).toString();
      return qs ? `${BASE}/employees/export?${qs}` : `${BASE}/employees/export`;
    },
  },
  analytics: {
    summary:    () => get("/analytics/summary"),
    departments:() => get("/analytics/departments"),
    countries:  () => get("/analytics/countries"),
    levels:     () => get("/analytics/levels"),
    bands:      () => get("/analytics/bands"),
    empTypes:   () => get("/analytics/employment-types"),
  },
  meta: {
    filters: () => get("/meta/filters"),
  },
  ask: (question) => post("/ask", { question }),
};

export function fmt$$(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(n);
}

export function fmtNum(n) {
  if (n == null) return "—";
  return new Intl.NumberFormat("en-US").format(n);
}
