import { useAppStore } from "../store/appStore";
import { getAlarmState } from "./alarm";
import type { AlarmCommandReply, AlarmServerEvent, CommandPayload } from "../types/alarm";

// Singleton connection manager, mirroring how utils/axiosClient.ts is a
// single shared REST client rather than something each component creates —
// there is only ever one alarm websocket for the whole app. useAlarmSocket
// (hooks/useAlarmSocket.ts) opens/closes it from the app shell; any
// component can import sendAlarmCommand directly to send a command.

let socket: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;
let reconnectAttempts = 0;
// Set to true only by disconnectAlarmSocket(), so onclose can tell an
// intentional disconnect (e.g. sign-out) apart from a dropped connection
// that should be retried.
let intentionallyClosed = false;

const MAX_BACKOFF_MS = 30_000;

function backoffDelay(): number {
  // 1s, 2s, 4s, 8s, ... capped at MAX_BACKOFF_MS.
  return Math.min(1000 * 2 ** reconnectAttempts, MAX_BACKOFF_MS);
}

function wsUrl(token: string): string {
  const httpBase = (import.meta.env.VITE_BACKEND_BASE_URL as string) || window.location.origin;
  const wsBase = httpBase.replace(/^http/, "ws");
  return `${wsBase}/api/v1/alarm/ws?token=${encodeURIComponent(token)}`;
}

// Event types the backend also writes to its history tables.
const HISTORY_EVENT_TYPES = new Set<AlarmServerEvent["type"]>([
  "armed_stay",
  "armed_away",
  "disarmed",
  "alarm_triggered",
  "alarm_restored",
  "alarm_panicked",
]);

// Re-syncs partitions/zones from the backend. Used after a command fails, to
// undo the optimistic UI update the command's sender already applied.
function resyncAlarmState(): void {
  getAlarmState()
    .then((snapshot) => useAppStore.getState().setAlarmSnapshot(snapshot))
    .catch((err) => console.error("Failed to resync alarm state", err));
}

// Handles a direct reply to a command this client sent.
function applyCommandReply(reply: AlarmCommandReply): void {
  const text =
    reply.error === "illegal_command" && "reason" in reply
      ? reply.reason ?? `The panel would reject "${reply.command}" right now.`
      : reply.error;
  useAppStore.getState().showPanelNotice("warning", text);
  resyncAlarmState();
}

// Applies one incoming server message to the store. See backend/alarm/events.py
// for the full contract each event type carries.
function applyServerEvent(event: AlarmServerEvent): void {
  const { setAlarmSnapshot, upsertPartition, upsertZone, trigger, setTrouble, showPanelNotice, bumpHistory } =
    useAppStore.getState();

  if (HISTORY_EVENT_TYPES.has(event.type)) bumpHistory();

  switch (event.type) {
    case "state_snapshot":
      // Full refresh — e.g. right after the plugin reconnects to the panel.
      setAlarmSnapshot({ partitions: event.partitions, zones: event.zones });
      break;

    case "armed_stay":
      upsertPartition({ partition_id: event.partition_id, state: "armed", is_armed: true, arm_mode: "stay" });
      break;
    case "armed_away":
      upsertPartition({ partition_id: event.partition_id, state: "armed", is_armed: true, arm_mode: "away" });
      break;
    case "disarmed":
      upsertPartition({ partition_id: event.partition_id, state: "disarmed", is_armed: false, arm_mode: null });
      break;
    case "alarm_triggered":
      upsertPartition({ partition_id: event.partition_id, state: "in_alarm" });
      if (event.zone_id !== undefined) {
        upsertZone({ zone_id: event.zone_id, in_alarm: true });
      }
      break;
    case "alarm_restored":
      if (event.zone_id !== undefined) {
        upsertZone({ zone_id: event.zone_id, in_alarm: false });
      }
      break;

    case "zone_open":
      // Only pass label through when the event actually carries one — an
      // explicit `label: undefined` key would overwrite a previously known
      // label when merged in upsertZone.
      upsertZone(
        event.label !== undefined
          ? { zone_id: event.zone_id, is_open: true, label: event.label }
          : { zone_id: event.zone_id, is_open: true }
      );
      break;
    case "zone_closed":
      upsertZone({ zone_id: event.zone_id, is_open: false });
      break;
    // zone_bypassed carries no field ZoneState (mirroring py-dsc-it100's
    // ZoneStatus) currently tracks, so there's nothing to merge here.

    case "alarm_panicked":
      if (event.panicked) {
        const panicType = event.panic_type === "fire" || event.panic_type === "auxiliary"
          ? event.panic_type
          : "panic";
        trigger(panicType);
      }
      break;

    case "trouble":
      setTrouble(event.trouble_type, !event.restored);
      showPanelNotice(
        event.restored ? "info" : "warning",
        `${troubleLabel(event.trouble_type)} trouble ${event.restored ? "restored" : "reported"}`
      );
      break;

    case "error":
      showPanelNotice("error", event.detail);
      resyncAlarmState();
      break;

    // "ready" / anything else: no store update needed today.
    default:
      break;
  }
}

// "ac_power" -> "AC power", "wireless_low_battery" -> "Wireless low battery".
export function troubleLabel(troubleType: string): string {
  const words = troubleType.split("_").map((w) => (w === "ac" || w === "tlm" || w === "ftc" ? w.toUpperCase() : w));
  const text = words.join(" ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

// Opens the alarm websocket if it isn't already open/connecting. No-op if
// there's no access token yet (caller should wait for sign-in).
export function connectAlarmSocket(): void {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }
  const token = useAppStore.getState().accessToken;
  if (!token) return;

  intentionallyClosed = false;
  // Captured locally so each handler can tell whether it still belongs to
  // the current connection — e.g. React StrictMode's mount/unmount/remount
  // can fire a stale onclose after a newer socket has already taken over;
  // without this guard that stale event would null out (or reconnect over)
  // the live socket and leave two connections open.
  const ws = new WebSocket(wsUrl(token));
  socket = ws;

  ws.onopen = () => {
    if (socket !== ws) return;
    reconnectAttempts = 0;
  };

  ws.onmessage = (message: MessageEvent<string>) => {
    if (socket !== ws) return;
    try {
      const data = JSON.parse(message.data) as AlarmServerEvent | AlarmCommandReply;
      if ("type" in data) applyServerEvent(data);
      else if ("error" in data) applyCommandReply(data);
    } catch (err) {
      console.error("Failed to parse alarm websocket message", err);
    }
  };

  ws.onclose = () => {
    if (socket !== ws) return;
    socket = null;
    if (intentionallyClosed) return;
    // Only keep retrying while the user is still signed in — a 401 from an
    // expired/invalid token would otherwise loop forever.
    if (!useAppStore.getState().accessToken) return;
    reconnectTimer = setTimeout(() => {
      reconnectAttempts += 1;
      connectAlarmSocket();
    }, backoffDelay());
  };

  ws.onerror = () => {
    // The browser follows this with a close event, which drives reconnect —
    // nothing to do here beyond letting onclose run.
  };
}

// Closes the alarm websocket and cancels any pending reconnect. Call on
// sign-out / app teardown.
export function disconnectAlarmSocket(): void {
  intentionallyClosed = true;
  if (reconnectTimer) {
    clearTimeout(reconnectTimer);
    reconnectTimer = null;
  }
  reconnectAttempts = 0;
  socket?.close();
  socket = null;
}

// Sends a command to the backend's alarm state machine (arm/disarm/panic/etc).
// Drops the command with a console warning if the socket isn't open — callers
// don't need to check readiness themselves.
export function sendAlarmCommand(payload: CommandPayload): void {
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    console.warn("Alarm websocket is not connected; dropping command", payload);
    return;
  }
  socket.send(JSON.stringify(payload));
}
