import { createMemoryClient } from "./memory-client.js";

export function createRecall(client) {
    return async function recall(query, limit) {
        const [atomic, core, scenarios] = await Promise.allSettled([
            client.searchAtomic(query, limit),
            client.readCore(),
            client.listScenarios(),
        ]);
        return {
            atomic: atomic.status === "fulfilled" ? atomic.value.items ?? atomic.value : [],
            core: core.status === "fulfilled" ? core.value.content ?? core.value : null,
            scenarios: scenarios.status === "fulfilled" ? scenarios.value.entries ?? scenarios.value : [],
        };
    };
}

export const recall = createRecall(createMemoryClient());
