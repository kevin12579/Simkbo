import type { TeamStats } from "@/types";

interface Props {
  stats: TeamStats[];
}

export default function TeamStatTable({ stats }: Props) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-center">
        <thead>
          <tr className="border-b border-gray-200 text-gray-500 text-xs">
            <th className="pb-2 text-left pl-2">팀</th>
            <th className="pb-2">경기</th>
            <th className="pb-2">승</th>
            <th className="pb-2">패</th>
            <th className="pb-2">승률</th>
            <th className="pb-2">평균득점</th>
            <th className="pb-2">연속</th>
          </tr>
        </thead>
        <tbody>
          {stats.map((s) => (
            <tr key={s.team.id} className="border-b border-gray-100 hover:bg-gray-50">
              <td className="py-2 text-left pl-2 font-semibold text-gray-800">{s.team.short_name}</td>
              <td className="py-2 text-gray-600">{s.recent_stats.last_n_games}</td>
              <td className="py-2 text-blue-700 font-medium">{s.recent_stats.wins}</td>
              <td className="py-2 text-red-600 font-medium">{s.recent_stats.losses}</td>
              <td className="py-2 text-gray-700">{(s.recent_stats.win_rate * 100).toFixed(1)}%</td>
              <td className="py-2 text-gray-600">{s.recent_stats.avg_runs_scored.toFixed(1)}</td>
              <td className="py-2 text-gray-500 text-xs">{s.recent_stats.streak}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
