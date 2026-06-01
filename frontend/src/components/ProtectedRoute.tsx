import { Navigate } from "react-router-dom";
import { useAppStore } from "../store/appStore";
import type { JSX } from "react/jsx-dev-runtime";

type Props = {
  children: JSX.Element;
};

export default function ProtectedRoute({ children }: Props) {
  const isAuthenticated = useAppStore((s) => !!s.accessToken);
  if (!isAuthenticated) {
    return <Navigate to="/signin" replace />;
  }
  return children;
}
