param(
  [string]$Root = (Split-Path -Parent $PSScriptRoot),
  [switch]$RequireClean,
  [switch]$IncludePytest
)

$ErrorActionPreference = "Stop"

$rootPath = (Resolve-Path -LiteralPath $Root).Path
$oldPythonDontWriteBytecode = $env:PYTHONDONTWRITEBYTECODE
$env:PYTHONDONTWRITEBYTECODE = "1"

function Convert-ToPublicPath([string]$Path) {
  try {
    $resolved = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
  } catch {
    $resolved = $Path
  }
  if ($resolved.Equals($rootPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    return "."
  }
  $windowsPrefix = $rootPath.TrimEnd("\", "/") + "\"
  $posixPrefix = $rootPath.TrimEnd("\", "/") + "/"
  if ($resolved.StartsWith($windowsPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
      $resolved.StartsWith($posixPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    return $resolved.Substring($rootPath.Length + 1).Replace("\", "/")
  }
  return (Split-Path -Leaf $resolved)
}

function Invoke-Checked([string]$Label, [scriptblock]$Command) {
  Write-Host "==> $Label"
  $global:LASTEXITCODE = 0
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Label failed with exit code $LASTEXITCODE"
  }
}

function Test-IsGitRepo {
  try {
    $result = @(git -C $rootPath rev-parse --is-inside-work-tree 2>$null)
    $ok = ($LASTEXITCODE -eq 0 -and $result.Count -gt 0 -and
      $result[0].Trim().ToLowerInvariant() -eq "true")
  } catch {
    $ok = $false
  }
  $global:LASTEXITCODE = 0
  return $ok
}

function Assert-RepositoryLayout {
  $required = @(
    "VERSION",
    "tools/ainp.py",
    "tools/ainp_public.py",
    "tools/ainp_validate.py",
    "tools/ainp_release_check.py",
    "tools/ainp_project_check.py",
    "tests/test_ainp.py",
    "schemas/ainp-generation-v1.0.0.schema.json",
    "schemas/ainp-generationreport-v1.0.0.schema.json",
    "examples/file_family/whitepaper.generation.json",
    "scripts/release_check.ps1"
  )
  $missing = @()
  foreach ($rel in $required) {
    $path = Join-Path $rootPath $rel
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
      $missing += (Convert-ToPublicPath $path)
    }
  }
  if ($missing.Count) {
    throw "Release root is not a complete AINP repository; missing:`n$($missing -join "`n")"
  }
  Write-Host "Repository layout ok."
}

function Invoke-JsonSyntaxCheck {
  $env:AINP_RELEASE_ROOT = $rootPath
  @'
import json
import os
import pathlib
import sys

root = pathlib.Path(os.environ["AINP_RELEASE_ROOT"])
errors = []

def reject_duplicate_keys(pairs):
    out = {}
    seen = set()
    for key, value in pairs:
        if key in seen:
            raise ValueError(f"duplicate object key {key!r}")
        seen.add(key)
        out[key] = value
    return out

def reject_constant(const):
    raise ValueError(f"non-standard JSON literal {const!r}")

for path in root.rglob("*.json"):
    rel = path.relative_to(root).parts
    if ".git" in rel:
        continue
    if len(rel) >= 3 and rel[:3] == ("tests", "fixtures", "invalid"):
        continue
    try:
        json.loads(path.read_text(encoding="utf-8-sig"),
                   object_pairs_hook=reject_duplicate_keys,
                   parse_constant=reject_constant)
    except Exception as exc:  # noqa: BLE001
        errors.append((str(path), str(exc)))
if errors:
    for path, error in errors:
        try:
            shown = pathlib.Path(path).relative_to(root).as_posix()
        except ValueError:
            shown = pathlib.Path(path).name
        print(f"{shown}: {error}")
    sys.exit(1)
print("json syntax ok")
'@ | python -B -
  if ($LASTEXITCODE -ne 0) {
    throw "JSON syntax check failed"
  }
}

function Invoke-PythonSyntaxCheck {
  $env:AINP_RELEASE_ROOT = $rootPath
  @'
import os
import pathlib
import sys

root = pathlib.Path(os.environ["AINP_RELEASE_ROOT"])
skip_dirs = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".ainp_test_tmp",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
}
errors = []
checked = 0
for path in root.rglob("*.py"):
    rel = path.relative_to(root).parts
    if any(part in skip_dirs for part in rel):
        continue
    try:
        compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
        checked += 1
    except Exception as exc:  # noqa: BLE001
        errors.append((str(path), f"{type(exc).__name__}: {exc}"))
if errors:
    for path, error in errors:
        try:
            shown = pathlib.Path(path).relative_to(root).as_posix()
        except ValueError:
            shown = pathlib.Path(path).name
        print(f"{shown}: {error}")
    sys.exit(1)
print(f"python syntax ok ({checked} files)")
'@ | python -B -
  if ($LASTEXITCODE -ne 0) {
    throw "Python syntax check failed"
  }
}

function Assert-NoSchemaMirrors {
  $specPath = Join-Path $rootPath "specification"
  $found = @(Get-ChildItem -LiteralPath $specPath -Force -File |
    Where-Object {
      $_.Name.EndsWith(".schema.json") -or
      ($_.Name.StartsWith("high_risk_types.v") -and $_.Name.EndsWith(".json"))
    })
  if ($found.Count) {
    $shown = @($found | ForEach-Object { Convert-ToPublicPath $_.FullName })
    throw "Schema/data mirrors are forbidden under specification/:`n$($shown -join "`n")"
  }
  Write-Host "No schema/data mirrors under specification/."
}

function Assert-NoForbiddenResidue {
  $names = @(
    "__pycache__",
    ".pytest_cache",
    ".ainp_test_tmp",
    ".mypy_cache",
    ".ruff_cache",
    ".execution_cache",
    ".evolution_snapshot",
    ".version_history",
    "site",
    "build",
    "dist"
  )
  $dirs = @(Get-ChildItem -LiteralPath $rootPath -Recurse -Force -Directory |
    Where-Object {
      ($names -contains $_.Name) -or $_.Name.EndsWith(".egg-info")
    })
  $files = @(Get-ChildItem -LiteralPath $rootPath -Recurse -Force -File |
    Where-Object { $_.Extension -in @(".pyc", ".pyo") })
  if ($dirs.Count -or $files.Count) {
    $items = @($dirs | ForEach-Object { Convert-ToPublicPath $_.FullName }) +
      @($files | ForEach-Object { Convert-ToPublicPath $_.FullName })
    throw "Forbidden generated residue found:`n$($items -join "`n")"
  }
  Write-Host "No forbidden generated residue found."
}

function Assert-NoPrivatePathLeak {
  $patterns = @(
    @{ Label = "Windows user profile path"; Value = ("C:" + [char]92 + "Users" + [char]92) },
    @{ Label = "Windows user profile path with forward slashes"; Value = ("C:" + [char]47 + "Users" + [char]47) },
    @{ Label = "local D-drive absolute path"; Value = ("D:" + [char]92) },
    @{ Label = "local D-drive absolute path with forward slash"; Value = ("D:" + [char]47) },
    @{ Label = "private key marker"; Value = ("BEGIN " + "PRIVATE " + "KEY") },
    @{ Label = "RSA private key marker"; Value = ("BEGIN " + "RSA " + "PRIVATE " + "KEY") },
    @{ Label = "OpenSSH private key marker"; Value = ("BEGIN " + "OPENSSH " + "PRIVATE " + "KEY") }
  )
  $regexPatterns = @(
    @{ Label = "Windows user profile path on any drive"; Value = "(?<![A-Za-z0-9+.-])[A-Za-z]:[\\/]*Users[\\/]" },
    @{ Label = "POSIX local absolute path"; Value = "(?<![A-Za-z0-9+.\-:/])/(?:Users|home|tmp|var|private|mnt|workspace|workspaces|root|run|opt/hostedtoolcache)(?:[\\/]|$)" }
  )
  $hits = @()
  Get-ChildItem -LiteralPath $rootPath -Recurse -Force -File |
    Where-Object {
      $rel = $_.FullName.Substring($rootPath.Length + 1)
      -not ($rel -split '[\\/]' | Where-Object { $_ -eq ".git" }) -and
      $_.Length -lt 5MB
    } |
    ForEach-Object {
      try {
        $text = Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8
      } catch {
        return
      }
      foreach ($pattern in $patterns) {
        if ($text.IndexOf($pattern.Value, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
          $hits += "$(Convert-ToPublicPath $_.FullName): contains $($pattern.Label)"
        }
      }
      foreach ($pattern in $regexPatterns) {
        if ([regex]::IsMatch($text, $pattern.Value, [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)) {
          $hits += "$(Convert-ToPublicPath $_.FullName): contains $($pattern.Label)"
        }
      }
    }
  if ($hits.Count) {
    throw "Potential private path/key leak found:`n$($hits -join "`n")"
  }
  Write-Host "No private path/key leak found outside .git."
}

function Assert-CleanWorkingTree {
  if (-not (Test-IsGitRepo)) {
    throw "RequireClean was requested, but $rootPath is not a Git repository."
  }
  $status = @(git -C $rootPath status --porcelain=v1 --untracked-files=all)
  if ($LASTEXITCODE -ne 0) {
    throw "git status failed with exit code $LASTEXITCODE"
  }
  if ($status.Count) {
    throw "Working tree is not clean:`n$($status -join "`n")"
  }
  Write-Host "Working tree is clean."
}

function Get-ExampleProjectPackages {
  $examplesPath = Join-Path $rootPath "examples"
  $packages = @(Get-ChildItem -LiteralPath $examplesPath -Force -Directory |
    Where-Object { $_.Name.EndsWith("_ainp") } |
    Sort-Object Name)
  if (-not $packages.Count) {
    throw "No example project packages found under examples/*_ainp."
  }
  return $packages
}

function Invoke-ExampleProjectHashChecks {
  foreach ($package in (Get-ExampleProjectPackages)) {
    $rel = $package.FullName.Substring($rootPath.Length + 1)
    $rel = $rel.Replace("\", "/")
    Invoke-Checked "project hash freshness $rel" {
      python -B tools/ainp_rehash.py $rel --check
    }
  }
}

function Invoke-ExampleReferenceManifestChecks {
  foreach ($package in (Get-ExampleProjectPackages)) {
    $manifest = Join-Path $package.FullName "ainp\references\reference_manifest.json"
    if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) {
      continue
    }
    $rel = $manifest.Substring($rootPath.Length + 1)
    $rel = $rel.Replace("\", "/")
    Invoke-Checked "reference manifest check $rel" {
      python -B tools/ainp_validate.py $rel
    }
  }
}

function Invoke-ExampleProjectPackageChecks {
  $packages = @(Get-ExampleProjectPackages)
  foreach ($package in $packages) {
    $rel = $package.FullName.Substring($rootPath.Length + 1)
    $rel = $rel.Replace("\", "/")
    Invoke-Checked "project package check $rel" {
      python -B tools/ainp_project_check.py $rel
    }
  }
}

function Invoke-ExampleProjectProgramTests {
  foreach ($package in (Get-ExampleProjectPackages)) {
    $tests = @(Get-ChildItem -LiteralPath $package.FullName -Recurse -Force -File -Filter "test_*.py" |
      Where-Object { ($_.FullName -split '[\\/]') -contains "tests" } |
      Sort-Object FullName)
    foreach ($test in $tests) {
      $rel = $test.FullName.Substring($rootPath.Length + 1)
      $rel = $rel.Replace("\", "/")
      Invoke-Checked "example project test $rel" {
        python -B $rel
      }
    }
  }
}

Push-Location $rootPath
try {
  Invoke-Checked "repository layout" { Assert-RepositoryLayout }
  Invoke-Checked "JSON syntax" { Invoke-JsonSyntaxCheck }
  Invoke-Checked "Python syntax" { Invoke-PythonSyntaxCheck }
  Invoke-Checked "conformance tests" { python -B tests/test_ainp.py }
  if ($IncludePytest) {
    Invoke-Checked "pytest tests" { python -B -m pytest -q -p no:cacheprovider -p no:asyncio }
  }
  Invoke-Checked "unified CLI doctor" { python -B tools/ainp.py doctor --json }
  Invoke-Checked "valid example plans, feedback and space" { python -B tools/ainp_validate.py examples/file_family/whitepaper.generation.json examples/file_family/high_risk_likeness.generation.json examples/file_family/landing_page.generation.json examples/file_family/dataset.generation.json examples/file_family/medical_advice.generation.json examples/file_family/security_exploit.generation.json examples/file_family/whitepaper_feedback.generationfeedback.json examples/file_family/high_risk_likeness_feedback.generationfeedback.json examples/file_family/project.ainp.json }
  Invoke-Checked "flat report check" { python -B tools/ainp_report_check.py examples/file_family/whitepaper.generationreport.json --mode release }
  Invoke-Checked "high-risk likeness report check" { python -B tools/ainp_report_check.py examples/file_family/high_risk_likeness.generationreport.json --mode release }
  Invoke-Checked "high-risk likeness release gate" { python -B tools/ainp_release_check.py examples/file_family/high_risk_likeness.generation.json --report examples/file_family/high_risk_likeness.generationreport.json }
  Invoke-Checked "project release gate" { python -B tools/ainp_release_check.py examples/whitepaper_ainp/ainp/whitepaper.generation.json --report examples/whitepaper_ainp/ainp/whitepaper.generationreport.json --project-root examples/whitepaper_ainp }
  Invoke-ExampleProjectProgramTests
  Invoke-ExampleReferenceManifestChecks
  Invoke-ExampleProjectHashChecks
  Invoke-ExampleProjectPackageChecks
  Invoke-Checked "docs command synchronization" { python -B tools/check_doc_sync.py --root . }
  Invoke-Checked "local Markdown links" { python -B tools/check_markdown_links.py --root . }

  Write-Host "==> schema mirror scan"
  Assert-NoSchemaMirrors
  Write-Host "==> generated residue scan"
  Assert-NoForbiddenResidue
  Write-Host "==> private path/key scan"
  Assert-NoPrivatePathLeak

  if (Test-IsGitRepo) {
    Invoke-Checked "whitespace errors" { git diff --check }
  } else {
    Write-Host "==> whitespace errors"
    Write-Host "Skipping git diff --check because this directory is not a Git repository."
  }

  if ($RequireClean) {
    Invoke-Checked "clean working tree" { Assert-CleanWorkingTree }
  }

  Write-Host "AINP release check passed."
}
catch {
  Write-Host "AINP release check failed: $($_.Exception.Message)"
  exit 1
}
finally {
  Pop-Location
  if ($null -eq $oldPythonDontWriteBytecode) {
    Remove-Item Env:PYTHONDONTWRITEBYTECODE -ErrorAction SilentlyContinue
  } else {
    $env:PYTHONDONTWRITEBYTECODE = $oldPythonDontWriteBytecode
  }
}
