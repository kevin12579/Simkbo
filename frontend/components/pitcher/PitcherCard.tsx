import type { PitcherStats } from "@/types";
import { formatEra } from "@/lib/utils/format";

interface Props {
  pitcher: PitcherStats;
}

export default function PitcherCard({ pitcher }: Props) {
  const latest = pitcher.recent_games[0];

  return (
    <div className="bg-white rounded-xl shadow-md p-4 border border-gray-100">
      <div className="flex justify-between items-start mb-3">
        <div>
          <p className="font-bold text-gray-800">{pitcher.name}</p>
          <p className="text-xs text-gray-500">{pitcher.team_name}</p>
        </div>
        {latest?.era != null && (
          <div className="text-right">
            <p className="text-sm font-semibold text-blue-700">ERA {formatEra(latest.era)}</p>
            {latest.whip != null && (
              <p className="text-xs text-gray-500">WHIP {latest.whip.toFixed(2)}</p>
            )}
          </div>
        )}
      </div>

      {pitcher.recent_games.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-center text-gray-600">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="pb-1">이닝</th>
                <th className="pb-1">자책</th>
                <th className="pb-1">삼진</th>
                <th className="pb-1">볼넷</th>
                <th className="pb-1">ERA</th>
              </tr>
            </thead>
            <tbody>
              {pitcher.recent_games.map((g) => (
                <tr key={g.game_id} className="border-b border-gray-50">
                  <td className="py-1">{g.innings_pitched ?? "-"}</td>
                  <td>{g.earned_runs ?? "-"}</td>
                  <td>{g.strikeouts ?? "-"}</td>
                  <td>{g.walks ?? "-"}</td>
                  <td>{g.era != null ? formatEra(g.era) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
