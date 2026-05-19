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

function scoreClass(score: number): string {
  if (score >= 0.75) return "score-high";
  if (score >= 0.5) return "score-mid";
  return "score-low";
}

export default function Home() {
  const [query, setQuery] = useState("");
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

  const doSearch = useCallback(async (q: string) => {
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
        body: JSON.stringify({ query: q, topK: 10 }),
      });

      const data = await res.json();

      if (res.status === 503 && data.error === "model_loading") {
        const wait: number = data.retryAfter ?? 20;
        setRetryMsg(`Embedding model se spouští, zkusím znovu za ${wait} s…`);
        setLoading(false);
        retryTimeout.current = setTimeout(() => doSearch(q), wait * 1000);
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

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const val = e.target.value;
    setQuery(val);
    debouncedSearch(val);
  }

  function handleExample(term: string) {
    setQuery(term);
    doSearch(term);
  }

  const showEmpty = !loading && !error && !retryMsg && query.trim() === "";
  const showNoResults =
    !loading && !error && !retryMsg && query.trim() !== "" && results.length === 0;

  return (
    <main className="container">
      <div className="header">
        <h1>Hledání synonym</h1>
        <p>Vektorové vyhledávání v autoritním souboru Národní knihovny ČR</p>
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
          type="search"
          className="search-input"
          placeholder="Zadejte výraz…"
          value={query}
          onChange={handleChange}
          autoFocus
          autoComplete="off"
          spellCheck={false}
        />
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
                <span className="preferred-term">{r.preferredTerm}</span>
                <div className="result-actions">
                  <button
                    className="copy-btn"
                    title="Zkopírovat výraz"
                    onClick={() => handleCopy(r.preferredTerm, `${r.recordId}-term`)}
                  >
                    {copiedKey === `${r.recordId}-term` ? "✓" : "⎘"}
                  </button>
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

              <div className="result-footer">
                <span className="record-id">{r.recordId}</span>
                <button
                  className="copy-btn"
                  title="Zkopírovat ID záznamu"
                  onClick={() => handleCopy(r.recordId, `${r.recordId}-id`)}
                >
                  {copiedKey === `${r.recordId}-id` ? "✓" : "⎘"}
                </button>
                {r.mdt.length > 0 && (
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
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
