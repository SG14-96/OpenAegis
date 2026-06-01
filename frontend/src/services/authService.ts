import { useAppStore } from "../store/appStore";
import { loginRequest, logoutRequest } from "./auth";

export async function login(username: string, password: string): Promise<void> {
  const data = await loginRequest(username, password);
  useAppStore.getState().signIn(
    { access: data.access_token, refresh: data.refresh_token },
    { username } as User
  );
}

export async function logout(): Promise<void> {
  const { refreshToken, signOut } = useAppStore.getState();
  try {
    if (refreshToken) await logoutRequest(refreshToken);
  } catch {
    // always clear local state even if the network call fails
  }
  signOut();
}
