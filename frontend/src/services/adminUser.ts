import axios from "axios";

const API_BASE = "/api/v1/admin/users";

export async function getAllUsers() {
  const res = await axios.get(`${API_BASE}/all`);
  return res.data;
}

export async function createUser(newUserData: {
  username: string;
  email: string;
  password: string;
}): Promise<any> {
  const res = await axios.post(`${API_BASE}/create`, newUserData);
  return res.data;
}

export async function updateUser(
  userID: number,
  updatedUserData: { username?: string; email?: string; is_active?: boolean }
): Promise<any> {
  const res = await axios.put(`${API_BASE}/${userID}`, updatedUserData);
  return res.data;
}

export async function changeUserPassword(
  userID: number,
  passwordData: { new_password: string }
): Promise<any> {
  const res = await axios.put(`${API_BASE}/${userID}/password`, passwordData);
  return res.data;
}

export async function deleteUser(
  userID: number,
  newAdminID: number
): Promise<any> {
  const res = await axios.delete(`${API_BASE}/${userID}`, {
    data: { new_admin_id: newAdminID },
  });
  return res.data;
}
