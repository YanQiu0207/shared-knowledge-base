param(
    [Parameter(Mandatory = $true)]
    [string]$MemorySourcePath,

    [Parameter(Mandatory = $true)]
    [string]$LlmConfigPath
)

$ErrorActionPreference = "Stop"
$bridgePath = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonEnv = @{ PYTHONUTF8 = "1"; PYTHONIOENCODING = "utf-8" }

if (-not (Test-Path (Join-Path $MemorySourcePath "src\gateway\server.ts"))) {
    throw "Memory source path does not contain src\\gateway\\server.ts: $MemorySourcePath"
}
if (-not (Test-Path $LlmConfigPath)) {
    throw "LLM config file does not exist: $LlmConfigPath"
}

Push-Location $bridgePath
try {
    npm install
    & python scripts\start_gateway.py --source $MemorySourcePath --llm-config $LlmConfigPath
    codex mcp remove tdai-memory 2>$null
    codex mcp add tdai-memory -- node (Join-Path $bridgePath "src\index.js")
    claude mcp remove tdai-memory -s user 2>$null
    claude mcp add --scope user tdai-memory -- node (Join-Path $bridgePath "src\index.js")
} finally {
    Pop-Location
}
