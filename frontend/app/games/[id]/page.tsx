import { fetchGamePrediction } from "@/lib/api/games";
import ProbabilityBar from "@/components/game/ProbabilityBar";
import ConfidenceBadge from "@/components/game/ConfidenceBadge";
import AiReasoning from "@/components/game/AiReasoning";
import TeamMark from "@/components/game/TeamMark";
import { getTeamColor } from "@/lib/utils/teamColors";
import Link from "next/link";
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
  const gameTime = new Date(scheduled_at).toLocaleString("ko-KR", {
    month: "long", day: "numeric", weekday: "short",
    hour: "2-digit", minute: "2-digit",
  });

  const homeColor = getTeamColor(home_team.short_name);
  const awayColor = getTeamColor(away_team.short_name);
  const homeProb = prediction?.home_win_prob ?? 0.5;
  const favHome = homeProb >= 0.5;

  return (
    <main style={{ maxWidth: 1280, margin: "0 auto", padding: "32px" }}>
      <Link href="/" style={{
        display: "inline-flex", alignItems: "center", gap: 6,
        fontSize: 13, color: "#4a5872", textDecoration: "none", marginBottom: 20,
      }}>
        ← 오늘의 경기로
      </Link>

      {/* Matchup header */}
      <div style={{
        background: "#fff", border: "1px solid #dce4f0", borderRadius: 16,
        padding: "32px 40px", marginBottom: 20,
      }}>
        <div style={{
          display: "flex", justifyContent: "space-between", alignItems: "center",
          marginBottom: 24, fontSize: 13, color: "#4a5872", fontFamily: "var(--font-mono)",
        }}>
          <span>{gameTime}{stadium ? ` · ${stadium}` : ""}</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", alignItems: "center", gap: 20 }}>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
            <TeamMark shortName={home_team.short_name} size={72} />
            <div style={{ fontSize: 22, fontWeight: 700, textAlign: "center" }}>{home_team.short_name}</div>
            <div style={{ fontSize: 12, color: "#4a5872", fontFamily: "var(--font-mono)" }}>홈</div>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 32, color: "#c0cce0", fontFamily: "var(--font-mono)", letterSpacing: "0.1em" }}>VS</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
            <TeamMark shortName={away_team.short_name} size={72} />
            <div style={{ fontSize: 22, fontWeight: 700, textAlign: "center" }}>{away_team.short_name}</div>
            <div style={{ fontSize: 12, color: "#4a5872", fontFamily: "var(--font-mono)" }}>원정</div>
          </div>
        </div>
      </div>

      {prediction && (
        <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 20 }}>
          {/* Left column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {/* Probability card */}
            <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 12, padding: 28 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
                <h2 style={{ fontSize: 16, fontWeight: 600, margin: 0 }}>승리 확률</h2>
                <ConfidenceBadge level={prediction.confidence_level} />
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr 1fr", alignItems: "center", gap: 20 }}>
                <div>
                  <div style={{
                    fontFamily: "var(--font-mono)", fontSize: 42, fontWeight: 700,
                    letterSpacing: "-0.03em",
                    color: favHome ? homeColor : "#9aa5bd",
                  }}>
                    {Math.round(homeProb * 100)}<span style={{ fontSize: 22 }}>%</span>
                  </div>
                  <div style={{ fontSize: 12, color: "#4a5872", marginTop: 2 }}>{home_team.short_name}</div>
                </div>
                <ProbabilityBar
                  homeTeamName={home_team.short_name}
                  awayTeamName={away_team.short_name}
                  homeWinProb={prediction.home_win_prob}
                  awayWinProb={prediction.away_win_prob}
                  height={14}
                />
                <div style={{ textAlign: "right" }}>
                  <div style={{
                    fontFamily: "var(--font-mono)", fontSize: 42, fontWeight: 700,
                    letterSpacing: "-0.03em",
                    color: !favHome ? awayColor : "#9aa5bd",
                  }}>
                    {Math.round((1 - homeProb) * 100)}<span style={{ fontSize: 22 }}>%</span>
                  </div>
                  <div style={{ fontSize: 12, color: "#4a5872", marginTop: 2 }}>{away_team.short_name}</div>
                </div>
              </div>

              {(prediction.xgboost_home_prob != null || prediction.lstm_home_prob != null) && (
                <div style={{ marginTop: 20, paddingTop: 16, borderTop: "1px solid #e8eef7" }}>
                  <div style={{ fontSize: 11, color: "#7886a0", letterSpacing: "0.1em", marginBottom: 12, fontWeight: 600 }}>
                    모델 분해
                  </div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                    {prediction.xgboost_home_prob != null && (
                      <ModelBar
                        label="XGBoost"
                        homeProb={prediction.xgboost_home_prob}
                        homeColor={homeColor}
                        awayColor={awayColor}
                      />
                    )}
                    {prediction.lstm_home_prob != null && (
                      <ModelBar
                        label="LSTM"
                        homeProb={prediction.lstm_home_prob}
                        homeColor={homeColor}
                        awayColor={awayColor}
                      />
                    )}
                    <ModelBar
                      label="앙상블"
                      homeProb={homeProb}
                      homeColor={homeColor}
                      awayColor={awayColor}
                      highlight
                    />
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right column */}
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {prediction.ai_reasoning && (
              <AiReasoning reasoning={prediction.ai_reasoning} />
            )}

            {(prediction.home_starter || prediction.away_starter) && (
              <div style={{ background: "#fff", border: "1px solid #dce4f0", borderRadius: 12, padding: 24 }}>
                <h2 style={{ fontSize: 16, fontWeight: 600, margin: "0 0 16px" }}>선발 투수 매치업</h2>
                <PitcherRow
                  teamName={home_team.short_name}
                  pitcher={prediction.home_starter}
                  side="홈"
                />
                <div style={{ height: 1, background: "#e8eef7", margin: "16px 0" }} />
                <PitcherRow
                  teamName={away_team.short_name}
                  pitcher={prediction.away_starter}
                  side="원정"
                />
              </div>
            )}
          </div>
        </div>
      )}
    </main>
  );
}

function ModelBar({
  label, homeProb, homeColor, awayColor, highlight = false,
}: {
  label: string; homeProb: number; homeColor: string; awayColor: string; highlight?: boolean;
}) {
  const hPct = Math.round(homeProb * 100);
  const aPct = 100 - hPct;
  return (
    <div style={{ display: "grid", gridTemplateColumns: "70px 1fr 50px", alignItems: "center", gap: 12 }}>
      <span style={{
        fontSize: 12, fontWeight: highlight ? 700 : 500,
        color: highlight ? "#0a0a0a" : "#4a5872", fontFamily: "var(--font-mono)",
      }}>{label}</span>
      <div style={{ position: "relative", height: 24, background: "#eef2f9", borderRadius: 4, overflow: "hidden", display: "flex" }}>
        <div style={{ width: `${hPct}%`, background: homeColor, opacity: highlight ? 1 : 0.7 }} />
        <div style={{ width: `${aPct}%`, background: awayColor, opacity: highlight ? 1 : 0.7 }} />
        <span style={{
          position: "absolute", inset: 0, display: "grid", placeItems: "center",
          fontSize: 11, fontFamily: "var(--font-mono)", color: "#fff", fontWeight: 600,
          textShadow: "0 0 4px rgba(0,0,0,0.4)",
        }}>
          {hPct} / {aPct}
        </span>
      </div>
    </div>
  );
}

function PitcherRow({
  teamName, pitcher, side,
}: {
  teamName: string;
  pitcher?: { player_id: number; name: string; recent_era?: number } | null;
  side: string;
}) {
  if (!pitcher) {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
        <TeamMark shortName={teamName} size={32} />
        <div>
          <div style={{ fontSize: 14, fontWeight: 600, color: "#9aa5bd" }}>선발 미정</div>
          <div style={{ fontSize: 11, color: "#9aa5bd", marginTop: 2 }}>{side}</div>
        </div>
      </div>
    );
  }
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      <TeamMark shortName={teamName} size={32} />
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 15, fontWeight: 600 }}>{pitcher.name}</div>
        <div style={{ fontSize: 11, color: "#7886a0", marginTop: 1 }}>{side}</div>
      </div>
      {pitcher.recent_era != null && (
        <div style={{ background: "#f5f8fd", borderRadius: 6, padding: "8px 12px", textAlign: "center" }}>
          <div style={{ fontSize: 10, color: "#7886a0", letterSpacing: "0.06em" }}>ERA</div>
          <div style={{ fontSize: 16, fontWeight: 700, fontFamily: "var(--font-mono)", marginTop: 2 }}>
            {pitcher.recent_era.toFixed(2)}
          </div>
        </div>
      )}
    </div>
  );
}
