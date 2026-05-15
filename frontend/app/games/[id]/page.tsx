import { fetchGamePrediction } from "@/lib/api/games";
import ProbabilityBar from "@/components/game/ProbabilityBar";
import ConfidenceBadge from "@/components/game/ConfidenceBadge";
import AiReasoning from "@/components/game/AiReasoning";
import { notFound } from "next/navigation";

interface Props {
  params: { id: string };
}

export default async function GameDetailPage({ params }: Props) {
  let game;
  try {
    game = await fetchGamePrediction(Number(params.id));
  } catch {
    notFound();
  }

  const { home_team, away_team, prediction, scheduled_at, stadium } = game;
  const gameTime = new Date(scheduled_at).toLocaleString("ko-KR");

  return (
    <main className="max-w-2xl mx-auto px-4 py-8 space-y-6">
      <div className="bg-white rounded-xl shadow-md p-6 text-center">
        <p className="text-gray-400 text-sm mb-1">{gameTime} · {stadium}</p>
        <div className="flex justify-around items-center mt-3">
          <div>
            <p className="text-3xl font-bold">{home_team.short_name}</p>
            <p className="text-xs text-gray-400 mt-1">홈</p>
          </div>
          <span className="text-gray-300 font-bold text-xl">VS</span>
          <div>
            <p className="text-3xl font-bold">{away_team.short_name}</p>
            <p className="text-xs text-gray-400 mt-1">원정</p>
          </div>
        </div>
      </div>

      {prediction && (
        <>
          <div className="bg-white rounded-xl shadow-md p-6 space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="font-bold text-gray-800">승리 확률</h2>
              <ConfidenceBadge level={prediction.confidence_level} />
            </div>
            <ProbabilityBar
              homeTeamName={home_team.short_name}
              awayTeamName={away_team.short_name}
              homeWinProb={prediction.home_win_prob}
              awayWinProb={prediction.away_win_prob}
            />
            {prediction.xgboost_home_prob && (
              <div className="text-xs text-gray-400 space-y-1">
                <p>XGBoost: {(prediction.xgboost_home_prob * 100).toFixed(1)}% / {((1 - prediction.xgboost_home_prob) * 100).toFixed(1)}%</p>
                {prediction.lstm_home_prob && (
                  <p>LSTM: {(prediction.lstm_home_prob * 100).toFixed(1)}% / {((1 - prediction.lstm_home_prob) * 100).toFixed(1)}%</p>
                )}
              </div>
            )}
          </div>

          {prediction.ai_reasoning && (
            <AiReasoning reasoning={prediction.ai_reasoning} />
          )}

          {(prediction.home_starter || prediction.away_starter) && (
            <div className="bg-white rounded-xl shadow-md p-6">
              <h2 className="font-bold text-gray-800 mb-3">선발 투수</h2>
              <div className="flex justify-around">
                <div className="text-center">
                  <p className="font-semibold">{prediction.home_starter?.name ?? "TBD"}</p>
                  {prediction.home_starter?.recent_era && (
                    <p className="text-sm text-gray-500">ERA {prediction.home_starter.recent_era.toFixed(2)}</p>
                  )}
                </div>
                <div className="text-center">
                  <p className="font-semibold">{prediction.away_starter?.name ?? "TBD"}</p>
                  {prediction.away_starter?.recent_era && (
                    <p className="text-sm text-gray-500">ERA {prediction.away_starter.recent_era.toFixed(2)}</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </>
      )}
    </main>
  );
}
