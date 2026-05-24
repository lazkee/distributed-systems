import type { AuthUser } from "./AuthUser";

export type AuthContextType = {
    user: AuthUser | null;
    login: () => Promise<void>;
    logout: () => Promise<void>;
    isAuthenticated: boolean;
    isLoading: boolean;
}
