import { useAppStore } from "../store/appStore";
import { login, logout } from "../services/authService";

export const useAuth = () => ({
  user: useAppStore((s) => s.user),
  isAuthenticated: useAppStore((s) => !!s.accessToken),
  login,
  logout,
});

export default useAuth;
