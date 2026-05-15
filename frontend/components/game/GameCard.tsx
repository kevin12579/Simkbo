"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import type { GameCard as GameCardType } from "@/types";
import ProbabilityBar from "./ProbabilityBar";
import ConfidenceBadge from "./ConfidenceBadge";
import { formatGameTime } from "@/lib/utils/date";

interface Props {
  game: GameCardType;
}

export default function GameCard({ game }: Props) {
  const { game_id, scheduled_at, stadium, home_team, away_team, prediction } = game;
  const [gameTime, setGameTime] = useState("");

  useEffect(() => {
    setGameTime(formatGameTime(scheduled_at));
  }, [scheduled_at]);

  return (
    <Link href={`/games/${game_id}`}>
      <div className="bg-white rounded-xl shadow-md p-5 hover:shadow-lg transition-shadow cursor-pointer border border-gray-100">
        <div className="flex justify-between items-center mb-3 text-sm text-gray-500">
          <span>{gameTime}</span>
          <span>{stadium}</span>
        </div>

        <div className="flex justify-between items-center mb-4">
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-800">{home_team.short_name}</p>
            <p className="text-xs text-gray-400">홈</p>
          </div>
          <div className="text-gray-400 font-bold text-lg">VS</div>
          <div className="text-center">
            <p className="text-2xl font-bold text-gray-800">{away_team.short_name}</p>
            <p className="text-xs text-gray-400">원정</p>
          </div>
        </div>

        {prediction ? (
          <div className="space-y-3">
            <ProbabilityBar
              homeTeamName={home_team.short_name}
              awayTeamName={away_team.short_name}
              homeWinProb={prediction.home_win_prob}
              awayWinProb={prediction.away_win_prob}
            />
            <div className="flex justify-between items-center">
              <ConfidenceBadge level={prediction.confidence_level} />
              {prediction.home_starter && (
                <p className="text-xs text-gray-500">
                  선발: {prediction.home_starter.name} vs {prediction.away_starter?.name ?? "TBD"}
                </p>
              )}
            </div>
          </div>
        ) : (
          <p className="text-center text-gray-400 text-sm py-2">예측 준비 중...</p>
        )}
      </div>
    </Link>
  );
}
