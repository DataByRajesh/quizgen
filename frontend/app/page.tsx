"use client";

import React, { useState } from "react";
import Link from "next/link";

type MCQ = {
  question: string;
  options: string[];
  answer_index?: number;
};

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [numQuestions, setNumQuestions] = useState<number>(5);
  const [loading, setLoading] = useState(false);
  const [mcqs, setMcqs] = useState<MCQ[] | null>(null);
  const [docId, setDocId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUploadAndGenerate = async () => {
    setError(null);
    if (!file) {
      setError("Please select a file to upload.");
      return;
    }
    setLoading(true);
    try {
      // Upload file
      const fd = new FormData();
      fd.append("file", file);
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
      const up = await fetch(`${apiUrl}/upload`, {
        method: "POST",
        body: fd,
      });
      if (!up.ok) throw new Error(`Upload failed: ${up.statusText}`);
      const upData = await up.json();
      const id = upData.doc_id;
      setDocId(id);

      // Request generation
      const gen = await fetch(`${apiUrl}/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_id: id, num_questions: numQuestions }),
      });
      if (!gen.ok) throw new Error(`Generate failed: ${gen.statusText}`);
      const genData = await gen.json();
      setMcqs(genData.mcqs || []);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 flex items-center justify-center p-8">
      <div className="w-full max-w-2xl bg-white rounded-lg shadow p-8">
        <h1 className="text-2xl font-semibold mb-4">Quiz Generator</h1>
        <div className="mb-4">
          <Link href="/documents" className="text-sm text-blue-600 underline">
            View uploaded documents
          </Link>
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Upload document</label>
          <input
            type="file"
            accept=".pdf,.docx,.doc,.txt"
            onChange={(e) => setFile(e.target.files ? e.target.files[0] : null)}
            className="block w-full text-sm text-gray-900 bg-gray-50 rounded border p-2"
          />
        </div>

        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">Number of questions</label>
          <input
            type="number"
            min={1}
            max={50}
            value={numQuestions}
            onChange={(e) => setNumQuestions(Number(e.target.value))}
            className="w-24 rounded border p-2"
          />
        </div>

        <div className="flex items-center gap-3">
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
            onClick={handleUploadAndGenerate}
            disabled={loading}
          >
            {loading ? "Generating..." : "Upload & Generate"}
          </button>
          {docId && <span className="text-sm text-gray-500">doc_id: {docId}</span>}
        </div>

        {error && <div className="mt-4 text-red-600">Error: {error}</div>}

        {mcqs && (
          <div className="mt-6">
            <h2 className="text-lg font-medium mb-3">Generated MCQs</h2>
            <ol className="list-decimal pl-5 space-y-4">
              {mcqs.map((m, idx) => (
                <li key={idx}>
                  <div className="font-semibold">{m.question}</div>
                  <ul className="mt-1 list-disc pl-5">
                    {m.options.map((opt, i) => (
                      <li key={i} className={i === m.answer_index ? "text-green-600 font-medium" : ""}>
                        {opt}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ol>
          </div>
        )}
      </div>
    </div>
  );
}
