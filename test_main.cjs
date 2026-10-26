const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const { transformSync } = require('esbuild');

let now = 0, nextId = 0, renders = 0, simulationTime = 0;
const timers = new Map(), listeners = {};
const media = { matches: false, addEventListener: (_, fn) => { listeners.motion = fn; } };
const canvas = { addEventListener() {} };
const document = {
  hidden: false, body: { style: {} }, querySelector: () => canvas,
  addEventListener: (name, fn) => { listeners[name] = fn; },
};
const window = {
  innerWidth: 1920, innerHeight: 1080, devicePixelRatio: 2,
  matchMedia: () => media, addEventListener() {},
  setTimeout: (fn, ms) => { timers.set(++nextId, { fn, due: now + ms }); return nextId; },
};
class World {
  time = 0;
  pointer = { speed: 0 };
  resize() {}
  step(dt) { this.time += dt; simulationTime += dt; }
}
class KoiRenderer {
  setTheme() {}
  setDimBoxes() {}
  resize(_w, _h, scale) { assert.equal(scale, 1); }
  render() { renders++; }
}
const source = fs.readFileSync(`${__dirname}/main.ts`, 'utf8').replace(/^import .*;\n/gm, '');
vm.runInNewContext(transformSync(source, { loader: 'ts' }).code, {
  World, KoiRenderer, window, document, location: { search: '' }, URLSearchParams,
  performance: { now: () => now }, clearTimeout: id => timers.delete(id),
});
function advance(ms) {
  const end = now + ms;
  while (timers.size) {
    const [id, timer] = [...timers].sort((a, b) => a[1].due - b[1].due)[0];
    if (timer.due > end) break;
    now = timer.due; timers.delete(id); timer.fn();
  }
  now = end;
}
advance(1000);
assert.equal(renders, 16);
assert.ok(simulationTime > .85 && simulationTime < 1.05);
window.pondSetActive(false);
assert.equal(timers.size, 0);
const pausedRenders = renders;
advance(60000);
assert.equal(renders, pausedRenders);
window.pondSetActive(true);
advance(80);
assert.equal(renders, pausedRenders + 1);
assert.ok(simulationTime < 1.2, 'resume must not simulate the time spent paused');
document.hidden = true;
listeners.visibilitychange();
assert.equal(timers.size, 0);
media.matches = true;
listeners.motion();
assert.equal(timers.size, 0);
console.log('PASS: 16 fps, native resolution, pause/resume, visibility and reduced motion');
