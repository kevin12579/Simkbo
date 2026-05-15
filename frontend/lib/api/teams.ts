import apiClient from "./client";
import type { Team, TeamStats } from "@/types";

export async function fetchTeams(): Promise<Team[]> {
  const { data } = await apiClient.get<Team[]>("/teams");
  return data;
}

export async function fetchTeamStats(teamId: number): Promise<TeamStats> {
  const { data } = await apiClient.get<TeamStats>(`/teams/${teamId}/stats`);
  return data;
}
