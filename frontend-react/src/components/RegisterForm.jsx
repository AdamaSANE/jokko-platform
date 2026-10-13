import { useState } from "react";
import { apiRequest } from "../api/client";
import { login } from "../api/jokko";

export default function RegisterForm({ onRegistered, onSwitchToLogin }) {
  const [form, setForm] = useState({
    email: "", username: "", password: "", display_name: "", country: "", tech_stack: "",
  });
  const [error, setError] = useState("");
  const update = (field) => (event) => setForm({ ...form, [field]: event.target.value });

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      await apiRequest("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          tech_stack: form.tech_stack.split(",").map((skill) => skill.trim()).filter(Boolean),
        }),
      });
      const result = await login(form.email, form.password);
      localStorage.setItem("jokko_token", result.access_token);
      onRegistered();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="auth"><form onSubmit={submit} className="panel register-form">
      <img className="brand-logo" src="/jokko-mark.png" alt="JOKKO" />
      <span className="eyebrow">REJOINDRE LA COMMUNAUTÉ</span>
      <h1>Créez votre passeport technique.</h1>
      <input value={form.display_name} onChange={update("display_name")} placeholder="Nom affiché" required />
      <input value={form.username} onChange={update("username")} placeholder="Nom d'utilisateur" required />
      <input value={form.email} onChange={update("email")} type="email" placeholder="Email" required />
      <input value={form.country} onChange={update("country")} placeholder="Pays (ex. Sénégal)" required />
      <input value={form.tech_stack} onChange={update("tech_stack")} placeholder="Stack (Python, React, Docker)" />
      <input value={form.password} onChange={update("password")} type="password" minLength="8" placeholder="Mot de passe (8 caractères minimum)" required />
      {error && <p className="error">{error}</p>}
      <button>Créer mon compte</button>
      <button type="button" className="link" onClick={onSwitchToLogin}>J'ai déjà un compte</button>
    </form></main>
  );
}
