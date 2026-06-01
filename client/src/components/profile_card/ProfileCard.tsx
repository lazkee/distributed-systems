import { useEffect, useMemo, useState } from "react";
import type { CloudinaryImageResponse } from "../../types/cloudinary/CloudinaryImageResponse";
import type { UserDto } from "../../models/user/UserDto";
import type { ProfileFormState } from "../../types/user/ProfileFormState";
import type { ProfileCardProps } from "../../types/user/ProfileCardProps";
import { validateChangeProfileDataForm } from "../../helpers/ValidateChangeProfileDataForm";

export function ProfileCard({
  setShowProfile,
  cloudinaryApi,
  usersApi,
}: ProfileCardProps) {
  const [profile, setProfile] = useState<UserDto | null>(null);
  const [form, setForm] = useState<ProfileFormState>({
    firstName: "",
    lastName: "",
    email: "",
    country: "",
  });

  const [profilePicture, setProfilePicture] = useState<string>("");
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [loadingPicture, setLoadingPicture] = useState(false);
  const [saving, setSaving] = useState(false);
  const [exportingData, setExportingData] = useState(false);
  const [exportError, setExportError] = useState<string>("");
  const [error, setError] = useState<string>("");
  const [errors, setErrors] = useState<Partial<Record<keyof ProfileFormState, string>>>({});

  const hasChanges = useMemo(() => {
    if (!profile) return false;
    return (
      profile.firstName !== form.firstName ||
      profile.lastName !== form.lastName ||
      profile.email !== form.email ||
      profile.country !== form.country
    );
  }, [profile, form]);

  useEffect(() => {
    const fetchMe = async () => {
      setLoadingProfile(true);
      setError("");

      const res = await usersApi.getMe();
      if (!res.success || !res.data) {
        setError(res.message || "Failed to fetch profile");
        setProfile(null);
        setProfilePicture("");
        setLoadingProfile(false);
        return;
      }

      const dto = res.data;
      setProfile(dto);
      setProfilePicture(dto.profilePictureUrl ?? "");
      setForm({
        firstName: dto.firstName ?? "",
        lastName: dto.lastName ?? "",
        email: dto.email ?? "",
        country: dto.country ?? "",
      });
      setLoadingProfile(false);
    };

    fetchMe();
  }, [usersApi]);

  const onChange =
    (field: keyof ProfileFormState) =>
      (e: React.ChangeEvent<HTMLInputElement>) => {
        setForm((prev) => ({ ...prev, [field]: e.target.value }));
      };

  const handleChangePicture = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    setLoadingPicture(true);
    try {
      const res: CloudinaryImageResponse = await cloudinaryApi.addOrChangeImage(file);
      if (res.success) {
        setProfilePicture(res.data.url);
        setProfile((prev) => prev ? { ...prev, profilePictureUrl: res.data.url } : prev);
      } else {
        alert(res.message);
      }
    } catch (err) {
      console.error(err);
      alert("Failed to upload image");
    } finally {
      setLoadingPicture(false);
    }
  };

  const handleExportData = async () => {
    setExportingData(true);
    setExportError("");
    const res = await usersApi.exportMyData();
    setExportingData(false);
    if (!res.success || !res.data) {
      setExportError(res.message || "Export failed");
      return;
    }
    const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "my-data-export.json";
    anchor.click();
    URL.revokeObjectURL(url);
  };

  const handleSave = async () => {
    if (!profile) return;

    const validationErrors = validateChangeProfileDataForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setSaving(true);
    setError("");

    const updates: Partial<UserDto> = {};
    if (profile.firstName !== form.firstName) updates.firstName = form.firstName;
    if (profile.lastName !== form.lastName) updates.lastName = form.lastName;
    if (profile.email !== form.email) updates.email = form.email;
    if (profile.country !== form.country) updates.country = form.country;

    const res = await usersApi.updateMe(updates);

    if (!res.success || !res.data) {
      setError(res.message || "Failed to save profile");
      setSaving(false);
      return;
    }

    const dto = res.data;
    setProfile(dto);
    setForm({
      firstName: dto.firstName ?? "",
      lastName: dto.lastName ?? "",
      email: dto.email ?? "",
      country: dto.country ?? "",
    });
    setSaving(false);
    setErrors({});
  };

  if (loadingProfile) {
    return (
      <div className="w-80 p-4 mx-auto mt-10 text-center bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-2xl">
        <p className="text-gray-300 animate-pulse">Loading profile...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="w-80 p-4 mx-auto mt-10 text-center bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-2xl">
        <p className="text-red-500">{error}</p>
        <button
          onClick={() => setShowProfile(false)}
          className="mt-4 px-4 py-2 bg-rose-700 hover:bg-rose-600 text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all duration-200"
        >
          Close
        </button>
      </div>
    );
  }

  if (!profile) return null;

  return (
    <div className="w-full max-w-2xl p-5 mx-auto mt-10 text-center bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-2xl overflow-y-auto">
      <img
        src={profilePicture}
        alt={`${form.firstName} ${form.lastName}`}
        className="w-24 h-24 rounded-full object-cover mx-auto mb-4"
      />

      <div className="mb-4">
        <label className="inline-block px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg cursor-pointer text-sm">
          {loadingPicture ? "Uploading..." : "Change Picture"}
          <input type="file" accept="image/*" onChange={handleChangePicture} className="hidden" />
        </label>
      </div>

      <h2 className="text-xl font-bold mb-3 text-gray-100">{form.firstName} {form.lastName}</h2>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-y-4 gap-x-8 text-left">
        <label className="text-gray-100">
          First Name
          <input value={form.firstName} onChange={onChange("firstName")} className="w-full mt-1 px-3 py-2 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 border border-gray-600 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150" />
          {errors.firstName && <p className="text-red-500 text-sm mt-1">{errors.firstName}</p>}
        </label>

        <label className="text-gray-100">
          Last Name
          <input value={form.lastName} onChange={onChange("lastName")} className="w-full mt-1 px-3 py-2 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 border border-gray-600 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150" />
          {errors.lastName && <p className="text-red-500 text-sm mt-1">{errors.lastName}</p>}
        </label>

        <label className="text-gray-100">
          Email
          <input value={form.email} onChange={onChange("email")} className="w-full mt-1 px-3 py-2 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 border border-gray-600 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150" />
          {errors.email && <p className="text-red-500 text-sm mt-1">{errors.email}</p>}
        </label>

        <label className="text-gray-100">
          Country
          <input value={form.country} onChange={onChange("country")} className="w-full mt-1 px-3 py-2 rounded-lg bg-gray-700 text-gray-100 placeholder-gray-400 border border-gray-600 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-all duration-150" />
          {errors.country && <p className="text-red-500 text-sm mt-1">{errors.country}</p>}
        </label>

        <div className="mt-1 text-gray-300">
          <strong>Role:</strong> {profile.role}
        </div>
      </div>

      {exportError && (
        <p className="text-red-500 text-sm mt-3">{exportError}</p>
      )}

      <div className="flex gap-2 justify-center mt-4">
        <button
          disabled={!hasChanges || saving}
          onClick={handleSave}
          className={`px-4 py-2 rounded-lg font-medium shadow-md hover:shadow-lg transition-all duration-200 min-w-[120px] ${!hasChanges || saving ? "bg-gray-500 cursor-not-allowed text-gray-200" : "bg-emerald-600 hover:bg-emerald-500 text-white cursor-pointer"}`}
        >
          {saving ? "Saving..." : "Save"}
        </button>

        <button
          disabled={exportingData}
          onClick={handleExportData}
          className={`px-4 py-2 rounded-lg font-medium shadow-md hover:shadow-lg transition-all duration-200 min-w-[120px] ${exportingData ? "bg-gray-500 cursor-not-allowed text-gray-200" : "bg-blue-700 hover:bg-blue-600 text-white cursor-pointer"}`}
        >
          {exportingData ? "Exporting..." : "Export my data"}
        </button>

        <button
          onClick={() => setShowProfile(false)}
          className="px-4 py-2 bg-rose-700 hover:bg-rose-600 text-white rounded-lg font-medium shadow-md hover:shadow-lg transition-all duration-200 min-w-[120px]"
        >
          Close
        </button>
      </div>
    </div>
  );
}
