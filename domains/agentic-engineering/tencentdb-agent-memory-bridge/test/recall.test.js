import test from "node:test";
import assert from "node:assert/strict";
import { createRecall } from "../src/recall.js";

test("returns the Gateway retrieval shape without LLM reranking", async () => {
    const recall = createRecall({
        searchAtomic: async () => ({ items: [{ id: "a" }, { id: "b" }] }),
        readCore: async () => ({ content: "core" }),
        listScenarios: async () => ({ entries: [{ path: "scenario.md" }] }),
    });

    assert.deepEqual(await recall("query", 2), {
        atomic: [{ id: "a" }, { id: "b" }],
        core: "core",
        scenarios: [{ path: "scenario.md" }],
    });
});
