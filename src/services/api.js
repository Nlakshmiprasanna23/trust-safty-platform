import axios from "axios";

const api = axios.create({
  baseURL:
    import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000",
  timeout: 20000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("ts_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,

  (error) => {
    console.error("========== API ERROR ==========");
    console.error("URL:", error.config?.url);
    console.error("METHOD:", error.config?.method);
    console.error("STATUS:", error.response?.status);
    console.error("RESPONSE:", error.response?.data);
    console.error("REQUEST DATA:", error.config?.data);
    console.error("================================");

    if (
      error.response?.status === 401 &&
      !location.pathname.startsWith("/login")
    ) {
      localStorage.removeItem("ts_token");
      location.href = "/login";
    }

    const responseData = error.response?.data;
    const detail = responseData?.detail;

    let message = "Something went wrong. Please try again.";

    if (responseData?.error) {
      message = responseData.error;
    } else if (typeof detail === "string") {
      message = detail;
    } else if (Array.isArray(detail)) {
      message = detail
        .map((item) => {
          const field = item.loc?.join(".") || "field";
          return `${field}: ${item.msg}`;
        })
        .join(" | ");
    } else if (error.code === "ERR_NETWORK") {
      message =
        "Cannot reach the backend at http://127.0.0.1:8000. Start the backend.";
    }

    return Promise.reject(new Error(message));
  }
);

export default api;

export const endpoints = {
  login: (body) =>
    api.post("/api/auth/login", body).then((r) => r.data),

  stats: () =>
    api.get("/api/dashboard/stats").then((r) => r.data),

  activity: () =>
    api.get("/api/activity").then((r) => r.data),

  analyzeRisk: (body) =>
    api.post("/api/risk/analyze", body).then((r) => r.data),

  analyzeAuthenticity: (form) =>
    api.post("/api/authenticity/analyze", form).then((r) => r.data),

  analyzeReview: (body) =>
    api.post("/api/reviews/analyze", body).then((r) => r.data),

  rings: () =>
    api.get("/api/review-rings").then((r) => r.data),

  cases: () =>
    api.get("/api/fraud/cases").then((r) => r.data),

  caseAction: (id, action, body) =>
    api.post(`/api/cases/${id}/${action}`, body).then((r) => r.data),

  listings: (status) =>
    api
      .get("/api/listings", { params: { status } })
      .then((r) => r.data),

  reviews: (decision) =>
    api
      .get("/api/reviews", { params: { decision } })
      .then((r) => r.data),

  auditLogs: (params) =>
    api
      .get("/api/audit-logs", { params })
      .then((r) => r.data),

  analytics: () =>
    api.get("/api/analytics").then((r) => r.data),

  fairness: () =>
    api.get("/api/fairness").then((r) => r.data),

  modelMetrics: () =>
    api.get("/api/model-metrics").then((r) => r.data),

  cost: () =>
    api.get("/api/cost").then((r) => r.data),

  businessImpact: (body) =>
    api.post("/api/business-impact", body).then((r) => r.data),

  security: () =>
    api.get("/api/security/overview").then((r) => r.data),

  scorecard: () =>
    api.get("/api/scorecard").then((r) => r.data),

  scenarios: () =>
    api.get("/api/demo/scenarios").then((r) => r.data),

  notifications: () =>
    api.get("/api/notifications").then((r) => r.data),

  health: () =>
    api.get("/api/health").then((r) => r.data),
};