import { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../../hooks/UseAuthHook";
import { validateRegisterForm } from "../../helpers/ValidateRegisterForm";
import type { AuthFormProps } from "../../types/auth/AuthFormProps";

export function RegisterForm({ authApi }: AuthFormProps) {
  const [firstName, setFirstName] = useState<string>("");
  const [lastName, setLastName] = useState<string>("");
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [dateOfBirth, setDateOfBirth] = useState<string>("");
  const [gender, setGender] = useState<string>("Male");
  const [country, setCountry] = useState<string>("Serbia");
  const [street, setStreet] = useState<string>("");
  const [streetNumber, setStreetNumber] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const { login } = useAuth();

  const applyRegisterForm = async (e: React.FormEvent) => {
    e.preventDefault();

    setErrorMessage("");

    const validationResult = validateRegisterForm(
      firstName,
      lastName,
      email,
      password,
      dateOfBirth,
      street,
      streetNumber
    );

    if (!validationResult.success) {
      setErrorMessage(validationResult.message ?? "Invalid data");
      return;
    }

    const authResult = await authApi.register(
      firstName,
      lastName,
      email,
      password,
      new Date(dateOfBirth),
      gender,
      country,
      street,
      streetNumber
    );

    console.log("Auth result:", authResult);

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
          Register
        </h1>

        <form onSubmit={applyRegisterForm} className="space-y-4">
          <input
            type="text"
            placeholder="First Name"
            value={firstName}
            min={3}
            max={20}
            required
            onChange={(e) => setFirstName(e.target.value)}
            className="w-full px-5 py-3 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150"
          />

          <input
            type="text"
            placeholder="Last Name"
            value={lastName}
            min={3}
            max={20}
            required
            onChange={(e) => setLastName(e.target.value)}
            className="w-full px-5 py-3 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150"
          />

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
            minLength={12}
            required
            onChange={(e) => setPassword(e.target.value)}
            className="w-full px-5 py-3 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150"
          />

          <div className="relative">
            <input
              type="date"
              value={dateOfBirth}
              required
              onChange={(e) => setDateOfBirth(e.target.value)}
              className="w-full px-5 py-3 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150 appearance-none cursor-pointer"
              style={{ colorScheme: 'dark' }}
            />
          </div>


          <select
            value={gender}
            onChange={(e) => setGender(e.target.value)}
            className="w-full px-5 py-3 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150">
            <option value="Male">Male</option>
            <option value="Female">Female</option>
          </select>


          <input
            type="text"
            placeholder="Country"
            value={country}
            min={3}
            max={20}
            required
            onChange={(e) => setCountry(e.target.value)}
            className="w-full px-5 py-3 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150"
          />

          <input
            type="text"
            placeholder="Street"
            value={street}
            min={3}
            max={20}
            required
            onChange={(e) => setStreet(e.target.value)}
            className="w-full px-5 py-3 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150"
          />

          <input
            type="text"
            placeholder="Street Number"
            value={streetNumber}
            min={3}
            max={20}
            required
            onChange={(e) => setStreetNumber(e.target.value)}
            className="w-full px-5 py-3 border border-gray-600 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150"
          />

          {errorMessage && (
            <p className="text-red-500 text-sm">{errorMessage}</p>
          )}

          <button
            type="submit"
            className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg shadow-md hover:shadow-lg transition-all duration-200"
          >
            Register
          </button>
        </form>

        <p className="mt-4 text-sm text-center text-gray-400">
          Already have an account?{" "}
          <Link
            to="/login"
            className="text-blue-400 font-medium hover:underline"
          >
            Login
          </Link>
        </p>
      </div>
    </div>
  );
}
