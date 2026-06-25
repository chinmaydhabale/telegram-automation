$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $projectRoot

$pyLauncher = Get-Command py -ErrorAction SilentlyContinue
if ($pyLauncher) {
    & py -3 -B -m banking_news_bot
} else {
    & python -B -m banking_news_bot
}

exit $LASTEXITCODE
