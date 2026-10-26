import { World } from './world';
import { KoiRenderer } from './renderer';

const canvas = document.querySelector<HTMLCanvasElement>('#pond')!;
const world = new World();
const renderer = new KoiRenderer(canvas);
const STEP = 1 / 30;
const FRAME_MS = 1000 / 16;
let last = 0, accumulator = 0, frameId = 0;
let desktopActive = true;
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
const params = new URLSearchParams(location.search);
renderer.setTheme(params.get('theme') === 'light');
document.body.style.background = params.get('theme') === 'light' ? '#f5f4f1' : '#1a1921';

function resize() {
  const w = window.innerWidth, h = window.innerHeight;
  if (!w || !h) return;
  renderer.resize(w, h, 1);
  world.resize(w, h);
  renderer.setDimBoxes([]);
  if (reducedMotion.matches) {
    for (let i = 0; i < 240 && world.time < 4; i++) world.step(STEP);
    renderer.render(world, STEP);
  }
}
function tick(now: number) {
  if (!desktopActive || document.hidden || reducedMotion.matches) return;
  const dt = Math.min(0.2, (now - last) / 1000);
  last = now; accumulator += dt;
  let n = 0;
  while (accumulator >= STEP && n < 4) { world.step(STEP); accumulator -= STEP; n++; }
  if (n === 4) accumulator = 0;
  renderer.render(world, dt);
  frameId = window.setTimeout(() => tick(performance.now()), FRAME_MS);
}
function schedule() {
  clearTimeout(frameId);
  if (!desktopActive || document.hidden || reducedMotion.matches) {
    if (reducedMotion.matches) renderer.render(world, STEP);
    return;
  }
  last = performance.now();
  accumulator = 0;
  frameId = window.setTimeout(() => tick(performance.now()), FRAME_MS);
}
(window as any).pondSetActive = (active: boolean) => {
  if (desktopActive === active) return;
  desktopActive = active;
  schedule();
};
let previousPointer = { x: 0, y: 0, time: 0 };
canvas.addEventListener('pointermove', e => {
  const elapsed = Math.max(1, e.timeStamp - previousPointer.time) / 1000;
  const speed = Math.hypot(e.clientX - previousPointer.x, e.clientY - previousPointer.y) / elapsed;
  world.pointer.speed += (Math.min(speed, 5000) - world.pointer.speed) * .5;
  world.pointer.x = e.clientX; world.pointer.y = e.clientY;
  world.pointer.active = e.pointerType !== 'touch';
  previousPointer = {x: e.clientX, y: e.clientY, time: e.timeStamp};
});
canvas.addEventListener('pointerleave', () => { world.pointer.active = false; world.pointer.speed = 0; });
canvas.addEventListener('click', e => { if (!reducedMotion.matches) world.feed(e.clientX, e.clientY); });
window.addEventListener('resize', resize);
document.addEventListener('visibilitychange', schedule);
reducedMotion.addEventListener('change', () => { resize(); schedule(); });
resize(); schedule();

// External X11 tracking, used when Nemo receives the desktop events.
let externalPointer = { x: 0, y: 0, t: 0 };
(window as any).pondExternalPointer = (x: number, y: number, feed: boolean) => {
  const now = performance.now();
  const w = window.innerWidth, h = window.innerHeight;
  const inside = x >= 0 && y >= 0 && x < w && y < h;
  if (inside && externalPointer.t > 0) {
    const secs = Math.max(0.001, (now - externalPointer.t) / 1000);
    const speed = Math.hypot(x - externalPointer.x, y - externalPointer.y) / secs;
    world.pointer.speed += (Math.min(speed, 5000) - world.pointer.speed) * 0.5;
  }
  world.pointer.x = x;
  world.pointer.y = y;
  world.pointer.active = inside;
  if (feed && inside && !reducedMotion.matches) world.feed(x, y);
  externalPointer = {x, y, t: now};
};
