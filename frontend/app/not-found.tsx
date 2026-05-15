import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center text-gray-400">
        <p className="text-5xl mb-4">⚾</p>
        <h2 className="text-xl font-bold text-gray-700 mb-2">페이지를 찾을 수 없습니다</h2>
        <p className="text-sm mb-6">요청하신 경기 또는 페이지가 존재하지 않습니다.</p>
        <Link href="/" className="text-blue-600 hover:underline text-sm font-medium">
          홈으로 돌아가기
        </Link>
      </div>
    </div>
  );
}
