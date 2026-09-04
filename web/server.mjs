import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { WebSocketServer } from "ws";

const root = path.dirname(fileURLToPath(import.meta.url));
const manifestPath = path.join(root, "public", "assets", "scene-manifest.json");
const manifest = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
const bindable = manifest.assets.filter((item) => item.asset_id);
const state = new Map(bindable.map((item, index) => [item.asset_id, {
  asset_id: item.asset_id,
  object_id: item.object_id,
  asset_type: item.asset_type,
  status: item.object_id === "server_b3_u3" ? "alarm" : "online",
  temperature_c: item.object_id === "server_b3_u3" ? 46.8 : 22.8 + (index % 7) * 0.55,
  cpu_percent: 18 + (index * 13) % 61,
  power_kw: Number((0.35 + (index % 6) * 0.16).toFixed(2)),
  updated_at: new Date().toISOString(),
}]));

const mime = { ".html": "text/html; charset=utf-8", ".js": "text/javascript", ".css": "text/css", ".glb": "model/gltf-binary", ".json": "application/json" };
function json(res, payload, status = 200) {
  res.writeHead(status, { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" });
  res.end(JSON.stringify(payload));
}

const server = http.createServer((req, res) => {
  const url = new URL(req.url, "http://localhost");
  if (url.pathname === "/api/health") return json(res, { ok: true, scene_id: manifest.scene_id, assets: state.size });
  if (url.pathname === "/api/assets") return json(res, [...state.values()]);
  if (url.pathname.startsWith("/api/assets/")) {
    const id = decodeURIComponent(url.pathname.slice("/api/assets/".length));
    return state.has(id) ? json(res, state.get(id)) : json(res, { error: "asset_not_found" }, 404);
  }
  if (process.argv.includes("--api-only")) return json(res, { error: "not_found" }, 404);

  const dist = path.join(root, "dist");
  let requested = url.pathname === "/" ? "index.html" : url.pathname.slice(1);
  let file = path.resolve(dist, requested);
  if (!file.startsWith(path.resolve(dist))) return json(res, { error: "invalid_path" }, 400);
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) file = path.join(dist, "index.html");
  res.writeHead(200, { "content-type": mime[path.extname(file)] || "application/octet-stream" });
  fs.createReadStream(file).pipe(res);
});

const wss = new WebSocketServer({ server, path: "/ws" });
wss.on("connection", (socket) => socket.send(JSON.stringify({ type: "snapshot", assets: [...state.values()] })));

setInterval(() => {
  for (const [id, item] of state) {
    const next = { ...item, updated_at: new Date().toISOString() };
    if (item.object_id === "server_b3_u3") {
      next.temperature_c = Number((45.2 + Math.random() * 3.8).toFixed(1));
      next.cpu_percent = Math.round(76 + Math.random() * 18);
      next.status = "alarm";
    } else {
      next.temperature_c = Number(Math.max(18, item.temperature_c + (Math.random() - 0.5) * 0.7).toFixed(1));
      next.cpu_percent = Math.max(2, Math.min(96, Math.round(item.cpu_percent + (Math.random() - 0.5) * 12)));
      next.status = next.temperature_c > 32 ? "warning" : "online";
    }
    state.set(id, next);
  }
  const message = JSON.stringify({ type: "telemetry", assets: [...state.values()] });
  for (const client of wss.clients) if (client.readyState === 1) client.send(message);
}, 2000);

server.listen(8787, "127.0.0.1", () => console.log("Digital Twin API: http://127.0.0.1:8787"));
