const origin = import.meta.env.API_ORIGIN;
export async function get(path) {
  const response = await fetch(origin + path, {
    signal: AbortSignal.timeout(15000),
  });
  if (!response.ok) {
    const error = new Error("Content service unavailable");
    error.status = response.status;
    throw error;
  }
  return response.json();
}
export async function post(action, body) {
  return fetch(origin + "/internal/" + action + "/", {
    method: "POST",
    signal: AbortSignal.timeout(100000),
    headers: {
      "Content-Type": "application/json",
      Authorization: "Bearer " + import.meta.env.INTERNAL_API_KEY,
    },
    body: JSON.stringify(body),
  });
}
export const date = (value) =>
  new Intl.DateTimeFormat("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    timeZone: "America/Chicago",
  }).format(new Date(value));