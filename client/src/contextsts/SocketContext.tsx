import { createContext, useContext, useEffect } from "react";
import { socket } from "../sockets/socket";
import { useAuth } from "../hooks/UseAuthHook";

const SocketContext = createContext(socket);

export const SocketProvider = ({ children }: { children: React.ReactNode }) => {
    const { user, token } = useAuth();

    useEffect(() => {
        if (!user || !token) {
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

        socket.auth = { token };

        if (!socket.connected) {
            socket.connect();
        }

        return () => {
            socket.off("connect", handleConnect);
            socket.disconnect();
        };
    }, [user, token]);

    return (
        <SocketContext.Provider value={socket}>
            {children}
        </SocketContext.Provider>
    );
};

export const useSocket = () => useContext(SocketContext);
