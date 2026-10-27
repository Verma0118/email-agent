# Install or update the Email Agent on Windows, without git or a GitHub account.
#   irm https://raw.githubusercontent.com/Verma0118/email-agent/main/get.ps1 | iex
# Downloads the latest code into %USERPROFILE%\email-agent, keeps your profile.json and
# personal\, then runs install.ps1. Run the same command again any time to update.
$ErrorActionPreference = 'Stop'
$Dir = if ($env:EMAIL_AGENT_DIR) { $env:EMAIL_AGENT_DIR } else { Join-Path $HOME 'email-agent' }
$Tmp = Join-Path ([IO.Path]::GetTempPath()) ("email-agent-" + [guid]::NewGuid())
New-Item -ItemType Directory -Path $Tmp | Out-Null
$Keep = 'profile.json', 'personal', '.jobs_repo'
try {
  if (Test-Path (Join-Path $Dir '.git')) {
    Write-Host 'git checkout found, updating with git pull'; git -C $Dir pull -q
  } else {
    Invoke-WebRequest -UseBasicParsing 'https://github.com/Verma0118/email-agent/archive/refs/heads/main.zip' -OutFile "$Tmp\src.zip"
    Expand-Archive "$Tmp\src.zip" -DestinationPath $Tmp
    New-Item -ItemType Directory -Force -Path $Dir | Out-Null
    foreach ($k in $Keep) { if (Test-Path "$Dir\$k") { Move-Item "$Dir\$k" "$Tmp\$k" } }
    Get-ChildItem -Force $Dir | Remove-Item -Recurse -Force
    Copy-Item -Recurse -Force "$Tmp\email-agent-main\*" $Dir
    Copy-Item -Force "$Tmp\email-agent-main\.gitignore" $Dir -ErrorAction SilentlyContinue
    foreach ($k in $Keep) { if (Test-Path "$Tmp\$k") { Move-Item "$Tmp\$k" "$Dir\$k" } }
    Write-Host "downloaded latest into $Dir"
  }
} finally { Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue }
powershell -NoProfile -ExecutionPolicy Bypass -File "$Dir\install.ps1"
