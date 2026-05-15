"use client";
import { useState, useMemo } from "react";
import Link from "next/link";
import GameCard from "@/components/game/GameCard";
import TeamMark from "@/components/game/TeamMark";
import type { GameCard as GameCardType } from "@/types";

interface Props {
  games: GameCardType[];
  today: string;
}

type Filter = "all" | "high" | "close";

const FILTERS: { id: Filter; label: string }[] = [
  { id: "all", label: "전체" },
  { id: "high", label: "신뢰도 높음" },
  { id: "close", label: "박빙" },
];

export default function HomeContent({ games, today }: Props) {
  const [filter, setFilter] = useState<Filter>("all");

  const filtered = useMemo(() => {
    if (filter === "high") return games.filter(g => g.prediction?.confidence_level === "HIGH");
    if (filter === "close") return games.filter(g => {
      const p = g.prediction?.home_win_prob ?? 0.5;
      return Math.abs(p - 0.5) < 0.1;
    });
    return games;
  }, [games, filter]);

  const bestGame = useMemo(() => {
    const withPrediction = games.filter(g => g.prediction);
    if (withPrediction.length === 0) return null;
    return withPrediction.sort((a, b) => {
      const aConf = Math.abs((a.prediction!.home_win_prob) - 0.5);
      const bConf = Math.abs((b.prediction!.home_win_prob) - 0.5);
      return bConf - aConf;
    })[0];
  }, [games]);

  const bestProb = bestGame?.prediction?.home_win_prob ?? 0.5;
  const bestFavHome = bestProb >= 0.5;
  const bestTeam = bestFavHome ? bestGame?.home_team : bestGame?.away_team;
  const bestOpp = bestFavHome ? bestGame?.away_team : bestGame?.home_team;
  const bestWinProb = Math.max(bestProb, 1 - bestProb);
  const bestDiff = Math.round(Math.abs(bestProb - 0.5) * 200);

  return (
    <main style={{ maxWidth: 1280, margin: "0 auto", padding: "32px" }}>
      {/* Page header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24 }}>
        <div>
          <div style={{ fontSize: 13, color: "#4a5872", fontFamily: "var(--font-mono)", letterSpacing: "0.04em" }}>
            {today}
          </div>
          <h1 style={{ fontSize: 36, fontWeight: 700, letterSpacing: "-0.02em", margin: "6px 0 0", color: "#0a0a0a" }}>
            오늘의 KBO 승부예측
          </h1>
          <p style={{ fontSize: 14, color: "#4a5872", marginTop: 6 }}>
            {games.length}경기 · XGBoost 모델이 분석한 승리 확률
          </p>
        </div>
        <Link href="/stats" style={{
          fontSize: 13, padding: "9px 16px", borderRadius: 6,
          background: "transparent", color: "#0a0a0a",
          border: "1px solid #c0cce0", textDecoration: "none", fontWeight: 500,
        }}>
          통계 보기 →
        </Link>
      </div>

      {/* Hero card: highest-confidence game */}
      {bestGame?.prediction && (
        <Link href={`/games/${bestGame.game_id}`} style={{ textDecoration: "none", display: "block", marginBottom: 32 }}>
          <div style={{
            background: "linear-gradient(135deg, #0a2a5e 0%, #1a3a6e 100%)",
            color: "#fff", borderRadius: 16, padding: "28px 32px",
            display: "grid", gridTemplateColumns: "1fr auto", gap: 32,
            cursor: "pointer", position: "relative", overflow: "hidden",
          }}>
            <div style={{
              position: "absolute", right: -40, top: -40,
              width: 240, height: 240, borderRadius: "50%",
              background: "rgba(200,16,46,0.25)", filter: "blur(60px)",
            }} />
            <div style={{ zIndex: 1 }}>
              <div style={{
                fontSize: 11, letterSpacing: "0.14em", color: "#9bb6e6",
                fontFamily: "var(--font-mono)", fontWeight: 600, marginBottom: 14,
              }}>
                ★ 오늘의 강력 추천
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 16 }}>
                {bestTeam && <TeamMark shortName={bestTeam.short_name} size={56} />}
                <div>
                  <div style={{ fontSize: 28, fontWeight: 700, letterSpacing: "-0.02em" }}>
                    {bestTeam?.short_name}
                  </div>
                  <div style={{ fontSize: 13, color: "#9bb6e6", marginTop: 4 }}>
                    {bestFavHome ? "홈" : "원정"} · vs {bestOpp?.short_name}
                  </div>
                </div>
              </div>
              <div style={{ fontSize: 13, color: "#cfdcf2", lineHeight: 1.65, maxWidth: 540 }}>
                선발 매치업과 최근 폼이 일치하는 가장 신뢰도 높은 경기입니다.
                모델이 확률 격차{" "}
                <b style={{ color: "#fff" }}>{bestDiff}%p</b>를 예측했습니다.
              </div>
            </div>
            <div style={{
              display: "flex", flexDirection: "column",
              justifyContent: "center", alignItems: "flex-end", zIndex: 1,
            }}>
              <div style={{
                fontFamily: "var(--font-mono)", fontSize: 72, fontWeight: 700,
                letterSpacing: "-0.04em", lineHeight: 1, color: "#fff",
              }}>
                {Math.round(bestWinProb * 100)}
                <span style={{ fontSize: 32, color: "#9bb6e6" }}>%</span>
              </div>
              <div style={{ fontSize: 12, color: "#9bb6e6", marginTop: 6, letterSpacing: "0.08em" }}>
                승리 확률
              </div>
              <div style={{ marginTop: 18, fontSize: 12, color: "#fff", opacity: 0.8 }}>
                상세 분석 보기 →
              </div>
            </div>
          </div>
        </Link>
      )}

      {/* Filter pills */}
      {games.length > 0 && (
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 6, marginBottom: 16 }}>
          {FILTERS.map(f => (
            <button key={f.id} onClick={() => setFilter(f.id)} style={{
              background: filter === f.id ? "#0a0a0a" : "transparent",
              color: filter === f.id ? "#fff" : "#4a5872",
              border: `1px solid ${filter === f.id ? "#0a0a0a" : "#c0cce0"}`,
              borderRadius: 999, padding: "5px 12px", fontSize: 12,
              cursor: "pointer", whiteSpace: "nowrap", fontFamily: "var(--font-sans)",
            }}>
              {f.label}
            </button>
          ))}
        </div>
      )}

      {/* Game grid */}
      {games.length === 0 ? (
        <div style={{ textAlign: "center", padding: "80px 0", color: "#7886a0" }}>
          <div style={{ fontSize: 36, marginBottom: 12, opacity: 0.5 }}>⚾</div>
          <div style={{ fontSize: 16, fontWeight: 600, color: "#0a0a0a", marginBottom: 4 }}>
            오늘은 KBO 경기가 없습니다
          </div>
          <div style={{ fontSize: 13 }}>내일 경기를 기대해주세요</div>
        </div>
      ) : (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(380px, 1fr))", gap: 16 }}>
          {filtered.map(game => (
            <GameCard key={game.game_id} game={game} />
          ))}
        </div>
      )}
    </main>
  );
}
