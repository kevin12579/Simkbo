import { fetchTeams } from "@/lib/api/teams";
import TeamStatTable from "@/components/stats/TeamStatTable";
import type { TeamStats } from "@/types";

export const revalidate = 3600;

async function fetchAllTeamStats(): Promise<TeamStats[]> {
  const teams = await fetchTeams();
  const results = await Promise.allSettled(
    teams.map(async (team) => {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/teams/${team.id}/stats`,
        { next: { revalidate: 3600 } }
      );
      if (!res.ok) return null;
      return res.json() as Promise<TeamStats>;
    })
  );
  return results
    .filter((r): r is PromiseFulfilledResult<TeamStats> => r.status === "fulfilled" && r.value !== null)
    .map((r) => r.value);
}

export default async function StatsPage() {
  let teamStats: TeamStats[] = [];
  try {
    teamStats = await fetchAllTeamStats();
    teamStats.sort((a, b) => b.recent_stats.win_rate - a.recent_stats.win_rate);
  } catch {
    teamStats = [];
  }

  const season = new Date().getFullYear();

  return (
    <main style={{ maxWidth: 1280, margin: "0 auto", padding: "32px" }}>
      <div style={{ marginBottom: 24 }}>
        <div style={{ fontSize: 13, color: "#4a5872", fontFamily: "var(--font-mono)" }}>
          {season} KBO 정규시즌
        </div>
        <h1 style={{ fontSize: 36, fontWeight: 700, letterSpacing: "-0.02em", margin: "6px 0 0", color: "#0a0a0a" }}>
          통계
        </h1>
        <p style={{ fontSize: 14, color: "#4a5872", marginTop: 6 }}>최근 10경기 기준</p>
      </div>

      {teamStats.length === 0 ? (
        <div style={{ textAlign: "center", padding: "80px 0", color: "#7886a0" }}>
          <div style={{ fontSize: 36, marginBottom: 12, opacity: 0.5 }}>📊</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a", marginBottom: 4 }}>
            통계 데이터를 불러올 수 없습니다
          </div>
          <div style={{ fontSize: 13 }}>잠시 후 다시 시도해주세요</div>
        </div>
      ) : (
        <TeamStatTable stats={teamStats} />
      )}
    </main>
  );
}
