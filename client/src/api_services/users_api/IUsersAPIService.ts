import type { UserDto } from "../../models/user/UserDto";
import type { UserResponse } from "../../types/user/UserResponse";

export interface IUsersAPIService {
    getMe(): Promise<UserResponse<UserDto>>;
    updateMe(updatedData: Partial<UserDto>): Promise<UserResponse<UserDto>>;
}
