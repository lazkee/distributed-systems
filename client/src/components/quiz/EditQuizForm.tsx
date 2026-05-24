import { useEffect, useState } from "react";
import type { EditQuizFormProps } from "../../types/quiz/EditQuizFormProps";
import { QuestionEditor } from "./QuestionEditor";
import type { QuizQuestionDto } from "../../models/quiz/QuizQuestionDto";
import type { AnswerMeta,QuestionMeta } from "../../types/quiz/AnswerMeta";

const STORAGE_KEY = "moderator_notifications";

export default function EditQuizForm({ quizId, quizApi, onSaved }: EditQuizFormProps) {
    const [title, setTitle] = useState("");
    const [duration, setDuration] = useState<number>(0);
    const [questions, setQuestions] = useState<QuizQuestionDto[]>([]);
    const [meta, setMeta] = useState<QuestionMeta[]>([]);     
    const [adminComment, setAdminComment] = useState<string | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [formErrors, setFormErrors] = useState<string[]>([]);

    useEffect(() => {
        const loadQuiz = async () => {
            const res = await quizApi.getRejectedQuiz(quizId);

            if (!res.success || !res.data) {
                setError(res.message || "Failed to load quiz");
                return;
            }

            const quiz = res.data;
            setTitle(quiz.title);
            setDuration(quiz.duration_seconds);
            setAdminComment(quiz.admin_comment ?? null);

            const loadedQuestions: QuizQuestionDto[] = quiz.questions.map((q: any) => ({
                text: q.text,
                points: q.points,
                answers: q.answers.map((a: any) => ({
                    text: a.text,
                    is_correct: a.is_correct,
                })),
            }));

            const loadedMeta: QuestionMeta[] = quiz.questions.map((q: any) => ({
                question_id: q.id,
                answers: q.answers.map((a: any) => ({ answer_id: a.id })),
            }));

            setQuestions(loadedQuestions);
            setMeta(loadedMeta);
            setLoading(false);
        };

        loadQuiz();
    }, [quizId, quizApi]);

    // ── Helpers ───────────────────────────────────────────────────────────────

    const addQuestion = () => {
        setQuestions(prev => [
            ...prev,
            { text: "", points: 1, answers: [{ text: "", is_correct: false }, { text: "", is_correct: false }] },
        ]);
        setMeta(prev => [
            ...prev,
            { question_id: null, answers: [{ answer_id: null }, { answer_id: null }] },
        ]);
    };

    const updateQuestion = (index: number, updated: QuizQuestionDto) => {
        setQuestions(prev => {
            const copy = [...prev];
            copy[index] = updated;
            return copy;
        });

        // Sync meta answers when answers are added inside QuestionEditor
        setMeta(prev => {
            const copy = [...prev];
            const existingMeta = copy[index];
            const newAnswerCount = updated.answers.length;
            const syncedAnswers: AnswerMeta[] = Array.from({ length: newAnswerCount }, (_, i) =>
                existingMeta.answers[i] ?? { answer_id: null }
            );
            copy[index] = { ...existingMeta, answers: syncedAnswers };
            return copy;
        });
    };

    // ── Validation ────────────────────────────────────────────────────────────

    const validateQuiz = (): boolean => {
        const newErrors: string[] = [];

        if (!title.trim()) newErrors.push("Title is required");
        if (questions.length === 0) newErrors.push("At least one question is required");

        questions.forEach((q, i) => {
            if (!q.text.trim()) newErrors.push(`Question ${i + 1} text is required`);
            if (q.answers.length < 2) newErrors.push(`Question ${i + 1} must have at least 2 answers`);
            if (!q.answers.some(a => a.is_correct)) newErrors.push(`Question ${i + 1} must have at least one correct answer`);
            q.answers.forEach((a, j) => {
                if (!a.text.trim()) newErrors.push(`Question ${i + 1}, Answer ${j + 1} text is required`);
            });
        });

        setFormErrors(newErrors);
        return newErrors.length === 0;
    };

    // ── Save ──────────────────────────────────────────────────────────────────

    const handleSave = async () => {

        setFormErrors([]);
        if (!validateQuiz()) return;

        const payload = {
            title,
            duration,
            questions: questions.map((q, qi) => ({
                question_id: meta[qi]?.question_id ?? null,
                text: q.text,
                points: q.points,
                answers: q.answers.map((a, ai) => ({
                    answer_id: meta[qi]?.answers[ai]?.answer_id ?? null,
                    text: a.text,
                    is_correct: a.is_correct,
                })),
            })),
        };

        const res = await quizApi.editQuiz(quizId, payload);

        if (!res.success) {
            if (res.errors) {
                setFormErrors(Object.values(res.errors) as string[]);
            } else {
                setFormErrors([res.message || "Failed to update quiz"]);
            }
            return;
        }

        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            const parsed = JSON.parse(saved);
            const updated = parsed.filter((n: any) => n.quiz_id !== quizId);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        }

        onSaved();
    };

    // ── Render ────────────────────────────────────────────────────────────────

    if (loading) return <p className="text-gray-300">Loading quiz...</p>;
    if (error) return <p className="text-red-500">{error}</p>;

    return (
        <div className="max-w-5xl mx-auto space-y-6 px-6">

            {/* Admin Rejection Reason Banner */}
            {adminComment && (
                <div className="flex gap-3 bg-red-950 border border-red-600 rounded-xl p-5 shadow-sm">
                    <div className="flex-shrink-0 mt-0.5">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                    </div>
                    <div>
                        <p className="text-red-300 font-semibold text-sm uppercase tracking-wide mb-1">Quiz Rejected by Admin</p>
                        <p className="text-red-100 text-sm leading-relaxed">{adminComment}</p>
                    </div>
                </div>
            )}

            {/* Title */}
            <div className="space-y-1">
                <label className="block text-gray-300 font-medium text-sm">Quiz Title</label>
                <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Enter quiz title"
                    className="w-full px-4 py-3 rounded-lg bg-gray-800 text-gray-100 border border-gray-700 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
            </div>

            {/* Duration */}
            <div className="space-y-1">
                <label className="block text-gray-300 font-medium text-sm">Duration (seconds)</label>
                <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))}
                    placeholder="Enter duration in seconds"
                    className="w-full px-4 py-3 rounded-lg bg-gray-800 text-gray-100 border border-gray-700 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    min={1}
                />
            </div>

            {/* Questions */}
            <div className="space-y-4">
                {questions.map((q, index) => (
                    <QuestionEditor
                        key={index}
                        question={q}
                        onChange={(updated) => updateQuestion(index, updated)}
                    />
                ))}
            </div>

            {/* Form errors */}
            {formErrors.length > 0 && (
                <div className="bg-gray-900 border border-red-600 text-red-400 p-4 rounded-lg shadow-sm">
                    {formErrors.map((err, i) => (
                        <p key={i} className="text-sm">• {err}</p>
                    ))}
                </div>
            )}

            <div className="flex justify-between mt-4">
                <button
                    onClick={addQuestion}
                    className="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded-lg shadow transition-colors duration-200"
                >
                    Add Question
                </button>

                <button
                    onClick={handleSave}
                    className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg shadow transition-colors duration-200"
                >
                    Save Changes
                </button>
            </div>
        </div>
    );
}