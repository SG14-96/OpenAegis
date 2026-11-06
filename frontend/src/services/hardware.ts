import axios from "../utils/axiosClient";

const API_BASE = "/api/v1/hardware";

export interface SerialPortInfo {
  device: string;
  description: string | null;
  vid: number | null;
  pid: number | null;
}

// Serial ports visible to the backend host (not the browser's machine).
export async function listSerialPorts(): Promise<SerialPortInfo[]> {
  const res = await axios.get(`${API_BASE}/ports`);
  return res.data.serial_ports;
}
