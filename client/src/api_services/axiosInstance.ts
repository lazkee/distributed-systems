import axios, { type InternalAxiosRequestConfig } from "axios";

const API_URL = import.meta.env.VITE_API_URL + "/auth";

export const apiAxios = axios.create({ withCredentials: true });

type RetryAxiosRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean };

let isRefreshing = false;
let pendingQueue: Array<{ resolve: () => void; reject: (err: unknown) => void }> = [];

let onRefreshFailure: (() => void) | null = null;

export function registerRefreshFailureCallback(callback: () => void): void {
    onRefreshFailure = callback;
}

function getCookie(name: string): string | null {
    const match = document.cookie.match(new RegExp("(?:^|; )" + name + "=([^;]*)"));
    return match ? decodeURIComponent(match[1]) : null;
}

function drainQueue(error: unknown): void {
    pendingQueue.forEach(({ resolve, reject }) => {
        if (error) reject(error);
        else resolve();
    });
    pendingQueue = [];
}

const STATE_CHANGING_METHODS = new Set(["post", "put", "patch", "delete"]);

apiAxios.interceptors.request.use(config => {
    const method = config.method?.toLowerCase() ?? "";
    if (STATE_CHANGING_METHODS.has(method)) {
        const isRefreshEndpoint = config.url?.includes("/auth/refresh");
        const csrfToken = isRefreshEndpoint
            ? getCookie("csrf_refresh_token")
            : getCookie("csrf_access_token");
        if (csrfToken) {
            config.headers["X-CSRF-TOKEN"] = csrfToken;
        }
    }
    return config;
});

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
            return new Promise<void>((resolve, reject) => {
                pendingQueue.push({ resolve, reject });
            })
                .then(() => apiAxios(originalRequest))
                .catch(err => Promise.reject(err));
        }

        originalRequest._retry = true;
        isRefreshing = true;

        try {
            const csrfToken = getCookie("csrf_refresh_token");
            await axios.post(
                `${API_URL}/refresh`,
                undefined,
                {
                    withCredentials: true,
                    headers: csrfToken ? { "X-CSRF-TOKEN": csrfToken } : {},
                }
            );

            drainQueue(null);
            return apiAxios(originalRequest);
        } catch (refreshError) {
            onRefreshFailure?.();
            drainQueue(refreshError);
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    }
);
