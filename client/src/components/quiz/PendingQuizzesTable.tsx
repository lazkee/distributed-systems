import { useEffect, useState } from "react";
import type { IQuizAPIService } from "../../api_services/quiz_api/IQuizAPIService";
import type { QuizFromList } from "../../types/quiz/QuizFromList";
import { useNavigate } from "react-router-dom";

interface QuizzesTableProps {
    quizApi: IQuizAPIService;
}

export default function PendingQuizzesTable({ quizApi }: QuizzesTableProps) {
    const [quizzes, setQuizzes] = useState<QuizFromList[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        async function fetchQuizzes() {
            try {
                const res = await quizApi.getPendingQuizzes();
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
                                Review
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
                                    <button
                                        onClick={() => navigate(`/admin/quizzes/${quiz.id}`)}
                                        className="
                    px-4 py-2 text-sm font-semibold rounded-lg
                    bg-indigo-600 hover:bg-indigo-500
                    text-white transition-colors
                    shadow-sm
                  "
                                    >
                                        Review
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}