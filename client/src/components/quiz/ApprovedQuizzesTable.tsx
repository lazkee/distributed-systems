import { useEffect, useState } from "react";
import type { IQuizAPIService } from "../../api_services/quiz_api/IQuizAPIService";
import type { QuizFromList } from "../../types/quiz/QuizFromList";
import type { IAdminAPIService } from "../../api_services/admin_api/IAdminAPIService";

interface QuizzesTableProps {
  quizApi: IQuizAPIService;
  adminApi: IAdminAPIService;
}

export default function ApprovedQuizzesTable({ quizApi, adminApi }: QuizzesTableProps) {
  const [quizzes, setQuizzes] = useState<QuizFromList[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedQuizzes, setSelectedQuizzes] = useState<string[]>([]);
  useEffect(() => {
    async function fetchQuizzes() {
      try {
        const res = await quizApi.getApprovedQuizzes();
        if (res.success && res.data) {
          setQuizzes(res.data);
        } else {
          setError(res.message);
        }
      } catch (e: any) {
        setError(e.message || "Unknown error");
      } finally {
        setLoading(false);
      }
    }

    fetchQuizzes();
  }, [quizApi]);

  const handleCheckboxChange = (quizId: string) => {
    setSelectedQuizzes((prev) =>
      prev.includes(quizId) ? prev.filter((id) => id !== quizId) : [...prev, quizId]
    );
  };

  const handleGenerateReport = async () => {
    if (selectedQuizzes.length === 0) {
      alert("Please select at least one quiz to generate a report.");
      return;
    }

    try {
      const quizIdsAsNumbers = selectedQuizzes.map((id) => parseInt(id, 10));
      const res = await adminApi.generateReport(quizIdsAsNumbers);

      if (res.success) {
        alert("Report generated successfully, check your email!");
        setSelectedQuizzes([]);
      } else {
        alert("Failed to generate report: " + res.message);
      }
    } catch (err: any) {
      console.error(err);
      alert("Error generating report: " + (err.message || "Unknown error"));
    }
  };

  const handleDeleteQuiz = async (quizId: string) => {
    const confirmDelete = window.confirm("Are you sure you want to delete this quiz?");
    if (!confirmDelete) return;

    try {
      const res = await quizApi.deleteQuiz(parseInt(quizId, 10));

      if (res.success) {
        setQuizzes((prev) => prev.filter((q) => q.id !== quizId));
        setSelectedQuizzes((prev) => prev.filter((id) => id !== quizId));
      } else {
        alert(res.message || "Delete failed");
      }
    } catch (err: any) {
      console.error(err);
      alert("Error deleting quiz");
    }
  };

  if (loading) return <p className="text-gray-500">Loading quizzes...</p>;
  if (error) return <p className="text-red-500">{error}</p>;

  return (
    <div>
      <div className="overflow-x-auto rounded-xl ring-1 ring-gray-700 bg-gray-900 shadow-lg">
        <table className="min-w-full border-separate border-spacing-0">
          <thead className="bg-gray-800">
            <tr>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-300">
                ID
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-300">
                Title
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-300">
                Duration
              </th>
              <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-300">
                Created
              </th>
              <th className="px-6 py-4 text-center text-xs font-semibold uppercase tracking-wider text-gray-300">
                Report
              </th>
              <th className="px-6 py-4 text-center text-xs font-semibold uppercase tracking-wider text-gray-300">
                Delete
              </th>
            </tr>
          </thead>

          <tbody>
            {quizzes.map((quiz, idx) => (
              <tr
                key={quiz.id}
                className={`
                ${idx % 2 === 0 ? "bg-gray-900" : "bg-gray-800/60"}
                hover:bg-gray-800 transition-colors
              `}
              >
                <td className="px-6 py-5 text-sm text-gray-400">
                  {quiz.id}
                </td>

                <td className="px-6 py-5 text-sm font-medium text-gray-100">
                  {quiz.title}
                </td>

                <td className="px-6 py-5 text-sm text-gray-400">
                  {quiz.duration_seconds}s
                </td>

                <td className="px-6 py-5 text-sm text-gray-400">
                  {quiz.created_at}
                </td>

                <td className="px-6 py-5 text-center">
                  <input
                    type="checkbox"
                    checked={selectedQuizzes.includes(quiz.id)}
                    onChange={() => handleCheckboxChange(quiz.id)}
                    className="
                    h-5 w-5 rounded-md
                    bg-gray-800 border-gray-600
                    text-indigo-500
                    focus:ring-2 focus:ring-indigo-500
                    focus:ring-offset-0
                  "
                  />
                </td>

                <td className="px-6 py-5 text-center">
                  <button
                    onClick={() => handleDeleteQuiz(quiz.id)}
                    className="
                    px-4 py-2 text-sm font-semibold rounded-lg
                    bg-rose-700 hover:bg-rose-600
                    text-white transition-colors
                    shadow-sm
                  "
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-end mt-4">
        <button
          onClick={handleGenerateReport}
          disabled={selectedQuizzes.length === 0}
          className="
          px-6 py-2 rounded-lg font-semibold text-sm
          bg-indigo-600 hover:bg-indigo-500
          text-white shadow-sm transition-colors
          disabled:bg-gray-700 disabled:text-gray-400
          disabled:cursor-not-allowed
        "
        >
          Generate Report
        </button>
      </div>
    </div>
  );
}
