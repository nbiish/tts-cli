# Global TTS CLI wrapper for native Windows (PowerShell 7+).
# Mirrors scripts/tts-cli-global.sh: resolves the project root from this
# script's location and runs the CLI through uv, preserving caller CWD.
$ScriptPath = $MyInvocation.MyCommand.Path
$ScriptDir = Split-Path -Parent $ScriptPath
$ProjectRoot = Split-Path -Parent $ScriptDir

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Error "❌ 'uv' is not installed or not in PATH. Install: https://docs.astral.sh/uv/"
    exit 1
}

$env:TTS_CLI_CALLER_DIR = (Get-Location).Path
uv --project $ProjectRoot run python -m tts_cli.cli @args
exit $LASTEXITCODE
