import { API_BASE_URL } from "./config";

export async function fetchGames(season, week) {
  const params = new URLSearchParams({ season, week });
  const url = `${API_BASE_URL}/games?${params.toString()}`;

  const res = await fetch(url);
  console.log("API BASE:", API_BASE_URL);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API error: ${res.status} ${text}`);
  }

  return res.json();
}
