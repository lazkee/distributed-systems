import { createContext, useContext, useEffect } from "react";
import { socket } from "../sockets/socket";
import { useAuth } from "../hooks/UseAuthHook";
import { authApi } from "../api_services/auth_api/AuthAPIService";

const SocketContext = createContext(socket);

export const SocketProvider = ({ children }: { children: React.ReactNode }) => {
    const { user } = useAuth();

    useEffect(() => {
        if (!user) {
            if (socket.connected) {
                socket.disconnect();
            }
            return;
        }

        const handleConnect = () => {
            if (user.role === "Admin") {
                socket.emit("join", "admins");
            }
            if (user.role === "Moderator") {
                socket.emit("join", `user_${user.id}`);
            }
        };

        socket.on("connect", handleConnect);

        let cancelled = false;

        authApi.getWebSocketToken().then(result => {
            if (cancelled) return;
            if (!result.success || !result.data?.ws_token) return;
            socket.auth = { token: result.data.ws_token };
            if (!socket.connected) {
                socket.connect();
            }
        });

        return () => {
            cancelled = true;
            socket.off("connect", handleConnect);
            socket.disconnect();
        };
    }, [user]);

    return (
        <SocketContext.Provider value={socket}>
            {children}
        </SocketContext.Provider>
    );
};

export const useSocket = () => useContext(SocketContext);
