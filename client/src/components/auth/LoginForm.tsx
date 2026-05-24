import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/UseAuthHook";
import type { AuthFormProps } from "../../types/auth/AuthFormProps";

export function LoginForm({ authApi }: AuthFormProps) {
    const [email, setEmail] = useState<string>("");
    const [password, setPassword] = useState<string>("");
    const [errorMessage, setErrorMessage] = useState<string>("");
    const { login } = useAuth();

    const applyLoginForm = async (e: React.FormEvent) => {
        e.preventDefault();

        const authResult = await authApi.login(email, password);
        if (authResult.success) {
            await login();
        } else {
            setErrorMessage(authResult.message);
            setPassword("");
        }
    };

    return (
        <div className="flex items-center justify-center min-h-screen bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900">
            <div className="w-full max-w-md p-6 bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-700">
                <h1 className="text-2xl font-bold text-gray-100 text-center mb-6">
                    Login
                </h1>

                <form onSubmit={applyLoginForm} className="space-y-4">
                    <input
                        type="text"
                        placeholder="Email"
                        value={email}
                        min={3}
                        max={20}
                        required
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full px-5 py-3 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150"
                    />

                    <input
                        type="password"
                        placeholder="Password"
                        value={password}
                        min={6}
                        max={20}
                        required
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full px-5 py-3 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150"
                    />

                    {errorMessage && (
                        <p className="text-red-500 text-sm whitespace-pre-line">{errorMessage}</p>
                    )}

                    <button
                        type="submit"
                        className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200"
                    >
                        Login
                    </button>
                </form>

                <p className="mt-4 text-sm text-center text-gray-400">
                    New user?{" "}
                    <Link to="/register" className="text-blue-400 font-medium hover:underline">
                        Register
                    </Link>
                </p>
            </div>
        </div>
    );
}
