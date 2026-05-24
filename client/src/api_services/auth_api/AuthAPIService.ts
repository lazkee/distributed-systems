import axios from "axios";
import { apiAxios } from "../axiosInstance";
import type { IAuthAPIService, WsTokenResponse } from "./IAuthAPIService";
import type { AuthResponse } from "../../types/auth/AuthResponse";

const API_URL: string = import.meta.env.VITE_API_URL + "/auth";

export const authApi: IAuthAPIService = {
    async login(email: string, password: string): Promise<AuthResponse> {
        try {
            const res = await axios.post<AuthResponse>(
                `${API_URL}/login`,
                { email, password },
                { withCredentials: true }
            );
            return res.data;
        } catch (error) {
            let message = "Login error";
            if (axios.isAxiosError(error))
                message = error.response?.data?.message || message;
            return { success: false, message };
        }
    },

    async register(firstName: string, lastName: string, email: string, password: string, dateOfBirth: Date, gender: string, country: string, street: string, streetNumber: string): Promise<AuthResponse> {
        try {
            const payload = {
                first_name: firstName,
                last_name: lastName,
                email,
                password,
                date_of_birth: dateOfBirth.toISOString().split("T")[0],
                gender,
                country,
                street,
                street_number: streetNumber,
            };
            const res = await axios.post<AuthResponse>(
                `${API_URL}/register`,
                payload,
                { withCredentials: true }
            );
            return res.data;
        } catch (error) {
            let message = "Register error";
            if (axios.isAxiosError(error))
                message = error.response?.data?.message || message;
            return { success: false, message };
        }
    },

    async getWebSocketToken(): Promise<WsTokenResponse> {
        try {
            const res = await apiAxios.get<WsTokenResponse>(`${API_URL}/ws-token`);
            return res.data;
        } catch (error) {
            let message = "Failed to get WebSocket token";
            if (axios.isAxiosError(error))
                message = error.response?.data?.message || message;
            return { success: false, message };
        }
    },
};
