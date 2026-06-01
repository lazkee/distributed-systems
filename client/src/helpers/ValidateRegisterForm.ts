import type { ValidationResult } from "../types/validation/ValidationResult";

export function validateRegisterForm(
  firstName: string,
  lastName: string,
  email: string,
  password: string,
  privacyPolicyAccepted: boolean
): ValidationResult {

  if (!privacyPolicyAccepted) {
    return { success: false, message: "You must accept the privacy policy to register." };
  }

  if (firstName.length < 3 || firstName.length > 20) {
    return { success: false, message: "First name must be 3–20 characters long." };
  }

  if (lastName.length < 3 || lastName.length > 20) {
    return { success: false, message: "Last name must be 3–20 characters long." };
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return { success: false, message: "Invalid email format." };
  }

  const passwordRe = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$/;
  if (!passwordRe.test(password)) {
    return {
      success: false,
      message:
        "Password must be at least 12 characters and include an uppercase letter, a lowercase letter, a digit, and a special character.",
    };
  }

  return { success: true };
}