import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

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
controls.enableDamping = true;
controls.dampingFactor = .06;
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
let selectedCount = 0;

function clamp(x, lo, hi) { return Math.max(lo, Math.min(hi, x)); }
function setFrame(seconds) {
  const time = Math.max(0, Number(seconds) || 0);
  plot.rotation.y = .10 * Math.sin(time * .34);
  selectedCount = clamp(Math.floor((time - .7) / 1.35) + 1, 0, dataset.retrieval.top_k_ids.length);
  for (const point of dataset.points) {
    const object = pointObjects.get(point.id);
    if (point.kind === 'query') continue;
    const selected = point.rank && point.rank <= selectedCount;
    object.mesh.material.color.copy(selected ? colorSelected : colorMuted);
    object.mesh.scale.setScalar(selected ? 1.35 : 1.0);
    object.label.material.opacity = selected ? 1 : .78;
  }
  for (const [id, line] of selectionLines) {
    const point = dataset.points.find(p => p.id === id);
    line.material.opacity = point.rank <= selectedCount ? .75 : 0;
  }
  const shown = dataset.retrieval.top_k_ids.slice(0, selectedCount);
  document.querySelector('#status').textContent = shown.length
    ? `실제 384차원 Top 3 선택: ${shown.join(' → ')}`
    : '질문 벡터와 문서 임베딩을 비교합니다';
  controls.update();
  renderer.render(scene, camera);
  window.__renderStats = {pointCount: pointObjects.size, selectedIds: shown,
                          sourceDimension: dataset.source_dimension,
                          displayDimension: dataset.display_dimension, drawCalls: renderer.info.render.calls};
}

fetch('/data/embedding_space_3d.json').then(r => {
  if (!r.ok) throw new Error(`projection load failed: ${r.status}`);
  return r.json();
}).then(data => {
  dataset = data;
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
    plot.add(mesh);
    const label = makeLabel(isQuery ? '질문' : point.id, isQuery ? '#38bdf8' : '#dce3ed');
    const labelOffsets = {C02: [-.30, .28, 0], C04: [-.35, .08, 0], C01: [.22, .32, 0]};
    const offset = labelOffsets[point.id] || [0, .24, 0];
    label.position.copy(p).add(new THREE.Vector3(...offset));
    plot.add(label);
    pointObjects.set(point.id, {mesh, label});
  }
  const query = data.points.find(p => p.kind === 'query');
  for (const point of data.points.filter(p => p.rank)) {
    const geometry = new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(...query.xyz), new THREE.Vector3(...point.xyz)]);
    const material = new THREE.LineBasicMaterial({color: colorSelected, transparent: true, opacity: 0, depthWrite: false});
    const line = new THREE.Line(geometry, material);
    plot.add(line);
    selectionLines.set(point.id, line);
  }
  window.__dataReady = true;
  window.setFrame = setFrame;
  setFrame(0);
  if (!new URLSearchParams(location.search).has('capture')) {
    renderer.setAnimationLoop(ms => setFrame((ms / 1000) % 8));
  }
}).catch(error => {
  console.error(error);
  document.querySelector('#status').textContent = `오류: ${error.message}`;
});

window.addEventListener('resize', () => {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight, false);
});
