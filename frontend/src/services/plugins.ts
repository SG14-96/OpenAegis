import axios from "../utils/axiosClient";
import { getAlarmConfig } from "./alarm";

const API_BASE = "/api/v1/alarm";

// Wizard answers keyed by step index — the shape a plugin's on_load receives.
export type PluginSetupValues = Record<string, string | number>;

export async function listAvailablePlugins() {
  const res = await axios.get(`${API_BASE}/plugins/available`);
  return res.data.plugins;
}

// Attaches a plugin to the alarm: creates the alarm configuration if none
// exists yet, otherwise swaps the plugin on the existing one (the backend
// rolls back to the previous plugin if the new one fails to load).
// Resolves to the loaded plugin's name.
export async function attachPlugin(
  modulePath: string,
  setupValues: PluginSetupValues,
  alarmName: string
): Promise<string> {
  const body = { module_path: modulePath, setup_values: setupValues };
  const existing = await getAlarmConfig();
  const res = existing
    ? await axios.patch(`${API_BASE}/update`, body)
    : await axios.post(`${API_BASE}/create`, { ...body, alarm_name: alarmName });
  return res.data.plugin;
}

// Unloads the plugin and removes the saved alarm configuration.
export async function detachPlugin(): Promise<void> {
  await axios.delete(`${API_BASE}/delete`);
}
