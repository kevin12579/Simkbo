import { getTeamColor } from "@/lib/utils/teamColors";

interface Props {
  shortName: string;
  size?: number;
}

export default function TeamMark({ shortName, size = 36 }: Props) {
  const color = getTeamColor(shortName);
  return (
    <div style={{
      width: size,
      height: size,
      borderRadius: 6,
      background: color,
      color: "#fff",
      display: "grid",
      placeItems: "center",
      fontFamily: "var(--font-mono)",
      fontSize: size * 0.34,
      fontWeight: 700,
      letterSpacing: "0.02em",
      flexShrink: 0,
    }}>
      {shortName}
    </div>
  );
}
