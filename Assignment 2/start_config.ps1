param(
    [Parameter(Mandatory=$true)][ValidateSet('llama3.2:1b','llama3.2:3b','qwen2.5:7b')][string]$Model,
    [Parameter(Mandatory=$true)][ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_.-]*$')][string]$RunId,
    [ValidateSet('','llama3.2:1b','llama3.2:3b','qwen2.5:7b')][string]$LargeModel='',
    [ValidateSet('','1','2')][string]$Setting='',
    [string]$AcceptCategories='',
    [ValidateRange(1,86400)][int]$ModelTimeout=600
)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$pins = @{
    'llama3.2:1b' = 'baf6a787fdffd633537aa2eb51cfd54cb93ff08e28040095462bb63daf552878'
    'llama3.2:3b' = 'a80c4f17acd55265feec403c7aef86be0c25983ab279d83f3bcd3abbcb5b8b72'
    'qwen2.5:7b' = '845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e'
}
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.ollama-reuse.json')) -or -not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.env'))) {
    python (Join-Path $PSScriptRoot '0_setup/setup_ollama.py')
    if ($LASTEXITCODE -ne 0) { throw 'Could not locate the original Assignment 1 models. See the setup output.' }
}
if (Test-Path -LiteralPath (Join-Path $PSScriptRoot "logs/$RunId.jsonl")) { throw 'Run ID already used; select a new ID to preserve evidence.' }
if ($LargeModel -and ($LargeModel -eq $Model -or -not $Setting)) { throw 'Choose a distinct large model and setting 1 or 2.' }
$env:MODE = if ($LargeModel) { 'cascade' } else { 'single' }
$env:MODEL_NAME = $Model
$env:MODEL_DIGEST = $pins[$Model]
$env:LARGE_MODEL = $LargeModel
$env:LARGE_MODEL_DIGEST = if ($LargeModel) { $pins[$LargeModel] } else { '' }
$env:CASCADE_SETTING = $Setting
$env:ACCEPT_CATEGORIES = $AcceptCategories
$env:RUN_ID = $RunId
$env:MODEL_TIMEOUT = "$ModelTimeout"
docker compose up -d --build --force-recreate triage-service
if ($LASTEXITCODE -ne 0) { throw 'Docker Compose could not start the configuration.' }
docker compose ps
