import type { CreateQuizDto } from "../../models/quiz/CreateQuizDto";
import type { EditQuizDto } from "../../models/quiz/EditQuizDto";
import type { CreateQuizResponse } from "../../types/quiz/CreateQuizResponse";
import type { EditQuizResponse } from "../../types/quiz/EditQuizResponse";
import type { GetAllQuizzesResponse } from "../../types/quiz/GetAllQuizzesResponse";
import type { GetQuizCatalogResponse } from "../../types/quiz/GetQuizCatalogResponse";
import type { GetQuizResponse } from "../../types/quiz/GetQuizResponses";
import type { QuizResponse } from "../../types/quiz/QuizResponse";
import type { GetLeaderboardResponse } from "../../types/leaderboard/GetLeaderboardResponse";

export interface IQuizAPIService {
    createQuiz(data: CreateQuizDto): Promise<CreateQuizResponse>;
    getQuiz(quizId: number): Promise<GetQuizResponse>;
    getRejectedQuiz(quizId: number): Promise<GetQuizResponse>;
    editQuiz(quizId: number, data: EditQuizDto): Promise<EditQuizResponse>;
    getApprovedQuizzes(): Promise<GetAllQuizzesResponse>;
    getPendingQuizzes(): Promise<GetAllQuizzesResponse>;
    getMyQuizzes(): Promise<GetAllQuizzesResponse>;
    getQuizForAdmin(quizId: number): Promise<GetQuizResponse>;
    approveQuiz(quizId: number, comment: string): Promise<QuizResponse>;
    rejectQuiz(quizId: number, comment: string): Promise<QuizResponse>;
    deleteQuiz(quizId: number): Promise<QuizResponse>;
    getCatalog(page: number, pageSize: number): Promise<GetQuizCatalogResponse>;
    getLeaderboard(quizId: number): Promise<GetLeaderboardResponse>;
}
