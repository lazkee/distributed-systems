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

const API_URL: string = import.meta.env.VITE_API_URL + "/quiz";

export const quizApi: IQuizAPIService = {
    async createQuiz(token: string, data: CreateQuizDto): Promise<CreateQuizResponse> {
        try {
            const res = await axios.post(
                `${API_URL}`,
                data,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message: string = "Create quiz error";

            if (isAxiosError(error)) {
                message = error.response?.data?.message || message;
            }

            return {
                success: false,
                message: message,
                data: undefined
            };
        }
    },

    async getQuiz(token: string, quizId: number): Promise<GetQuizResponse> {
        try {
            const res = await axios.get<GetQuizResponse>(
                `${API_URL}/${quizId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message = "Get quiz error";
            if (isAxiosError(error))
                message = error.response?.data?.message || message;

            return { success: false, message, data: undefined };
        }
    },

    async getApprovedQuizzes(token: string): Promise<GetAllQuizzesResponse> {
        try {
            const res = await axios.get<GetAllQuizzesResponse>(
                `${API_URL}/approvedQuizzes`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            return res.data;
        } catch (error) {
            let message = "Get approved quizzes error";
            if (isAxiosError(error))
                message = error.response?.data?.message || message;

            return { success: false, message, data: undefined };
        }
    },

    async getPendingQuizzes(token: string): Promise<GetAllQuizzesResponse> {
        try {
            const res = await axios.get<GetAllQuizzesResponse>(
                `${API_URL}/pendingQuizzes`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            return res.data;
        } catch (error) {
            let message = "Get pending quizzes error";
            if (isAxiosError(error))
                message = error.response?.data?.message || message;

            return { success: false, message, data: undefined };
        }
    },

    async getCatalog(
        token: string,
        page: number = 1,
        pageSize: number = 12
    ): Promise<GetQuizCatalogResponse> {
        try {
            const res = await axios.get<GetQuizCatalogResponse>(
                `${API_URL}/catalog`,
                {
                    params: { page, page_size: pageSize },
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message = "Get quiz catalog error";
            if (isAxiosError(error))
                message = error.response?.data?.message || message;

            return { success: false, message, data: undefined };
        }
    },




    async getQuizForAdmin(token: string, quizId: number): Promise<GetQuizResponse> {
        try {
            const res = await axios.get(
                `${API_URL}/admin/${quizId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            return res.data;
        } catch (error) {
            let message = "Get quiz for admin error";
            if (isAxiosError(error))
                message = error.response?.data?.message || message;

            return { success: false, message, data: undefined };
        }
    },

    async approveQuiz(
        token: string,
        quizId: number,
        comment: string
    ): Promise<{ success: boolean; message: string }> {
        try {
            const res = await axios.put(
                `${API_URL}/admin/${quizId}/approve`,
                { comment },
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message = "Approve quiz error";

            if (isAxiosError(error)) {
                message = error.response?.data?.message || message;
            }

            return { success: false, message };
        }
    },

    async rejectQuiz(
        token: string,
        quizId: number,
        comment: string
    ): Promise<{ success: boolean; message: string }> {
        try {
            const res = await axios.put(
                `${API_URL}/admin/${quizId}/reject`,
                { comment },
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message = "Reject quiz error";

            if (isAxiosError(error)) {
                message = error.response?.data?.message || message;
            }

            return { success: false, message };
        }
    },

    async deleteQuiz(quizId: number, token: string): Promise<{ success: boolean; message: string }> {
        try {
            const res = await axios.delete(
                `${API_URL}/delete/${quizId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json"
                    }
                }
            );

            return res.data;
        } catch (error) {
            let message = "Delete quiz error";

            if (isAxiosError(error)) {
                message = error.response?.data?.message || message;
            }

            return { success: false, message };
        }
    },

    async getMyQuizzes(token: string): Promise<GetAllQuizzesResponse> {
        try {
            const res = await axios.get<GetAllQuizzesResponse>(
                `${API_URL}/my`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`
                    }
                }
            );
            return res.data;
        } catch (error) {
            let message = "Get my quizzes error";
            if (isAxiosError(error))
                message = error.response?.data?.message || message;

            return { success: false, message, data: undefined };
        }
    },

    async getRejectedQuiz(token: string, quizId: number): Promise<GetQuizResponse> {
        try {
            const res = await axios.get<GetQuizResponse>(
                `${API_URL}/getRejected/${quizId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            return res.data;
        } catch (error) {
            let message = "Get rejected quiz error";
            if (isAxiosError(error))
                message = error.response?.data?.message || message;

            return { success: false, message, data: undefined };
        }
    },

    async editQuiz(
        token: string,
        quizId: number,
        data: EditQuizDto
    ): Promise<EditQuizResponse> {
        try {
            const res = await axios.put(
                `${API_URL}/edit/${quizId}`,
                data,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                }
            );

            return res.data;
        } catch (error) {
            let message = "Edit quiz error";
            let errors: Record<string, string> | undefined = undefined;

            if (isAxiosError(error)) {
                message = error.response?.data?.message || message;
                errors = error.response?.data?.errors;
            }

            return {
                success: false,
                message,
                errors
            };
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
