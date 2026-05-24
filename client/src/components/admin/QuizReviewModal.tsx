import { useEffect, useState } from "react";
import type { GetQuizResponseData } from "../../types/quiz/GetQuizResponses";
import { quizApi } from "../../api_services/quiz_api/QuizAPIService";

const STORAGE_KEY = "admin_notifications";

type Props = {
    quizId: number;
    onClose: () => void;
    onApprove: (comment: string) => Promise<void>;
    onReject: (comment: string) => Promise<void>;
};

export function QuizReviewModal({
    quizId,
    onClose,
    onApprove,
    onReject,
}: Props) {
    const [quiz, setQuiz] = useState<GetQuizResponseData | null>(null);
    const [comment, setComment] = useState("");
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [isPending, setIsPending] = useState(false);

    useEffect(() => {
        const loadQuiz = async () => {
            try {
                const res = await quizApi.getQuizForAdmin(quizId);

                if (!res.success || !res.data) {
                    removeNotificationFromStorage();
                    setError(res.message || "Failed to load quiz");
                    return;
                }

                setQuiz(res.data);
                console.log(res.data.status);
                setIsPending(res.data.status === "pending");
            } catch (e) {
                removeNotificationFromStorage();
                console.error(e);
                setError("Error while loading quiz");
            } finally {
                setLoading(false);
            }
        };

        if (quizId) {
            loadQuiz();
        }
    }, [quizId]);

    const removeNotificationFromStorage = () => {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (!saved) return;

        const notifications = JSON.parse(saved);
        const updated = notifications.filter((n: any) => n.quiz_id !== quizId);

        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
    };

    const handleApprove = async () => {
        if (!isPending) return;

        try {
            setSubmitting(true);
            await onApprove(comment);
            removeNotificationFromStorage();
            onClose();
        } catch (e) {
            console.error(e);
            alert("Approve failed");
        } finally {
            setSubmitting(false);
        }
    };

    const handleReject = async () => {
        if (!isPending) return;

        if (!comment.trim()) {
            alert("Comment is required when rejecting a quiz");
            return;
        }

        try {
            setSubmitting(true);
            await onReject(comment);
            removeNotificationFromStorage();
            onClose();
        } catch (e) {
            console.error(e);
            alert("Reject failed");
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) {
        return (
            <div className="bg-gray-800 p-6 rounded-xl shadow text-gray-200">
                Loading quiz details...
            </div>
        );
    }

    if (error || !quiz) {
        return (
            <div className="bg-red-800 p-6 rounded-xl shadow text-red-200">
                {error || "Quiz not found"}
            </div>
        );
    }

    return (
        <div className="bg-gray-900 rounded-xl shadow p-6 space-y-6">
            {/* Quiz Header */}
            <div className="space-y-2">
                <h2 className="text-2xl font-bold text-white">{quiz.title}</h2>
                <p className="text-gray-400">{quiz.description}</p>
                <div className="flex gap-3 mt-2">
                    <span className="bg-gray-800 px-3 py-1 rounded text-sm text-gray-300">
                        {quiz.duration_seconds}s
                    </span>
                    <span className="bg-gray-800 px-3 py-1 rounded text-sm text-gray-300">
                        {quiz.questions.length} questions
                    </span>
                </div>
            </div>

            {/* Questions */}
            <div className="space-y-4">
                {quiz.questions.map((q, qi) => (
                    <div
                        key={q.question_id}
                        className="bg-gray-800 border border-gray-700 rounded-xl p-4 shadow-sm"
                    >
                        <div className="text-white font-semibold mb-2">
                            {qi + 1}. {q.text}{" "}
                            <span className="ml-2 text-green-400">
                                ({q.points} pts)
                            </span>
                        </div>
                        <div className="space-y-2">
                            {q.answers.map((a) => (
                                <div
                                    key={a.answer_id}
                                    className={`p-2 rounded ${a.is_correct
                                        ? "bg-green-700 text-green-100 border border-green-500"
                                        : "bg-gray-700 text-gray-300"
                                        }`}
                                >
                                    {a.text}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Admin Comment */}
            <div>
                <label className="block text-gray-300 mb-2 font-medium">
                    Admin comment (required for rejection)
                </label>
                <textarea
                    value={comment}
                    onChange={(e) => setComment(e.target.value)}
                    className="w-full p-3 bg-gray-800 border border-gray-700 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    rows={4}
                    placeholder="Write feedback..."
                />
            </div>

            {/* Actions */}
            <div className="flex justify-between mt-4">
                <button
                    disabled={submitting || !isPending}
                    onClick={handleReject}
                    className="px-6 py-2 bg-rose-600 hover:bg-rose-500 rounded-lg text-white font-semibold shadow-sm transition-colors disabled:opacity-50"
                >
                    Reject
                </button>

                <button
                    disabled={submitting || !isPending}
                    onClick={handleApprove}
                    className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 rounded-lg text-white font-semibold shadow-sm transition-colors disabled:opacity-50"
                >
                    Approve
                </button>
            </div>

            {!isPending && (
                <div className="bg-rose-900/40 border border-rose-700 text-white px-4 py-2 rounded-lg text-sm">
                    This quiz is already <strong>{quiz.status}</strong> and cannot be modified.
                </div>
            )}
        </div>
    );
}
