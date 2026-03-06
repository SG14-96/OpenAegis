import axios from "../utils/axiosClient";

export async function loginRequest(username: string, password: string) {
    const body = new URLSearchParams();
    body.append("username", username);
    body.append("password", password);

    const res = await axios.post("/api/v1/auth/token", body.toString(), {
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    return res.data;
}

export async function refreshRequest(refreshToken: string) {
    const res = await axios.post("/api/v1/auth/refresh", { refresh_token: refreshToken });
    return res.data;
}

export async function logoutRequest(refreshToken: string) {
    const res = await axios.post("/api/v1/auth/logout", { refresh_token: refreshToken });
    return res.data;
}
