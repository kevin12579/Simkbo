import apiClient from "./client";
import type { PitcherStats } from "@/types";

export async function fetchPitcherStats(playerId: number): Promise<PitcherStats> {
  const { data } = await apiClient.get<PitcherStats>(`/pitchers/${playerId}/stats`);
  return data;
}
