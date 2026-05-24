import { isAxiosError } from "axios";
import { apiAxios as axios } from "../axiosInstance";
import type { IQuizAPIService } from "./IQuizAPIService";
import type { CreateQuizDto } from "../../models/quiz/CreateQuizDto";
import type { GetQuizResponse } from "../../types/quiz/GetQuizResponses";
import type { GetAllQuizzesResponse } from "../../types/quiz/GetAllQuizzesResponse";
import type { EditQuizResponse } from "../../types/quiz/EditQuizResponse";
import type { CreateQuizResponse } from "../../types/quiz/CreateQuizResponse";
import type { GetQuizCatalogResponse } from "../../types/quiz/GetQuizCatalogResponse";
import type { EditQuizDto } from "../../models/quiz/EditQuizDto";
import type { GetLeaderboardResponse } from "../../types/leaderboard/GetLeaderboardResponse";
import type { QuizResponse } from "../../types/quiz/QuizResponse";

const API_URL: string = import.meta.env.VITE_API_URL + "/quiz";

export const quizApi: IQuizAPIService = {
    async createQuiz(data: CreateQuizDto): Promise<CreateQuizResponse> {
        try {
            const res = await axios.post(API_URL, data);
            return res.data;
        } catch (error) {
            let message = "Create quiz error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },

    async getQuiz(quizId: number): Promise<GetQuizResponse> {
        try {
            const res = await axios.get<GetQuizResponse>(`${API_URL}/${quizId}`);
            return res.data;
        } catch (error) {
            let message = "Get quiz error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },

    async getApprovedQuizzes(): Promise<GetAllQuizzesResponse> {
        try {
            const res = await axios.get<GetAllQuizzesResponse>(`${API_URL}/approvedQuizzes`);
            return res.data;
        } catch (error) {
            let message = "Get approved quizzes error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },

    async getPendingQuizzes(): Promise<GetAllQuizzesResponse> {
        try {
            const res = await axios.get<GetAllQuizzesResponse>(`${API_URL}/pendingQuizzes`);
            return res.data;
        } catch (error) {
            let message = "Get pending quizzes error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },

    async getCatalog(page: number = 1, pageSize: number = 12): Promise<GetQuizCatalogResponse> {
        try {
            const res = await axios.get<GetQuizCatalogResponse>(`${API_URL}/catalog`, {
                params: { page, page_size: pageSize },
            });
            return res.data;
        } catch (error) {
            let message = "Get quiz catalog error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },

    async getQuizForAdmin(quizId: number): Promise<GetQuizResponse> {
        try {
            const res = await axios.get(`${API_URL}/admin/${quizId}`);
            return res.data;
        } catch (error) {
            let message = "Get quiz for admin error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },

    async approveQuiz(quizId: number, comment: string): Promise<QuizResponse> {
        try {
            const res = await axios.put(`${API_URL}/admin/${quizId}/approve`, { comment });
            return res.data;
        } catch (error) {
            let message = "Approve quiz error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message };
        }
    },

    async rejectQuiz(quizId: number, comment: string): Promise<QuizResponse> {
        try {
            const res = await axios.put(`${API_URL}/admin/${quizId}/reject`, { comment });
            return res.data;
        } catch (error) {
            let message = "Reject quiz error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message };
        }
    },

    async deleteQuiz(quizId: number): Promise<QuizResponse> {
        try {
            const res = await axios.delete(`${API_URL}/delete/${quizId}`);
            return res.data;
        } catch (error) {
            let message = "Delete quiz error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message };
        }
    },

    async getMyQuizzes(): Promise<GetAllQuizzesResponse> {
        try {
            const res = await axios.get<GetAllQuizzesResponse>(`${API_URL}/my`);
            return res.data;
        } catch (error) {
            let message = "Get my quizzes error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },

    async getRejectedQuiz(quizId: number): Promise<GetQuizResponse> {
        try {
            const res = await axios.get<GetQuizResponse>(`${API_URL}/getRejected/${quizId}`);
            return res.data;
        } catch (error) {
            let message = "Get rejected quiz error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },

    async editQuiz(quizId: number, data: EditQuizDto): Promise<EditQuizResponse> {
        try {
            const res = await axios.put(`${API_URL}/edit/${quizId}`, data);
            return res.data;
        } catch (error) {
            let message = "Edit quiz error";
            let errors: Record<string, string> | undefined;
            if (isAxiosError(error)) {
                message = error.response?.data?.message || message;
                errors = error.response?.data?.errors;
            }
            return { success: false, message, errors };
        }
    },

    async getLeaderboard(quizId: number): Promise<GetLeaderboardResponse> {
        try {
            const res = await axios.get<GetLeaderboardResponse>(`${API_URL}/${quizId}/leaderboard`);
            return res.data;
        } catch (error) {
            let message = "Get leaderboard error";
            if (isAxiosError(error)) message = error.response?.data?.message || message;
            return { success: false, message, data: undefined };
        }
    },
};
