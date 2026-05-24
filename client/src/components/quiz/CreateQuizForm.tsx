import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../hooks/UseAuthHook";
import type { CreateQuizPageProps } from "../../types/quiz/CreateQuizPageProps";
import { QuestionEditor } from "./QuestionEditor";
import type { QuizQuestionDto } from "../../models/quiz/QuizQuestionDto";
import type { CreateQuizDto } from "../../models/quiz/CreateQuizDto";
import type { CreateQuizResponse } from "../../types/quiz/CreateQuizResponse";

const STORAGE_KEY = "moderator_notifications";

export function CreateQuizForm({ quizApi }: CreateQuizPageProps) {
    const { user } = useAuth();
    const navigate = useNavigate();

    const [title, setTitle] = useState("");
    const [duration, setDuration] = useState<number>(60);
    const [questions, setQuestions] = useState<QuizQuestionDto[]>([]);
    const [formErrors, setFormErrors] = useState<string[]>([]);

    const addQuestion = () => {
        setQuestions(prev => [
            ...prev,
            {
                text: "",
                points: 1,
                answers: [
                    { text: "", is_correct: false },
                    { text: "", is_correct: false },
                ],
            },
        ]);
    };

    const validateQuiz = (): boolean => {
        const newErrors: string[] = [];

        if (!title.trim()) newErrors.push("Title is required");
        if (duration <= 0) newErrors.push("Duration must be a positive number");
        if (questions.length === 0) newErrors.push("At least one question is required");

        questions.forEach((q, i) => {
            if (!q.text.trim()) newErrors.push(`Question ${i + 1} text is required`);
            if (!q.points) newErrors.push(`Question ${i + 1} points must be > 0`);

            if (q.answers.length < 2) {
                newErrors.push(`Question ${i + 1} must have at least 2 answers`);
            }

            if (!q.answers.some(a => a.is_correct)) {
                newErrors.push(`Question ${i + 1} must have at least one correct answer`);
            }

            q.answers.forEach((a, j) => {
                if (!a.text.trim()) {
                    newErrors.push(`Question ${i + 1}, Answer ${j + 1} text is required`);
                }
            });
        });

        setFormErrors(newErrors);
        return newErrors.length === 0;
    };

    const handleSubmit = async () => {
        if (!user) return;

        setFormErrors([]);
        if (!validateQuiz()) return;

        const payload: CreateQuizDto = {
            title,
            duration,
            author_id: user.id,
            questions,
        };

        const res: CreateQuizResponse = await quizApi.createQuiz(payload);

        if (!res.success) {
            if (res.errors) {
                setFormErrors(Object.values(res.errors));
            } else {
                setFormErrors([res.message || "Failed to create quiz"]);
            }
            return;
        }

        // Remove notification from storage
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
            const parsed = JSON.parse(saved);
            const updated = parsed.filter((n: any) => n.quiz_id !== res.data.quiz_id);
            localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
        }

        // Reset form
        setTitle("");
        setDuration(60);
        setQuestions([]);
        navigate("/Moderator-dashboard");
    };

    return (
        <div className="max-w-5xl mx-auto space-y-6 px-6">
            <div className="space-y-1">
                <label className="block text-gray-300 font-medium text-sm">Quiz Title</label>
                <input
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="Enter quiz title"
                    className="w-full px-4 py-3 rounded-lg bg-gray-800 text-gray-100 border border-gray-700 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                />
            </div>

            <div className="space-y-1">
                <label className="block text-gray-300 font-medium text-sm">
                    Duration (seconds)
                </label>
                <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))}
                    placeholder="Enter duration in seconds"
                    className="w-full px-4 py-3 rounded-lg bg-gray-800 text-gray-100 border border-gray-700 focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    min={1}
                />
            </div>

            <div className="space-y-4">
                {questions.map((q, index) => (
                    <QuestionEditor
                        key={index}
                        question={q}
                        onChange={(updated) => {
                            const copy = [...questions];
                            copy[index] = updated;
                            setQuestions(copy);
                        }}
                    />
                ))}
            </div>

            {/* Errors */}
            {formErrors.length > 0 && (
                <div className="bg-gray-900 border border-red-600 text-red-400 p-4 rounded-lg shadow-sm">
                    {formErrors.map((err, i) => (
                        <p key={i} className="text-sm">
                            • {err}
                        </p>
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
                    onClick={handleSubmit}
                    className="px-6 py-2 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded-lg shadow transition-colors duration-200"
                >
                    Save Quiz
                </button>
            </div>
        </div>
    );
}
