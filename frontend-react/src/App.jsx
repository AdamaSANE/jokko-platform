import { useCallback, useEffect, useState } from "react";
import { getCurrentUser, getDashboardData } from "./api/jokko";
import LoginForm from "./components/LoginForm";
import RegisterForm from "./components/RegisterForm";
import ExchangePanel from "./components/ExchangePanel";
import AssetMarketplace from "./components/AssetMarketplace";
import { ActivityPanel, Leaderboard } from "./components/CommunityPanels";

export default function App() {
  const [authenticated, setAuthenticated] = useState(Boolean(localStorage.getItem("jokko_token")));
  const [showRegister, setShowRegister] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [data, setData] = useState({ exchanges: [], developers: [], messages: [], notifications: [] });
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [user, values] = await Promise.all([getCurrentUser(), getDashboardData()]);
      setCurrentUser(user);
      setData({
        exchanges: values[0], developers: values[1], messages: values[2], notifications: values[3],
      });
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }, []);

  useEffect(() => { if (authenticated) load(); }, [authenticated, load]);
  if (!authenticated) {
    return showRegister
      ? <RegisterForm onRegistered={() => setAuthenticated(true)} onSwitchToLogin={() => setShowRegister(false)} />
      : <LoginForm onLogin={() => setAuthenticated(true)} onSwitchToRegister={() => setShowRegister(true)} />;
  }

  function logout() {
    localStorage.removeItem("jokko_token");
    setAuthenticated(false);
  }

  return (
    <div className="app">
      <header><div className="brand"><img className="header-logo" src="/jokko-mark.png" alt="JOKKO" />
        <span className="muted">Échange. Entraide. Impact.</span></div>
        <button className="secondary" onClick={logout}>Déconnexion</button>
      </header>
      <main className="content">
        <section className="hero"><div><span className="eyebrow">PLATEFORME D'ÉCHANGE POUR DEVS</span>
          <h1>Construisons l'impact, une solution à la fois.</h1></div>
          <div className="stats"><strong>{data.developers.length}</strong><span>devs actifs</span>
            <strong>{data.messages.length}</strong><span>messages</span>
            <strong>{data.notifications.length}</strong><span>notifications</span></div>
        </section>
        {error && <p className="error">{error}</p>}
        <div className="grid">
          <ExchangePanel exchanges={data.exchanges} currentUser={currentUser} onReload={load} />
          <Leaderboard developers={data.developers} />
          <ActivityPanel title="Notifications" items={data.notifications} limit={9} emptyLabel="Aucune notification." />
          <ActivityPanel title="Messages" items={data.messages} limit={8} emptyLabel="Aucun message." />
          <AssetMarketplace />
        </div>
      </main>
    </div>
  );
}
