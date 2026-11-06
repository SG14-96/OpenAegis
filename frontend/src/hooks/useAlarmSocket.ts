import { useEffect } from "react";
import { useAppStore } from "../store/appStore";
import { getAlarmConfig, getAlarmState } from "../services/alarm";
import { connectAlarmSocket, disconnectAlarmSocket } from "../services/alarmSocket";

// Wires the frontend up to the backend's alarm state machine:
//   1. HTTP GET /api/v1/alarm/state once, to hydrate app-wide state
//      immediately (no need to wait for the first websocket event).
//   2. HTTP GET /api/v1/alarm/ once, to learn which plugin is running.
//   3. Opens the websocket for live updates from then on.
// Call once from the authenticated app shell (AppWrapper) — it connects
// when a token appears and disconnects when it's mounted without one
// (signed out) or unmounted.
export function useAlarmSocket(): void {
  const accessToken = useAppStore((s) => s.accessToken);
  const setAlarmSnapshot = useAppStore((s) => s.setAlarmSnapshot);
  const setActivePlugin = useAppStore((s) => s.setActivePlugin);

  useEffect(() => {
    if (!accessToken) {
      disconnectAlarmSocket();
      return;
    }

    let cancelled = false;
    getAlarmState()
      .then((snapshot) => {
        if (!cancelled) setAlarmSnapshot(snapshot);
      })
      .catch((err) => console.error("Failed to fetch initial alarm state", err));

    getAlarmConfig()
      .then((config) => {
        if (cancelled) return;
        setActivePlugin(
          config?.active_plugin
            ? { plugin: config.active_plugin, status: "loaded" }
            : { plugin: "None", status: "not_loaded" }
        );
      })
      .catch((err) => console.error("Failed to fetch alarm configuration", err));

    connectAlarmSocket();

    return () => {
      cancelled = true;
      disconnectAlarmSocket();
    };
  }, [accessToken, setAlarmSnapshot, setActivePlugin]);
}

export default useAlarmSocket;
