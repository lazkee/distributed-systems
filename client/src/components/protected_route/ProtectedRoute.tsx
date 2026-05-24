import React from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../hooks/UseAuthHook";

type ProtectedRouteProps = {
    children: React.ReactNode;
    requiredRole: string;
    redirectTo?: string;
};

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole, redirectTo = "/login" }) => {
    const { isAuthenticated, user, isLoading, logout } = useAuth();
    const location = useLocation();

    if (isLoading) {
        return (
            <h1 className="text-center text-gray-400 text-lg mt-10 animate-pulse">
                Loading...
            </h1>
        );
    }

    if (!isAuthenticated) {
        return <Navigate to={redirectTo} state={{ from: location }} replace />;
    }

    if (requiredRole && user?.role !== requiredRole) {
        return (
            <main className="min-h-screen flex items-center justify-center bg-gray-900 p-6">
                <div className="bg-gray-800/90 backdrop-blur-sm p-8 rounded-2xl shadow-2xl text-center text-gray-100 max-w-md">
                    <h2 className="text-2xl font-bold mb-4">Access denied</h2>
                    <p className="mb-6 text-gray-300">
                        Required role: <span className="font-semibold">{`"${requiredRole}"`}</span>
                    </p>
                    <button
                        onClick={logout}
                        className="px-6 py-2 bg-rose-700 hover:bg-rose-600 rounded-lg font-medium shadow-md hover:shadow-lg transition-all duration-200"
                    >
                        Log out
                    </button>
                </div>
            </main>
        );
    }

    return <>{children}</>;
};
