import type { AuthResponse } from "../../types/auth/AuthResponse";
import type { RefreshResponse } from "../../types/auth/RefreshResponse";

export interface IAuthAPIService {
    login(email: string, password: string): Promise<AuthResponse>;
    register(firstName: string, lastName: string, email: string, password: string, dateOfBirth: Date, gender: string, country: string, street: string, streetNumber: string): Promise<AuthResponse>;
    refresh(refreshToken: string): Promise<RefreshResponse>;
}