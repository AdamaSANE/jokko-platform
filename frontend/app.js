const state = { mode: "login", token: localStorage.getItem("jokko_token") };
const $ = (id) => document.getElementById(id);

function setMode(mode) {
  state.mode = mode;
  document.querySelectorAll(".tab").forEach((tab) => tab.classList.toggle("active", tab.dataset.mode === mode));
  const registering = mode === "register";
  $("auth-title").textContent = registering ? "Rejoignez JOKKO" : "Bienvenue sur JOKKO";
  $("auth-subtitle").textContent = registering ? "Créez votre profil développeur en quelques secondes." : "Connectez-vous pour accéder à votre espace privé.";
  $("auth-submit").textContent = registering ? "Créer mon compte" : "Se connecter";
  $("username-field").classList.toggle("hidden", !registering);
  $("display-name-field").classList.toggle("hidden", !registering);
  $("username").required = registering;
  $("display-name").required = registering;
  $("auth-message").textContent = "";
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(path, { ...options, headers });
  const body = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) throw new Error(body?.detail || "Une erreur est survenue.");
  return body;
}

function showDashboard(data, user) {
  $("auth-view").classList.add("hidden");
  $("dashboard-view").classList.remove("hidden");
  $("welcome").textContent = `Bonjour, ${user.username}`;
  $("stats").innerHTML = `<div class="stat"><span class="muted">Discussions</span><strong>${data.stats.discussions}</strong></div><div class="stat"><span class="muted">Projets</span><strong>${data.stats.projects}</strong></div>`;
  $("discussions").innerHTML = data.recent_discussions.length
    ? data.recent_discussions.map((item) => `<article class="feed-item"><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.body_markdown.slice(0, 140))}</small></article>`).join("")
    : '<p class="muted">Aucune discussion pour le moment.</p>';
  $("notifications").innerHTML = data.unread_notifications.length
    ? data.unread_notifications.map((item) => `<article class="feed-item"><strong>${escapeHtml(item.title)}</strong><small>${escapeHtml(item.body)}</small></article>`).join("")
    : '<p class="muted">Vous êtes à jour.</p>';
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" })[char]);
}

async function loadDashboard() {
  try {
    const user = await request("/auth/me");
    const data = await request("/api/dashboard");
    showDashboard(data, user);
  } catch {
    localStorage.removeItem("jokko_token");
    state.token = null;
  }
}

document.querySelectorAll(".tab").forEach((tab) => tab.addEventListener("click", () => setMode(tab.dataset.mode)));
$("auth-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  $("auth-message").textContent = "";
  try {
    if (state.mode === "register") {
      await request("/auth/register", { method: "POST", body: JSON.stringify({
        email: $("email").value, username: $("username").value,
        password: $("password").value, display_name: $("display-name").value,
      })});
    }
    const token = await request("/auth/login", { method: "POST", body: JSON.stringify({ email: $("email").value, password: $("password").value })});
    state.token = token.access_token;
    localStorage.setItem("jokko_token", state.token);
    await loadDashboard();
  } catch (error) {
    $("auth-message").textContent = error.message;
  }
});
$("logout").addEventListener("click", async () => {
  try { await request("/auth/logout", { method: "POST" }); } finally {
    localStorage.removeItem("jokko_token"); state.token = null;
    $("dashboard-view").classList.add("hidden"); $("auth-view").classList.remove("hidden"); setMode("login");
  }
});
if (state.token) loadDashboard();
