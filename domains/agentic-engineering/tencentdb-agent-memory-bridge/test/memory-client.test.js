import test from "node:test";
import assert from "node:assert/strict";
import { createMemoryClient } from "../src/memory-client.js";

test("searchAtomic sends Gateway headers and the query", async () => {
    const originalFetch = globalThis.fetch;
    let request;
    globalThis.fetch = async (url, options) => {
        request = { url, options };
        return new Response(JSON.stringify({ code: 0, data: { items: [] } }), { status: 200 });
    };
    try {
        const client = createMemoryClient({
            endpoint: "http://127.0.0.1:8420/",
            apiKey: "test-key",
            serviceId: "test-service",
        });
        assert.deepEqual(await client.searchAtomic("preferences", 3), { items: [] });
        assert.equal(request.url, "http://127.0.0.1:8420/v2/atomic/search");
        assert.equal(request.options.headers.authorization, "Bearer test-key");
        assert.equal(request.options.headers["x-tdai-service-id"], "test-service");
        assert.deepEqual(JSON.parse(request.options.body), { query: "preferences", limit: 3 });
    } finally {
        globalThis.fetch = originalFetch;
    }
});
