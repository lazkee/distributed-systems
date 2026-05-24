import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import { Navbar } from "../../components/navbar/Navbar";
import { DashboardLayout } from "../../components/dashboard/DashboardLayout";
import { DashboardHeader } from "../../components/player_dashboard/DashboardHeader";
import { CatalogState } from "../../components/player_dashboard/CatalogState";

import QuizList from "../../components/leaderboard/QuizList";
import type { QuizCatalogItem } from "../../models/quizCatalog/QuizCatalog";
import { ProfileCard } from "../../components/profile_card/ProfileCard";
import type { ICloudinariImageAPIService } from "../../api_services/cloudinary_image_api/ICloudinaryImageAPIService";
import type { IUsersAPIService } from "../../api_services/users_api/IUsersAPIService";
import type { IQuizAPIService } from "../../api_services/quiz_api/IQuizAPIService";

interface LeaderboardHomePageProps {
  cloudinaryApi: ICloudinariImageAPIService;
  usersApi: IUsersAPIService;
  quizApi: IQuizAPIService;
}

export function LeaderboardHomePage({ cloudinaryApi, usersApi, quizApi, }: LeaderboardHomePageProps) {
  const navigate = useNavigate();

  const [items, setItems] = useState<QuizCatalogItem[]>([]);
  const [page, setPage] = useState<number>(1);
  const pageSize = 8;

  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>("");
  const [showProfile, setShowProfile] = useState(false);

  const canPrev = useMemo(() => page > 1, [page]);
  const canNext = useMemo(() => page < totalPages, [page, totalPages]);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      setLoading(true);
      setErrorMsg("");

      try {
        const res = await quizApi.getCatalog(page, pageSize);

        if (cancelled) return;

        if (!res.success || !res.data) {
          setItems([]);
          setTotalPages(1);
          setErrorMsg(res.message || "Failed to load quizzes.");
          return;
        }

        setItems(res.data.items ?? []);
        setTotalPages(res.data.total_pages ?? 1);
      } catch (e: any) {
        if (!cancelled) {
          setItems([]);
          setTotalPages(1);
          setErrorMsg(e?.message || "Failed to load quizzes.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [page]);

  const onPrev = () => setPage((p) => Math.max(1, p - 1));
  const onNext = () => setPage((p) => Math.min(totalPages, p + 1));

  const onViewLeaderboard = (quizId: number) => {
    navigate(`/quiz/${quizId}/leaderboard`);
  };

  return (
    <DashboardLayout navbar={<Navbar onProfileClick={() => setShowProfile(true)} />}>
      <DashboardHeader
        title="Leaderboards"
        page={page}
        totalPages={totalPages}
        canPrev={canPrev}
        canNext={canNext}
        loading={loading}
        onPrev={onPrev}
        onNext={onNext}
      />

      <CatalogState
        loading={loading}
        errorMsg={errorMsg}
        isEmpty={!loading && !errorMsg && items.length === 0}
      />

      {!loading && !errorMsg && items.length > 0 && (
        <div className="w-full max-w-5xl px-6">
          <QuizList
            quizzes={items.map((q) => ({
              id: q.id,
              name: q.title,
            }))}
            onViewLeaderboard={onViewLeaderboard}
          />
        </div>
      )}

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

export default LeaderboardHomePage;
