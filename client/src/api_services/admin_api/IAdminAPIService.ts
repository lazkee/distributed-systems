import type { UserDto } from "../../models/user/UserDto";
import type { AdminReportResponse } from "../../types/admin/AdminReportResponse";
import type { AdminResponse } from "../../types/admin/AdminResponse";

export interface IAdminAPIService {
    listUsers(): Promise<AdminResponse<UserDto[]>>;
    changeUserRole(userId: string, newRole: string): Promise<AdminResponse<UserDto>>;
    deleteUser(userId: string): Promise<AdminResponse<null>>;
    generateReport(quiz_ids: number[]): Promise<AdminReportResponse>;
}
