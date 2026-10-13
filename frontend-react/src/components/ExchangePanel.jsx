import { useState } from "react";
import {
  createExchange, getSolutions, proposeSolution, solveExchange,
} from "../api/jokko";

export default function ExchangePanel({ exchanges, currentUser, onReload }) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selected, setSelected] = useState(null);
  const [solutions, setSolutions] = useState([]);
  const [solutionText, setSolutionText] = useState("");

  async function selectExchange(exchange) {
    setSelected(exchange);
    setSolutions(await getSolutions(exchange.id));
  }

  async function publish(event) {
    event.preventDefault();
    await createExchange({ title, description, kind: "problem", language: "python" });
    setTitle("");
    setDescription("");
    onReload();
  }

  async function submitSolution(event) {
    event.preventDefault();
    await proposeSolution(selected.id, solutionText);
    setSolutionText("");
    await selectExchange(selected);
  }

  async function validate(solutionId) {
    await solveExchange(selected.id, solutionId);
    await onReload();
    await selectExchange({ ...selected, status: "solved" });
  }

  return (
    <section className="panel wide">
      <div className="section-title"><h2>Code Exchange</h2><span className="badge">Partage & revue</span></div>
      <form onSubmit={publish} className="create">
        <input value={title} onChange={(event) => setTitle(event.target.value)}
          placeholder="Titre de votre problème ou snippet" required />
        <textarea value={description} onChange={(event) => setDescription(event.target.value)}
          placeholder="Décrivez votre besoin..." required />
        <button>Publier l'échange</button>
      </form>
      {exchanges.map((exchange) => (
        <article className="exchange" key={exchange.id}>
          <div><span className="badge">{exchange.kind}</span><h3>{exchange.title}</h3>
            <p>{exchange.description}</p>
            <button className="link" onClick={() => selectExchange(exchange)}>
              Voir les solutions
            </button>
          </div>
          <span className={exchange.status === "solved" ? "status solved" : "status"}>
            {exchange.status}
          </span>
        </article>
      ))}
      {selected && (
        <div className="solutions">
          <h3>Solutions · {selected.title}</h3>
          {solutions.map((solution) => (
            <div className="solution" key={solution.id}>
              <p>{solution.content}</p>
              {selected.status !== "solved" && selected.author_id === currentUser?.id && (
                <button onClick={() => validate(solution.id)}>Valider cette solution (+10 pts)</button>
              )}
            </div>
          ))}
          {selected.status !== "solved" && selected.author_id !== currentUser?.id && (
            <form onSubmit={submitSolution} className="create">
              <textarea value={solutionText} onChange={(event) => setSolutionText(event.target.value)}
                placeholder="Proposer une solution..." required />
              <button>Envoyer la solution</button>
            </form>
          )}
        </div>
      )}
    </section>
  );
}
