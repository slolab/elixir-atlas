import { useEffect, useState } from "react";

export type Value = string | number | boolean | string[] | null;
export type Row = Record<string, Value>;

export function apiUrl(endpoint: string, params: Record<string, string | number | boolean> = {}): string {
  return `/api/${endpoint}?${new URLSearchParams(Object.entries(params).map(([key, value]) => [key, String(value)]))}`;
}

export function useApi<T>(url: string, delay = 0) {
  const [state, setState] = useState<{ url: string; data?: T; error?: string }>({ url: "" });
  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(async () => {
      setState({ url });
      try {
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) {
          const body = await response.json().catch(() => ({}));
          throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${response.status}).`);
        }
        const data = (await response.json()) as T;
        if (!controller.signal.aborted) setState({ url, data });
      } catch (error) {
        if (!controller.signal.aborted) setState({ url, error: error instanceof Error ? error.message : String(error) });
      }
    }, delay);
    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [url, delay]);
  return state.url === url ? state : { url };
}

export function list(value: Value | undefined): string[] {
  return Array.isArray(value) ? value : [];
}
