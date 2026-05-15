import TeamMark from "@/components/game/TeamMark";
import type { TeamStats } from "@/types";

interface Props {
  stats: TeamStats[];
}

export default function TeamStatTable({ stats }: Props) {
  return (
    <div style={{ border: "1px solid #dce4f0", borderRadius: 10, overflow: "hidden", background: "#fff" }}>
      {/* Header row */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "50px 2fr 80px 70px 70px 100px 120px 90px",
        padding: "12px 20px",
        fontSize: 11, color: "#7886a0", letterSpacing: "0.08em", fontWeight: 600,
        background: "#f5f8fd", borderBottom: "1px solid #dce4f0",
      }}>
        <span>순위</span>
        <span>팀</span>
        <span style={{ textAlign: "right" }}>경기</span>
        <span style={{ textAlign: "right" }}>승</span>
        <span style={{ textAlign: "right" }}>패</span>
        <span style={{ textAlign: "right" }}>승률</span>
        <span style={{ textAlign: "right" }}>평균 득점</span>
        <span style={{ textAlign: "right" }}>연속</span>
      </div>

      {stats.map((s, i) => {
        const { team, recent_stats } = s;
        const streakWin = recent_stats.streak.startsWith("W");
        return (
          <div key={team.id} style={{
            display: "grid",
            gridTemplateColumns: "50px 2fr 80px 70px 70px 100px 120px 90px",
            padding: "14px 20px",
            fontSize: 13, alignItems: "center",
            borderBottom: i < stats.length - 1 ? "1px solid #eef2f9" : "none",
            background: i < 5 ? "#fff" : "#fafcff",
          }}>
            <span style={{
              fontFamily: "var(--font-mono)", fontWeight: 700,
              color: i < 5 ? "#c8102e" : "#9aa5bd",
            }}>
              {String(i + 1).padStart(2, "0")}
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <TeamMark shortName={team.short_name} size={28} />
              <span style={{ fontWeight: 600 }}>{team.short_name}</span>
            </span>
            <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", color: "#4a5872" }}>
              {recent_stats.last_n_games}
            </span>
            <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 600 }}>
              {recent_stats.wins}
            </span>
            <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", color: "#4a5872" }}>
              {recent_stats.losses}
            </span>
            <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 14 }}>
              {(recent_stats.win_rate * 100).toFixed(1)}%
            </span>
            <span style={{ textAlign: "right", fontFamily: "var(--font-mono)", fontSize: 12, color: "#4a5872" }}>
              {recent_stats.avg_runs_scored.toFixed(1)}
            </span>
            <span style={{
              textAlign: "right", fontFamily: "var(--font-mono)", fontWeight: 700, fontSize: 13,
              color: streakWin ? "#1a7a3a" : "#c8102e",
            }}>
              {recent_stats.streak}
            </span>
          </div>
        );
      })}
    </div>
  );
}
