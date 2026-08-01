import { recall } from "./recall.js";

const mode = process.argv[2];
const MAX_HOOK_RESULTS = 4;

async function readStdin() {
    let text = "";
    for await (const chunk of process.stdin) {
        text += chunk;
    }
    return text;
}

function contextFor(result) {
    return [
        "TencentDB Agent Memory recall (non-authoritative context):",
        "Use only when relevant. Current code, configuration, tests, and runtime evidence take precedence.",
        JSON.stringify(result, null, 2),
    ].join("\n");
}

try {
    if (mode !== "codex" && mode !== "claude") {
        throw new Error("Expected hook mode: codex or claude");
    }

    const input = JSON.parse(await readStdin());
    const prompt = typeof input.prompt === "string" ? input.prompt.trim() : "";
    if (prompt.length < 3) {
        process.exit(0);
    }

    const result = await recall(prompt, MAX_HOOK_RESULTS);
    if (result.atomic.length === 0 && result.core === null && result.scenarios.length === 0) {
        process.exit(0);
    }

    const context = contextFor(result);
    if (mode === "claude") {
        process.stdout.write(JSON.stringify({
            hookSpecificOutput: {
                hookEventName: "UserPromptSubmit",
                additionalContext: context,
            },
        }));
    } else {
        process.stdout.write(context);
    }
} catch {
    // Recall is best-effort. Do not block a user prompt when local memory is unavailable.
}
