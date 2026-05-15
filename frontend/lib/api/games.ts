import apiClient from "./client";
import type { GameCard, TodayGamesResponse } from "@/types";

export async function fetchTodayGames(date?: string): Promise<TodayGamesResponse> {
  const params = date ? { target_date: date } : {};
  const { data } = await apiClient.get<TodayGamesResponse>("/games/today", { params });
  return data;
}

export async function fetchGamePrediction(gameId: number): Promise<GameCard> {
  const { data } = await apiClient.get<GameCard>(`/games/${gameId}/prediction`);
  return data;
}
