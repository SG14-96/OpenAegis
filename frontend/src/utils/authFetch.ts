import { REFRESH_KEY, ACCESS_KEY } from "../context/authKeys";
import { refreshRequest } from "../services/auth";

async function getAccessToken() {
    return localStorage.getItem(ACCESS_KEY);
}

async function getRefreshToken() {
    return localStorage.getItem(REFRESH_KEY);
}

function setAccessToken(token: string) {
    localStorage.setItem(ACCESS_KEY, token);
}

export async function authFetch(input: RequestInfo, init: RequestInit = {}) {
    let accessToken = await getAccessToken();

    const headers = new Headers(init.headers || {});
    if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

    let res = await fetch(input, { ...init, headers });

    if (res.status === 401) {
        // Try refresh
        const refreshToken = await getRefreshToken();
        if (refreshToken) {
            try {
                const data = await refreshRequest(refreshToken);
                if (data && data.access_token) {
                    setAccessToken(data.access_token);
                    // retry original request with new token
                    const retryHeaders = new Headers(init.headers || {});
                    retryHeaders.set("Authorization", `Bearer ${data.access_token}`);
                    res = await fetch(input, { ...init, headers: retryHeaders });
                    return res;
                }
            } catch (e) {
                // refresh failed, fall through and return original 401
                console.warn("Token refresh failed", e);
            }
        }
    }
    return res;
}

export default authFetch;
