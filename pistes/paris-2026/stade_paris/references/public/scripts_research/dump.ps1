param([string]$json, [long]$id, [double]$az = 25.5)
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture
$j = Get-Content $json -Raw | ConvertFrom-Json
$e = $j.elements | Where-Object { $_.id -eq $id -and $_.type -eq 'relation' } | Select-Object -First 1
$lat0 = 48.8956; $lon0 = 2.2297; $R = 6378137
$kx = [math]::PI / 180 * $R * [math]::Cos($lat0 * [math]::PI / 180); $ky = [math]::PI / 180 * $R
$t = (90 - $az) * [math]::PI / 180; $c = [math]::Cos($t); $s = [math]::Sin($t)
# centroid of outer
$outer = $e.members[0].geometry
$cx = ($outer | ForEach-Object { ($_.lon - $lon0) * $kx } | Measure-Object -Average).Average
$cy = ($outer | ForEach-Object { ($_.lat - $lat0) * $ky } | Measure-Object -Average).Average
foreach ($m in $e.members) {
    "--- {0} {1}" -f $m.role, $m.ref
    foreach ($p in $m.geometry) {
        $x = ($p.lon - $lon0) * $kx - $cx; $y = ($p.lat - $lat0) * $ky - $cy
        $u = $x * $c + $y * $s; $v = - $x * $s + $y * $c
        "{0:F7},{1:F7}  u={2,7:F1} v={3,7:F1}" -f $p.lat, $p.lon, $u, $v
    }
}
