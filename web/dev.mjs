import { spawn } from "node:child_process";

const api = spawn(process.execPath, ["server.mjs", "--api-only"], { stdio: "inherit" });
const vite = spawn(process.execPath, ["node_modules/vite/bin/vite.js", "--host", "127.0.0.1"], { stdio: "inherit" });

function stop() {
  api.kill();
  vite.kill();
}
process.on("SIGINT", stop);
process.on("SIGTERM", stop);
vite.on("exit", (code) => { api.kill(); process.exit(code ?? 0); });
