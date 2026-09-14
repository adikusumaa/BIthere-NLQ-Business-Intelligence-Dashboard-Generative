import { create } from "zustand";

import { supabase } from "../services/supabase";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function fetchProfile(token) {
  if (!token) return null;
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) return null;
    return await response.json();
  } catch {
    return null;
  }
}

export const useAuthStore = create((set, get) => ({
  user: null,
  session: null,
  role: null,
  loading: true,

  init: async () => {
    const { data } = await supabase.auth.getSession();
    let session = data?.session ?? null;
    let user = session?.user ?? null;

    // If session exists but token is expired, try refresh
    if (session && session.expires_at * 1000 < Date.now()) {
      const { data: refreshed, error } = await supabase.auth.refreshSession();
      if (!error && refreshed?.session) {
        session = refreshed.session;
        user = refreshed.user;
      } else {
        session = null;
        user = null;
      }
    }

    let role = null;
    if (session?.access_token) {
      const profile = await fetchProfile(session.access_token);
      role = profile?.role ?? null;
    }

    set({ session, user, role, loading: false });

    // Listen to future auth events (login, logout, token refresh)
    supabase.auth.onAuthStateChange(async (event, newSession) => {
      const nextUser = newSession?.user ?? null;
      let nextRole = null;
      if (newSession?.access_token) {
        const profile = await fetchProfile(newSession.access_token);
        nextRole = profile?.role ?? null;
      }
      set({
        session: newSession,
        user: nextUser,
        role: nextRole,
      });
    });
  },

  login: async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;

    const profile = await fetchProfile(data.session.access_token);
    set({
      session: data.session,
      user: data.user,
      role: profile?.role ?? null,
    });
    return data.session;
  },

  logout: async () => {
    await supabase.auth.signOut();
    set({ session: null, user: null, role: null });
  },

  getToken: () => {
    const session = get().session;
    if (!session) return null;
    // If expired, trigger refresh and return null
    if (session.expires_at * 1000 < Date.now()) {
      console.warn("Token expired, triggering refresh...");
      supabase.auth.refreshSession();
      return null;
    }
    return session.access_token;
  },

  isAdmin: () => get().role === "admin",
}));