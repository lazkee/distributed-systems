import axios, { type InternalAxiosRequestConfig } from "axios";
import { ReadValueByKey, SaveValueByKey, DeleteValueByKey } from "../helpers/LocalStorage";

const API_URL = import.meta.env.VITE_API_URL + "/auth";

export const apiAxios = axios.create();

type RetryAxiosRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean };

let isRefreshing = false;
let pendingQueue: Array<{ resolve: (token: string) => void; reject: (err: unknown) => void }> = [];

let tokenRefreshCallback: ((newToken: string | null) => void) | null = null;

export function registerTokenRefreshCallback(callback: (newToken: string | null) => void): void {
    tokenRefreshCallback = callback;
}

function drainQueue(error: unknown, token: string | null): void {
    pendingQueue.forEach(({ resolve, reject }) => {
        if (error) {
            reject(error);
        } else {
            resolve(token!);
        }
    });
    pendingQueue = [];
}

apiAxios.interceptors.response.use(
    response => response,
    async error => {
        const originalRequest = error.config as RetryAxiosRequestConfig | undefined;

        if (
            !originalRequest ||
            error.response?.status !== 401 ||
            originalRequest._retry ||
            originalRequest.url?.includes("/auth/refresh")
        ) {
            return Promise.reject(error);
        }

        if (isRefreshing) {
            return new Promise<string>((resolve, reject) => {
                pendingQueue.push({ resolve, reject });
            }).then(newToken => {
                originalRequest.headers.Authorization = `Bearer ${newToken}`;
                return apiAxios(originalRequest);
            }).catch(err => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        const refreshToken = ReadValueByKey("refreshToken");

        if (!refreshToken) {
            DeleteValueByKey("authToken");
            DeleteValueByKey("refreshToken");
            tokenRefreshCallback?.(null);
            isRefreshing = false;
            drainQueue(error, null);
            return Promise.reject(error);
        }

        try {
            const res = await axios.post(
                `${API_URL}/refresh`,
                undefined,
                { headers: { Authorization: `Bearer ${refreshToken}` } }
            );

            const newAccessToken: string = res.data?.data?.access_token;
            if (!newAccessToken) throw new Error("No access token in refresh response");

            SaveValueByKey("authToken", newAccessToken);
            tokenRefreshCallback?.(newAccessToken);
            drainQueue(null, newAccessToken);

            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
            return apiAxios(originalRequest);
        } catch (refreshError) {
            DeleteValueByKey("authToken");
            DeleteValueByKey("refreshToken");
            tokenRefreshCallback?.(null);
            drainQueue(refreshError, null);
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    }
);
