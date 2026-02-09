"use client";

import React, { useEffect, useState } from "react";

type Doc = {
  id: string;
  filename: string;
  uploaded_at: string;
};

type MCQ = {
  question: string;
  options: string[];
  answer_index: number;
};

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);
  const [query, setQuery] = useState("");
  const [mcqs, setMcqs] = useState<Record<string, MCQ[]>>({});
  const [generating, setGenerating] = useState<Record<string, boolean>>({});

  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

  const fetchDocs = () => {
    setLoading(true);
    setError(null);
    const offset = page * pageSize;
    const q = query ? `&q=${encodeURIComponent(query)}` : "";
    fetch(`${apiBase}/documents?limit=${pageSize}&offset=${offset}${q}`)
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to fetch: ${r.status}`);
        return r.json();
      })
      .then((data) => setDocs(data.documents || []))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchDocs();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [apiBase, page, pageSize]);

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-8">
      <div className="w-full max-w-3xl bg-white rounded-lg shadow p-8">
        <h1 className="text-2xl font-semibold mb-4">Uploaded Documents</h1>
        {loading && <div>Loading…</div>}
        {error && <div className="text-red-600">Error: {error}</div>}
        {docs && docs.length === 0 && <div className="text-gray-600">No documents found.</div>}
        <div className="mb-4 flex gap-2">
          <input
            className="border rounded px-2 py-1 w-full"
            placeholder="Search filename or content"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button
            className="bg-blue-600 text-white px-3 py-1 rounded"
            onClick={() => {
              setPage(0);
              fetchDocs();
            }}
          >
            Search
          </button>
        </div>

        {docs && docs.length > 0 && (
          <>
            <table className="w-full table-auto border-collapse">
              <thead>
                <tr className="text-left border-b">
                  <th className="py-2">ID</th>
                  <th className="py-2">Filename</th>
                  <th className="py-2">Uploaded At (UTC)</th>
                  <th className="py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {docs.map((d) => (
                  <React.Fragment key={d.id}>
                    <tr className="border-b align-top">
                      <td className="py-2 text-sm text-gray-700 break-words max-w-xs">{d.id}</td>
                      <td className="py-2">{d.filename}</td>
                      <td className="py-2">{d.uploaded_at}</td>
                      <td className="py-2">
                        <div className="flex gap-2">
                          <a
                            className="text-sm text-blue-600 underline"
                            href={`${apiBase}/files/${d.id}`}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Download
                          </a>
                          <button
                            className="text-sm bg-green-600 text-white px-2 py-1 rounded"
                            onClick={async () => {
                              setGenerating((s) => ({ ...s, [d.id]: true }));
                              try {
                                const res = await fetch(`${apiBase}/generate`, {
                                  method: "POST",
                                  headers: { "Content-Type": "application/json" },
                                  body: JSON.stringify({ doc_id: d.id, num_questions: 5 }),
                                });
                                if (!res.ok) throw new Error(`generate failed: ${res.status}`);
                                const data = await res.json();
                                setMcqs((m) => ({ ...m, [d.id]: data.mcqs || [] }));
                              } catch (e) {
                                setError(String(e));
                              } finally {
                                setGenerating((s) => ({ ...s, [d.id]: false }));
                              }
                            }}
                            disabled={!!generating[d.id]}
                          >
                            {generating[d.id] ? "Generating…" : "Generate again"}
                          </button>
                        </div>
                      </td>
                    </tr>
                    {mcqs[d.id] && mcqs[d.id].length > 0 && (
                      <tr className="bg-gray-50">
                        <td colSpan={4} className="p-4">
                          <div>
                            <h4 className="font-semibold mb-2">MCQs</h4>
                            <ol className="list-decimal pl-5">
                              {mcqs[d.id].map((q, qi) => (
                                <li key={qi} className="mb-3">
                                  <div className="font-medium">{q.question}</div>
                                  <ul className="pl-4 list-disc">
                                    {q.options.map((opt, oi) => (
                                      <li key={oi} className={oi === q.answer_index ? "text-green-700" : ""}>
                                        {opt}
                                      </li>
                                    ))}
                                  </ul>
                                </li>
                              ))}
                            </ol>
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                ))}
              </tbody>
            </table>

            <div className="mt-4 flex items-center justify-between">
              <div>
                <button
                  className="mr-2 px-2 py-1 border rounded"
                  onClick={() => setPage((p) => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  Prev
                </button>
                <button
                  className="px-2 py-1 border rounded"
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </button>
              </div>
              <div>
                <label className="text-sm mr-2">Page size:</label>
                <select value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0); }}>
                  <option value={5}>5</option>
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                </select>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
