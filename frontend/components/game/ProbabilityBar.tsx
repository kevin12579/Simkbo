import { getTeamColor } from "@/lib/utils/teamColors";

interface Props {
  homeTeamName: string;
  awayTeamName: string;
  homeWinProb: number;
  awayWinProb: number;
  height?: number;
}

export default function ProbabilityBar({
  homeTeamName,
  awayTeamName,
  homeWinProb,
  height = 8,
}: Props) {
  const homePercent = Math.round(homeWinProb * 100);
  const awayPercent = 100 - homePercent;
  const homeColor = getTeamColor(homeTeamName);
  const awayColor = getTeamColor(awayTeamName);

  return (
    <div style={{ display: "flex", height, borderRadius: 999, overflow: "hidden", background: "#eeeeec" }}>
      <div style={{ width: `${homePercent}%`, background: homeColor, transition: "width 0.4s" }} />
      <div style={{ width: `${awayPercent}%`, background: awayColor, transition: "width 0.4s" }} />
    </div>
  );
}
