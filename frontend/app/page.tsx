"use client";

import { useEffect, useState } from "react";
import {
  createJournalEntry,
  getJournalEntries,
  analyzeJournal,
  getInsights,
} from "@/lib/api";

type Analysis = {
  emotion: string;
  keywords: string[];
  summary: string;
};

type Entry = {
  id: number;
  userId: string;
  ambience: string;
  text: string;
  createdAt: string;
  analysis?: Analysis | null;
};

type Insights = {
  totalEntries?: number;
  topEmotion?: string | null;
  mostUsedAmbience?: string | null;
  recentKeywords?: string[];
};

export default function Home() {
  const [userId, setUserId] = useState("123");
  const [ambience, setAmbience] = useState("forest");
  const [text, setText] = useState("");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [insights, setInsights] = useState<Insights | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const loadEntries = async () => {
    try {
      const data = await getJournalEntries(userId);
      setEntries(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error(error);
      setMessage(
        error instanceof Error ? error.message : "Failed to load entries"
      );
      setEntries([]);
    }
  };

  const loadInsights = async () => {
    try {
      const data = await getInsights(userId);
      setInsights(data ?? null);
    } catch (error) {
      console.error(error);
      setMessage(
        error instanceof Error ? error.message : "Failed to load insights"
      );
      setInsights(null);
    }
  };

  useEffect(() => {
    if (!userId.trim()) {
      setEntries([]);
      setInsights(null);
      return;
    }

    loadEntries();
    loadInsights();
  }, [userId]);

  const handleCreate = async () => {
    if (!userId.trim()) {
      setMessage("Please enter a user ID");
      return;
    }

    if (!text.trim()) {
      setMessage("Please write a journal entry");
      return;
    }

    try {
      setLoading(true);
      setMessage("");

      await createJournalEntry({
        userId,
        ambience,
        text,
      });

      setText("");
      setMessage("Journal entry saved");

      await loadEntries();
      await loadInsights();
    } catch (error) {
      console.error(error);
      setMessage(
        error instanceof Error ? error.message : "Failed to save journal entry"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (entry: Entry) => {
    try {
      setLoading(true);
      setMessage("");

      await analyzeJournal({
        text: entry.text,
        entryId: entry.id,
      });

      setMessage("Analysis complete");

      await loadEntries();
      await loadInsights();
    } catch (error) {
      console.error(error);
      setMessage(
        error instanceof Error ? error.message : "Failed to analyze entry"
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen p-8 max-w-4xl mx-auto space-y-8">
      <h1 className="text-3xl font-bold">AI-Assisted Journal System</h1>

      <section className="border rounded-lg p-4 space-y-4">
        <h2 className="text-xl font-semibold">New Journal Entry</h2>

        <div className="space-y-2">
          <label className="block font-medium">User ID</label>
          <input
            className="w-full border rounded px-3 py-2"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Enter user ID"
          />
        </div>

        <div className="space-y-2">
          <label className="block font-medium">Ambience</label>
          <select
            className="w-full border rounded px-3 py-2"
            value={ambience}
            onChange={(e) => setAmbience(e.target.value)}
          >
            <option value="forest">forest</option>
            <option value="ocean">ocean</option>
            <option value="mountain">mountain</option>
          </select>
        </div>

        <div className="space-y-2">
          <label className="block font-medium">Journal Text</label>
          <textarea
            className="w-full border rounded px-3 py-2 min-h-[120px]"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Write your journal entry here..."
          />
        </div>

        <button
          onClick={handleCreate}
          disabled={loading}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
        >
          {loading ? "Working..." : "Save Entry"}
        </button>

        {message && <p className="text-sm text-zinc-300">{message}</p>}
      </section>

      <section className="border rounded-lg p-4 space-y-4">
        <h2 className="text-xl font-semibold">Insights</h2>

        {insights ? (
          <div className="space-y-2">
            <p>
              <strong>Total Entries:</strong> {insights.totalEntries ?? 0}
            </p>
            <p>
              <strong>Top Emotion:</strong> {insights.topEmotion ?? "N/A"}
            </p>
            <p>
              <strong>Most Used Ambience:</strong>{" "}
              {insights.mostUsedAmbience ?? "N/A"}
            </p>
            <p>
              <strong>Recent Keywords:</strong>{" "}
              {Array.isArray(insights.recentKeywords) &&
              insights.recentKeywords.length > 0
                ? insights.recentKeywords.join(", ")
                : "N/A"}
            </p>
          </div>
        ) : (
          <p>No insights yet</p>
        )}
      </section>

      <section className="border rounded-lg p-4 space-y-4">
        <h2 className="text-xl font-semibold">Previous Entries</h2>

        {entries.length === 0 ? (
          <p>No entries found</p>
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => (
              <div key={entry.id} className="border rounded p-4 space-y-2">
                <p>
                  <strong>ID:</strong> {entry.id}
                </p>
                <p>
                  <strong>Ambience:</strong> {entry.ambience}
                </p>
                <p>
                  <strong>Created:</strong> {entry.createdAt}
                </p>
                <p>
                  <strong>Text:</strong> {entry.text}
                </p>

                {entry.analysis ? (
                  <div className="bg-zinc-900 border rounded p-3 space-y-1">
                    <p>
                      <strong>Emotion:</strong> {entry.analysis.emotion}
                    </p>
                    <p>
                      <strong>Keywords:</strong>{" "}
                      {entry.analysis.keywords.join(", ")}
                    </p>
                    <p>
                      <strong>Summary:</strong> {entry.analysis.summary}
                    </p>
                  </div>
                ) : (
                  <button
                    onClick={() => handleAnalyze(entry)}
                    disabled={loading}
                    className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded font-medium cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    Analyze
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}