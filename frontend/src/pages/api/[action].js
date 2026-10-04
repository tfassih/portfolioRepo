import { createHmac } from "node:crypto";
import { post } from "../../lib/backend.js";

export async function POST({ request, url, params, clientAddress, redirect }) {
    const action = params.action;
  if (!["subscribe", "confirm", "track"].includes(action))
    return new Response(null, { status: 404 });
  if (request.headers.get("origin") !== url.origin)
    return new Response(null, { status: 403 });
  const raw = await request.text();
  if (raw.length > 4096) return new Response(null, { status: 413 });
  let body;
  try {
    body =
      action === "track"
        ? JSON.parse(raw)
        : Object.fromEntries(new URLSearchParams(raw));
    body.client_key = createHmac("sha256", import.meta.env.INTERNAL_API_KEY)
      .update(clientAddress)
      .digest("hex");
    const response = await post(action, body);
    if (action === "track")
      return new Response(null, { status: response.ok ? 204 : 400 });
    if (!response.ok) return redirect("/subscribe/?state=error", 303);
    return redirect(
      action === "confirm" ? "/subscribe/confirm/?done=1" : "/subscribe/",
      303,
    );
  } catch (_) {
    return action === "track"
      ? new Response(null, { status: 503 })
      : redirect("/subscribe/?state=error", 303);
  }
}