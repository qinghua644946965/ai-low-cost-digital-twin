import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import "./style.css";

document.querySelector("#app").innerHTML = `
  <main class="shell">
    <header class="topbar">
      <div><span class="eyebrow">DT / ROOM 01</span><h1>机房数字孪生</h1></div>
      <div class="connection"><span id="connection-dot"></span><span id="connection-text">正在连接</span></div>
    </header>
    <section class="workspace">
      <aside class="rail">
        <div class="section-title">设备</div>
        <div class="search-wrap"><input id="search" aria-label="搜索设备" placeholder="搜索资产编号" /></div>
        <div id="asset-list" class="asset-list"></div>
      </aside>
      <div class="viewport">
        <canvas id="scene" aria-label="机房三维场景"></canvas>
        <div class="stats">
          <div><span>设备</span><strong id="total-count">—</strong></div>
          <div><span>在线</span><strong id="online-count" class="ok">—</strong></div>
          <div><span>告警</span><strong id="alarm-count" class="danger">—</strong></div>
        </div>
        <div class="hint">拖动旋转 · 滚轮缩放 · 点击设备</div>
        <div id="loading" class="loading"><span></span>正在载入 Blender 场景</div>
      </div>
      <aside class="details" id="details">
        <div class="section-title">实时指标</div>
        <div id="empty-detail" class="empty-detail"><div class="target-icon">⌖</div><p>选择场景中的机柜或设备</p></div>
        <div id="asset-detail" hidden>
          <div class="detail-head"><div><span id="detail-type" class="tag"></span><h2 id="detail-id"></h2></div><span id="detail-status" class="status"></span></div>
          <div class="metric primary"><span>温度</span><strong><span id="metric-temp">—</span><small>°C</small></strong><div class="bar"><i id="temp-bar"></i></div></div>
          <div class="metric-grid">
            <div class="metric"><span>CPU</span><strong><span id="metric-cpu">—</span><small>%</small></strong></div>
            <div class="metric"><span>功率</span><strong><span id="metric-power">—</span><small>kW</small></strong></div>
          </div>
          <dl><div><dt>场景对象</dt><dd id="detail-object"></dd></div><div><dt>数据源</dt><dd>模拟设备网关</dd></div><div><dt>更新时间</dt><dd id="detail-time"></dd></div></dl>
        </div>
      </aside>
    </section>
  </main>`;

const canvas = document.querySelector("#scene");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.AgXToneMapping;
renderer.toneMappingExposure = 1.15;
renderer.shadowMap.enabled = true;
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x070b12);
scene.fog = new THREE.FogExp2(0x070b12, 0.018);
const camera = new THREE.PerspectiveCamera(46, 1, 0.1, 200);
camera.position.set(11, 10, 13);
const controls = new OrbitControls(camera, canvas);
controls.target.set(0, 1.2, 0);
controls.enableDamping = true;
controls.minDistance = 4;
controls.maxDistance = 35;
controls.maxPolarAngle = Math.PI * 0.49;

scene.add(new THREE.HemisphereLight(0xb8d8ff, 0x121722, 2.2));
const key = new THREE.DirectionalLight(0xffe2c2, 3.4);
key.position.set(7, 12, 8);
key.castShadow = true;
scene.add(key);
const rim = new THREE.DirectionalLight(0x4f8cff, 2.0);
rim.position.set(-8, 6, -4);
scene.add(rim);

const state = { assets: new Map(), objects: new Map(), selected: null, model: null };
const statusLabel = { online: "在线", warning: "注意", alarm: "告警" };

function parseMeta(object) {
  let node = object;
  while (node) {
    const raw = node.userData?.digital_twin_metadata;
    if (raw) {
      try {
        const metadata = typeof raw === "string" ? JSON.parse(raw) : raw;
        if (metadata.asset_id) return { node, metadata, objectId: node.userData.digital_twin_id || node.name };
      } catch {}
    }
    node = node.parent;
  }
  return null;
}

function registerModel(root) {
  root.traverse((object) => {
    object.castShadow = object.isMesh;
    object.receiveShadow = object.isMesh;
    const id = object.userData?.digital_twin_id;
    if (id) state.objects.set(id, object);
    if (object.isMesh && object.material) {
      object.userData.baseEmissive = object.material.emissive?.clone();
      object.userData.baseIntensity = object.material.emissiveIntensity || 0;
    }
  });
}

function statusColor(status) { return status === "alarm" ? 0xff334f : status === "warning" ? 0xffb020 : 0x39e58c; }
function applyStatuses() {
  for (const asset of state.assets.values()) {
    const root = state.objects.get(asset.object_id);
    if (!root) continue;
    const color = new THREE.Color(statusColor(asset.status));
    root.traverse((object) => {
      if (!object.isMesh || !object.material?.emissive) return;
      if (!object.userData.statusMaterial) {
        object.material = object.material.clone();
        object.userData.statusMaterial = true;
      }
      const selected = state.selected === asset.asset_id;
      object.material.emissive.copy(color);
      object.material.emissiveIntensity = selected ? 0.75 : asset.status === "alarm" ? 0.38 : 0.06;
    });
  }
}

function updateDashboard() {
  const assets = [...state.assets.values()];
  document.querySelector("#total-count").textContent = assets.length;
  document.querySelector("#online-count").textContent = assets.filter((x) => x.status === "online").length;
  document.querySelector("#alarm-count").textContent = assets.filter((x) => x.status === "alarm").length;
  renderList(document.querySelector("#search").value);
  if (state.selected) renderDetail(state.assets.get(state.selected));
  applyStatuses();
}

function renderList(query = "") {
  const list = document.querySelector("#asset-list");
  const filtered = [...state.assets.values()].filter((asset) =>
    asset.asset_id.toLowerCase().includes(query.toLowerCase()) && ["rack", "server", "precision_cooling", "temperature_sensor"].includes(asset.asset_type)
  );
  list.innerHTML = filtered.map((asset) => `<button class="asset-row ${state.selected === asset.asset_id ? "selected" : ""}" data-id="${asset.asset_id}">
    <span class="state-dot ${asset.status}"></span><span><strong>${asset.asset_id}</strong><small>${asset.asset_type}</small></span><b>${asset.temperature_c.toFixed(1)}°</b>
  </button>`).join("");
  list.querySelectorAll("button").forEach((button) => button.addEventListener("click", () => selectAsset(button.dataset.id)));
}

function renderDetail(asset) {
  if (!asset) return;
  document.querySelector("#empty-detail").hidden = true;
  document.querySelector("#asset-detail").hidden = false;
  document.querySelector("#detail-type").textContent = asset.asset_type;
  document.querySelector("#detail-id").textContent = asset.asset_id;
  const badge = document.querySelector("#detail-status");
  badge.textContent = statusLabel[asset.status];
  badge.className = `status ${asset.status}`;
  document.querySelector("#metric-temp").textContent = asset.temperature_c.toFixed(1);
  document.querySelector("#metric-cpu").textContent = asset.cpu_percent;
  document.querySelector("#metric-power").textContent = asset.power_kw.toFixed(2);
  document.querySelector("#temp-bar").style.width = `${Math.min(100, asset.temperature_c / 55 * 100)}%`;
  document.querySelector("#detail-object").textContent = asset.object_id;
  document.querySelector("#detail-time").textContent = new Date(asset.updated_at).toLocaleTimeString("zh-CN", { hour12: false });
}

function selectAsset(id) {
  if (!state.assets.has(id)) throw new Error(`未知资产：${id}`);
  state.selected = id;
  updateDashboard();
}

function registerWebMcp() {
  const context = document.modelContext;
  if (!context?.registerTool) return;
  context.registerTool({
    name: "select_asset",
    title: "选择数字孪生设备",
    description: "在三维机房中选择一个资产，并在右侧显示其实时指标。",
    inputSchema: {
      type: "object",
      properties: { asset_id: { type: "string", description: "例如 RACK_B3 或 SERVER_B3_U3" } },
      required: ["asset_id"],
      additionalProperties: false,
    },
    annotations: { readOnlyHint: false, untrustedContentHint: false },
    execute(input) {
      if (!input || typeof input.asset_id !== "string") throw new Error("asset_id 必须是字符串");
      selectAsset(input.asset_id);
      return { selected_asset_id: input.asset_id, metrics: state.assets.get(input.asset_id) };
    },
  });
  context.registerTool({
    name: "read_twin_status",
    title: "读取数字孪生状态",
    description: "读取机房设备数量、告警数和当前选中的资产。",
    inputSchema: { type: "object", properties: {}, additionalProperties: false },
    annotations: { readOnlyHint: true, untrustedContentHint: false },
    execute() {
      const assets = [...state.assets.values()];
      return { total: assets.length, alarms: assets.filter((x) => x.status === "alarm").length,
               selected_asset_id: state.selected };
    },
  });
}

document.querySelector("#search").addEventListener("input", (event) => renderList(event.target.value));
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
canvas.addEventListener("pointerdown", (event) => {
  const rect = canvas.getBoundingClientRect();
  pointer.set(((event.clientX - rect.left) / rect.width) * 2 - 1, -((event.clientY - rect.top) / rect.height) * 2 + 1);
  raycaster.setFromCamera(pointer, camera);
  const hit = raycaster.intersectObject(state.model, true)[0];
  const found = hit && parseMeta(hit.object);
  if (found?.metadata.asset_id) selectAsset(found.metadata.asset_id);
});

function connect() {
  const protocol = location.protocol === "https:" ? "wss" : "ws";
  const socket = new WebSocket(`${protocol}://${location.host}/ws`);
  socket.onopen = () => { document.querySelector("#connection-dot").className = "live"; document.querySelector("#connection-text").textContent = "实时数据已连接"; };
  socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    for (const asset of message.assets || []) state.assets.set(asset.asset_id, asset);
    updateDashboard();
  };
  socket.onclose = () => { document.querySelector("#connection-dot").className = ""; document.querySelector("#connection-text").textContent = "正在重连"; setTimeout(connect, 1500); };
}

new GLTFLoader().load("/assets/server-room.glb", (gltf) => {
  state.model = gltf.scene;
  registerModel(state.model);
  scene.add(state.model);
  document.querySelector("#loading").remove();
}, undefined, (error) => { document.querySelector("#loading").textContent = `场景载入失败：${error.message}`; });
connect();
registerWebMcp();

function resize() {
  const width = canvas.clientWidth, height = canvas.clientHeight;
  if (canvas.width !== width || canvas.height !== height) {
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  }
}
function frame() { resize(); controls.update(); renderer.render(scene, camera); requestAnimationFrame(frame); }
frame();
