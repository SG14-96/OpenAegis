import axios from "../utils/axiosClient";
import type { AlarmStateSnapshot } from "../types/alarm";

const API_BASE = "/api/v1/alarm";

// One-shot fetch of current partitions/zones, used to hydrate app-wide state
// on load before the websocket takes over for live updates.
export async function getAlarmState(): Promise<AlarmStateSnapshot> {
  const res = await axios.get(`${API_BASE}/state`);
  return res.data;
}
