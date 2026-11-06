import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { AlarmStateSnapshot, PartitionState, ZoneState } from "../types/alarm";

export type AlarmState = "disarmed" | "armed_stay" | "armed_away" | "triggered";
export type TriggerType = "panic" | "fire" | "auxiliary";

// The UI cards were built around a single flat AlarmState/TriggerType (one
// alarm, one partition). Partition "1" is treated as that primary partition
// so those cards keep working, while the full partitions/zones maps below
// carry everything the backend actually knows for future per-zone UI.
const PRIMARY_PARTITION_ID = "1";

function deriveAlarmState(partition: PartitionState | undefined): AlarmState {
  if (!partition) return "disarmed";
  if (partition.state === "in_alarm") return "triggered";
  if (!partition.is_armed) return "disarmed";
  return partition.arm_mode === "stay" || partition.arm_mode === "stay_no_delay"
    ? "armed_stay"
    : "armed_away";
}

// A transient message from the panel/backend worth surfacing to the user
// (e.g. a rejected command). `id` changes on every notice so the same text
// twice in a row still re-triggers the toast in AppWrapper.
export type PanelNotice = { id: number; level: "error" | "warning" | "info"; text: string };

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
  partitions: Record<string, PartitionState>;
  zones: Record<string, ZoneState>;
  // Active system-wide trouble conditions (AC loss, low battery, ...), keyed
  // by trouble_type. Restored troubles are removed.
  troubles: Record<string, true>;
  panelNotice: PanelNotice | null;
  // Bumped whenever an event that lands in the history tables arrives, so
  // views showing GET /api/v1/alarm/events know to refetch.
  historyVersion: number;
  signIn: (tokens: { access: string; refresh?: string }, user?: User) => void;
  signOut: () => void;
  setActivePlugin: (plugin: {
    plugin: string;
    status: "loaded" | "not_loaded";
  }) => void;
  setAlarmState: (alarmState: AlarmState) => void;
  trigger: (triggerType: TriggerType) => void;
  // Replaces the full partitions/zones map, e.g. from the initial
  // GET /api/v1/alarm/state fetch or a "state_snapshot" websocket event.
  setAlarmSnapshot: (snapshot: AlarmStateSnapshot) => void;
  // Merges a partial partition update (e.g. from an "armed_stay" /
  // "disarmed" / "alarm_triggered" websocket event) into the store.
  upsertPartition: (partial: Partial<PartitionState> & { partition_id: number }) => void;
  // Merges a partial zone update (e.g. from a "zone_open" websocket event).
  upsertZone: (partial: Partial<ZoneState> & { zone_id: number }) => void;
  setTrouble: (troubleType: string, active: boolean) => void;
  showPanelNotice: (level: PanelNotice["level"], text: string) => void;
  bumpHistory: () => void;
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
      partitions: {},
      zones: {},
      troubles: {},
      panelNotice: null,
      historyVersion: 0,
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
          partitions: {},
          zones: {},
          troubles: {},
          activePlugin: { plugin: "None", status: "not_loaded" },
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
      setAlarmSnapshot: (snapshot) =>
        set({
          partitions: snapshot.partitions,
          zones: snapshot.zones,
          alarmState: deriveAlarmState(snapshot.partitions[PRIMARY_PARTITION_ID]),
          ...(snapshot.troubles
            ? { troubles: Object.fromEntries(snapshot.troubles.map((t) => [t, true as const])) }
            : {}),
        }),
      upsertPartition: (partial) =>
        set((s) => {
          const id = String(partial.partition_id);
          const existing = s.partitions[id];
          const merged: PartitionState = {
            state: existing?.state ?? "unknown",
            is_armed: existing?.is_armed ?? false,
            arm_mode: existing?.arm_mode ?? null,
            trouble: existing?.trouble ?? false,
            label: existing?.label ?? null,
            last_user: existing?.last_user ?? null,
            ...partial,
          };
          return {
            partitions: { ...s.partitions, [id]: merged },
            ...(id === PRIMARY_PARTITION_ID ? { alarmState: deriveAlarmState(merged) } : {}),
          };
        }),
      upsertZone: (partial) =>
        set((s) => {
          const id = String(partial.zone_id);
          const existing = s.zones[id];
          const merged: ZoneState = {
            partition_id: existing?.partition_id ?? null,
            is_open: existing?.is_open ?? null,
            in_alarm: existing?.in_alarm ?? false,
            tampered: existing?.tampered ?? false,
            faulted: existing?.faulted ?? false,
            label: existing?.label ?? null,
            ...partial,
          };
          return { zones: { ...s.zones, [id]: merged } };
        }),
      setTrouble: (troubleType, active) =>
        set((s) => {
          const troubles = { ...s.troubles };
          if (active) troubles[troubleType] = true;
          else delete troubles[troubleType];
          return { troubles };
        }),
      showPanelNotice: (level, text) =>
        set((s) => ({ panelNotice: { id: (s.panelNotice?.id ?? 0) + 1, level, text } })),
      bumpHistory: () => set((s) => ({ historyVersion: s.historyVersion + 1 })),
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
