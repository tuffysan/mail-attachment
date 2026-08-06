param(
  [Parameter(Mandatory=$true)][string]$RepositoryPath,
  [switch]$Commit,
  [string]$CommitMessage = "feat: add IMAP email accounts"
)

$ErrorActionPreference = "Stop"
$source = Split-Path -Parent $PSScriptRoot
$repo = (Resolve-Path $RepositoryPath).Path

if (-not (Test-Path (Join-Path $repo ".git"))) {
  throw "RepositoryPath must point to a cloned Git repository."
}

Get-ChildItem $repo -Force |
  Where-Object { $_.Name -ne ".git" } |
  Remove-Item -Recurse -Force

Get-ChildItem $source -Force |
  Where-Object { $_.Name -ne "tools" } |
  Copy-Item -Destination $repo -Recurse -Force

Push-Location $repo
try {
  git add -A
  git status
  if ($Commit) {
    git commit -m $CommitMessage
  }
}
finally {
  Pop-Location
}
