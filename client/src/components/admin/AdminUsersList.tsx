import { useCallback, useEffect, useState } from "react";
import type { UserDto } from "../../models/user/UserDto";
import type { AdminUsersProps } from "../../types/admin/AdminUsersPageProps";

const PAGE_SIZE = 20;

export function AdminUsersList({ adminApi }: AdminUsersProps) {
  const [users, setUsers] = useState<UserDto[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(async (currentPage: number) => {
    setLoading(true);
    setError(null);
    try {
      const res = await adminApi.listUsers(currentPage, PAGE_SIZE);
      if (res.success && res.data) {
        setUsers(res.data.items);
        setTotalPages(res.data.pages);
      } else {
        setError(res.message || "Failed to load users.");
      }
    } catch (e: any) {
      setError(e?.message || "Failed to load users.");
    } finally {
      setLoading(false);
    }
  }, [adminApi]);

  useEffect(() => {
    fetchUsers(page);
  }, [fetchUsers, page]);

  const handleDeleteUser = async (userId: number) => {
    const confirmed = window.confirm("Are you sure you want to delete this user?");
    if (!confirmed) return;
    try {
      const res = await adminApi.deleteUser(userId.toString());
      if (res.success) {
        fetchUsers(page);
      } else {
        alert(res.message || "Delete failed.");
      }
    } catch (e: any) {
      alert(e?.message || "Delete failed.");
    }
  };

  const handleChangeRole = async (userId: number, newRole: "Player" | "Moderator") => {
    const confirmed = window.confirm(`Change role to '${newRole}'?`);
    if (!confirmed) return;
    try {
      const res = await adminApi.changeUserRole(userId.toString(), newRole);
      if (res.success && res.data) {
        setUsers((prev) => prev.map((u) => (u.id === userId ? res.data! : u)));
      } else {
        alert(res.message || "Role change failed.");
      }
    } catch (e: any) {
      alert(e?.message || "Role change failed.");
    }
  };

  if (loading) return <p className="text-gray-500">Loading users...</p>;
  if (error) return <p className="text-red-500">{error}</p>;

  return (
    <div>
      <div className="overflow-x-auto rounded-xl ring-1 ring-gray-700 bg-gray-900 shadow-lg">

        <table className="min-w-full border-separate border-spacing-0">
          <thead className="bg-gray-800">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-300">ID</th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-300">Email</th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-300">Name</th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-300">Role</th>
              <th className="px-6 py-4 text-center text-xs font-semibold uppercase tracking-wider text-gray-300">Delete</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user, idx) => {
              const isAdmin = user.role === "Admin";
              return (
                <tr key={user.id} className={`${idx % 2 === 0 ? "bg-gray-900" : "bg-gray-800/60"} hover:bg-gray-800 transition-colors`}>
                  <td className="px-6 py-5 text-sm text-gray-400">{user.id}</td>
                  <td className="px-6 py-5 text-sm text-gray-300">{user.email}</td>
                  <td className="px-6 py-5 text-sm font-medium text-gray-100">{user.firstName} {user.lastName}</td>
                  <td className="px-6 py-5 text-sm">
                    {isAdmin ? (
                      <span className="px-2 py-1 rounded-md text-xs font-semibold bg-gray-700 text-gray-200">Admin</span>
                    ) : (
                      <select
                        value={user.role}
                        onChange={(e) => handleChangeRole(user.id, e.target.value as "Player" | "Moderator")}
                        className="bg-gray-800 border border-gray-600 text-gray-100 text-sm rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      >
                        <option value="Player">Player</option>
                        <option value="Moderator">Moderator</option>
                      </select>
                    )}
                  </td>
                  <td className="px-6 py-5 text-center">
                    {isAdmin ? (
                      <span className="text-gray-500">—</span>
                    ) : (
                      <button
                        onClick={() => handleDeleteUser(user.id)}
                        className="px-4 py-2 text-sm font-semibold rounded-lg bg-rose-700 hover:bg-rose-600 text-white transition-colors shadow-sm"
                      >
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              );
            })}
            {users.length === 0 && (
              <tr>
                <td colSpan={5} className="px-6 py-8 text-center text-sm text-gray-400">No users found</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-between mt-4 px-1">
        <button
          type="button"
          disabled={page <= 1}
          onClick={() => setPage((p) => p - 1)}
          className={`px-4 py-2 text-sm rounded-lg font-medium transition-colors ${page <= 1 ? "bg-gray-700 text-gray-500 cursor-not-allowed" : "bg-gray-700 hover:bg-gray-600 text-gray-100 cursor-pointer"}`}
        >
          Previous
        </button>
        <span className="text-sm text-gray-400">
          Page {page} of {totalPages}
        </span>
        <button
          type="button"
          disabled={page >= totalPages}
          onClick={() => setPage((p) => p + 1)}
          className={`px-4 py-2 text-sm rounded-lg font-medium transition-colors ${page >= totalPages ? "bg-gray-700 text-gray-500 cursor-not-allowed" : "bg-gray-700 hover:bg-gray-600 text-gray-100 cursor-pointer"}`}
        >
          Next
        </button>
      </div>
    </div>
  );
}
