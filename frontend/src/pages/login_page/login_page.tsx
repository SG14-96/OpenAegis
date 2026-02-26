import type React from "react";
import useAuth from "../../hooks/useAuth";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import UICard from "../../ui/card/ui_card";

export function DemoAuthControls() {
    const { isAuthenticated, user, login, logout } = useAuth();

    const handleLogin = async () => {
        try {
            await login("admin", "admin123");
        } catch (e) {
            console.error("Login failed", e);
            alert("Login failed: " + e);
        }
    };

    return (
        <UICard>
            <div style={{ marginTop: 12 }}>
                {isAuthenticated ? (
                    <>
                        <div>Signed in as: {user?.username}</div>
                        <button onClick={() => logout()}>Sign out</button>
                    </>
                ) : (
                    <div>
                        <p>Click the button below to sign in.</p>
                        
                        <button onClick={handleLogin}>Sign in (demo)</button>
                    </div>
                )}
            </div>
        </UICard>
    );
}

const LoginPage = (): React.ReactElement => {
    const { isAuthenticated } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        if (isAuthenticated) {
            navigate("/account", { replace: true });
        }
    }, [isAuthenticated, navigate]);

    return (
        <div>
            <DemoAuthControls />
        </div>
    );

}

export default LoginPage;