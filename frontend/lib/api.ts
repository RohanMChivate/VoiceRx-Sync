import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({ baseURL: API_BASE });

// Attach JWT to every request
api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("voicerx_token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auth
export const verifyFirebaseToken = (id_token: string) =>
  api.post("/api/auth/verify", { id_token }).then((r) => r.data);

// Consultations
export const processAudio = (formData: FormData) =>
  api.post("/api/consultations/process-audio", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  }).then((r) => r.data);

export const saveConsultation = (data: Record<string, unknown>) =>
  api.post("/api/consultations/save", data).then((r) => r.data);

export const listConsultations = (doctor_email: string) =>
  api.get("/api/consultations", { params: { doctor_email } }).then((r) => r.data);

export const getConsultation = (id: string) =>
  api.get(`/api/consultations/${id}`).then((r) => r.data);

export const getPdfUrl = (id: string) =>
  `${API_BASE}/api/consultations/${id}/pdf`;

// Analytics
export const getAnalytics = (doctor_email: string, period = "month") =>
  api.get("/api/analytics", { params: { doctor_email, period } }).then((r) => r.data);

// Doctor profile (clinic details — set once in dashboard)
export const getProfile = () =>
  api.get("/api/auth/profile").then((r) => r.data);

export const updateProfile = (data: Record<string, string>) =>
  api.put("/api/auth/profile", data).then((r) => r.data);
