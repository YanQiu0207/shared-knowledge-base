import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { createMemoryClient } from "./memory-client.js";
import { recall } from "./recall.js";

const MAX_RECALL_RESULTS = 10;
const client = createMemoryClient();

const tools = [
    {
        name: "memory_recall",
        description: "Retrieve relevant atomic memories, the core profile, and available scenario paths before starting work.",
        inputSchema: {
            type: "object",
            properties: {
                query: { type: "string", description: "The current user request or task summary." },
                limit: { type: "integer", minimum: 1, maximum: MAX_RECALL_RESULTS, default: 5 },
            },
            required: ["query"],
            additionalProperties: false,
        },
    },
    {
        name: "memory_read_scenario",
        description: "Read one scenario memory by the path returned from memory_recall.",
        inputSchema: {
            type: "object",
            properties: {
                path: { type: "string", minLength: 1 },
            },
            required: ["path"],
            additionalProperties: false,
        },
    },
    {
        name: "memory_capture",
        description: "Store one confirmed user-assistant exchange as L0 conversation memory. Do not store secrets, credentials, or unverified conclusions.",
        inputSchema: {
            type: "object",
            properties: {
                session_id: { type: "string", minLength: 1 },
                user_message: { type: "string", minLength: 1 },
                assistant_message: { type: "string", minLength: 1 },
            },
            required: ["session_id", "user_message", "assistant_message"],
            additionalProperties: false,
        },
    },
    {
        name: "memory_status",
        description: "Check whether the local TencentDB Agent Memory Gateway is healthy.",
        inputSchema: { type: "object", properties: {}, additionalProperties: false },
    },
];

function textResult(value) {
    return { content: [{ type: "text", text: JSON.stringify(value, null, 2) }] };
}

function requireString(args, key) {
    const value = args[key];
    if (typeof value !== "string" || value.trim() === "") {
        throw new Error(key + " must be a non-empty string");
    }
    return value.trim();
}

const server = new Server(
    { name: "tdai-memory-bridge", version: "0.1.0" },
    { capabilities: { tools: {} } },
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const args = request.params.arguments ?? {};
    switch (request.params.name) {
        case "memory_recall": {
            const query = requireString(args, "query");
            const requestedLimit = args.limit ?? 5;
            if (!Number.isInteger(requestedLimit) || requestedLimit < 1 || requestedLimit > MAX_RECALL_RESULTS) {
                throw new Error("limit must be an integer from 1 to " + MAX_RECALL_RESULTS);
            }
            return textResult(await recall(query, requestedLimit));
        }
        case "memory_read_scenario":
            return textResult(await client.readScenario(requireString(args, "path")));
        case "memory_capture":
            return textResult(await client.capture([
                { role: "user", content: requireString(args, "user_message") },
                { role: "assistant", content: requireString(args, "assistant_message") },
            ], requireString(args, "session_id")));
        case "memory_status":
            return textResult(await client.health());
        default:
            throw new Error("Unknown tool: " + request.params.name);
    }
});

await server.connect(new StdioServerTransport());
