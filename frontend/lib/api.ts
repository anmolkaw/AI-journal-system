const BASE_URL = "/api/proxy";

async function handleResponse(res: Response, fallbackMessage: string) {
  const text = await res.text();

  if (!res.ok) {
    throw new Error(`${fallbackMessage}: ${res.status} ${text}`);
  }

  try {
    return JSON.parse(text);
  } catch {
    throw new Error(`${fallbackMessage}: backend did not return valid JSON`);
  }
}

export async function createJournalEntry(payload: {
  userId: string;
  ambience: string;
  text: string;
}) {
  const res = await fetch(`${BASE_URL}/journal`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return handleResponse(res, "Failed to create journal entry");
}

export async function getJournalEntries(userId: string) {
  const res = await fetch(`${BASE_URL}/journal/${userId}`, {
    cache: "no-store",
  });

  return handleResponse(res, "Failed to fetch journal entries");
}

export async function analyzeJournal(payload: {
  text: string;
  entryId?: number;
}) {
  const res = await fetch(`${BASE_URL}/journal/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return handleResponse(res, "Failed to analyze journal entry");
}

export async function getInsights(userId: string) {
  const res = await fetch(`${BASE_URL}/journal/insights/${userId}`, {
    cache: "no-store",
  });

  return handleResponse(res, "Failed to fetch insights");
}