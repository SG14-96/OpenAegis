import axios from "../utils/axiosClient";
import type { AlarmConfig, AlarmHistoryEvent, AlarmStateSnapshot } from "../types/alarm";

const API_BASE = "/api/v1/alarm";

// One-shot fetch of current partitions/zones, used to hydrate app-wide state
// on load before the websocket takes over for live updates.
export async function getAlarmState(): Promise<AlarmStateSnapshot> {
  const res = await axios.get(`${API_BASE}/state`);
  return res.data;
}

// Saved alarm configuration, or null when no alarm has been set up yet.
export async function getAlarmConfig(): Promise<AlarmConfig | null> {
  try {
    const res = await axios.get(`${API_BASE}/`);
    return res.data;
  } catch (err) {
    if ((err as { response?: { status?: number } })?.response?.status === 404) return null;
    throw err;
  }
}

// Arm/disarm and alarm/panic history, newest first. Pass the created_at of
// the oldest row already shown as `before` to load the next page.
export async function getAlarmEvents(limit = 50, before?: string): Promise<AlarmHistoryEvent[]> {
  const res = await axios.get(`${API_BASE}/events`, { params: { limit, before } });
  return res.data;
}
