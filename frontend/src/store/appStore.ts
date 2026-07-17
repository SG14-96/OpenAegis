import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type AlarmState = "disarmed" | "armed_stay" | "armed_away" | "triggered";
export type TriggerType = "panic" | "fire" | "auxiliary";

type AppStore = {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  activePlugin: {
    plugin: string;
    status: "loaded" | "not_loaded";
  };
  alarmState: AlarmState;
  triggerType: TriggerType;
  signIn: (tokens: { access: string; refresh?: string }, user?: User) => void;
  signOut: () => void;
  setActivePlugin: (plugin: {
    plugin: string;
    status: "loaded" | "not_loaded";
  }) => void;
  setAlarmState: (alarmState: AlarmState) => void;
  trigger: (triggerType: TriggerType) => void;
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
      alarmState: "disarmed",
      triggerType: "panic",
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
      setAlarmState: (alarmState) => set({ alarmState }),
      trigger: (triggerType) => set({ triggerType, alarmState: "triggered" }),
    }),
    {
      name: "openAegis-app",
      storage: createJSONStorage(() => localStorage),
      partialize: (s) => ({
        user: s.user,
        accessToken: s.accessToken,
        refreshToken: s.refreshToken,
      }),
    }
  )
);
