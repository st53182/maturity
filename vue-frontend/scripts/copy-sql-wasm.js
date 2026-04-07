/* Копирует sql-wasm.wasm в public/ для загрузки в браузере (locateFile). */
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = path.join(root, 'node_modules', 'sql.js', 'dist', 'sql-wasm.wasm');
const destDir = path.join(root, 'public');
const dest = path.join(destDir, 'sql-wasm.wasm');

if (!fs.existsSync(src)) {
  console.warn('copy-sql-wasm: sql-wasm.wasm not found (run npm install).');
  process.exit(0);
}
if (!fs.existsSync(destDir)) {
  fs.mkdirSync(destDir, { recursive: true });
}
fs.copyFileSync(src, dest);
console.log('copy-sql-wasm: copied to public/sql-wasm.wasm');
