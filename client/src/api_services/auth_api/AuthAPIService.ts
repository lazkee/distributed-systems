import axios from "axios";
import type { IAuthAPIService } from "./IAuthAPIService";
import type { AuthResponse } from "../../types/auth/AuthResponse";
import type { RefreshResponse } from "../../types/auth/RefreshResponse";

const API_URL: string = import.meta.env.VITE_API_URL + "/auth";

export const authApi: IAuthAPIService = {
    async login(email: string, password: string): Promise<AuthResponse> {
        try {
            const res = await axios.post<AuthResponse>(`${API_URL}/login`, { email, password });
            return res.data;
        } catch (error) {
            let message: string = "Login error";
            if (axios.isAxiosError(error))
                message = error.response?.data?.message || message;

            return {
                success: false,
                message: message,
                data: undefined
            };
        }
    },

    async register(firstName: string, lastName: string, email: string, password: string, dateOfBirth: Date, gender: string, country: string, street: string, streetNumber: string): Promise<AuthResponse> {
        try {
            const payload = {
                first_name: firstName,
                last_name: lastName,
                email: email,
                password: password,
                date_of_birth: dateOfBirth.toISOString().split("T")[0], // "YYYY-MM-DD"
                gender: gender,
                country: country,
                street: street,
                street_number: streetNumber
            };

            //console.log("I am sending the payload: ", payload);

            const res = await axios.post<AuthResponse>(`${API_URL}/register`, payload);
            return res.data;
        } catch (error) {
            let message: string = "Register error";
            if (axios.isAxiosError(error))
                message = error.response?.data?.message || message;

            return {
                success: false,
                message: message,
                data: undefined
            };
        }
    },

    async refresh(refreshToken: string): Promise<RefreshResponse> {
        try {
            const res = await axios.post<RefreshResponse>(
                `${API_URL}/refresh`,
                undefined,
                { headers: { Authorization: `Bearer ${refreshToken}` } }
            );
            return res.data;
        } catch (error) {
            let message: string = "Refresh error";
            if (axios.isAxiosError(error))
                message = error.response?.data?.message || message;

            return {
                success: false,
                message: message,
                data: undefined
            };
        }
    }
}