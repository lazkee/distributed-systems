import { isAxiosError } from "axios";
import { apiAxios as axios } from "../axiosInstance";
import type { QuizStartResponse, SubmitAnswerResponse, FinishQuizResponse } from "../../types/quiz_execution/QuizResponses";
import type { IQuizExecutionAPIService } from "./IQuizExecutionAPIService";

const API_URL: string = import.meta.env.VITE_API_URL + "/quiz-execution";

export const quizExecutionApi: IQuizExecutionAPIService = {
    async startQuiz(quizId: number): Promise<QuizStartResponse> {
        try {
            const res = await axios.post<QuizStartResponse>(`${API_URL}/start`, { quiz_id: quizId });
            return res.data;
        } catch (error) {
            let message = "Error starting quiz";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },

    async submitAnswer(attemptId: number, questionId: number, answerIds: number[]): Promise<SubmitAnswerResponse> {
        try {
            const res = await axios.post<SubmitAnswerResponse>(`${API_URL}/answer`, {
                attempt_id: attemptId,
                question_id: questionId,
                answer_ids: answerIds,
            });
            return res.data;
        } catch (error) {
            let message = "Error submitting answer";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },

    async finishQuiz(attemptId: number): Promise<FinishQuizResponse> {
        try {
            const res = await axios.post<FinishQuizResponse>(`${API_URL}/finish`, { attempt_id: attemptId });
            return res.data;
        } catch (error) {
            let message = "Error finishing quiz";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message };
        }
    },
};
