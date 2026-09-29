/**
 * Base API Client configured for FastAPI backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || "";

export class APIError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = "APIError";
  }
}

export async function apiClient<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!res.ok) {
      let errMsg = `Request failed with status ${res.status}`;
      try {
        const errorData = await res.json();
        if (errorData?.detail) {
          errMsg = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch {
        // Fallback to text status
      }
      throw new APIError(errMsg, res.status);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    if (err instanceof APIError) {
      throw err;
    }
    throw new APIError(err?.message || "Network error connecting to Smart Factory API", 0);
  }
}
