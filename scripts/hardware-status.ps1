# Instalika Power – kompiuterio būsenos ir temperatūrų nuskaitymas
# Paleiskite ant pačio PC (ne iš debesies). Reikia Administratoriaus teisių geresniems duomenims.
#
#   powershell -ExecutionPolicy Bypass -File hardware-status.ps1
#   powershell -ExecutionPolicy Bypass -File hardware-status.ps1 -Json -OutputFile status.json

param(
    [switch]$Json,
    [string]$OutputFile = ""
)

$ErrorActionPreference = "SilentlyContinue"

$result = [ordered]@{
    timestamp = (Get-Date).ToString("yyyy-MM-ddTHH:mm:ss")
    computer  = $env:COMPUTERNAME
    bios      = @{}
    system    = @{}
    cpu       = @{}
    memory    = @{}
    disks     = @()
    temperatures = @()
    fans      = @()
    battery   = $null
    warnings  = @()
}

# --- SMBIOS / BIOS (statiniai duomenys) ---
$bios = Get-CimInstance Win32_BIOS | Select-Object -First 1
$result.bios = @{
    manufacturer = $bios.Manufacturer
    version      = $bios.SMBIOSBIOSVersion
    releaseDate  = $bios.ReleaseDate
    serialNumber = $bios.SerialNumber
}

$cs = Get-CimInstance Win32_ComputerSystem | Select-Object -First 1
$result.system = @{
    manufacturer = $cs.Manufacturer
    model        = $cs.Model
    totalMemoryGb = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)
}

# --- CPU ---
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$result.cpu = @{
    name       = $cpu.Name.Trim()
    cores      = $cpu.NumberOfCores
    threads    = $cpu.NumberOfLogicalProcessors
    loadPercent = $cpu.LoadPercentage
    maxClockMhz = $cpu.MaxClockSpeed
    currentClockMhz = $cpu.CurrentClockSpeed
}

# --- RAM ---
$os = Get-CimInstance Win32_OperatingSystem
$result.memory = @{
    totalGb     = [math]::Round($os.TotalVisibleMemorySize / 1MB, 2)
    freeGb      = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    usedPercent = [math]::Round((1 - $os.FreePhysicalMemory / $os.TotalVisibleMemorySize) * 100, 1)
}

# --- Diskai ---
Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
    $result.disks += @{
        drive       = $_.DeviceID
        label       = $_.VolumeName
        totalGb     = [math]::Round($_.Size / 1GB, 2)
        freeGb      = [math]::Round($_.FreeSpace / 1GB, 2)
        usedPercent = if ($_.Size) { [math]::Round((1 - $_.FreeSpace / $_.Size) * 100, 1) } else { 0 }
    }
}

# --- Temperatūros: ACPI thermal zones (dažnai tuščia ant desktop) ---
Get-CimInstance -Namespace root/wmi -ClassName MSAcpi_ThermalZoneTemperature -ErrorAction SilentlyContinue |
    ForEach-Object {
        $c = [math]::Round(($_.CurrentTemperature / 10) - 273.15, 1)
        $result.temperatures += @{
            source = "ACPI:$($_.InstanceName)"
            celsius = $c
        }
    }

# --- Temperatūros: LibreHardwareMonitor (jei paleistas) ---
$lhm = Get-CimInstance -Namespace root/LibreHardwareMonitor -ClassName Sensor -ErrorAction SilentlyContinue |
    Where-Object { $_.SensorType -eq "Temperature" -and $_.Value -ne $null }

foreach ($s in $lhm) {
    $result.temperatures += @{
        source  = "LHM:$($s.Parent)/$($s.Name)"
        celsius = [math]::Round($s.Value, 1)
    }
}

# --- Ventiliatoriai (LHM) ---
Get-CimInstance -Namespace root/LibreHardwareMonitor -ClassName Sensor -ErrorAction SilentlyContinue |
    Where-Object { $_.SensorType -eq "Fan" -and $_.Value -ne $null } |
    ForEach-Object {
        $result.fans += @{
            name = "$($_.Parent)/$($_.Name)"
            rpm  = [math]::Round($_.Value, 0)
        }
    }

# --- Baterija (laptop) ---
$bat = Get-CimInstance Win32_Battery | Select-Object -First 1
if ($bat) {
    $result.battery = @{
        status          = switch ($bat.BatteryStatus) { 1 {"įkraunama"} 2 {"AC"} 3 {"įkrauta"} default {"kita"} }
        chargePercent   = $bat.EstimatedChargeRemaining
        estimatedMinutes = $bat.EstimatedRunTime
    }
}

# --- Įspėjimai ---
if ($result.temperatures.Count -eq 0) {
    $result.warnings += "Temperatūrų sensorių nerasta per ACPI/LibreHardwareMonitor. Įdiekite ir paleiskite LibreHardwareMonitor geresniems duomenims."
}
foreach ($t in $result.temperatures) {
    if ($t.celsius -ge 90) {
        $result.warnings += "KRITINĖ temperatūra: $($t.source) = $($t.celsius)°C (galimas perkaitimas / išsijungimas)"
    } elseif ($t.celsius -ge 80) {
        $result.warnings += "Aukšta temperatūra: $($t.source) = $($t.celsius)°C"
    }
}
if ($result.memory.usedPercent -ge 90) {
    $result.warnings += "RAM naudojama $($result.memory.usedPercent)%"
}
foreach ($d in $result.disks) {
    if ($d.usedPercent -ge 90) {
        $result.warnings += "Diskas $($d.drive) užpildytas $($d.usedPercent)%"
    }
}

# --- Išvestis ---
if ($Json) {
    $text = $result | ConvertTo-Json -Depth 6
    if ($OutputFile) {
        $text | Out-File -FilePath $OutputFile -Encoding UTF8
        Write-Host "JSON išsaugotas: $OutputFile"
    } else {
        Write-Output $text
    }
} else {
    Write-Host ""
    Write-Host "=== Instalika Power – kompiuterio būsena ===" -ForegroundColor Cyan
    Write-Host "Laikas: $($result.timestamp)  |  PC: $($result.computer)"
    Write-Host ""
    Write-Host "BIOS / plokštė:" -ForegroundColor Yellow
    Write-Host "  $($result.bios.manufacturer) $($result.bios.version)"
    Write-Host "  $($result.system.manufacturer) $($result.system.model)"
    Write-Host ""
    Write-Host "CPU: $($result.cpu.name)" -ForegroundColor Yellow
    Write-Host "  Apkrova: $($result.cpu.loadPercent)%  |  $($result.cpu.cores)c/$($result.cpu.threads)t  |  $($result.cpu.currentClockMhz) MHz"
    Write-Host ""
    Write-Host "RAM: $($result.memory.usedPercent)% naudojama ($($result.memory.freeGb) GB laisva / $($result.memory.totalGb) GB)" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Diskai:" -ForegroundColor Yellow
    foreach ($d in $result.disks) {
        Write-Host "  $($d.drive) $($d.label): $($d.usedPercent)% ($($d.freeGb) GB laisva)"
    }
    Write-Host ""
    Write-Host "Temperatūros:" -ForegroundColor Yellow
    if ($result.temperatures.Count -gt 0) {
        foreach ($t in $result.temperatures) {
            $color = if ($t.celsius -ge 90) { "Red" } elseif ($t.celsius -ge 80) { "Yellow" } else { "Green" }
            Write-Host "  $($t.source): $($t.celsius)°C" -ForegroundColor $color
        }
    } else {
        Write-Host "  (nerasta – žr. įspėjimus žemiau)" -ForegroundColor DarkGray
    }
    if ($result.fans.Count -gt 0) {
        Write-Host ""
        Write-Host "Ventiliatoriai:" -ForegroundColor Yellow
        foreach ($f in $result.fans) {
            Write-Host "  $($f.name): $($f.rpm) RPM"
        }
    }
    if ($result.warnings.Count -gt 0) {
        Write-Host ""
        Write-Host "Įspėjimai:" -ForegroundColor Red
        foreach ($w in $result.warnings) { Write-Host "  ! $w" -ForegroundColor Red }
    }
    Write-Host ""
}
