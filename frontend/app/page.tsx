import { fetchTodayGames } from "@/lib/api/games";
import GameCard from "@/components/game/GameCard";
import { formatKoreanDate } from "@/lib/utils/date";

export const revalidate = 1800;

export default async function HomePage() {
  let data;
  try {
    data = await fetchTodayGames();
  } catch {
    data = { date: "", games: [], total: 0 };
  }

  const today = formatKoreanDate(new Date().toISOString());

  return (
    <main className="max-w-2xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">오늘의 경기 예측</h1>
      <p className="text-gray-400 text-sm mb-6">{today}</p>

      {data.total === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">⚾</p>
          <p className="font-medium">오늘은 KBO 경기가 없습니다.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {data.games.map((game) => (
            <GameCard key={game.game_id} game={game} />
          ))}
        </div>
      )}
    </main>
  );
}
