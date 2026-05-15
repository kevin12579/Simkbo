"use client";
import Link from "next/link";
import { useState, useEffect } from "react";
import type { GameCard as GameCardType } from "@/types";
import ProbabilityBar from "./ProbabilityBar";
import ConfidenceBadge from "./ConfidenceBadge";
import TeamMark from "./TeamMark";
import { getTeamColor } from "@/lib/utils/teamColors";
import { formatGameTime } from "@/lib/utils/date";

interface Props {
  game: GameCardType;
}

export default function GameCard({ game }: Props) {
  const { game_id, scheduled_at, stadium, home_team, away_team, prediction } = game;
  const [gameTime, setGameTime] = useState("");
  const [hov, setHov] = useState(false);

  useEffect(() => {
    setGameTime(formatGameTime(scheduled_at));
  }, [scheduled_at]);

  const homeColor = getTeamColor(home_team.short_name);
  const awayColor = getTeamColor(away_team.short_name);
  const homeProb = prediction?.home_win_prob ?? 0.5;
  const hPct = Math.round(homeProb * 100);
  const aPct = 100 - hPct;
  const favHome = homeProb >= 0.5;

  return (
    <Link href={`/games/${game_id}`} style={{ textDecoration: "none" }}>
      <div
        onMouseEnter={() => setHov(true)}
        onMouseLeave={() => setHov(false)}
        style={{
          background: "#fff",
          border: "1px solid #dce4f0",
          borderRadius: 12,
          padding: 20,
          transition: "all 0.15s",
          position: "relative",
          overflow: "hidden",
          boxShadow: hov ? "0 8px 24px rgba(10,42,94,0.10)" : "0 1px 2px rgba(10,42,94,0.03)",
          transform: hov ? "translateY(-2px)" : "translateY(0)",
          cursor: "pointer",
        }}
      >
        {/* Top team-color accent bar */}
        <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 4, display: "flex" }}>
          <div style={{ flex: homeProb, background: homeColor }} />
          <div style={{ flex: 1 - homeProb, background: awayColor }} />
        </div>

        {/* Time + Stadium */}
        <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 16, marginTop: 6 }}>
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 13, fontWeight: 600, color: "#0a0a0a" }}>
            {gameTime}
          </span>
          {stadium && (
            <>
              <span style={{ color: "#c0cce0" }}>·</span>
              <span style={{ fontSize: 12, color: "#7886a0" }}>{stadium}</span>
            </>
          )}
        </div>

        {/* Teams + Probability number */}
        <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", alignItems: "center", gap: 12, marginBottom: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, opacity: prediction ? (favHome ? 1 : 0.55) : 1 }}>
            <TeamMark shortName={home_team.short_name} size={36} />
            <div style={{ minWidth: 0 }}>
              <div style={{
                fontSize: 15, fontWeight: 600, whiteSpace: "nowrap",
                overflow: "hidden", textOverflow: "ellipsis",
                color: prediction && favHome ? homeColor : "#0a0a0a",
              }}>
                {home_team.short_name}
              </div>
              <div style={{ fontSize: 11, color: "#7886a0", marginTop: 2 }}>홈</div>
            </div>
          </div>

          {prediction ? (
            <div style={{ textAlign: "center", fontFamily: "var(--font-mono)" }}>
              <div style={{ fontSize: 22, fontWeight: 700, letterSpacing: "-0.02em" }}>
                <span style={{ color: favHome ? homeColor : "#c0cce0" }}>{hPct}</span>
                <span style={{ color: "#c0cce0", margin: "0 4px" }}>:</span>
                <span style={{ color: !favHome ? awayColor : "#c0cce0" }}>{aPct}</span>
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", color: "#c0cce0", fontWeight: 700, fontSize: 16 }}>VS</div>
          )}

          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            opacity: prediction ? (!favHome ? 1 : 0.55) : 1,
            justifyContent: "flex-end", minWidth: 0,
          }}>
            <div style={{ textAlign: "right", minWidth: 0 }}>
              <div style={{
                fontSize: 15, fontWeight: 600, whiteSpace: "nowrap",
                overflow: "hidden", textOverflow: "ellipsis",
                color: prediction && !favHome ? awayColor : "#0a0a0a",
              }}>
                {away_team.short_name}
              </div>
              <div style={{ fontSize: 11, color: "#7886a0", marginTop: 2 }}>원정</div>
            </div>
            <TeamMark shortName={away_team.short_name} size={36} />
          </div>
        </div>

        {prediction ? (
          <>
            <ProbabilityBar
              homeTeamName={home_team.short_name}
              awayTeamName={away_team.short_name}
              homeWinProb={prediction.home_win_prob}
              awayWinProb={prediction.away_win_prob}
              height={6}
            />

            <div style={{
              display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12,
              marginTop: 14, fontSize: 12, fontFamily: "var(--font-mono)",
            }}>
              <div style={{ color: "#4a5872" }}>
                {prediction.home_starter
                  ? <><b style={{ color: "#0a0a0a" }}>{prediction.home_starter.name}</b>
                      {prediction.home_starter.recent_era
                        ? ` ERA ${prediction.home_starter.recent_era.toFixed(2)}`
                        : ""}</>
                  : <span style={{ color: "#9aa5bd" }}>선발 미정</span>
                }
              </div>
              <div style={{ color: "#4a5872", textAlign: "right" }}>
                {prediction.away_starter
                  ? <><b style={{ color: "#0a0a0a" }}>{prediction.away_starter.name}</b>
                      {prediction.away_starter.recent_era
                        ? ` ERA ${prediction.away_starter.recent_era.toFixed(2)}`
                        : ""}</>
                  : <span style={{ color: "#9aa5bd" }}>선발 미정</span>
                }
              </div>
            </div>

            <div style={{ marginTop: 16, paddingTop: 14, borderTop: "1px solid #e8eef7" }}>
              <ConfidenceBadge level={prediction.confidence_level} />
            </div>
          </>
        ) : (
          <p style={{ textAlign: "center", color: "#9aa5bd", fontSize: 13, padding: "8px 0" }}>
            예측 준비 중...
          </p>
        )}
      </div>
    </Link>
  );
}
