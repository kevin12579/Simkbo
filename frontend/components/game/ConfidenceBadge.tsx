interface Props {
  level: "HIGH" | "MEDIUM" | "LOW";
}

const CONF_MAP = {
  HIGH:   { bg: "#e8f5ec", fg: "#1a7a3a", label: "신뢰도 높음" },
  MEDIUM: { bg: "#fdf4e1", fg: "#9a6f0a", label: "신뢰도 보통" },
  LOW:    { bg: "#f0f0ee", fg: "#7a7a78", label: "신뢰도 낮음" },
};

export default function ConfidenceBadge({ level }: Props) {
  const s = CONF_MAP[level];
  return (
    <span style={{
      background: s.bg,
      color: s.fg,
      fontSize: 11,
      fontWeight: 600,
      padding: "4px 9px",
      borderRadius: 4,
      display: "inline-flex",
      alignItems: "center",
      gap: 5,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: 3, background: s.fg, display: "inline-block" }} />
      {s.label}
    </span>
  );
}
