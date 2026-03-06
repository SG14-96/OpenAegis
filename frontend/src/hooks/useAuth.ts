import { useContext, useCallback } from "react";
import AuthContext from "../context/AuthContext";
import { loginRequest, logoutRequest } from "../services/auth";
import axiosClient from "../utils/axiosClient";

export const useAuth = () => {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error("useAuth must be used within AuthProvider");

    const login = useCallback(async (username: string, password: string) => {
        const data = await loginRequest(username, password);
        // data: { access_token, refresh_token, token_type }
        ctx.signIn({ access: data.access_token, refresh: data.refresh_token }, { username });
        return data;
    }, [ctx]);

    const logout = useCallback(async () => {
        try {
            if (ctx.refreshToken) {
                await logoutRequest(ctx.refreshToken);
            }
        } catch (err) {
            // ignore network errors during logout but proceed to clear local state
            console.warn("logout request failed", err);
        }
        ctx.signOut();
    }, [ctx]);

    return {
        user: ctx.user,
        accessToken: ctx.accessToken,
        refreshToken: ctx.refreshToken,
        isAuthenticated: ctx.isAuthenticated,
        signIn: ctx.signIn,
        signOut: ctx.signOut,
        login,
        logout,
        axios: axiosClient,
    };
};

export default useAuth;
