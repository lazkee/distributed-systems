import { isAxiosError } from "axios";
import { apiAxios as axios } from "../axiosInstance";
import type { IAdminAPIService, PaginatedUsers } from "./IAdminAPIService";
import type { AdminResponse } from "../../types/admin/AdminResponse";
import type { UserDto } from "../../models/user/UserDto";
import type { AdminReportResponse } from "../../types/admin/AdminReportResponse";

const API_URL: string = import.meta.env.VITE_API_URL + "/admin";

export const adminApi: IAdminAPIService = {
    async listUsers(page: number, pageSize: number): Promise<AdminResponse<PaginatedUsers>> {
        try {
            const res = await axios.get<AdminResponse<PaginatedUsers>>(
                `${API_URL}/users`,
                { params: { page, page_size: pageSize } }
            );
            return res.data;
        } catch (error) {
            let message = "Failed to fetch users";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: null };
        }
    },

    async changeUserRole(userId: string, newRole: string): Promise<AdminResponse<UserDto>> {
        try {
            const res = await axios.post<AdminResponse<UserDto>>(
                `${API_URL}/change-role`,
                { user_id: userId, new_role: newRole }
            );
            return res.data;
        } catch (error) {
            let message = "Failed to change user role";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: null };
        }
    },

    async deleteUser(userId: string): Promise<AdminResponse<null>> {
        try {
            const res = await axios.delete<AdminResponse<null>>(`${API_URL}/delete-user/${userId}`);
            return res.data;
        } catch (error) {
            let message = "Failed to delete user";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: null };
        }
    },

    async generateReport(quiz_ids: number[]): Promise<AdminReportResponse> {
        try {
            const res = await axios.post<AdminReportResponse>(`${API_URL}/report`, { quiz_ids });
            return res.data;
        } catch (error) {
            let message = "Failed to generateReport";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message };
        }
    },
};
