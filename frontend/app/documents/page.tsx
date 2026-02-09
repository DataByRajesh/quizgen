"use client";

import React, { useEffect, useState } from "react";

type Doc = {
  id: string;
  filename: string;
  uploaded_at: string;
};

export default function DocumentsPage() {
  const [docs, setDocs] = useState<Doc[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

  useEffect(() => {
    setLoading(true);
    fetch(`${apiBase}/documents`)
      .then((r) => {
        if (!r.ok) throw new Error(`Failed to fetch: ${r.status}`);
        return r.json();
      })
      .then((data) => setDocs(data.documents || []))
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [apiBase]);

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-8">
      <div className="w-full max-w-3xl bg-white rounded-lg shadow p-8">
        <h1 className="text-2xl font-semibold mb-4">Uploaded Documents</h1>
        {loading && <div>Loading…</div>}
        {error && <div className="text-red-600">Error: {error}</div>}
        {docs && docs.length === 0 && <div className="text-gray-600">No documents found.</div>}
        {docs && docs.length > 0 && (
          <table className="w-full table-auto border-collapse">
            <thead>
              <tr className="text-left border-b">
                <th className="py-2">ID</th>
                <th className="py-2">Filename</th>
                <th className="py-2">Uploaded At (UTC)</th>
              </tr>
            </thead>
            <tbody>
              {docs.map((d) => (
                <tr key={d.id} className="border-b">
                  <td className="py-2 text-sm text-gray-700 break-words">{d.id}</td>
                  <td className="py-2">{d.filename}</td>
                  <td className="py-2">{d.uploaded_at}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
