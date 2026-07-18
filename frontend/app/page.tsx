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
  ambience: "forest" | "ocean" | "mountain";
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
type MessageTone = "success" | "error" | "info";

const ambienceOptions = {
  forest: { label: "Forest", icon: "🌲", detail: "Grounded & quiet" },
  ocean: { label: "Ocean", icon: "🌊", detail: "Open & restorative" },
  mountain: { label: "Mountain", icon: "⛰️", detail: "Clear & expansive" },
} as const;

const emotionColors: Record<string, string> = {
  calm: "bg-emerald-100 text-emerald-800",
  joyful: "bg-amber-100 text-amber-800",
  hopeful: "bg-sky-100 text-sky-800",
  reflective: "bg-indigo-100 text-indigo-800",
  anxious: "bg-orange-100 text-orange-800",
  stressed: "bg-rose-100 text-rose-800",
  sad: "bg-blue-100 text-blue-800",
  lonely: "bg-violet-100 text-violet-800",
  frustrated: "bg-red-100 text-red-800",
  tired: "bg-slate-200 text-slate-700",
  mixed: "bg-purple-100 text-purple-800",
  neutral: "bg-stone-200 text-stone-700",
};

function titleCase(value: string | null) {
  if (!value) return "Not enough data";
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export default function Home() {
  const [userId, setUserId] = useState<string | null>(null);
  const [authReady, setAuthReady] = useState(false);
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [ambience, setAmbience] = useState<Entry["ambience"]>("forest");
  const [journalText, setJournalText] = useState("");
  const [entries, setEntries] = useState<Entry[]>([]);
  const [insights, setInsights] = useState<Insights | null>(null);
  const [loading, setLoading] = useState(false);
  const [analyzingEntryId, setAnalyzingEntryId] = useState<number | null>(null);
  const [message, setMessage] = useState("");
  const [messageTone, setMessageTone] = useState<MessageTone>("info");

  const showError = (error: unknown, fallback: string) => {
    setMessage(error instanceof Error ? error.message : fallback);
    setMessageTone("error");
  };

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
    refreshJournal().catch((error) => showError(error, "Failed to load journal"));
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
      setMessage(authMode === "login" ? "Welcome back" : "Your private journal is ready");
      setMessageTone("success");
    } catch (error) {
      showError(error, "Authentication failed");
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
      setMessage("Reflection saved. Analyze it when you are ready.");
      setMessageTone("success");
    } catch (error) {
      showError(error, "Failed to save entry");
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (entryId: number) => {
    try {
      setAnalyzingEntryId(entryId);
      setMessage("");
      await analyzeJournal(entryId);
      await refreshJournal();
      setMessage("Emotion analysis complete");
      setMessageTone("success");
    } catch (error) {
      showError(error, "Analysis failed");
    } finally {
      setAnalyzingEntryId(null);
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
      <main className="min-h-screen bg-[#f3f6f1] text-slate-900 lg:grid lg:grid-cols-2">
        <section className="relative hidden min-w-0 overflow-hidden bg-[#153f36] p-12 text-white lg:flex lg:flex-col lg:justify-between">
          <div className="absolute -right-28 -top-24 h-80 w-80 rounded-full bg-emerald-300/10" />
          <div className="absolute -bottom-32 -left-20 h-96 w-96 rounded-full bg-teal-200/10" />
          <div className="relative">
            <div className="mb-16 flex items-center gap-3 text-sm font-semibold tracking-wide">
              <span className="grid h-10 w-10 place-items-center rounded-2xl bg-white/10 text-xl">A</span>
              ARVYAX REFLECTIONS
            </div>
            <p className="mb-5 text-xs font-bold uppercase tracking-[0.28em] text-emerald-200">After the session</p>
            <h1 className="max-w-xl text-5xl font-semibold leading-[1.08]">Notice what changed within you.</h1>
            <p className="mt-7 max-w-lg text-lg leading-8 text-emerald-50/75">
              Capture a private reflection, explore its emotional tone, and notice patterns across your nature sessions.
            </p>
          </div>
          <div className="relative grid max-w-xl grid-cols-3 gap-3 text-sm">
            {Object.values(ambienceOptions).map((option) => (
              <div key={option.label} className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur">
                <div className="mb-2 text-2xl" aria-hidden>{option.icon}</div>
                <div className="font-semibold">{option.label}</div>
                <div className="mt-1 text-xs text-emerald-50/60">{option.detail}</div>
              </div>
            ))}
          </div>
        </section>

        <section className="grid min-h-screen place-items-center px-5 py-10 sm:px-10">
          <form onSubmit={handleAuth} className="w-full max-w-md rounded-[2rem] border border-slate-200 bg-white p-7 shadow-[0_24px_80px_rgba(15,23,42,0.09)] sm:p-9">
            <div className="mb-8 lg:hidden">
              <span className="rounded-full bg-emerald-100 px-3 py-1 text-xs font-bold tracking-wide text-emerald-800">ARVYAX REFLECTIONS</span>
            </div>
            <p className="text-sm font-semibold text-emerald-700">{authMode === "login" ? "Welcome back" : "Begin your journal"}</p>
            <h2 className="mt-2 text-3xl font-semibold tracking-tight">{authMode === "login" ? "Sign in to continue" : "Create a private account"}</h2>
            <p className="mt-3 text-sm leading-6 text-slate-500">Your entries are isolated by account and stored in a persistent database.</p>

            <div className="mt-8 space-y-5">
              <div>
                <label htmlFor="username" className="mb-2 block text-sm font-semibold">Username</label>
                <input id="username" required minLength={3} maxLength={64} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-600 focus:bg-white focus:ring-4 focus:ring-emerald-100" value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
              </div>
              <div>
                <label htmlFor="password" className="mb-2 block text-sm font-semibold">Password</label>
                <input id="password" required minLength={8} maxLength={128} type="password" className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 outline-none transition focus:border-emerald-600 focus:bg-white focus:ring-4 focus:ring-emerald-100" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete={authMode === "login" ? "current-password" : "new-password"} />
              </div>
            </div>

            {message && (
              <p role="status" className={`mt-5 rounded-xl px-4 py-3 text-sm ${messageTone === "error" ? "bg-rose-50 text-rose-700" : "bg-emerald-50 text-emerald-800"}`}>{message}</p>
            )}

            <button disabled={loading} className="mt-6 w-full rounded-xl bg-[#176b58] px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-[#125746] disabled:cursor-not-allowed disabled:opacity-60">
              {loading ? "Please wait…" : authMode === "login" ? "Sign in" : "Create account"}
            </button>
            <button type="button" className="mt-4 w-full text-sm font-semibold text-emerald-700 hover:text-emerald-900" onClick={() => { setAuthMode(authMode === "login" ? "register" : "login"); setMessage(""); }}>
              {authMode === "login" ? "New here? Create an account" : "Already registered? Sign in"}
            </button>
          </form>
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f5f7f4] text-slate-900">
      <header className="border-b border-slate-200/80 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-5 py-5 sm:px-8">
          <div className="flex items-center gap-3">
            <span className="grid h-11 w-11 place-items-center rounded-2xl bg-[#176b58] font-bold text-white">A</span>
            <div>
              <div className="font-semibold tracking-tight">ArvyaX Reflections</div>
              <div className="text-xs text-slate-500">Private by design</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden rounded-full bg-slate-100 px-3 py-1.5 text-sm text-slate-600 sm:block">{userId}</span>
            <button onClick={logout} className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold transition hover:border-slate-300 hover:bg-slate-50">Sign out</button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-6xl space-y-8 px-5 py-8 sm:px-8 sm:py-10">
        <section>
          <p className="text-sm font-semibold text-emerald-700">Your reflection space</p>
          <div className="mt-1 flex flex-wrap items-end justify-between gap-4">
            <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">How did the session leave you feeling?</h1>
            <p className="max-w-sm text-sm leading-6 text-slate-500">AI observations support reflection; they are not medical advice or a diagnosis.</p>
          </div>
        </section>

        <section className="grid gap-6 lg:grid-cols-[1.45fr_0.8fr]">
          <form onSubmit={handleCreate} className="rounded-[1.75rem] border border-slate-200 bg-white p-6 shadow-sm sm:p-7">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">New journal entry</h2>
                <p className="mt-1 text-sm text-slate-500">Write naturally. Analysis uses only the text you choose to save.</p>
              </div>
              <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">Encrypted in transit</span>
            </div>

            <fieldset className="mt-6">
              <legend className="mb-3 text-sm font-semibold">Session ambience</legend>
              <div className="grid gap-3 sm:grid-cols-3">
                {(Object.entries(ambienceOptions) as [Entry["ambience"], (typeof ambienceOptions)[Entry["ambience"]]][]).map(([value, option]) => (
                  <label key={value} className={`cursor-pointer rounded-2xl border p-4 transition ${ambience === value ? "border-emerald-600 bg-emerald-50 ring-2 ring-emerald-100" : "border-slate-200 hover:border-slate-300"}`}>
                    <input className="sr-only" type="radio" name="ambience" value={value} checked={ambience === value} onChange={() => setAmbience(value)} />
                    <span className="text-xl" aria-hidden>{option.icon}</span>
                    <span className="ml-2 font-semibold">{option.label}</span>
                    <span className="mt-1 block text-xs text-slate-500">{option.detail}</span>
                  </label>
                ))}
              </div>
            </fieldset>

            <div className="mt-6">
              <div className="mb-2 flex items-center justify-between gap-3">
                <label htmlFor="journal-text" className="text-sm font-semibold">Reflection</label>
                <span className="text-xs text-slate-400">{journalText.length.toLocaleString()} / 10,000</span>
              </div>
              <textarea id="journal-text" required maxLength={10_000} className="min-h-40 w-full resize-y rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 leading-7 outline-none transition placeholder:text-slate-400 focus:border-emerald-600 focus:bg-white focus:ring-4 focus:ring-emerald-100" value={journalText} onChange={(event) => setJournalText(event.target.value)} placeholder="What did you notice during or after the session?" />
            </div>

            <div className="mt-5 flex flex-wrap items-center justify-between gap-4">
              <p className="text-xs text-slate-400">You decide when an entry is sent for AI analysis.</p>
              <button disabled={loading} className="rounded-xl bg-[#176b58] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#125746] disabled:cursor-not-allowed disabled:opacity-60">{loading ? "Saving…" : "Save reflection"}</button>
            </div>

            {message && (
              <p role="status" className={`mt-5 rounded-xl px-4 py-3 text-sm ${messageTone === "error" ? "bg-rose-50 text-rose-700" : messageTone === "success" ? "bg-emerald-50 text-emerald-800" : "bg-sky-50 text-sky-800"}`}>{message}</p>
            )}
          </form>

          <aside className="rounded-[1.75rem] bg-[#173f36] p-6 text-white shadow-sm sm:p-7">
            <p className="text-xs font-bold uppercase tracking-[0.22em] text-emerald-200">Pattern snapshot</p>
            <div className="mt-6 space-y-4">
              <div className="rounded-2xl bg-white/8 p-5">
                <div className="text-3xl font-semibold">{insights?.totalEntries ?? 0}</div>
                <div className="mt-1 text-sm text-emerald-50/70">Saved reflections</div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-2xl bg-white/8 p-4">
                  <div className="text-lg font-semibold">{titleCase(insights?.topEmotion ?? null)}</div>
                  <div className="mt-1 text-xs text-emerald-50/65">Top emotion</div>
                </div>
                <div className="rounded-2xl bg-white/8 p-4">
                  <div className="text-lg font-semibold">{titleCase(insights?.mostUsedAmbience ?? null)}</div>
                  <div className="mt-1 text-xs text-emerald-50/65">Most-used ambience</div>
                </div>
              </div>
              <div className="rounded-2xl bg-white/8 p-4">
                <div className="text-xs text-emerald-50/65">Recent themes</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {insights?.recentKeywords?.length ? insights.recentKeywords.map((keyword) => (
                    <span key={keyword} className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium">{keyword}</span>
                  )) : <span className="text-sm text-emerald-50/70">Analyze an entry to discover themes.</span>}
                </div>
              </div>
            </div>
          </aside>
        </section>

        <section className="pb-12">
          <div className="mb-5 flex items-center justify-between gap-4">
            <div>
              <h2 className="text-2xl font-semibold tracking-tight">Previous reflections</h2>
              <p className="mt-1 text-sm text-slate-500">Newest first. Repeated text reuses a cached analysis to reduce LLM cost.</p>
            </div>
            <span className="rounded-full bg-white px-3 py-1.5 text-sm font-semibold text-slate-600 shadow-sm">{entries.length} total</span>
          </div>

          {!entries.length ? (
            <div className="rounded-[1.75rem] border border-dashed border-slate-300 bg-white px-6 py-14 text-center">
              <div className="text-3xl" aria-hidden>✦</div>
              <h3 className="mt-3 font-semibold">Your journal starts here</h3>
              <p className="mt-2 text-sm text-slate-500">Save your first reflection to begin seeing patterns over time.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {entries.map((entry) => (
                <article key={entry.id} className="rounded-[1.5rem] border border-slate-200 bg-white p-5 shadow-sm sm:p-6">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <span className="grid h-10 w-10 place-items-center rounded-xl bg-slate-100 text-lg" aria-hidden>{ambienceOptions[entry.ambience].icon}</span>
                      <div>
                        <div className="font-semibold">{ambienceOptions[entry.ambience].label} session</div>
                        <time className="text-xs text-slate-400" dateTime={entry.createdAt}>{formatDate(entry.createdAt)}</time>
                      </div>
                    </div>
                    {entry.analysis && <span className={`rounded-full px-3 py-1 text-xs font-bold ${emotionColors[entry.analysis.emotion] ?? emotionColors.neutral}`}>{titleCase(entry.analysis.emotion)}</span>}
                  </div>

                  <p className="mt-5 whitespace-pre-wrap leading-7 text-slate-700">{entry.text}</p>

                  {entry.analysis ? (
                    <div className="mt-5 rounded-2xl border border-emerald-100 bg-emerald-50/70 p-5">
                      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.18em] text-emerald-800"><span aria-hidden>✦</span> AI reflection</div>
                      <p className="mt-3 leading-7 text-slate-700">{entry.analysis.summary}</p>
                      <div className="mt-4 flex flex-wrap gap-2">
                        {entry.analysis.keywords.map((keyword) => <span key={keyword} className="rounded-full bg-white px-3 py-1 text-xs font-medium text-slate-600 shadow-sm">#{keyword}</span>)}
                      </div>
                    </div>
                  ) : (
                    <div className="mt-5 flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-5">
                      <p className="text-xs text-slate-400">Analysis is opt-in and cached by normalized text hash.</p>
                      <button type="button" onClick={() => handleAnalyze(entry.id)} disabled={analyzingEntryId !== null} className="rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-emerald-800 disabled:cursor-not-allowed disabled:opacity-60">{analyzingEntryId === entry.id ? "Analyzing…" : "Analyze emotion"}</button>
                    </div>
                  )}
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
