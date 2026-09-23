import { create } from "zustand";
import { v4 as uuidFallback } from "./uuidFallback";

import { streamChat } from "../services/sse";
import { useWorkspaceStore } from "./workspaceStore";

export const useChatStore = create((set, get) => ({
  sessionId: null,
  messages: [],
  isStreaming: false,
  activeDashboardUrl: null,
  activeDashboardMetabaseId: null,
  error: null,

  ensureSession: () => {
    const current = get().sessionId;
    if (current) return current;
    const newId =
      typeof crypto !== "undefined" && crypto.randomUUID
        ? crypto.randomUUID()
        : uuidFallback();
    set({ sessionId: newId });
    return newId;
  },

  reset: () =>
    set({
      sessionId: null,
      messages: [],
      isStreaming: false,
      activeDashboardUrl: null,
      activeDashboardMetabaseId: null,
      error: null,
    }),

  sendMessage: async (prompt) => {
    const trimmed = prompt.trim();
    if (!trimmed) return;
    if (get().isStreaming) return;

    const workspaceId = useWorkspaceStore.getState().activeWorkspace?.id;

    if (!workspaceId) {
      set({ error: "No workspace selected. Please complete setup first." });
      return;
    }

    const sessionId = get().ensureSession();
    const userMessage = { role: "user", content: trimmed };
    const aiMessage = { role: "assistant", content: "", insight: null };
    set((state) => ({
      messages: [...state.messages, userMessage, aiMessage],
      isStreaming: true,
      error: null,
    }));

    const updateLastAi = (updater) => {
      set((state) => {
        const list = [...state.messages];
        for (let i = list.length - 1; i >= 0; i -= 1) {
          if (list[i].role === "assistant") {
            list[i] = { ...list[i], ...updater(list[i]) };
            break;
          }
        }
        return { messages: list };
      });
    };

    try {
      await streamChat({
        prompt: trimmed,
        sessionId,
        workspaceId,
        onEvent: ({ event, data }) => {
          switch (event) {
            case "start":
              if (data?.session_id) set({ sessionId: data.session_id });
              break;
            case "token":
              updateLastAi((msg) => ({
                content: (msg.content || "") + (data?.text || ""),
              }));
              break;
            case "insight":
              updateLastAi(() => ({ insight: data?.text || "" }));
              break;
            case "dashboard":
              if (data?.url) set({ activeDashboardUrl: data.url });
              if (data?.metabase_id) set({ activeDashboardMetabaseId: data.metabase_id });
              break;
            case "error":
              set({ error: data?.message || "Unknown error" });
              updateLastAi((msg) => ({
                content:
                  msg.content || "Terjadi kesalahan saat memproses permintaan.",
              }));
              break;
            case "done":
              set({ isStreaming: false });
              break;
            default:
              break;
          }
        },
      });
    } catch (err) {
      set({ error: err.message || "Request failed" });
      updateLastAi(() => ({ content: "Maaf, gagal memproses permintaan." }));
    } finally {
      set({ isStreaming: false });
    }
  },
}));