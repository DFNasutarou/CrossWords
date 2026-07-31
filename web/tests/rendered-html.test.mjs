import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

const templateRoot = new URL("../", import.meta.url);

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders CrossMaker Web", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>CrossMaker Web<\/title>/i);
  assert.match(html, /CrossMaker Web/);
  assert.match(html, /JSONを開く/);
  assert.match(html, /JSONを書き出す/);
  assert.match(html, /保存データ管理/);
  assert.match(html, /この端末のブラウザ内に保存/);
  assert.match(html, /role="status"/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton/);
});

test("includes local restore and removes starter assets", async () => {
  const [client, storage, page, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/CrosswordApp.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/project-storage.ts", import.meta.url), "utf8"),
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(client, /loadLastProject/);
  assert.match(client, /saveProject/);
  assert.match(client, /removeStoredProject/);
  assert.match(client, /removeAllStoredProjects/);
  assert.match(client, /parseProjectDocument/);
  assert.match(storage, /indexedDB\.open/);
  assert.match(storage, /requestPersistentStorage/);
  assert.match(storage, /deleteProject/);
  assert.match(storage, /clearProjects/);
  assert.match(page, /export const metadata:\s*Metadata/);
  assert.match(page, /<CrosswordApp \/>/);
  assert.match(layout, /generateMetadata/);
  assert.match(layout, /title:\s*"CrossMaker Web"/);
  assert.match(layout, /images:\s*\["\/og\.png"\]/);
  assert.doesNotMatch(page, /codex-preview|_sites-preview/);
  assert.doesNotMatch(packageJson, /drizzle|react-loading-skeleton|tailwind/);

  await assert.rejects(
    access(new URL("app/_sites-preview/SkeletonPreview.tsx", templateRoot)),
  );
});
