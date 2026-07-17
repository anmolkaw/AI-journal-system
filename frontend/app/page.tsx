"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import {
  TOKEN_KEY,
  USER_KEY,
  analyzeJournal,
  createJournalEntry,
  getInsights,
  getJournalEntries,
  login,
  register,
} from "@/lib/api";

type Analysis = { emotion: string; keywords: string[]; summary: string };
type Entry = {
  id: number;
  ambience: string;
  text: string;
  createdAt: string;
  analysis?: Analysis | null;
};
type Insights = {
  totalEntries: number;
  topEmotion: string | null;
  mostUsedAmbience: string | null;
  recentKeywords: string[];
};

export default function Home() {
  const [userId, setUserId] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [ambience, setAmbience] = useState("forest");
  const [journalText, setJournalText] = useState("");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [insights, setInsights] = useState<Insights | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const refreshJournal = useCallback(async () => {
    const [entryData, insightData] = await Promise.all([
      getJournalEntries(),
      getInsights(),
    ]);
    setEntries(Array.isArray(entryData) ? (entryData as Entry[]) : []);
    setInsights(insightData as Insights);
  }, []);

  useEffect(() => {
    const token = window.localStorage.getItem(TOKEN_KEY);
    const storedUser = window.localStorage.getItem(USER_KEY);
    if (token && storedUser) setUserId(storedUser);
    setAuthReady(true);
  }, []);

  useEffect(() => {
    if (!userId) return;
    refreshJournal().catch((error) => {
      setMessage(error instanceof Error ? error.message : "Failed to load journal");
    });
  }, [refreshJournal, userId]);

  const handleAuth = async (event: FormEvent) => {
    event.preventDefault();
    try {
      setLoading(true);
      setMessage("");
      const result = await (authMode === "login" ? login : register)({
        username,
        password,
      });
      window.localStorage.setItem(TOKEN_KEY, result.accessToken);
      window.localStorage.setItem(USER_KEY, result.userId);
      setUserId(result.userId);
      setPassword("");
      setMessage(authMode === "login" ? "Signed in" : "Account created");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (event: FormEvent) => {
    event.preventDefault();
    try {
      setLoading(true);
      setMessage("");
      await createJournalEntry({ ambience, text: journalText });
      setJournalText("");
      await refreshJournal();
      setMessage("Journal entry saved");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Failed to save entry");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (entryId: number) => {
    try {
      setLoading(true);
      setMessage("");
      await analyzeJournal(entryId);
      await refreshJournal();
      setMessage("Analysis complete");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    window.localStorage.removeItem(TOKEN_KEY);
    window.localStorage.removeItem(USER_KEY);
    setUserId(null);
    setEntries([]);
    setInsights(null);
    setMessage("");
  };

  if (!authReady) return null;

  if (!userId) {
    return (
      <main className="min-h-screen grid place-items-center p-6">
        <form onSubmit={handleAuth} className="w-full max-w-md border rounded-xl p-6 space-y-5 shadow-sm">
          <div>
            <h1 className="text-3xl font-bold">AI-Assisted Journal</h1>
            <p className="text-zinc-500 mt-2">A private space for reflection and AI-powered insights.</p>
          </div>
          <div>
            <label htmlFor="username" className="block font-medium mb-1">Username</label>
            <input id="username" required minLength={3} maxLength={64} className="w-full border rounded px-3 py-2" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
          </div>
          <div>
            <label htmlFor="password" className="block font-medium mb-1">Password</label>
            <input id="password" required minLength={8} maxLength={128} type="password" className="w-full border rounded px-3 py-2" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={authMode === "login" ? "current-password" : "new-password"} />
          </div>
          <button disabled={loading} className="w-full bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium disabled:opacity-60">
            {loading ? "Please wait…" : authMode === "login" ? "Sign in" : "Create account"}
          </button>
          <button type="button" className="w-full text-blue-600 hover:underline" onClick={() => { setAuthMode(authMode === "login" ? "register" : "login"); setMessage(""); }}>
            {authMode === "login" ? "Need an account? Register" : "Already registered? Sign in"}
          </button>
          {message && <p role="status" className="text-sm text-red-600">{message}</p>}
        </form>
      </main>
    );
  }

  return (
    <main className="min-h-screen p-6 md:p-8 max-w-4xl mx-auto space-y-8">
      <header className="flex items-center justify-between gap-4">
        <div><h1 className="text-3xl font-bold">AI-Assisted Journal</h1><p className="text-zinc-500">Signed in as {userId}</p></div>
        <button onClick={logout} className="border rounded px-4 py-2 hover:bg-zinc-100 dark:hover:bg-zinc-900">Sign out</button>
      </header>

      <form onSubmit={handleCreate} className="border rounded-xl p-5 space-y-4">
        <h2 className="text-xl font-semibold">New journal entry</h2>
        <div><label htmlFor="ambience" className="block font-medium mb-1">Ambience</label><select id="ambience" className="w-full border rounded px-3 py-2 bg-transparent" value={ambience} onChange={(e) => setAmbience(e.target.value)}><option value="forest">Forest</option><option value="ocean">Ocean</option><option value="mountain">Mountain</option></select></div>
        <div><label htmlFor="journal-text" className="block font-medium mb-1">Reflection</label><textarea id="journal-text" required maxLength={10000} className="w-full border rounded px-3 py-2 min-h-32" value={journalText} onChange={(e) => setJournalText(e.target.value)} placeholder="Write what is on your mind…" /></div>
        <button disabled={loading} className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded font-medium disabled:opacity-60">{loading ? "Working…" : "Save entry"}</button>
        {message && <p role="status" className="text-sm text-blue-700 dark:text-blue-300">{message}</p>}
      </form>

      <section className="border rounded-xl p-5 space-y-3">
        <h2 className="text-xl font-semibold">Insights</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          <p><strong>Total entries:</strong> {insights?.totalEntries ?? 0}</p>
          <p><strong>Top emotion:</strong> {insights?.topEmotion ?? "Not available"}</p>
          <p><strong>Most-used ambience:</strong> {insights?.mostUsedAmbience ?? "Not available"}</p>
          <p><strong>Recent keywords:</strong> {insights?.recentKeywords?.length ? insights.recentKeywords.join(", ") : "Not available"}</p>
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Previous entries</h2>
        {!entries.length && <p className="text-zinc-500">No entries yet.</p>}
        {entries.map((entry) => (
          <article key={entry.id} className="border rounded-xl p-5 space-y-3">
            <div className="flex justify-between gap-3 text-sm text-zinc-500"><span className="capitalize">{entry.ambience}</span><time dateTime={entry.createdAt}>{new Date(entry.createdAt).toLocaleString()}</time></div>
            <p className="whitespace-pre-wrap">{entry.text}</p>
            {entry.analysis ? (
              <div className="bg-zinc-100 dark:bg-zinc-900 rounded p-4 space-y-1"><p><strong>Emotion:</strong> {entry.analysis.emotion}</p><p><strong>Keywords:</strong> {entry.analysis.keywords.join(", ")}</p><p><strong>Summary:</strong> {entry.analysis.summary}</p></div>
            ) : (
              <button type="button" onClick={() => handleAnalyze(entry.id)} disabled={loading} className="bg-green-700 hover:bg-green-800 text-white px-4 py-2 rounded font-medium disabled:opacity-60">Analyze</button>
            )}
          </article>
        ))}
      </section>
    </main>
  );
}
