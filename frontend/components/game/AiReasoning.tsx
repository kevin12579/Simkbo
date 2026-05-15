interface Props {
  reasoning: string;
}

export default function AiReasoning({ reasoning }: Props) {
  return (
    <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-blue-600 text-lg">🤖</span>
        <h3 className="font-semibold text-blue-800 text-sm">AI 예측 근거</h3>
      </div>
      <p className="text-gray-700 text-sm leading-relaxed">{reasoning}</p>
    </div>
  );
}
