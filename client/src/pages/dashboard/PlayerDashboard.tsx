// src/pages/dashboard/PlayerDashboard.tsx
import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Navbar } from "../../components/navbar/Navbar";
import { ProfileCard } from "../../components/profile_card/ProfileCard";

import { DashboardLayout } from "../../components/dashboard/DashboardLayout";
import { DashboardHeader } from "../../components/player_dashboard/DashboardHeader";
import { CatalogState } from "../../components/player_dashboard/CatalogState";
import { QuizCatalogGrid } from "../../components/player_dashboard/QuizCatalogGrid";

import type { QuizCatalogItem } from "../../models/quizCatalog/QuizCatalog";
import type { PlayerDashboardProps } from "../../types/player/PlayerDashboardProps";

export default function PlayerDashboard({
  cloudinaryApi,
  usersApi,
  quizApi,
}: PlayerDashboardProps) {
  const navigate = useNavigate();

  const [showProfile, setShowProfile] = useState(false);

  // Catalog state
  const [items, setItems] = useState<QuizCatalogItem[]>([]);
  const [page, setPage] = useState<number>(1);
  const pageSize = 12;

  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>("");

  const canPrev = useMemo(() => page > 1, [page]);
  const canNext = useMemo(() => page < totalPages, [page, totalPages]);

  const formatDuration = (seconds: number) => {
    const mins = Math.ceil(seconds / 60);
    return `${mins} min`;
  };

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
  }, [quizApi, page]);

  const onPrev = () => setPage((p) => Math.max(1, p - 1));
  const onNext = () => setPage((p) => p + 1);

  const onPlay = (quizId: number) => {
    navigate(`/quiz/play/${quizId}`);
  };

  return (
    <DashboardLayout
      navbar={<Navbar onProfileClick={() => setShowProfile(true)} />}
    >
      <DashboardHeader
        title="Quizzes"
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
        <QuizCatalogGrid
          items={items}
          formatDuration={formatDuration}
          onPlay={onPlay}
        />
      )}

      {showProfile && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
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
