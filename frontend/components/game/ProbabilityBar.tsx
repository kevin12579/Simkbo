import { formatProbability } from "@/lib/utils/format";

interface Props {
  homeTeamName: string;
  awayTeamName: string;
  homeWinProb: number;
  awayWinProb: number;
}

export default function ProbabilityBar({ homeTeamName, awayTeamName, homeWinProb, awayWinProb }: Props) {
  const homePercent = Math.round(homeWinProb * 100);
  const awayPercent = 100 - homePercent;

  return (
    <div className="w-full space-y-2">
      <div className="flex justify-between text-sm font-semibold">
        <span className="text-blue-700">{homeTeamName} {formatProbability(homeWinProb)}</span>
        <span className="text-red-700">{awayTeamName} {formatProbability(awayWinProb)}</span>
      </div>
      <div className="flex h-4 w-full rounded-full overflow-hidden">
        <div className="bg-blue-500 transition-all duration-500" style={{ width: `${homePercent}%` }} />
        <div className="bg-red-500 transition-all duration-500" style={{ width: `${awayPercent}%` }} />
      </div>
    </div>
  );
}
