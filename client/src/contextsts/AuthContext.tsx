import React, { createContext, useState, useEffect, type ReactNode } from 'react';
import type { AuthContextType } from '../types/auth/AuthContext';
import type { AuthUser } from '../types/auth/AuthUser';
import { usersApi } from '../api_services/users_api/UsersAPIService';
import { apiAxios, registerRefreshFailureCallback } from '../api_services/axiosInstance';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<AuthUser | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        registerRefreshFailureCallback(() => {
            setUser(null);
        });
    }, []);

    useEffect(() => {
        const init = async () => {
            try {
                const result = await usersApi.getMe();
                if (result.success && result.data) {
                    setUser({ id: result.data.id, email: result.data.email, role: result.data.role });
                }
            } catch {
                // 401 or network error means no valid session
            } finally {
                setIsLoading(false);
            }
        };
        init();
    }, []);

    const login = async (): Promise<void> => {
        try {
            const result = await usersApi.getMe();
            if (result.success && result.data) {
                setUser({ id: result.data.id, email: result.data.email, role: result.data.role });
            }
        } catch {
            setUser(null);
        }
    };

    const logout = async (): Promise<void> => {
        const apiUrl = import.meta.env.VITE_API_URL;
        await Promise.allSettled([
            apiAxios.post(`${apiUrl}/auth/logout`),
            apiAxios.post(`${apiUrl}/auth/refresh/logout`),
        ]);
        setUser(null);
    };

    const isAuthenticated = !!user;

    const value: AuthContextType = {
        user,
        login,
        logout,
        isAuthenticated,
        isLoading,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;
