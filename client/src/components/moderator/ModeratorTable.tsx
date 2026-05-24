import { useEffect, useState } from "react";
import type { ModeratorTableProps } from "../../types/moderator/ModeratorTableProps";
import type { QuizFromList } from "../../types/quiz/QuizFromList";
import { useNavigate } from "react-router-dom";

export function ModeratorTable({ quizApi }: ModeratorTableProps) {
    const [quizzes, setQuizzes] = useState<QuizFromList[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        async function fetchMyQuizzes() {
            try {
                const res = await quizApi.getMyQuizzes();
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

        fetchMyQuizzes();
    }, [quizApi]);

    const handleDeleteQuiz = async (quizId: string) => {
        const confirmDelete = window.confirm("Are you sure you want to delete this quiz?");
        if (!confirmDelete) return;

        try {
            const res = await quizApi.deleteQuiz(parseInt(quizId, 10));

            if (res.success) {
                setQuizzes((prev) => prev.filter((q) => q.id !== quizId));
            } else {
                alert(res.message || "Delete failed");
            }
        } catch (err: any) {
            console.error(err);
            alert("Error deleting quiz");
        }
    };

    if (loading) return <p className="text-gray-400 px-6 py-4">Loading quizzes...</p>;
    if (error) return <p className="text-red-500 px-6 py-4">{error}</p>;

    return (
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
                        <th className="px-6 py-4 text-left text-xs font-semibold uppercase tracking-wider text-gray-300">
                            Status
                        </th>
                        <th className="px-6 py-4 text-center text-xs font-semibold uppercase tracking-wider text-gray-300">
                            Actions
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
                                {quiz.status.toLowerCase() === "rejected" ? (
                                    <span
                                        onClick={() => navigate(`/quiz/edit/${quiz.id}`)}
                                        className="underline cursor-pointer text-red-500 hover:text-red-400 transition-colors"
                                        title="Click to edit this rejected quiz"
                                    >
                                        {quiz.title}
                                    </span>
                                ) : (
                                    quiz.title
                                )}

                            </td>

                            <td className="px-6 py-5 text-sm text-gray-400">
                                {quiz.duration_seconds}s
                            </td>

                            <td className="px-6 py-5 text-sm text-gray-400">
                                {quiz.created_at}
                            </td>

                            <td className="px-6 py-5">
                                <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-gray-700 text-gray-200">
                                    {quiz.status.charAt(0).toUpperCase() + quiz.status.slice(1)}
                                </span>
                            </td>


                            <td className="px-6 py-5 text-center">
                                <button
                                    onClick={() => handleDeleteQuiz(quiz.id)}
                                    className="px-4 py-2 text-sm font-semibold rounded-lg
                                           bg-rose-700 hover:bg-rose-600
                                           text-white transition-colors shadow-sm"
                                >
                                    Delete
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}
