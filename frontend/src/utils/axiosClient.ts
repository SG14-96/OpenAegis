import axios from "axios";
import { ACCESS_KEY, REFRESH_KEY } from "../context/authKeys";
import { refreshRequest } from "../services/auth";

const client = axios.create({
    baseURL: (import.meta.env.VITE_BACKEND_BASE_URL as string) || "/",
    headers: { "Content-Type": "application/json" },
});

let isRefreshing = false;
let failedQueue: Array<any> = [];

const processQueue = (error: any, token: string | null = null) => {
    failedQueue.forEach((prom) => {
        if (error) {
            prom.reject(error);
        } else {
            prom.resolve(token);
        }
    });
    failedQueue = [];
};

client.interceptors.request.use((config) => {
    const token = localStorage.getItem(ACCESS_KEY);
    if (token) {
        config.headers = config.headers || {};
        config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
});

client.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;
        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            if (isRefreshing) {
                return new Promise(function (resolve, reject) {
                    failedQueue.push({ resolve, reject });
                })
                    .then((token) => {
                        originalRequest.headers["Authorization"] = `Bearer ${token}`;
                        return axios(originalRequest);
                    })
                    .catch((err) => Promise.reject(err));
            }

            originalRequest._retry = true;
            isRefreshing = true;

            const refreshToken = localStorage.getItem(REFRESH_KEY);
            if (!refreshToken) {
                isRefreshing = false;
                return Promise.reject(error);
            }

            try {
                const data = await refreshRequest(refreshToken);
                const newAccess = data.access_token;
                localStorage.setItem(ACCESS_KEY, newAccess);
                client.defaults.headers.common["Authorization"] = `Bearer ${newAccess}`;
                processQueue(null, newAccess);
                return client(originalRequest);
            } catch (err) {
                processQueue(err, null);
                // optionally clear tokens here
                localStorage.removeItem(ACCESS_KEY);
                localStorage.removeItem(REFRESH_KEY);
                isRefreshing = false;
                return Promise.reject(err);
            } finally {
                isRefreshing = false;
            }
        }
        return Promise.reject(error);
    }
);

export default client;
