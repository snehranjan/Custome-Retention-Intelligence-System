/**
 * RetainIQ Customer Retention Intelligence System
 * Authenticated FastAPI REST API Client (Phase 8.4.2)
 *
 * Requirements:
 * - Centralized fetch wrapper attaching Supabase JWT Bearer token when authenticated.
 * - Handles JSON and non-JSON responses safely.
 * - Uniform error parsing distinguishing HTTP 401 (Unauthorized) and HTTP 403 (Forbidden).
 * - Avoids infinite retries or logging credentials.
 * - Does NOT directly query Supabase database tables; routes strictly through FastAPI backend.
 */

import { supabase } from "./supabase";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  constructor(message, status, data = null, code = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
    this.code = code;
    this.isAuthError = status === 401;
    this.isForbiddenError = status === 403;
  }
}

/**
 * Retrieves the current valid access token from Supabase session.
 * Returns null if no active session exists or if Supabase is unconfigured.
 */
export const getAccessToken = async () => {
  if (!supabase) return null;
  try {
    const { data: { session }, error } = await supabase.auth.getSession();
    if (error || !session) return null;
    return session.access_token || null;
  } catch {
    return null;
  }
};

/**
 * Core HTTP request handler.
 * Attaches Authorization Bearer token if not explicitly provided and session exists.
 */
export const apiRequest = async (endpoint, options = {}) => {
  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${cleanEndpoint}`;
  const headers = new Headers(options.headers || {});

  // Default to application/json when sending a stringified JSON body
  if (options.body && !headers.has("Content-Type") && typeof options.body === "string") {
    headers.set("Content-Type", "application/json");
  }

  // Attach Authorization Bearer token from Supabase session if available
  if (!headers.has("Authorization")) {
    const token = await getAccessToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  const config = {
    ...options,
    headers,
  };

  let response;
  try {
    response = await fetch(url, config);
  } catch (networkError) {
    throw new ApiError(
      `Network connection failure contacting backend service: ${networkError.message}`,
      0,
      null,
      "NETWORK_ERROR"
    );
  }

  // Parse response body (handle JSON, text, or empty body)
  let responseData = null;
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    try {
      responseData = await response.json();
    } catch {
      responseData = null;
    }
  } else {
    try {
      responseData = await response.text();
    } catch {
      responseData = null;
    }
  }

  // Handle Non-2xx Responses with uniform ApiError
  if (!response.ok) {
    const status = response.status;
    let errorMessage = `HTTP ${status} Request Failed`;
    let errorCode = "REQUEST_FAILED";

    if (responseData && typeof responseData === "object") {
      if (responseData.error && typeof responseData.error === "object") {
        errorMessage = responseData.error.message || errorMessage;
        errorCode = responseData.error.code || errorCode;
      } else if (responseData.detail) {
        errorMessage = typeof responseData.detail === "string"
          ? responseData.detail
          : JSON.stringify(responseData.detail);
      } else if (responseData.message) {
        errorMessage = responseData.message;
      }
    }

    if (status === 401) {
      throw new ApiError(
        errorMessage || "Unauthorized: Valid employee authentication required",
        401,
        responseData,
        errorCode || "UNAUTHORIZED"
      );
    }
    if (status === 403) {
      throw new ApiError(
        errorMessage || "Forbidden: Account lacks administrative privileges",
        403,
        responseData,
        errorCode || "FORBIDDEN"
      );
    }

    throw new ApiError(errorMessage, status, responseData, errorCode);
  }

  return responseData;
};

export const apiClient = {
  get: (endpoint, options = {}) => apiRequest(endpoint, { ...options, method: "GET" }),
  post: (endpoint, body, options = {}) =>
    apiRequest(endpoint, {
      ...options,
      method: "POST",
      body: typeof body === "object" ? JSON.stringify(body) : body,
    }),
  put: (endpoint, body, options = {}) =>
    apiRequest(endpoint, {
      ...options,
      method: "PUT",
      body: typeof body === "object" ? JSON.stringify(body) : body,
    }),
  delete: (endpoint, options = {}) => apiRequest(endpoint, { ...options, method: "DELETE" }),

  // ---------------------------------------------------------------------------
  // Authentication Integration Endpoints
  // ---------------------------------------------------------------------------
  auth: {
    getHealth: () => apiClient.get("/api/v1/auth/health"),
    getProfile: () => apiClient.get("/api/v1/auth/me"),
    registerEmployee: (payload) => apiClient.post("/api/v1/employee/register", payload),
  },

  // ---------------------------------------------------------------------------
  // Employee Portal Endpoints (Phase 8.4.7)
  // ---------------------------------------------------------------------------
  employee: {
    getProfile: () => apiClient.get("/api/v1/employee/me"),
  },


  // ---------------------------------------------------------------------------
  // Administrator Review & Directory Endpoints (Phase 8.4.5 & Phase 8.4.6)
  // ---------------------------------------------------------------------------
  admin: {
    getProfile: () => apiClient.get("/api/v1/admin/me"),
    getStats: () => apiClient.get("/api/v1/admin/stats"),
    listEmployees: (params = {}) => {
      const query = new URLSearchParams();
      if (params.status && params.status !== "ALL") query.append("status", params.status);
      if (params.search && String(params.search).trim() !== "") query.append("search", String(params.search).trim());
      if (params.limit !== undefined && params.limit !== null) query.append("limit", params.limit);
      if (params.offset !== undefined && params.offset !== null) query.append("offset", params.offset);
      const qs = query.toString();
      return apiClient.get(`/api/v1/admin/employees${qs ? `?${qs}` : ""}`);
    },
    getPendingEmployees: (params = {}) => {
      const query = new URLSearchParams();
      if (params.limit !== undefined && params.limit !== null) query.append("limit", params.limit);
      if (params.offset !== undefined && params.offset !== null) query.append("offset", params.offset);
      const qs = query.toString();
      return apiClient.get(`/api/v1/admin/employees/pending${qs ? `?${qs}` : ""}`);
    },
    getEmployeeDetails: (employeeId) => {
      const cleanId = encodeURIComponent(String(employeeId).trim());
      return apiClient.get(`/api/v1/admin/employees/${cleanId}`);
    },
    inviteEmployee: (payload) => {
      return apiClient.post("/api/v1/admin/employees/invite", payload);
    },
    approveEmployee: (employeeId, body = {}) => {
      const cleanId = encodeURIComponent(String(employeeId).trim());
      return apiClient.post(`/api/v1/admin/employees/${cleanId}/approve`, body);
    },
    rejectEmployee: (employeeId, body) => {
      const cleanId = encodeURIComponent(String(employeeId).trim());
      return apiClient.post(`/api/v1/admin/employees/${cleanId}/reject`, body);
    },
  },

  // ---------------------------------------------------------------------------
  // Machine Learning & Customer Analysis Endpoints
  // ---------------------------------------------------------------------------
  ml: {
    getStatus: () => apiClient.get("/api/v1/ml/status"),
    predictChurn: (features) => apiClient.post("/api/v1/predictions/churn", features),
    predictSegment: (rfm) => apiClient.post("/api/v1/segmentation/predict", rfm),
    getRecommendations: (features) => apiClient.post("/api/v1/retention/recommendations", features),
    analyzeCustomer: (request, persist = false) =>
      apiClient.post(`/api/v1/customers/analyze?persist=${persist}`, request),
  },

  // ---------------------------------------------------------------------------
  // Storage & Database Management Endpoints
  // ---------------------------------------------------------------------------
  database: {
    getHealth: () => apiClient.get("/api/v1/database/health"),
    getStatus: () => apiClient.get("/api/v1/database/status"),
    getCustomerCounts: () => apiClient.get("/api/v1/database/customers/count"),
    getImportStatus: () => apiClient.get("/api/v1/database/import/status"),
  },

  // ---------------------------------------------------------------------------
  // Customer Management Endpoints (Phase 8.4.8)
  // ---------------------------------------------------------------------------
  customers: {
    list: (params = {}) => {
      const query = new URLSearchParams();
      if (params.limit !== undefined && params.limit !== null) query.append("limit", params.limit);
      if (params.offset !== undefined && params.offset !== null) query.append("offset", params.offset);
      if (params.search !== undefined && params.search !== null && String(params.search).trim() !== "") {
        query.append("search", String(params.search).trim());
      }
      if (params.segment !== undefined && params.segment !== null && params.segment !== "ALL") {
        query.append("segment", params.segment);
      }
      if (params.risk_tier && params.risk_tier !== "ALL") {
        query.append("risk_tier", params.risk_tier);
      }
      if (params.state && params.state !== "ALL") {
        query.append("state", params.state);
      }
      if (params.city && params.city !== "ALL") {
        query.append("city", params.city);
      }
      if (params.sort_by) {
        query.append("sort_by", params.sort_by);
      }
      if (params.sort_dir) {
        query.append("sort_dir", params.sort_dir);
      }
      const qs = query.toString();
      return apiClient.get(`/api/v1/customers${qs ? `?${qs}` : ""}`);
    },
    getById: (customerId) => {
      const cleanId = encodeURIComponent(String(customerId).trim());
      return apiClient.get(`/api/v1/customers/${cleanId}`);
    },
    predict: (customerId) => {
      const cleanId = encodeURIComponent(String(customerId).trim());
      return apiClient.post(`/api/v1/customers/${cleanId}/predict`);
    },
  },

  // ---------------------------------------------------------------------------
  // Analytics & Intelligence Endpoints (Phase 8.4.8)
  // ---------------------------------------------------------------------------
  analytics: {
    getOverview: () => apiClient.get("/api/v1/analytics/overview"),
    getModelPerformance: () => apiClient.get("/api/v1/analytics/model-performance"),
    getSegments: () => apiClient.get("/api/v1/analytics/segments"),
  },

  // ---------------------------------------------------------------------------
  // Retention Recommendations Endpoints (Phase 8.4.8)
  // ---------------------------------------------------------------------------
  recommendations: {
    list: (params = {}) => {
      const query = new URLSearchParams();
      if (params.limit !== undefined && params.limit !== null) query.append("limit", params.limit);
      if (params.offset !== undefined && params.offset !== null) query.append("offset", params.offset);
      if (params.segment !== undefined && params.segment !== null && params.segment !== "ALL") {
        query.append("segment", params.segment);
      }
      if (params.priority && params.priority !== "ALL") {
        query.append("priority", params.priority);
      }
      if (params.category && params.category !== "ALL") {
        query.append("category", params.category);
      }
      if (params.risk_tier && params.risk_tier !== "ALL") {
        query.append("risk_tier", params.risk_tier);
      }
      if (params.search && String(params.search).trim() !== "") {
        query.append("search", String(params.search).trim());
      }
      const qs = query.toString();
      return apiClient.get(`/api/v1/recommendations${qs ? `?${qs}` : ""}`);
    },
  },
};
