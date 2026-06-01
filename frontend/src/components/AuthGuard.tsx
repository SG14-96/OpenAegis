import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAppStore } from "../store/appStore";

const PUBLIC_PATHS = ["/signin"];

export function AuthGuard() {
  const isAuthenticated = useAppStore((s) => !!s.accessToken);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    if (!isAuthenticated && !PUBLIC_PATHS.includes(location.pathname)) {
      navigate("/signin", { replace: true });
    }
  }, [isAuthenticated, location.pathname, navigate]);

  return null;
}
