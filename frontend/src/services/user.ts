import axios from "../utils/axiosClient";

const API_BASE = "/api/v1/users";

export async function getCurrentUser(): Promise<any> {
  const res = await axios.get(`${API_BASE}/me`);
  return res.data;
}

export async function updateUserSettings(userInformation: User): Promise<any> {
  const res = await axios.put(`${API_BASE}/me`, userInformation);
  return res.data;
}

export async function changeUserPassword(passwordData: {
  current_password: string;
  new_password: string;
}): Promise<any> {
  const res = await axios.put(`${API_BASE}/me/password`, passwordData);
  return res.data;
}

export async function deleteUserAccount(userUUID: string): Promise<any> {
  const res = await axios.delete(`${API_BASE}/${userUUID}`);
  return res.data;
}
