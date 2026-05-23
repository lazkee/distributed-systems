import { isAxiosError } from "axios";
import { apiAxios as axios } from "../axiosInstance";
import type { IUsersAPIService } from "./IUsersAPIService";
import type { UserDto } from "../../models/user/UserDto";
import type { UserApi } from "../../mappers/user_mapper";
import { mapUserApiToDto, mapUserDtoToApi } from "../../mappers/user_mapper";
import type { UserResponse } from "../../types/user/UserResponse";

const API_URL: string = import.meta.env.VITE_API_URL + "/users";

export const usersApi: IUsersAPIService = {
  async getMe(token: string): Promise<UserResponse<UserDto>> {
    try {
      const res = await axios.get<UserResponse<UserApi>>(`${API_URL}/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      return {
        success: res.data.success,
        message: res.data.message,
        data: res.data.data ? mapUserApiToDto(res.data.data) : null,
      };
    } catch (error) {
      let message = "Failed to fetch user profile";
      if (isAxiosError(error)) {
        message = (error.response?.data as any)?.message || message;
      }

      return { success: false, message, data: null };
    }
  },

  async updateMe(
    token: string,
    updatedData: Partial<UserDto>
  ): Promise<UserResponse<UserDto>> {
    try {
      const payload = mapUserDtoToApi(updatedData);

      const res = await axios.patch<UserResponse<UserApi>>(
        `${API_URL}/me`,
        payload,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      return {
        success: res.data.success,
        message: res.data.message,
        data: res.data.data ? mapUserApiToDto(res.data.data) : null,
      };
    } catch (error) {
      let message = "Failed to update user profile";
      if (isAxiosError(error)) {
        message = (error.response?.data as any)?.message || message;
      }

      return { success: false, message, data: null };
    }
  },
};
