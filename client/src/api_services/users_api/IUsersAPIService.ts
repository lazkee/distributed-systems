import type { UserDto } from "../../models/user/UserDto";
import type { UserResponse } from "../../types/user/UserResponse";

export type ExportAttempt = {
    attempt_id: number;
    quiz_id: number;
    started_at: string | null;
    finished_at: string | null;
    score: number | null;
    time_taken_seconds: number | null;
    status: string;
};

export type ExportProfile = {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    country: string | null;
    role: string;
    consent_given_at: string | null;
    profile_picture_url: string | null;
};

export type ExportData = {
    profile: ExportProfile;
    quiz_attempts: ExportAttempt[];
};

export interface IUsersAPIService {
    getMe(): Promise<UserResponse<UserDto>>;
    updateMe(updatedData: Partial<UserDto>): Promise<UserResponse<UserDto>>;
    exportMyData(): Promise<UserResponse<ExportData>>;
}
