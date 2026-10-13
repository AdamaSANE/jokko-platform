/**
 * Client HTTP partagé : le token reste centralisé ici pour éviter
 * de dupliquer la gestion de l'authentification dans les composants.
 */
export async function apiRequest(path, options = {}) {
  const token = localStorage.getItem("jokko_token");
  const response = await fetch(path, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });
  const body = response.status === 204
    ? null
    : await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error(body?.detail || "Une erreur est survenue.");
  }
  return body;
}
