export function formatProbability(prob: number): string {
  return `${(prob * 100).toFixed(1)}%`;
}

export function formatEra(era: number): string {
  return era.toFixed(2);
}

export function formatConfidence(level: "HIGH" | "MEDIUM" | "LOW"): string {
  const map = { HIGH: "높음", MEDIUM: "보통", LOW: "낮음" };
  return map[level];
}

export function confidenceColor(level: "HIGH" | "MEDIUM" | "LOW"): string {
  const map = {
    HIGH: "bg-green-100 text-green-800",
    MEDIUM: "bg-yellow-100 text-yellow-800",
    LOW: "bg-gray-100 text-gray-600",
  };
  return map[level];
}
