import { useEffect, useState } from "react";
import { createAsset, getAssets, registerAssetDownload } from "../api/jokko";

export default function AssetMarketplace() {
  const [assets, setAssets] = useState([]);
  const [form, setForm] = useState({ title: "", description: "", url: "", kind: "script", language: "", license: "MIT" });
  const [error, setError] = useState("");
  useEffect(() => {
    getAssets().then(setAssets).catch((err) => setError(err.message));
  }, []);

  async function download(asset) {
    const updated = await registerAssetDownload(asset.id);
    setAssets(assets.map((item) => item.id === updated.id ? updated : item));
    window.open(asset.url, "_blank", "noopener,noreferrer");
  }

  async function publish(event) {
    event.preventDefault();
    try {
      const asset = await createAsset(form);
      setAssets([asset, ...assets]);
      setForm({ title: "", description: "", url: "", kind: "script", language: "", license: "MIT" });
    } catch (err) {
      setError(err.message);
    }
  }

  return <section className="panel asset-panel">
    <div className="section-title"><h2>Marketplace</h2><span className="badge">Composants africains</span></div>
    <p className="muted">Scripts, middlewares et configurations prêts à réutiliser.</p>
    {error && <p className="error">{error}</p>}
    <form className="asset-form" onSubmit={publish}>
      <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Nom du composant" required />
      <input value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} type="url" placeholder="URL du dépôt" required />
      <select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
        {["script", "middleware", "docker", "mobile_money", "ussd"].map((kind) => <option key={kind}>{kind}</option>)}
      </select>
      <input value={form.language} onChange={(e) => setForm({ ...form, language: e.target.value })} placeholder="Langage" />
      <input value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="À quoi sert-il ?" required />
      <button>Publier</button>
    </form>
    {assets.map((asset) => <article className="asset" key={asset.id}>
      <div><span className="badge">{asset.kind}</span><h3>{asset.title}</h3><p>{asset.description}</p>
        <small>{asset.language || "Multi-stack"} · Licence {asset.license}</small></div>
      <button onClick={() => download(asset)}>Utiliser · {asset.download_count}</button>
    </article>)}
    {!assets.length && !error && <p className="muted">Aucun composant publié pour le moment.</p>}
  </section>;
}
