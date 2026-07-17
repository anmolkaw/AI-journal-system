const BASE_URL = "/api/proxy";
export const TOKEN_KEY = "ai-journal-token";
export const USER_KEY = "ai-journal-user";

type AuthPayload = {
  username: string;
  password: string;
};

type AuthResponse = {
  accessToken: string;
  tokenType: "bearer";
  userId: string;
};

async function handleResponse<T>(
  res: Response,
  fallbackMessage: string
): Promise<T> {
  const text = await res.text();
  let data: unknown = null;

  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      if (res.ok) {
        throw new Error(`${fallbackMessage}: server returned invalid JSON`);
      }
    }
  }

  if (!res.ok) {
    const detail =
      typeof data === "object" && data && "detail" in data
        ? String(data.detail)
        : fallbackMessage;
    throw new Error(detail);
  }

  return data as T;
}

function authHeaders(): HeadersInit {
  const token = window.localStorage.getItem(TOKEN_KEY);
  if (!token) {
    throw new Error("Please sign in to continue");
  }
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

async function authenticate(
  action: "register" | "login",
  payload: AuthPayload
): Promise<AuthResponse> {
  const res = await fetch(`${BASE_URL}/auth/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return handleResponse<AuthResponse>(res, `Failed to ${action}`);
}

export const register = (payload: AuthPayload) =>
  authenticate("register", payload);
export const login = (payload: AuthPayload) => authenticate("login", payload);

export async function createJournalEntry(payload: {
  ambience: string;
  text: string;
}) {
  const res = await fetch(`${BASE_URL}/journal`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  return handleResponse(res, "Failed to create journal entry");
}

export async function getJournalEntries() {
  const res = await fetch(`${BASE_URL}/journal`, {
    headers: authHeaders(),
    cache: "no-store",
  });
  return handleResponse(res, "Failed to fetch journal entries");
}

export async function analyzeJournal(entryId: number) {
  const res = await fetch(`${BASE_URL}/journal/analyze`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ entryId }),
  });
  return handleResponse(res, "Failed to analyze journal entry");
}

export async function getInsights() {
  const res = await fetch(`${BASE_URL}/journal/insights`, {
    headers: authHeaders(),
    cache: "no-store",
  });
  return handleResponse(res, "Failed to fetch insights");
}
