import type { QuizStartResponse, SubmitAnswerResponse, FinishQuizResponse } from "../../types/quiz_execution/QuizResponses";

export interface IQuizExecutionAPIService {
    startQuiz(quizId: number): Promise<QuizStartResponse>;
    submitAnswer(attemptId: number, questionId: number, answerIds: number[]): Promise<SubmitAnswerResponse>;
    finishQuiz(attemptId: number): Promise<FinishQuizResponse>;
}
