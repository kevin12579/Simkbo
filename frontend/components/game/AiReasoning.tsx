interface Props {
  reasoning: string;
}

export default function AiReasoning({ reasoning }: Props) {
  return (
    <div style={{
      background: "linear-gradient(160deg, #eef2fa, #f5f8fd)",
      border: "1px solid #dce4f0", borderRadius: 12, padding: 22,
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
        <span style={{ color: "#9a6f0a", fontSize: 16 }}>✦</span>
        <span style={{ fontSize: 14, fontWeight: 600 }}>AI 분석 근거</span>
      </div>
      <p style={{ fontSize: 13.5, lineHeight: 1.75, color: "#2a3548", margin: 0 }}>
        {reasoning}
      </p>
    </div>
  );
}
