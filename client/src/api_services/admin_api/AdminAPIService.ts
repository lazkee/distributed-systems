import { isAxiosError } from "axios";
import { apiAxios as axios } from "../axiosInstance";
import type { IAdminAPIService } from "./IAdminAPIService";
import type { AdminResponse } from "../../types/admin/AdminResponse";
import type { UserDto } from "../../models/user/UserDto";
import type { AdminReportResponse } from "../../types/admin/AdminReportResponse";

const API_URL: string = import.meta.env.VITE_API_URL + "/admin";

export const adminApi: IAdminAPIService = {
    async listUsers(token: string): Promise<AdminResponse<UserDto[]>> {
        try {
            const res = await axios.get<AdminResponse<UserDto[]>>(
                `${API_URL}/users`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message = "Failed to fetch users";
            if (isAxiosError(error)) message = error.response?.data?.message || message;

            return { success: false, message, data: null };
        }
    },

    async changeUserRole(token: string, userId: string, newRole: string): Promise<AdminResponse<UserDto>> {
        try {
            const payload = { user_id: userId, new_role: newRole };
            const res = await axios.post<AdminResponse<UserDto>>(
                `${API_URL}/change-role`,
                payload,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message = "Failed to change user role";
            if (isAxiosError(error)) message = error.response?.data?.message || message;

            return { success: false, message, data: null };
        }
    },

    async deleteUser(token: string, userId: string): Promise<AdminResponse<null>> {
        try {
            const res = await axios.delete<AdminResponse<null>>(
                `${API_URL}/delete-user/${userId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            return res.data;
        } catch (error) {
            let message = "Failed to delete user";
            if (isAxiosError(error)) message = error.response?.data?.message || message;

            return { success: false, message, data: null };
        }
    },

    async generateReport(token: string, quiz_ids: number[]): Promise<AdminReportResponse> {
        try {
            const res = await axios.post<AdminReportResponse>(
                `${API_URL}/report`,
                {
                    quiz_ids,
                },
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            return res.data;
        } catch (error) {
            let message = "Failed to generateReport";
            if (isAxiosError(error)) message = error.response?.data?.message || message;

            return { success: false, message };
        }
    }
};