import React, { createContext, useState, useEffect, type ReactNode } from 'react';
import { jwtDecode } from 'jwt-decode';
import type { AuthContextType } from '../types/auth/AuthContext';
import type { JwtTokenClaims } from '../types/auth/JwtTokenClaims';
import type { AuthUser } from '../types/auth/AuthUser';
import { DeleteValueByKey, ReadValueByKey, SaveValueByKey } from '../helpers/LocalStorage';
import { authApi } from '../api_services/auth_api/AuthAPIService';

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const decodeJWT = (token: string): JwtTokenClaims | null => {
    try {
        const decoded: any = jwtDecode(token);

        if (!decoded.sub) return null;

        return {
            id: parseInt(decoded.sub), // sub is now a string
            email: decoded.email,      // from additional_claims
            role: decoded.role          // from additional_claims
        };
    } catch (error) {
        console.error('Error while decoding JWT token: ', error);
        return null;
    }
};

const isTokenExpired = (token: string): boolean => {
    try {
        const decoded = jwtDecode(token);
        const currentTime = Date.now() / 1000;

        return decoded.exp ? decoded.exp < currentTime : false;
    } catch {
        return true;
    }
};

export const AuthProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
    const [user, setUser] = useState<AuthUser | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    const applyToken = (newToken: string): boolean => {
        const claims = decodeJWT(newToken);
        if (!claims || isTokenExpired(newToken)) return false;
        setToken(newToken);
        setUser({ id: claims.id, email: claims.email, role: claims.role });
        SaveValueByKey("authToken", newToken);
        return true;
    };

    useEffect(() => {
        const init = async () => {
            const savedToken = ReadValueByKey("authToken");
            const savedRefreshToken = ReadValueByKey("refreshToken");

            if (savedToken && !isTokenExpired(savedToken)) {
                applyToken(savedToken);
                setIsLoading(false);
                return;
            }

            if (savedRefreshToken && !isTokenExpired(savedRefreshToken)) {
                const result = await authApi.refresh(savedRefreshToken);
                if (result.success && result.data?.access_token) {
                    applyToken(result.data.access_token);
                    setIsLoading(false);
                    return;
                }
            }

            DeleteValueByKey("authToken");
            DeleteValueByKey("refreshToken");
            setIsLoading(false);
        };

        init();
    }, []);

    const login = (newToken: string) => {
        if (!applyToken(newToken)) {
            console.error('Invalid or expired token');
        }
    };

    const logout = async () => {
        const accessToken = ReadValueByKey("authToken");
        const refreshToken = ReadValueByKey("refreshToken");
        const apiUrl = import.meta.env.VITE_API_URL;

        const requests: Promise<Response>[] = [];

        if (accessToken) {
            requests.push(
                fetch(`${apiUrl}/auth/logout`, {
                    method: "POST",
                    headers: { Authorization: `Bearer ${accessToken}` },
                })
            );
        }

        if (refreshToken) {
            requests.push(
                fetch(`${apiUrl}/auth/logout-refresh`, {
                    method: "POST",
                    headers: { Authorization: `Bearer ${refreshToken}` },
                })
            );
        }

        await Promise.allSettled(requests);

        setToken(null);
        setUser(null);
        DeleteValueByKey("authToken");
        DeleteValueByKey("refreshToken");
    };

    const isAuthenticated = !!user && !!token;

    const value: AuthContextType = {
        user,
        token,
        login,
        logout,
        isAuthenticated,
        isLoading
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export default AuthContext;