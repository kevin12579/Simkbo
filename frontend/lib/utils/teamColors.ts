export const TEAM_COLORS: Record<string, string> = {
  "두산": "#131230",
  "LG": "#C30452",
  "키움": "#570514",
  "KT": "#000000",
  "SSG": "#CE0E2D",
  "NC": "#315288",
  "KIA": "#EA0029",
  "롯데": "#041E42",
  "삼성": "#074CA1",
  "한화": "#FF6600",
};

export function getTeamColor(shortName: string): string {
  return TEAM_COLORS[shortName] ?? "#4a5872";
}
