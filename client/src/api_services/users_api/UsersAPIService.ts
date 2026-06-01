import { isAxiosError } from "axios";
import { apiAxios as axios } from "../axiosInstance";
import type { IUsersAPIService, ExportData } from "./IUsersAPIService";
import type { UserDto } from "../../models/user/UserDto";
import type { UserApi } from "../../mappers/user_mapper";
import { mapUserApiToDto, mapUserDtoToApi } from "../../mappers/user_mapper";
import type { UserResponse } from "../../types/user/UserResponse";

const API_URL: string = import.meta.env.VITE_API_URL + "/users";

export const usersApi: IUsersAPIService = {
    async getMe(): Promise<UserResponse<UserDto>> {
        try {
            const res = await axios.get<UserResponse<UserApi>>(`${API_URL}/me`);
            return {
                success: res.data.success,
                message: res.data.message,
                data: res.data.data ? mapUserApiToDto(res.data.data) : null,
            };
        } catch (error) {
            let message = "Failed to fetch user profile";
            if (isAxiosError(error))
                message = (error.response?.data as any)?.message || message;
            return { success: false, message, data: null };
        }
    },

    async updateMe(updatedData: Partial<UserDto>): Promise<UserResponse<UserDto>> {
        try {
            const payload = mapUserDtoToApi(updatedData);
            const res = await axios.patch<UserResponse<UserApi>>(`${API_URL}/me`, payload);
            return {
                success: res.data.success,
                message: res.data.message,
                data: res.data.data ? mapUserApiToDto(res.data.data) : null,
            };
        } catch (error) {
            let message = "Failed to update user profile";
            if (isAxiosError(error))
                message = (error.response?.data as any)?.message || message;
            return { success: false, message, data: null };
        }
    },

    async exportMyData(): Promise<UserResponse<ExportData>> {
        try {
            const res = await axios.get<UserResponse<ExportData>>(`${API_URL}/me/export`);
            return {
                success: res.data.success,
                message: res.data.message,
                data: res.data.data ?? null,
            };
        } catch (error) {
            let message = "Failed to export data";
            if (isAxiosError(error))
                message = (error.response?.data as any)?.message || message;
            return { success: false, message, data: null };
        }
    },

    async eraseMyAccount(): Promise<UserResponse<null>> {
        try {
            const res = await axios.delete<UserResponse<null>>(`${API_URL}/me`);
            return { success: res.data.success, message: res.data.message, data: null };
        } catch (error) {
            let message = "Failed to erase account";
            if (isAxiosError(error))
                message = (error.response?.data as any)?.message || message;
            return { success: false, message, data: null };
        }
    },
};
