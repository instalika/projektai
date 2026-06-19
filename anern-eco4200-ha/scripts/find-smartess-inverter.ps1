# Anern ECO-4200 / SmartESS Wi-Fi Plug Pro — tinklo paieska
# Paleiskite PowerShell kaip administratorius arba paprastas vartotojas.

param(
    [string]$Subnet = "",
    [switch]$Quick
)

function Get-LocalSubnet {
    $ip = Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object {
            $_.IPAddress -notlike "127.*" -and
            $_.PrefixOrigin -ne "WellKnown"
        } |
        Select-Object -First 1

    if (-not $ip) {
        throw "Nepavyko nustatyti vietinio IPv4 tinklo."
    }

    $octets = $ip.IPAddress.Split(".")
    return "$($octets[0]).$($octets[1]).$($octets[2])"
}

function Test-SmartEssPorts {
    param([string]$TargetIp)

    $tcp8899 = $false
    $tcp502 = $false

    try {
        $tcp8899 = Test-NetConnection -ComputerName $TargetIp -Port 8899 -WarningAction SilentlyContinue -InformationLevel Quiet
    } catch {}

    try {
        $tcp502 = Test-NetConnection -ComputerName $TargetIp -Port 502 -WarningAction SilentlyContinue -InformationLevel Quiet
    } catch {}

    return [PSCustomObject]@{
        Ip = $TargetIp
        Tcp8899 = [bool]$tcp8899
        Tcp502 = [bool]$tcp502
        LikelySmartEss = [bool]$tcp8899
    }
}

if (-not $Subnet) {
    $Subnet = Get-LocalSubnet
}

Write-Host ""
Write-Host "=== Anern ECO-4200 / SmartESS tinklo paieska ===" -ForegroundColor Cyan
Write-Host "Tinklas: $Subnet.0/24"
Write-Host "Ieskoma: TCP 8899 (SmartESS/EyeBond), TCP 502 (Modbus)"
Write-Host ""

$activeHosts = @()
$jobs = 1..254 | ForEach-Object {
    $ip = "$Subnet.$_"
    Start-Job -ScriptBlock {
        param($Address)
        if (Test-Connection -ComputerName $Address -Count 1 -Quiet -TimeoutSeconds 1) {
            return $Address
        }
        return $null
    } -ArgumentList $ip
}

Wait-Job $jobs | Out-Null
foreach ($job in $jobs) {
    $result = Receive-Job $job
    Remove-Job $job -Force
    if ($result) {
        $activeHosts += $result
    }
}

if ($activeHosts.Count -eq 0) {
    Write-Host "Aktyviu irenginiu nerasta." -ForegroundColor Yellow
    exit 1
}

Write-Host "Rasta aktyviu irenginiu: $($activeHosts.Count)" -ForegroundColor Green
Write-Host ""

$candidates = @()
foreach ($hostIp in ($activeHosts | Sort-Object {[version]$_.Replace('.', '.0.')})) {
    if ($Quick) {
        Write-Host "Aktyvus: $hostIp"
        continue
    }

    $result = Test-SmartEssPorts -TargetIp $hostIp
    if ($result.LikelySmartEss) {
        Write-Host ">>> SMARTESS LOGGERIS: $($result.Ip)  (TCP 8899=TAIP, TCP 502=$($result.Tcp502))" -ForegroundColor Green
        $candidates += $result
    } else {
        Write-Host "Aktyvus: $($result.Ip)  (8899=NE, 502=$($result.Tcp502))"
    }
}

Write-Host ""
if ($candidates.Count -gt 0) {
    $best = $candidates[0]
    Write-Host "Rekomenduojamas IP Home Assistant:" -ForegroundColor Cyan
    Write-Host "  $($best.Ip)"
    Write-Host ""
    Write-Host "Kitas zingsnis:"
    Write-Host "  1. Routeryje rezervuokite si IP Wi-Fi Plug Pro adapteriui"
    Write-Host "  2. Home Assistant -> HACS -> SmartESS Local arba DESS Monitor"
    Write-Host ""
    $best.Ip | Out-File -FilePath "$PSScriptRoot\found-smartess-ip.txt" -Encoding utf8
    Write-Host "IP issaugotas: $PSScriptRoot\found-smartess-ip.txt"
} else {
    Write-Host "SmartESS loggerio su atviru 8899 portu nerasta." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Patikrinkite:"
    Write-Host "  - Ar Wi-Fi Plug Pro ijungtas ir prisijunges prie to paties Wi-Fi kaip PC"
    Write-Host "  - Ar routeryje matote irengini su PN W00... arba ESP_..."
    Write-Host "  - SmartESS programele -> Device Information -> PN numeris"
}
