import type { ProfileFormState } from "../types/user/ProfileFormState";

export const validateChangeProfileDataForm = (form: ProfileFormState) => {
  const errors: Partial<Record<keyof ProfileFormState, string>> = {};

  if (!form.firstName.trim()) errors.firstName = "First name is required";
  if (form.firstName.length < 3) errors.firstName = "First name is too short";
  if (!form.lastName.trim()) errors.lastName = "Last name is required";
  if (form.lastName.length < 3) errors.lastName = "Last name is too short";

  if (!form.email.trim()) {
    errors.email = "Email is required";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = "Invalid email address";
  }

  if (!form.country) errors.country = "Country is required";
  if (form.country && form.country.length > 50) errors.country = "Country is too long";
  if (form.country && form.country.length < 2) errors.country = "Country is too short";

  return errors;
};
