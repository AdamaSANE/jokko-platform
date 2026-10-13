import { useState } from "react";
import { getPortfolio } from "../api/jokko";

export function Leaderboard({ developers }) {
  const [portfolio, setPortfolio] = useState(null);
  return (
    <section className="panel">
      <div className="section-title"><h2>Leaderboard</h2><span className="badge">Impact</span></div>
      {developers.map((developer, index) => (
        <div className="row" key={developer.user_id}>
          <strong>#{index + 1}</strong>
          <div><b>{developer.display_name}</b><small>{developer.country}</small></div>
          <button className="link" onClick={async () => setPortfolio(await getPortfolio(developer.user_id))}>
            Portfolio
          </button>
          <em>{developer.impact_score} pts</em>
        </div>
      ))}
      {portfolio && <div className="portfolio"><h3>{portfolio.display_name}</h3>
        <p>{portfolio.skills.join(" · ")}</p>
        <strong>{portfolio.solved_exchanges} échanges résolus</strong>
      </div>}
    </section>
  );
}

export function ActivityPanel({ title, items, limit, emptyLabel }) {
  return (
    <section className="panel">
      <div className="section-title"><h2>{title}</h2><span className="badge">{items.length}</span></div>
      {items.slice(0, limit).map((item) => (
        <div className="feed" key={item.id}>
          <b>{title === "Messages" ? "Message communautaire" : item.title}</b>
          <small>{title === "Messages" ? item.body : item.body}</small>
        </div>
      ))}
      {!items.length && <p className="muted">{emptyLabel}</p>}
    </section>
  );
}
