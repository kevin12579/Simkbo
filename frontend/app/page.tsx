import { fetchTodayGames } from "@/lib/api/games";
import HomeContent from "@/components/home/HomeContent";

export const revalidate = 1800;

export default async function HomePage() {
  let data;
  try {
    data = await fetchTodayGames();
  } catch {
    data = { date: "", games: [], total: 0 };
  }

  const today = new Date().toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    weekday: "short",
  });

  return <HomeContent games={data.games} today={today} />;
}
