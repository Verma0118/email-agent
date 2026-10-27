# Installs the Email Agent for Claude Code on Windows:
#   - links this folder to %USERPROFILE%\.claude\skills\email-agent (a junction, no admin needed)
#   - copies the reviewer agent into %USERPROFILE%\.claude\agents\
#   - adds an `email-agent` command in %USERPROFILE%\.local\bin (and puts it on your PATH)
#   - optionally sets up the job-search pipeline (ai-job-search) in %USERPROFILE%\ai-job-search
# Flags: -Jobs (set up job search without asking), -NoJobs (skip it)
param([switch]$Jobs, [switch]$NoJobs)
$ErrorActionPreference = 'Stop'
$Repo = $PSScriptRoot
$Skills = Join-Path $HOME '.claude\skills'; $Agents = Join-Path $HOME '.claude\agents'; $Bin = Join-Path $HOME '.local\bin'
$JobsDir = if ($env:JOBS_DIR) { $env:JOBS_DIR } else { Join-Path $HOME 'ai-job-search' }
New-Item -ItemType Directory -Force -Path $Skills, $Agents, $Bin | Out-Null

$py = if (Get-Command py -ErrorAction SilentlyContinue) { 'py' } elseif (Get-Command python -ErrorAction SilentlyContinue) { 'python' } else { $null }
if (-not $py) { Write-Host 'Python 3 not found. Install it from https://www.python.org/downloads/ (tick "Add to PATH"), then rerun.'; exit 1 }

$Link = Join-Path $Skills 'email-agent'
if ((Resolve-Path $Repo).Path -ne $Link) {
  if (Test-Path $Link) {
    $item = Get-Item $Link -Force
    if (-not ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { Write-Host "refusing: $Link exists and is not a link"; exit 1 }
    $item.Delete()
  }
  New-Item -ItemType Junction -Path $Link -Target $Repo | Out-Null
  Write-Host "linked $Link"
}
Copy-Item -Force (Join-Path $Repo 'agents\email-reviewer.md') (Join-Path $Agents 'email-reviewer.md')
Write-Host "copied $Agents\email-reviewer.md"

Set-Content -Encoding ASCII -Path (Join-Path $Bin 'email-agent.cmd') -Value '@claude "/email-agent %*"'
Write-Host "installed command: $Bin\email-agent.cmd"
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if (($userPath -split ';') -notcontains $Bin) {
  $newPath = if ($userPath) { "$userPath;$Bin" } else { $Bin }
  [Environment]::SetEnvironmentVariable('Path', $newPath, 'User')
  Write-Host "added $Bin to your PATH (open a new terminal window to use it)"
}

# --- Job search (optional) -------------------------------------------------
$want = if ($Jobs) { 'y' } elseif ($NoJobs) { 'n' } elseif (Test-Path "$JobsDir\.git") { 'y' } else {
  Read-Host 'Set up the job search pipeline too (find jobs, tailor CV, cover letters)? [y/N]' }
if ($want -match '^[Yy]') {
  if (Test-Path "$JobsDir\.git") {
    Write-Host "job search repo found at $JobsDir (update it from inside the agent: say 'check job search updates')"
  } else {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { Write-Host 'job search needs git. Install Git for Windows: https://git-scm.com/download/win, then rerun.'; exit 1 }
    git clone -q https://github.com/MadsLorentzen/ai-job-search.git $JobsDir
    # Local clone only: your profile data stays on this computer. Keep `origin` as upstream for updates.
    git -C $JobsDir remote rename origin upstream
    Write-Host "cloned job search into $JobsDir"
  }
  if (-not (Test-Path "$JobsDir\.venv")) { & $py -m venv "$JobsDir\.venv" }
  & "$JobsDir\.venv\Scripts\python.exe" -m pip install -q pypdf; Write-Host 'python env ready'
  $bunDir = Join-Path $HOME '.bun\bin'
  if (-not (Get-Command bun -ErrorAction SilentlyContinue) -and -not (Test-Path "$bunDir\bun.exe")) {
    Write-Host 'installing bun (runs the job board search tools)'
    powershell -NoProfile -ExecutionPolicy Bypass -c "irm bun.sh/install.ps1 | iex" | Out-Null
  }
  $env:Path = "$bunDir;$env:Path"
  Push-Location $JobsDir; try { & $py tools\install_portal_clis.py | Out-Null; Write-Host 'job board tools ready' } finally { Pop-Location }
  if (-not (Get-Command lualatex -ErrorAction SilentlyContinue)) {
    Write-Host 'note: no LaTeX found. Needed only to turn CVs into PDFs (install MiKTeX: https://miktex.org/download).'
  }
  Set-Content -Encoding UTF8 -Path (Join-Path $Repo '.jobs_repo') -Value $JobsDir
}

if (-not (Get-Command claude -ErrorAction SilentlyContinue)) { Write-Host 'WARNING: Claude Code not found. Install it first: https://claude.com/claude-code' }
& $py (Join-Path $Repo 'tests\run_tests.py') *> $null
if ($LASTEXITCODE -eq 0) { Write-Host 'self-test: pass' } else { Write-Host 'self-test: FAILED (run: py tests\run_tests.py)' }
Write-Host 'done. Open a new terminal and type: email-agent'
