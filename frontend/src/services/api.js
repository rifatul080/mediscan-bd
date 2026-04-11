import axios from 'axios';

const API = axios.create({
  baseURL: 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' }
});

// ─── MEDICINE ────────────────────────────────────────────
export const searchMedicine = (query) =>
  API.get(`/medicines/search?query=${query}`);

export const getMedicineById = (id) =>
  API.get(`/medicines/${id}`);

// ─── BILLING ─────────────────────────────────────────────
export const createBill = (billData) =>
  API.post('/billing/create', billData);

export const getBill = (transactionId) =>
  API.get(`/billing/${transactionId}`);

export const downloadReceipt = (transactionId) =>
  API.get(`/billing/${transactionId}/receipt`, {
    responseType: 'blob'  // important for PDF download
  });

export default API;