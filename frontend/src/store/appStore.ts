import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

type AppStore = {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  activePlugin: {
    plugin: string;
    status: "loaded" | "not_loaded";
  };
  signIn: (tokens: { access: string; refresh?: string }, user?: User) => void;
  signOut: () => void;
  setActivePlugin: (plugin: {
    plugin: string;
    status: "loaded" | "not_loaded";
  }) => void;
};

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      activePlugin: {
        plugin: "None",
        status: "not_loaded",
      },
      signIn: (tokens, user) =>
        set((s) => ({
          accessToken: tokens.access,
          refreshToken: tokens.refresh ?? s.refreshToken,
          ...(user ? { user } : {}),
        })),
      signOut: () =>
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
        }),
      setActivePlugin: (plugin) =>
        set({
          activePlugin: {
            plugin: plugin.plugin ?? "None",
            status: plugin?.status ?? "not_loaded",
          },
        }),
    }),
    {
      name: "openAegis-app",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({
        user: s.user,
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
        activePlugin: s.activePlugin,
      }),
    }
  )
);
