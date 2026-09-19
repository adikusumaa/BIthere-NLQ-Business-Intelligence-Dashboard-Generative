/**
 * SSE client for BIthere v2 chat endpoint.
 * Uses fetch + ReadableStream because EventSource does not support POST.
 */

import { supabase } from "./supabase";

const API_BASE = import.meta.env.VITE_API_BASE_URL;

async function getAuthToken() {
  const { data } = await supabase.auth.getSession();
  return data?.session?.access_token || null;
}

export async function streamChat({
  prompt,
  sessionId,
  workspaceId,
  onEvent,
  signal,
}) {
  const token = await getAuthToken();
  const headers = {
    "Content-Type": "application/json",
    Accept: "text/event-stream",
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (workspaceId) headers["X-Workspace-ID"] = workspaceId;

  const response = await fetch(`${API_BASE}/api/chat/v2`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message: prompt, session_id: sessionId }),
    signal,
  });

  if (!response.ok) {
    const text = await response.text().catch(() => "");
    throw new Error(`HTTP ${response.status}: ${text || "Unknown error"}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";

    for (const block of parts) {
      if (!block.trim()) continue;
      let eventName = "message";
      let dataRaw = "";
      for (const line of block.split("\n")) {
        if (line.startsWith("event:")) {
          eventName = line.slice(6).trim();
        } else if (line.startsWith("data:")) {
          dataRaw += line.slice(5).trim();
        }
      }
      let payload = null;
      if (dataRaw) {
        try {
          payload = JSON.parse(dataRaw);
        } catch {
          payload = { text: dataRaw };
        }
      }
      onEvent({ event: eventName, data: payload });
    }
  }
}