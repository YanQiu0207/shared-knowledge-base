const DEFAULT_TIMEOUT_MS = 10_000;

export function createMemoryClient({
    endpoint = process.env.TDAI_MEMORY_ENDPOINT ?? "http://127.0.0.1:8420",
    apiKey = process.env.TDAI_MEMORY_API_KEY ?? "local",
    serviceId = process.env.TDAI_MEMORY_SERVICE_ID ?? "default",
    timeoutMs = Number.parseInt(process.env.TDAI_MEMORY_TIMEOUT_MS ?? `${DEFAULT_TIMEOUT_MS}`, 10),
} = {}) {
    const normalizedEndpoint = endpoint.replace(/\/$/, "");

    async function post(path, body) {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), timeoutMs);
        try {
            const response = await fetch(`${normalizedEndpoint}${path}`, {
                method: "POST",
                headers: {
                    authorization: `Bearer ${apiKey}`,
                    "content-type": "application/json",
                    "x-tdai-service-id": serviceId,
                },
                body: JSON.stringify(body),
                signal: controller.signal,
            });
            const payload = await response.json().catch(() => ({}));
            if (!response.ok || (typeof payload.code === "number" && payload.code !== 0)) {
                throw new Error(payload.message ?? `Memory Gateway request failed: HTTP ${response.status}`);
            }
            return payload.data ?? payload;
        } finally {
            clearTimeout(timeout);
        }
    }

    return {
        capture(messages, sessionId) {
            return post("/v2/conversation/add", { session_id: sessionId, messages });
        },
        health() {
            return fetch(`${normalizedEndpoint}/health`).then(async (response) => {
                if (!response.ok) throw new Error(`Memory Gateway health check failed: HTTP ${response.status}`);
                return response.json();
            });
        },
        listScenarios() {
            return post("/v2/scenario/ls", { path_prefix: "" });
        },
        readCore() {
            return post("/v2/core/read", {});
        },
        readScenario(path) {
            return post("/v2/scenario/read", { path });
        },
        searchAtomic(query, limit) {
            return post("/v2/atomic/search", { query, limit });
        },
    };
}
