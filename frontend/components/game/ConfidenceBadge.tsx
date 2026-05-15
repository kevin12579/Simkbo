import { confidenceColor, formatConfidence } from "@/lib/utils/format";

interface Props {
  level: "HIGH" | "MEDIUM" | "LOW";
}

export default function ConfidenceBadge({ level }: Props) {
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${confidenceColor(level)}`}>
      신뢰도 {formatConfidence(level)}
    </span>
  );
}
