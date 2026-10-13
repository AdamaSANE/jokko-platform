import { useState } from "react";
import { login } from "../api/jokko";

export default function LoginForm({ onLogin, onSwitchToRegister }) {
  const [email, setEmail] = useState("adama@jokko.sn");
  const [password, setPassword] = useState("Password123!");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const result = await login(email, password);
      localStorage.setItem("jokko_token", result.access_token);
      onLogin();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <main className="auth">
      <form onSubmit={submit} className="panel">
        <img className="brand-logo" src="/jokko-mark.png" alt="JOKKO, plateforme d'échange des développeurs en Afrique" />
        <span className="eyebrow">JOKKO · CADEV 2026</span>
        <h1>La communauté qui fait grandir les devs africains.</h1>
        <p className="muted">
          Connectez-vous pour échanger, aider et prouver votre impact.
        </p>
        <input value={email} onChange={(event) => setEmail(event.target.value)}
          type="email" placeholder="Email" required />
        <input value={password} onChange={(event) => setPassword(event.target.value)}
          type="password" placeholder="Mot de passe" required />
        {error && <p className="error">{error}</p>}
        <button>Entrer dans JOKKO</button>
        <button type="button" className="link" onClick={onSwitchToRegister}>Créer un compte développeur</button>
      </form>
    </main>
  );
}
