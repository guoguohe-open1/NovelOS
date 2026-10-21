import assert from "node:assert/strict";

const url = process.env.NOVELOS_WEB_URL ?? "http://127.0.0.1:3000";
const response = await fetch(url, { signal: AbortSignal.timeout(10_000) });
assert.equal(response.status, 200, "Web must return HTTP 200");
const html = await response.text();
assert.match(html, /<html[^>]*lang="zh-CN"/);
assert.match(html, /<main[\s>]/);
assert.match(html, /NovelOS/);
console.log("Web smoke passed (HTTP 200, Chinese document, main content).");
