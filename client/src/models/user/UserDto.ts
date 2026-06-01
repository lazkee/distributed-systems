export interface UserDto {
    id: number;
    firstName: string;
    lastName: string;
    email: string;
    country: string;
    role: "Player" | "Moderator" | "Admin";
    profilePictureUrl?: string;
}
