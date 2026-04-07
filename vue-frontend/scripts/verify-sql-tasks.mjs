/**
 * CI helper: run every checkSql on seed DB (non-empty result) and ensure exampleSql matches checkSql
 * so «показать пример» and «верный ответ» never disagree (e.g. stray ORDER BY).
 */
import initSqlJs from 'sql.js';
import path from 'path';
import { fileURLToPath } from 'url';
import { getSeedSQL, SQL_LESSONS, getLastSelectResult } from '../src/qa/sqlSandbox.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const wasmPath = path.join(__dirname, '../node_modules/sql.js/dist/sql-wasm.wasm');

const SQL = await initSqlJs({ locateFile: () => wasmPath });
const db = new SQL.Database();
db.run(getSeedSQL());

function normSql(s) {
  return String(s || '')
    .trim()
    .replace(/\s+/g, ' ');
}

let failed = 0;
for (const lesson of SQL_LESSONS) {
  for (const t of lesson.tasks) {
    if (t.exampleSql != null && t.checkSql != null && normSql(t.exampleSql) !== normSql(t.checkSql)) {
      console.error(`MISMATCH ${t.id}: exampleSql and checkSql differ (normalize whitespace)`);
      failed++;
    }
    let res;
    try {
      res = getLastSelectResult(db, t.checkSql);
    } catch (e) {
      console.error(`FAIL ${t.id}: ${e.message}`);
      failed++;
      continue;
    }
    if (!res || !res.columns?.length) {
      console.error(`FAIL ${t.id}: no SELECT result`);
      failed++;
      continue;
    }
    const n = res.rows?.length ?? 0;
    if (n === 0) {
      console.error(`FAIL ${t.id}: zero rows`);
      failed++;
    }
  }
}
db.close();
if (failed) {
  console.error(`\n${failed} task(s) failed`);
  process.exit(1);
}
console.log('OK: every checkSql returns ≥1 row; exampleSql matches checkSql (normalized).');
