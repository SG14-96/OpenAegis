import { Navigate } from "react-router-dom";
import useAuth from "../hooks/useAuth";
import type { JSX } from "react/jsx-dev-runtime";

type Props = {
    children: JSX.Element;
};

export default function ProtectedRoute({ children }: Props) {
    const { isAuthenticated } = useAuth();
    if (!isAuthenticated) {
        return <Navigate to="/signin" replace />;
    }
    return children;
}
