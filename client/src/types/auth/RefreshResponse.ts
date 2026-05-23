export type RefreshResponse = {
    success: boolean;
    message: string;
    data?: {
        access_token: string;
    };
}
