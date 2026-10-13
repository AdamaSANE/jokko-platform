import { apiRequest } from "./client";

export const getCurrentUser = () => apiRequest("/api/v1/auth/me");
export const login = (email, password) => apiRequest("/api/v1/auth/login", {
  method: "POST",
  body: JSON.stringify({ email, password }),
});
export const getDashboardData = () => Promise.all([
  apiRequest("/api/v1/exchanges/?limit=20"),
  apiRequest("/api/v1/devs/leaderboard"),
  apiRequest("/api/messages"),
  apiRequest("/api/notifications"),
]);
export const createExchange = (payload) => apiRequest("/api/v1/exchanges/", {
  method: "POST",
  body: JSON.stringify(payload),
});
export const getSolutions = (exchangeId) =>
  apiRequest(`/api/v1/exchanges/${exchangeId}/solutions`);
export const proposeSolution = (exchangeId, content) => apiRequest(
  `/api/v1/exchanges/${exchangeId}/solutions`,
  { method: "POST", body: JSON.stringify({ content }) },
);
export const solveExchange = (exchangeId, solutionId) => apiRequest(
  `/api/v1/exchanges/${exchangeId}/solve`,
  { method: "PUT", body: JSON.stringify({ solution_id: solutionId }) },
);
export const getPortfolio = (userId) =>
  apiRequest(`/api/v1/devs/portfolio/${userId}`);
export const getAssets = () => apiRequest("/api/v1/assets");
export const createAsset = (payload) => apiRequest("/api/v1/assets", {
  method: "POST",
  body: JSON.stringify(payload),
});
export const registerAssetDownload = (assetId) =>
  apiRequest(`/api/v1/assets/${assetId}/download`, { method: "POST" });
