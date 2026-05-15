"use client";

export default function Error({ reset }: { reset: () => void }) {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center text-gray-400">
        <p className="text-5xl mb-4">⚠️</p>
        <h2 className="text-xl font-bold text-gray-700 mb-2">오류가 발생했습니다</h2>
        <button
          onClick={reset}
          className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700"
        >
          다시 시도
        </button>
      </div>
    </div>
  );
}
