import type { UserDto } from "../models/user/UserDto";

export type UserApi = {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  country: string | null;
  role: "Player" | "Moderator" | "Admin";
  profile_picture_url?: string | null;
};

export const mapUserApiToDto = (u: UserApi): UserDto => ({
  id: u.id,
  firstName: u.first_name,
  lastName: u.last_name,
  email: u.email,
  country: u.country ?? "",
  role: u.role,
  profilePictureUrl: u.profile_picture_url ?? undefined,
});

export const mapUserDtoToApi = (
  dto: Partial<UserDto>
): Record<string, unknown> => ({
  ...(dto.firstName !== undefined && { first_name: dto.firstName }),
  ...(dto.lastName !== undefined && { last_name: dto.lastName }),
  ...(dto.email !== undefined && { email: dto.email }),
  ...(dto.country !== undefined && { country: dto.country }),
});
