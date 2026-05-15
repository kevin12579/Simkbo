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

  return (
    <main className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">팀 통계</h1>
      <p className="text-gray-400 text-sm mb-6">최근 10경기 기준</p>

      {teamStats.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">📊</p>
          <p className="font-medium">통계 데이터를 불러올 수 없습니다.</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl shadow-md p-4">
          <TeamStatTable stats={teamStats} />
        </div>
      )}
    </main>
  );
}
