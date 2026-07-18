param(
    [switch]$Live,
    [switch]$Full,
    [ValidateRange(1, 10)]
    [int]$Repeat = 1,
    [ValidateSet(
        "",
        "aligned-package-no-ai-finding",
        "visual-condition-evidence",
        "incomplete-comparable-commentary"
    )]
    [string]$Case = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

function Invoke-Checked {
    param(
        [string]$Label,
        [string]$Command,
        [string[]]$Arguments
    )

    Write-Host "`n== $Label ==" -ForegroundColor Cyan
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE."
    }
}

Push-Location $root
try {
    if ($Full) {
        Invoke-Checked "Django system check" "python" @("manage.py", "check")
        Invoke-Checked "Django test suite" "python" @("manage.py", "test")
    }

    Invoke-Checked "Official UAD corpus gate" "python" @(
        "manage.py", "evaluate_uad_corpus", "--strict"
    )
    Invoke-Checked "Controlled cross-source regressions" "python" @(
        "manage.py", "evaluate_uad_regressions", "--strict"
    )

    if ($Live) {
        $liveArguments = @(
            "run",
            "python",
            "scripts/run_isolated_gpt_eval.py",
            "--repeat",
            "$Repeat",
            "--confirm-paid-api",
            "--strict"
        )
        if ($Case) {
            $liveArguments += @("--case", $Case)
        }
        Invoke-Checked "Paid isolated GPT-5.6 evaluation" "railway" $liveArguments
    }

    Write-Host "`nAll requested evaluation gates passed." -ForegroundColor Green
    Write-Host "Reports: .eval-data\reports\"
}
finally {
    Pop-Location
}
