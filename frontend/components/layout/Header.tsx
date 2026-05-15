import Link from "next/link";

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
      <nav className="max-w-2xl mx-auto px-4 py-3 flex justify-between items-center">
        <Link href="/" className="font-bold text-lg text-blue-700">⚾ KBO 예측</Link>
        <div className="flex gap-4 text-sm font-medium text-gray-600">
          <Link href="/" className="hover:text-blue-700">오늘 경기</Link>
          <Link href="/stats" className="hover:text-blue-700">통계</Link>
        </div>
      </nav>
    </header>
  );
}
