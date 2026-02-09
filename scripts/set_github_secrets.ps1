<#
set_github_secrets.ps1

Interactive PowerShell script to add repository secrets to a GitHub repo using the GitHub CLI (`gh`).

Usage:
  1. Authenticate gh: `gh auth login` (if not already authenticated).
  2. Run this script from the repository root:
     powershell -ExecutionPolicy Bypass -File .\scripts\set_github_secrets.ps1

The script will prompt for each secret; leave blank to skip.
#>

function ConvertFrom-SecureStringToPlain {
    param([System.Security.SecureString]$secure)
    if (-not $secure) { return "" }
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    }
    finally {
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
    }
}

# Check gh CLI
try {
    gh --version | Out-Null
} catch {
    Write-Error "GitHub CLI 'gh' is not available in PATH. Install and authenticate it first: https://cli.github.com/"
    exit 1
}

$defaultRepo = "DataByRajesh/quizgen"
$repo = Read-Host "Repository to set secrets for (owner/repo) [$defaultRepo]"
if ([string]::IsNullOrWhiteSpace($repo)) { $repo = $defaultRepo }

Write-Host "Setting secrets for repository: $repo"

$secrets = @(
    'VERCEL_TOKEN',
    'RENDER_API_KEY',
    'RENDER_SERVICE_ID',
    'RAILWAY_TOKEN',
    'RAILWAY_PROJECT_ID',
    'OPENAI_API_KEY'
)

foreach ($name in $secrets) {
    $secure = Read-Host -AsSecureString "Enter value for $name (leave blank to skip)"
    if (-not $secure -or $secure.Length -eq 0) {
        Write-Host "Skipping $name"
        continue
    }

    $plain = ConvertFrom-SecureStringToPlain $secure

    try {
        gh secret set $name --body $plain --repo $repo
        Write-Host "Set secret: $name"
    }
    catch {
        Write-Warning "Failed to set secret $name: $_"
    }

    # Clear plain text variable
    Remove-Variable plain -ErrorAction SilentlyContinue
}

Write-Host "Done. Verify secrets with: gh secret list --repo $repo"
