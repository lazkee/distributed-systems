import type { UserDto } from "../../models/user/UserDto";
import type { AdminReportResponse } from "../../types/admin/AdminReportResponse";
import type { AdminResponse } from "../../types/admin/AdminResponse";

export type PaginatedUsers = {
    items: UserDto[];
    page: number;
    page_size: number;
    total: number;
    pages: number;
};

export interface IAdminAPIService {
    listUsers(page: number, pageSize: number): Promise<AdminResponse<PaginatedUsers>>;
    changeUserRole(userId: string, newRole: string): Promise<AdminResponse<UserDto>>;
    deleteUser(userId: string): Promise<AdminResponse<null>>;
    generateReport(quiz_ids: number[]): Promise<AdminReportResponse>;
}
