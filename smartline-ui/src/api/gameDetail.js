import { API_BASE_URL } from "./config";

export async function fetchGameDetail(gameId) {
  const res = await fetch(`${API_BASE_URL}/games/${gameId}`);

  if (!res.ok) {
    throw new Error("Failed to load game detail");
  }

  return res.json();
}
