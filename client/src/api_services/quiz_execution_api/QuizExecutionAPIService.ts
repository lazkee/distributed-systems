import { isAxiosError } from "axios";
import { apiAxios as axios } from "../axiosInstance";
import type {
    QuizStartResponse,
    SubmitAnswerResponse,
    FinishQuizResponse
} from "../../types/quiz_execution/QuizResponses";
import type { IQuizExecutionAPIService } from "./IQuizExecutionAPIService";

const API_URL: string = import.meta.env.VITE_API_URL + "/quiz-execution";

export const quizExecutionApi: IQuizExecutionAPIService = {
    async startQuiz(token: string, quizId: number): Promise<QuizStartResponse> {
        try {
            const payload = { quiz_id: quizId };

            const res = await axios.post<QuizStartResponse>(
                `${API_URL}/start`,
                payload,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message = "Error starting quiz";
            if (isAxiosError(error))
                message = error.response?.data?.message || message;

            return { success: false, message, data: undefined };
        }
    },

    async submitAnswer(token: string, attemptId: number, questionId: number, answerIds: number[]): Promise<SubmitAnswerResponse> {
        try {
            const payload = {
                attempt_id: attemptId,
                question_id: questionId,
                answer_ids: answerIds
            };

            const res = await axios.post<SubmitAnswerResponse>(
                `${API_URL}/answer`,
                payload,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message = "Error submitting answer";
            if (isAxiosError(error)) {
                message = error.response?.data?.message || message;
            }

            return { success: false, message, data: undefined };
        }
    },

    async finishQuiz(token: string, attemptId: number): Promise<FinishQuizResponse> {
        try {
            const payload = { attempt_id: attemptId };

            const res = await axios.post<FinishQuizResponse>(
                `${API_URL}/finish`,
                payload,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message = "Error finishing quiz";
            if (isAxiosError(error))
                message = error.response?.data?.message || message;

            return { success: false, message };
        }
    }
};