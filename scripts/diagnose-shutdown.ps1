# Instalika Power – kompiuterio išjungimo diagnostika
# Paleiskite ADMINISTRATORIAUS teisėmis ant PC, kuris netikėtai išsijungia.
# Pvz.: powershell -ExecutionPolicy Bypass -File diagnose-shutdown.ps1

param(
    [int]$Days = 7,
    [string]$OutputFile = ""
)

$ErrorActionPreference = "SilentlyContinue"
$since = (Get-Date).AddDays(-$Days)

function Write-Section($title) {
    Write-Host ""
    Write-Host ("=" * 60) -ForegroundColor Cyan
    Write-Host $title -ForegroundColor Cyan
    Write-Host ("=" * 60) -ForegroundColor Cyan
}

$report = [System.Collections.Generic.List[string]]::new()
function Add-Line($text) {
    $script:report.Add($text)
    Write-Host $text
}

Add-Line "Instalika Power – išjungimo diagnostika"
Add-Line "Kompiuteris: $env:COMPUTERNAME"
Add-Line "Laikas: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Add-Line "Tikrinama nuo: $($since.ToString('yyyy-MM-dd HH:mm:ss'))"
Add-Line ""

# --- 1. Išjungimo įvykiai (kas išjungė) ---
Write-Section "1. Išjungimo įvykiai (Event ID 1074 – kas inicijavo)"

$shutdownEvents = Get-WinEvent -FilterHashtable @{
    LogName   = "System"
    Id        = 1074
    StartTime = $since
} -ErrorAction SilentlyContinue | Sort-Object TimeCreated -Descending

if ($shutdownEvents) {
    foreach ($ev in $shutdownEvents) {
        Add-Line ""
        Add-Line "  Data: $($ev.TimeCreated)"
        Add-Line "  Pranešimas: $($ev.Message -replace '\s+', ' ')"
    }
} else {
    Add-Line "  Nerasta 1074 įvykių (planuotas išjungimas/restartas)."
}

# --- 2. Netikėti išjungimai ---
Write-Section "2. Netikėti išjungimai (6008, 41, 109)"

$unexpectedIds = @(6008, 41, 109)
foreach ($id in $unexpectedIds) {
    $events = Get-WinEvent -FilterHashtable @{
        LogName   = "System"
        Id        = $id
        StartTime = $since
    } -ErrorAction SilentlyContinue | Sort-Object TimeCreated -Descending

    if ($events) {
        Add-Line ""
        Add-Line "  Event ID $id :"
        foreach ($ev in $events | Select-Object -First 5) {
            Add-Line "    $($ev.TimeCreated) – $($ev.Message.Split("`n")[0])"
        }
    }
}

# --- 3. Maitinimo / miego nustatymai ---
Write-Section "3. Maitinimo schema ir miegas"

$activeScheme = powercfg /getactivescheme
Add-Line "  $activeScheme"

$sleep = powercfg /query SCHEME_CURRENT SUB_SLEEP
Add-Line ""
Add-Line "  Miego nustatymai (powercfg):"
$sleep -split "`n" | Where-Object { $_ -match "Current AC|Current DC|GUID" } | ForEach-Object { Add-Line "    $_" }

# --- 4. Suplanuotos užduotys su shutdown ---
Write-Section "4. Suplanuotos užduotys (shutdown / restart / hibernate)"

$tasks = Get-ScheduledTask -ErrorAction SilentlyContinue | Where-Object {
    $_.State -ne "Disabled" -and (
        $_.Actions.Execute -match "shutdown|restart|hibernate|powercfg" -or
        $_.Actions.Arguments -match "shutdown|restart|hibernate|/s |/r "
    )
}

if ($tasks) {
    foreach ($t in $tasks) {
        $info = Get-ScheduledTaskInfo -TaskName $t.TaskName -TaskPath $t.TaskPath -ErrorAction SilentlyContinue
        Add-Line ""
        Add-Line "  Užduotis: $($t.TaskPath)$($t.TaskName)"
        Add-Line "    Veiksmas: $($t.Actions.Execute) $($t.Actions.Arguments)"
        Add-Line "    Paskutinis paleidimas: $($info.LastRunTime)"
        Add-Line "    Kitas paleidimas: $($info.NextRunTime)"
    }
} else {
    Add-Line "  Nerasta aktyvių shutdown/restart užduočių."
}

# --- 5. Windows Update ---
Write-Section "5. Windows Update (galimas automatinis restartas)"

$wuEvents = Get-WinEvent -FilterHashtable @{
    LogName   = "System"
    ProviderName = "Microsoft-Windows-WindowsUpdateClient"
    StartTime = $since
} -ErrorAction SilentlyContinue | Sort-Object TimeCreated -Descending | Select-Object -First 5

if ($wuEvents) {
    foreach ($ev in $wuEvents) {
        Add-Line "  $($ev.TimeCreated) [ID $($ev.Id)] $($ev.Message.Split("`n")[0])"
    }
} else {
    Add-Line "  Nėra Windows Update įvykių per laikotarpį."
}

# --- 6. Tinklo adapteris / WoL ---
Write-Section "6. Tinklo adapteris (IP, MAC, Wake-on-LAN)"

Get-NetAdapter -Physical -ErrorAction SilentlyContinue | ForEach-Object {
  $ip = (Get-NetIPAddress -InterfaceIndex $_.ifIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
         Where-Object { $_.IPAddress -notlike "169.254.*" } | Select-Object -First 1).IPAddress
  Add-Line ""
  Add-Line "  $($_.Name): $($_.Status), MAC $($_.MacAddress), IP $ip"
  $wol = Get-NetAdapterAdvancedProperty -Name $_.Name -ErrorAction SilentlyContinue |
         Where-Object { $_.DisplayName -match "Wake" }
  if ($wol) {
      $wol | ForEach-Object { Add-Line "    $($_.DisplayName) = $($_.DisplayValue)" }
  }
}

# --- 7. Santrauka ---
Write-Section "SANTRAUKA"

Add-Line @"

Dažniausios netikėto išsijungimo priežastys:

  A) Home Assistant / automacija
     - Patikrinkite HA: Nustatymai → Automacijos → filtras „shutdown“, „restart“, „off“
     - shell_command, script, wake_on_lan (tik ĮJUNGIA, neišjungia)
     - Smart kištukas (TP-Link, Shelly) – ar nepertraukia maitinimo?

  B) Windows planuotas restartas (1074 įvykis rodo procesą, pvz. TiWorker.exe = Update)

  C) Maitinimo gedimas / perkaitimas (Event 41, 6008 – be 1074)

  D) UPS programinė įranga ar BIOS „AC Power Recovery“

  E) Instalika Power / šis projektas – TIK ĮJUNGIA per WoL, neišjungia kompiuterių.

Jei 1074 rodo procesą – tai PLANUOTAS išjungimas (ne gedimas).
Jei tik 41/6008 – tikėtina HARDVERINĖ ar maitinimo problema.
"@

if ($OutputFile) {
    $report | Out-File -FilePath $OutputFile -Encoding UTF8
    Write-Host ""
    Write-Host "Ataskaita išsaugota: $OutputFile" -ForegroundColor Green
}
