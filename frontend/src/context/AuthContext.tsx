import { createContext, useState, useEffect, type ReactNode } from "react";

type User = {
    username: string;
    email?: string;
};

type AuthContextType = {
    user: User | null;
    accessToken: string | null;
    refreshToken: string | null;
    signIn: (tokens: { access: string; refresh?: string }, user?: User) => void;
    signOut: () => void;
    isAuthenticated: boolean;
};

const AuthContext = createContext<AuthContextType | undefined>(undefined);

import { ACCESS_KEY, REFRESH_KEY, USER_KEY } from "./authKeys";

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [accessToken, setAccessToken] = useState<string | null>(null);
    const [refreshToken, setRefreshToken] = useState<string | null>(null);
    const [user, setUser] = useState<User | null>(null);

    useEffect(() => {
        // load from storage on mount
        const a = localStorage.getItem(ACCESS_KEY);
        const r = localStorage.getItem(REFRESH_KEY);
        const u = localStorage.getItem(USER_KEY);
        if (a) setAccessToken(a);
        if (r) setRefreshToken(r);
        if (u) {
            try {
                setUser(JSON.parse(u));
            } catch {
                setUser(null);
            }
        }
    }, []);

    const signIn = (tokens: { access: string; refresh?: string }, u?: User) => {
        setAccessToken(tokens.access);
        localStorage.setItem(ACCESS_KEY, tokens.access);
        if (tokens.refresh) {
            setRefreshToken(tokens.refresh);
            localStorage.setItem(REFRESH_KEY, tokens.refresh);
        }
        if (u) {
            setUser(u);
            localStorage.setItem(USER_KEY, JSON.stringify(u));
        }
    };

    const signOut = () => {
        setAccessToken(null);
        setRefreshToken(null);
        setUser(null);
        localStorage.removeItem(ACCESS_KEY);
        localStorage.removeItem(REFRESH_KEY);
        localStorage.removeItem(USER_KEY);
    };

    const revoke = () => {
        // convenience: clear and optionally call logout endpoint from services
        signOut();
    };

    const value: AuthContextType = {
        user,
        accessToken,
        refreshToken,
        signIn,
        signOut: revoke,
        isAuthenticated: !!accessToken,
    };

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
