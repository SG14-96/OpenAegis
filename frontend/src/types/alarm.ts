// Mirrors backend/alarm/commands.py — commands the client can send over the
// alarm websocket.
export type AlarmCommand =
  | "arm_stay"
  | "arm_away"
  | "disarm"
  | "bypass_zone"
  | "panic"
  | "status";

export interface CommandPayload {
  command: AlarmCommand;
  partition_id?: number;
  zone_id?: number;
  user_code?: string;
  panic_type?: string;
  bypassed?: boolean;
}

// Mirrors backend/schema/state.py, which mirrors py-dsc-it100's
// StateStore.snapshot() shape — the payload of a "state_snapshot" event and
// the response body of GET /api/v1/alarm/state.
export interface ZoneState {
  zone_id: number;
  partition_id: number | null;
  is_open: boolean | null;
  in_alarm: boolean;
  tampered: boolean;
  faulted: boolean;
  label: string | null;
}

export interface PartitionState {
  partition_id: number;
  state: string;
  is_armed: boolean;
  arm_mode: string | null;
  trouble: boolean;
  label: string | null;
  last_user: number | null;
}

export interface AlarmStateSnapshot {
  partitions: Record<string, PartitionState>;
  zones: Record<string, ZoneState>;
}

// Mirrors backend/alarm/events.py — messages broadcast to every connected
// client over the alarm websocket. Only the fields each type actually
// carries are declared; unknown types are ignored by the socket handler.
export type AlarmServerEvent =
  | ({ type: "state_snapshot" } & AlarmStateSnapshot)
  | { type: "zone_open"; zone_id: number; label?: string }
  | { type: "zone_closed"; zone_id: number }
  | { type: "zone_bypassed"; zone_id: number; bypassed: boolean }
  | { type: "armed_stay"; partition_id: number }
  | { type: "armed_away"; partition_id: number }
  | { type: "disarmed"; partition_id: number }
  | { type: "alarm_triggered"; partition_id: number; zone_id?: number }
  | { type: "alarm_restored"; partition_id: number; zone_id?: number }
  | { type: "alarm_panicked"; partition_id: number; panicked: boolean; panic_type: string }
  | { type: "ready" }
  | { type: "error"; detail: string };
