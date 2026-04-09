/**
 * Flatten vue-i18n JSON keys
 */
function flattenKeys(obj, prefix = "") {
  const out = [];
  if (obj && typeof obj === "object" && !Array.isArray(obj)) {
    for (const k of Object.keys(obj)) {
      const p = prefix ? `${prefix}.${k}` : k;
      if (obj[k] !== null && typeof obj[k] === "object" && !Array.isArray(obj[k])) {
        out.push(...flattenKeys(obj[k], p));
      } else {
        out.push(p);
      }
    }
  }
  return out;
}

const fs = require("fs");
const path = require("path");
const ru = JSON.parse(fs.readFileSync(path.join(__dirname, "../src/i18n/locales/ru.json"), "utf8"));
const en = JSON.parse(fs.readFileSync(path.join(__dirname, "../src/i18n/locales/en.json"), "utf8"));
const r = new Set(flattenKeys(ru));
const e = new Set(flattenKeys(en));
const onlyRu = [...r].filter((k) => !e.has(k)).sort();
const onlyEn = [...e].filter((k) => !r.has(k)).sort();
if (onlyRu.length || onlyEn.length) {
  console.warn("i18n parity: missing keys (fix over time):");
  if (onlyRu.length) console.warn("  only ru:", onlyRu.length, "keys");
  if (onlyEn.length) console.warn("  only en:", onlyEn.length, "keys");
  if (process.env.I18N_STRICT === "1") {
    console.error("I18N_STRICT=1 set, failing.");
    process.exit(1);
  }
}
console.log("i18n check done. ru:", r.size, "en:", e.size, "shared:", [...r].filter((k) => e.has(k)).length);
