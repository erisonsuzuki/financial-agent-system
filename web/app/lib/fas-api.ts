const API_BASE = process.env.FASTAPI_BASE_URL || "http://localhost:8000";

export async function fastapiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    cache: "no-store",
  });

  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `FastAPI request failed with ${res.status}`);
  }

  return res.json() as Promise<T>;
}
