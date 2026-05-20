"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useDebouncedCallback } from "use-debounce";
import type { SearchResult } from "./api/search/route";

const EXAMPLES = [
  "kulturní změna",
  "aeromechanika",
  "diagnostika",
  "ochrana životního prostředí",
  "počítačové sítě",
];

const MODELS: Record<string, string> = {
  "intfloat/multilingual-e5-small": "Základní (intfloat/multilingual-e5-small)",
  "Qwen/Qwen3-Embedding-0.6B": "Pokročilý (Qwen/Qwen3-Embedding-0.6B)",
};

const SOURCE_LABELS: Record<string, string> = {
  ph: "Předmětové heslo",
  ge: "Geografický termín",
  sk: "Konspekt",
  fd: "Formální deskriptor",
};

function scoreClass(score: number): string {
  if (score >= 0.75) return "score-high";
  if (score >= 0.5) return "score-mid";
  return "score-low";
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState<number>(10);
  const [sourceFilter, setSourceFilter] = useState<string>("");
  const [model, setModel] = useState<string>("intfloat/multilingual-e5-small");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [retryMsg, setRetryMsg] = useState<string | null>(null);
  const [copiedKey, setCopiedKey] = useState<string | null>(null);
  const retryTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function handleCopy(text: string, key: string) {
    await navigator.clipboard.writeText(text);
    setCopiedKey(key);
    setTimeout(() => setCopiedKey(null), 1500);
  }

  const doSearch = useCallback(async (q: string, k: number, src = "", mdl = "intfloat/multilingual-e5-small") => {
    if (!q.trim()) {
      setResults([]);
      setError(null);
      setRetryMsg(null);
      return;
    }

    setLoading(true);
    setError(null);
    setRetryMsg(null);

    try {
      const res = await fetch("/api/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, topK: k, source: src, model: mdl }),
      });

      const data = await res.json();

      if (res.status === 503 && data.error === "model_loading") {
        const wait: number = data.retryAfter ?? 20;
        setRetryMsg(`Embedding model se spouští, zkusím znovu za ${wait} s…`);
        setLoading(false);
        retryTimeout.current = setTimeout(() => doSearch(q, k, src, mdl), wait * 1000);
        return;
      }

      if (!res.ok) {
        setError(data.error ?? "Vyhledávání selhalo");
        setResults([]);
        return;
      }

      setResults(data.results ?? []);
    } catch {
      setError("Nepodařilo se připojit k serveru.");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  const debouncedSearch = useDebouncedCallback(doSearch, 400);

  useEffect(() => {
    return () => {
      if (retryTimeout.current) clearTimeout(retryTimeout.current);
    };
  }, []);

  // Načíst výraz a filtr z URL při prvním otevření stránky
  useEffect(() => {
    const hash = decodeURIComponent(window.location.hash.slice(1));
    const src = new URLSearchParams(window.location.search).get("source") ?? "";
    if (src) setSourceFilter(src);
    if (hash) {
      setQuery(hash);
      doSearch(hash, topK, src, model);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Synchronizovat URL fragment s aktuálním výrazem (zachovat search params)
  useEffect(() => {
    const search = window.location.search;
    if (query) {
      window.history.replaceState(null, "", `${search}#${encodeURIComponent(query)}`);
    } else {
      window.history.replaceState(null, "", window.location.pathname + search);
    }
  }, [query]);

  // Synchronizovat source filtr do URL search params
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (sourceFilter) {
      params.set("source", sourceFilter);
    } else {
      params.delete("source");
    }
    const search = params.toString() ? `?${params.toString()}` : "";
    window.history.replaceState(null, "", `${window.location.pathname}${search}${window.location.hash}`);
  }, [sourceFilter]);

  useEffect(() => {
    if (query.trim()) doSearch(query, topK, sourceFilter, model);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [topK]);

  useEffect(() => {
    if (query.trim()) doSearch(query, topK, sourceFilter, model);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sourceFilter]);

  useEffect(() => {
    if (query.trim()) doSearch(query, topK, sourceFilter, model);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [model]);

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setQuery(val);
    debouncedSearch(val, topK, sourceFilter, model);
  }

  function handleExample(term: string) {
    setQuery(term);
    doSearch(term, topK, sourceFilter, model);
  }

  function handleReset() {
    setQuery("");
    setResults([]);
    setError(null);
    setRetryMsg(null);
  }

  const showEmpty = !loading && !error && !retryMsg && query.trim() === "";
  const showNoResults =
    !loading && !error && !retryMsg && query.trim() !== "" && results.length === 0;

  return (
    <main className="container">
      <div className="header">
        <button className="logo-btn" onClick={handleReset} aria-label="Domů">
          <img src="/logo.svg" alt="Logo" className="logo" />
        </button>
        <div>
          <h1>Nový hlodač 😉</h1>
          <p>Nástroj pro dohledávání autoritních termínů na základě významové podobnosti</p>
        </div>
      </div>

      <div className="search-box">
        <svg
          className="search-icon"
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="text"
          className="search-input"
          placeholder="Zadejte výraz…"
          value={query}
          onChange={handleChange}
          autoFocus
          autoComplete="off"
          spellCheck={false}
        />
        {query && (
          <button
            className="search-clear"
            aria-label="Smazat výraz"
            onClick={() => {
              setQuery("");
              setResults([]);
              setError(null);
              setRetryMsg(null);
            }}
          >
            ×
          </button>
        )}
      </div>

      <div className="search-controls">
        <label htmlFor="model-select" className="controls-label">Model:</label>
        <select
          id="model-select"
          className="topk-select"
          value={model}
          onChange={(e) => setModel(e.target.value)}
        >
          {Object.entries(MODELS).map(([id, label]) => (
            <option key={id} value={id}>{label}</option>
          ))}
        </select>
        <label htmlFor="topk-select" className="controls-label">Počet výsledků:</label>
        <select
          id="topk-select"
          className="topk-select"
          value={topK}
          onChange={(e) => setTopK(Number(e.target.value))}
        >
          {[10, 20, 50, 100].map((n) => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>

      <div className="source-filter">
        <span className="controls-label">Typ záznamu:</span>
        {(["", ...Object.keys(SOURCE_LABELS)] as string[]).map((src) => (
          <button
            key={src}
            className={`source-filter-btn${src ? ` source-filter-btn-${src}` : ""}${sourceFilter === src ? " active" : ""}`}
            onClick={() => setSourceFilter(src)}
          >
            {src === "" ? "Vše" : SOURCE_LABELS[src]}
          </button>
        ))}
      </div>

      <div className="status-bar">
        {loading && <span className="status-loading">Hledám…</span>}
        {retryMsg && <span className="status-retry">{retryMsg}</span>}
        {error && <span className="status-error">{error}</span>}
      </div>

      {showEmpty && (
        <div className="empty-state">
          <p>Zadejte výraz pro vyhledání synonym.</p>
          <p style={{ fontSize: "0.875rem" }}>Příklady:</p>
          <div className="examples">
            {EXAMPLES.map((ex) => (
              <button key={ex} className="example-chip" onClick={() => handleExample(ex)}>
                {ex}
              </button>
            ))}
          </div>
        </div>
      )}

      {showNoResults && (
        <div className="empty-state">
          <p>Žádné výsledky pro „{query}".</p>
        </div>
      )}

      {results.length > 0 && (
        <ul className="results-list" aria-label="Výsledky vyhledávání">
          {results.map((r) => (
            <li
              key={r.recordId}
              className={`result-card${r.isVariant ? " is-variant" : ""}`}
            >
              <div className="result-header">
                <span className="term-with-copy">
                  <span className="preferred-term">{r.preferredTerm}</span>
                  <button
                    className="copy-btn"
                    title="Zkopírovat výraz"
                    onClick={() => handleCopy(r.preferredTerm, `${r.recordId}-term`)}
                  >
                    {copiedKey === `${r.recordId}-term` ? "✓" : "⎘"}
                  </button>
                </span>
                <div className="result-actions">
                  {SOURCE_LABELS[r.source] && (
                    <span className={`source-badge source-badge-${r.source}`}>{SOURCE_LABELS[r.source]}</span>
                  )}
                  <span className={`score ${scoreClass(r.score)}`}>
                    {(r.score * 100).toFixed(1)} %
                  </span>
                </div>
              </div>

              {r.isVariant && (
                <div className="variant-note">
                  nalezeno přes variantu: <strong>{r.matchedTerm}</strong>
                </div>
              )}

              <div className="meta-rows">
                <div className="meta-row">
                  <span className="meta-label">ID</span>
                  <span className="record-id">{r.recordId}</span>
                  <button
                    className="copy-btn"
                    title="Zkopírovat ID záznamu"
                    onClick={() => handleCopy(r.recordId, `${r.recordId}-id`)}
                  >
                    {copiedKey === `${r.recordId}-id` ? "✓" : "⎘"}
                  </button>
                </div>

                {r.authorityUrl && (
                  <div className="meta-row">
                    <span className="meta-label">Záznam</span>
                    <a
                      href={r.authorityUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="authority-link"
                    >
                      {r.authorityUrl}
                    </a>
                    <button
                      className="copy-btn"
                      title="Zkopírovat URL"
                      onClick={() => handleCopy(r.authorityUrl, `${r.recordId}-url`)}
                    >
                      {copiedKey === `${r.recordId}-url` ? "✓" : "⎘"}
                    </button>
                  </div>
                )}

                {r.mdt.length > 0 && (
                  <div className="meta-row">
                    <span className="meta-label">MDT</span>
                    <span className="mdt-list">
                      {r.mdt.map((v) => (
                        <span key={v} className="mdt-item">
                          <span className="mdt-badge">{v}</span>
                          <button
                            className="copy-btn"
                            title="Zkopírovat MDT"
                            onClick={() => handleCopy(v, `${r.recordId}-mdt-${v}`)}
                          >
                            {copiedKey === `${r.recordId}-mdt-${v}` ? "✓" : "⎘"}
                          </button>
                        </span>
                      ))}
                    </span>
                  </div>
                )}

                {r.konspekt.length > 0 && (
                  <div className="meta-row">
                    <span className="meta-label">Konspekt</span>
                    <span className="konspekt-list">
                      {r.konspekt.map((k) => (
                        <span key={k} className="konspekt-item">
                          <span className="konspekt-badge">{k}</span>
                          <button
                            className="copy-btn"
                            title="Zkopírovat konspekt"
                            onClick={() => handleCopy(k, `${r.recordId}-k-${k}`)}
                          >
                            {copiedKey === `${r.recordId}-k-${k}` ? "✓" : "⎘"}
                          </button>
                        </span>
                      ))}
                    </span>
                  </div>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
