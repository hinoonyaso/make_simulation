import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const captureMode = new URLSearchParams(location.search).has('capture');
if (captureMode) document.body.classList.add('capture');
const canvas = document.querySelector('#scene');
const renderer = new THREE.WebGLRenderer({canvas, antialias: true, alpha: false});
renderer.setPixelRatio(1);
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.1;
const scene = new THREE.Scene();
scene.background = new THREE.Color('#0b1020');
const camera = new THREE.PerspectiveCamera(44, window.innerWidth / window.innerHeight, .1, 80);
camera.position.set(0, 1.4, 9.4);
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 0, 0);
controls.enableDamping = false;
controls.enabled = !captureMode;
controls.minDistance = 5;
controls.maxDistance = 16;
scene.add(new THREE.HemisphereLight(0xb7d4ff, 0x182033, 2.2));
const key = new THREE.DirectionalLight(0xffffff, 2.0);
key.position.set(-3, 5, 7);
scene.add(key);
const plot = new THREE.Group();
scene.add(plot);

function makeLabel(text, color) {
  const c = document.createElement('canvas');
  c.width = 256; c.height = 96;
  const ctx = c.getContext('2d');
  ctx.font = 'bold 42px Arial, sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.shadowColor = '#0b1020'; ctx.shadowBlur = 10;
  ctx.fillStyle = color; ctx.fillText(text, 128, 48);
  const texture = new THREE.CanvasTexture(c);
  texture.colorSpace = THREE.SRGBColorSpace;
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({map: texture, transparent: true, depthWrite: false}));
  sprite.scale.set(.76, .29, 1);
  return sprite;
}

const colorMuted = new THREE.Color('#8a94a6');
const colorQuery = new THREE.Color('#38bdf8');
const colorSelected = new THREE.Color('#34d399');
const pointObjects = new Map();
const selectionLines = new Map();
let dataset;
const duration = Number(new URLSearchParams(location.search).get('duration') || 8);

function setFrame(seconds) {
  if (!dataset) return;
  const time = Math.max(0, Number(seconds) || 0);
  const chunks = dataset.points.filter(point => point.kind === 'chunk');
  const revealEnd = duration * .42;
  const shownChunks = Math.min(chunks.length, Math.floor(chunks.length * time / revealEnd));
  const queryVisible = time >= revealEnd;
  const topK = dataset.retrieval.top_k_ids.length;
  const selectionStart = duration * .50;
  const selectionWindow = Math.max(.1, duration * .42);
  const selectedCount = queryVisible
    ? Math.max(0, Math.min(topK, Math.floor((time - selectionStart) / (selectionWindow / Math.max(topK, 1))) + 1)) : 0;

  chunks.forEach((point, index) => {
    const object = pointObjects.get(point.id);
    object.mesh.visible = index < shownChunks;
    object.label.visible = index < shownChunks && point.rank <= topK;
    const selected = point.rank && point.rank <= selectedCount;
    object.mesh.material.color.copy(selected ? colorSelected : colorMuted);
    object.mesh.scale.setScalar(selected ? 1.35 : 1.0);
    object.label.material.opacity = selected ? 1 : .78;
  });
  const query = pointObjects.get(dataset.query_id);
  query.mesh.visible = queryVisible;
  query.label.visible = queryVisible;
  for (const [id, line] of selectionLines) {
    const point = dataset.points.find(candidate => candidate.id === id);
    const active = point.rank <= selectedCount;
    line.material.opacity = active ? .8 : 0;
    pointObjects.get(id).mesh.material.color.copy(active ? colorSelected : colorMuted);
  }

  const list = document.querySelector('#ranking');
  for (const [index, entry] of dataset.retrieval.ranking.slice(0, topK).entries()) {
    const row = list.children[index];
    row.style.opacity = index < selectedCount ? '1' : '0';
  }
  document.querySelector('#status').textContent = !queryVisible
    ? '문서 청크를 벡터로 바꿉니다'
    : selectedCount
      ? `기록된 ${dataset.retrieval.metric} 순위로 선택됩니다`
      : '질문 벡터가 들어오고 실제 점수를 비교합니다';
  controls.update();
  renderer.render(scene, camera);
  window.__renderStats = {pointCount: shownChunks + Number(queryVisible), selectedIds:
    dataset.retrieval.top_k_ids.slice(0, selectedCount), queryVisible,
    sourceDimension: dataset.source_dimension, displayDimension: dataset.display_dimension,
    drawCalls: renderer.info.render.calls};
}

const projectionUrl = new URLSearchParams(location.search).get('projection') || 'data/embedding_space_3d.json';
fetch(projectionUrl).then(response => {
  if (!response.ok) throw new Error(`projection load failed: ${response.status}`);
  return response.json();
}).then(data => {
  dataset = data;
  document.querySelector('header h1').textContent = data.vector_label || '문서와 질문의 벡터 공간';
  document.querySelector('header p').textContent =
    `${data.points.filter(point => point.kind === 'chunk').length}개 청크와 질문의 표시 투영 → 기록된 ${data.retrieval.metric} 순위`;
  document.querySelector('#selected-label').textContent = `검색 Top ${data.retrieval.top_k}`;
  document.querySelector('#status').textContent = `원본 ${data.source_dimension}차원 벡터의 점수 순위를 재생합니다`;
  const grid = new THREE.GridHelper(7, 14, 0x334155, 0x1e293b);
  grid.position.y = -2.15;
  plot.add(grid);
  const axes = new THREE.AxesHelper(1.15);
  axes.position.set(-3.4, -2.1, -3.4);
  plot.add(axes);
  const sphere = new THREE.SphereGeometry(.085, 20, 16);
  const queryGeometry = new THREE.IcosahedronGeometry(.15, 1);
  for (const point of data.points) {
    const p = new THREE.Vector3(...point.xyz);
    const isQuery = point.kind === 'query';
    const mesh = new THREE.Mesh(isQuery ? queryGeometry : sphere,
      new THREE.MeshStandardMaterial({color: isQuery ? colorQuery : colorMuted,
        emissive: isQuery ? colorQuery : colorMuted,
        emissiveIntensity: isQuery ? .3 : .05, roughness: .34, metalness: .12}));
    mesh.position.copy(p);
    const label = makeLabel(isQuery ? '질문' : point.id, isQuery ? '#38bdf8' : '#dce3ed');
    const offset = [0, (point.rank && point.rank % 2 ? .28 : .22), 0];
    label.position.copy(p).add(new THREE.Vector3(...offset));
    mesh.visible = false;
    label.visible = false;
    plot.add(mesh, label);
    pointObjects.set(point.id, {mesh, label});
  }
  const queryPoint = data.points.find(point => point.id === data.query_id);
  for (const item of data.retrieval.ranking.slice(0, data.retrieval.top_k)) {
    const point = data.points.find(candidate => candidate.id === item.id);
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(...queryPoint.xyz), new THREE.Vector3(...point.xyz)]);
    const material = new THREE.LineBasicMaterial({color: colorSelected, transparent: true,
      opacity: 0, depthWrite: false});
    const line = new THREE.Line(geometry, material);
    plot.add(line);
    selectionLines.set(point.id, line);
  }
  const list = document.querySelector('#ranking');
  for (const item of data.retrieval.ranking.slice(0, data.retrieval.top_k)) {
    const row = document.createElement('li');
    row.textContent = `${item.id} · ${Number(item.score).toFixed(4)}`;
    row.classList.toggle('rank-selected', item.rank <= data.retrieval.top_k);
    list.appendChild(row);
  }
  window.__dataReady = true;
  window.setFrame = setFrame;
  setFrame(0);
  if (!captureMode) renderer.setAnimationLoop(ms => setFrame((ms / 1000) % duration));
}).catch(error => {
  console.error(error);
  document.querySelector('#status').textContent = `오류: ${error.message}`;
});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight, false);
});
