import axios from "../utils/axiosClient";

const API_BASE = "/api/v1/alarm";

export async function listAvailablePlugins() {
  const res = await axios.get(`${API_BASE}/plugins/available`);
  return res.data.plugins;
}

export async function loadPlugin(
  modulePath: string,
  setupValues?: Record<string, { option?: string | number; input?: string }>
) {
  const res = await axios.post(`${API_BASE}/plugins/load`, {
    module_path: modulePath,
    setup_values: setupValues ?? null,
  });
  return res.data;
}

export async function unloadPlugin(pluginName: string) {
  const res = await axios.post(`${API_BASE}/plugins/unload`, {
    plugin_name: pluginName,
  });
  return res.data;
}
