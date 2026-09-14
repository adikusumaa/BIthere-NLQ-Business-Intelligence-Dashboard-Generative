import { create } from "zustand";

import { supabase } from "../services/supabase";

export const useAuthStore = create((set, get) => ({
  user: null,
  session: null,
  loading: true,

  init: async () => {
    const { data } = await supabase.auth.getSession();
    const session = data?.session ?? null;
    const user = session?.user ?? null;
    set({ session, user, loading: false });

    supabase.auth.onAuthStateChange((_event, newSession) => {
      set({
        session: newSession,
        user: newSession?.user ?? null,
      });
    });
  },

  login: async (email, password) => {
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    if (error) throw error;
    set({ session: data.session, user: data.user });
    return data.session;
  },

  logout: async () => {
    await supabase.auth.signOut();
    set({ session: null, user: null });
  },

  getToken: () => get().session?.access_token ?? null,
}));