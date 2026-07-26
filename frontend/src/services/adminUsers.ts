import axios from "../utils/axiosClient";

const API_BASE = "/api/v1/admin/users";

export async function listUsers(): Promise<User[]> {
  const res = await axios.get(`${API_BASE}/`);
  return res.data;
}

export async function updateUser(
  userUuid: string,
  update: {
    username?: string;
    email?: string;
    full_name?: string;
    disabled?: boolean;
  }
): Promise<User> {
  const res = await axios.put(`${API_BASE}/${userUuid}`, update);
  return res.data;
}

export async function disableUser(userUuid: string): Promise<User> {
  const res = await axios.patch(`${API_BASE}/${userUuid}/disable`);
  return res.data;
}

// There's no dedicated "enable" endpoint on the backend — re-enabling
// goes through the generic update endpoint with disabled: false.
export async function enableUser(userUuid: string): Promise<User> {
  return updateUser(userUuid, { disabled: false });
}

export async function deleteUser(userUuid: string): Promise<void> {
  await axios.delete(`${API_BASE}/${userUuid}`);
}
