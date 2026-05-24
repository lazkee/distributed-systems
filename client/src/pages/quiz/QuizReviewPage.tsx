import { useNavigate, useParams } from "react-router-dom";
import { QuizReviewModal } from "../../components/admin/QuizReviewModal";

import DashboardLayout from "../../components/dashboard/DashboardLayout";
import { Navbar } from "../../components/navbar/Navbar";
import { ProfileCard } from "../../components/profile_card/ProfileCard";
import type { ICloudinariImageAPIService } from "../../api_services/cloudinary_image_api/ICloudinaryImageAPIService";
import type { IUsersAPIService } from "../../api_services/users_api/IUsersAPIService";
import type { IQuizAPIService } from "../../api_services/quiz_api/IQuizAPIService";
import { useState } from "react";

interface QuizReviewPageProps {
    cloudinaryApi: ICloudinariImageAPIService;
    usersApi: IUsersAPIService;
    quizApi: IQuizAPIService;
}

export default function QuizReviewPage({ cloudinaryApi, usersApi, quizApi }: QuizReviewPageProps) {
    const { quizId } = useParams<{ quizId: string }>();
    const navigate = useNavigate();
    const [showProfile, setShowProfile] = useState(false);

    const approve = async (comment: string) => {
        await quizApi.approveQuiz(Number(quizId), comment);
        navigate("/Admin-dashboard");
    };

    const reject = async (comment: string) => {
        await quizApi.rejectQuiz(Number(quizId), comment);
        navigate("/Admin-dashboard");
    };

    return (
        <DashboardLayout navbar={<Navbar onProfileClick={() => setShowProfile(true)} />}>
            <div className="w-full max-w-5xl px-6 flex items-center justify-between mb-6">
                <h1 className="text-3xl font-bold text-gray-100">Review Quiz</h1>
            </div>

            <div className="w-full max-w-5xl px-6">
                <QuizReviewModal
                    quizId={Number(quizId)}
                    onClose={() => navigate("/Admin-dashboard")}
                    onApprove={approve}
                    onReject={reject}
                />
            </div>

            {showProfile && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <ProfileCard
                        setShowProfile={setShowProfile}
                        cloudinaryApi={cloudinaryApi}
                        usersApi={usersApi}
                    />
                </div>
            )}
        </DashboardLayout>
    );
}