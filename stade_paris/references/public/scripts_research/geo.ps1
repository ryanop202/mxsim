param([string]$json, [string]$ids)
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture
$j = Get-Content $json -Raw | ConvertFrom-Json
$lat0 = 48.8956; $lon0 = 2.2297; $R = 6378137
$kx = [math]::PI / 180 * $R * [math]::Cos($lat0 * [math]::PI / 180); $ky = [math]::PI / 180 * $R

function Get-Pts($g) {
    $list = New-Object System.Collections.ArrayList
    foreach ($p in $g) { [void]$list.Add(@((($p.lon - $lon0) * $kx), (($p.lat - $lat0) * $ky))) }
    return ,$list
}
function Analyze($pts, $label) {
    $n = $pts.Count; $area = 0.0; $P = 0.0
    for ($i = 0; $i -lt $n - 1; $i++) {
        $area += $pts[$i][0] * $pts[$i + 1][1] - $pts[$i + 1][0] * $pts[$i][1]
        $P += [math]::Sqrt([math]::Pow($pts[$i + 1][0] - $pts[$i][0], 2) + [math]::Pow($pts[$i + 1][1] - $pts[$i][1], 2))
    }
    $best = $null
    for ($deg = 0.0; $deg -lt 180; $deg += 0.25) {
        $t = $deg * [math]::PI / 180; $c = [math]::Cos($t); $s = [math]::Sin($t)
        $umin = 1e9; $umax = -1e9; $vmin = 1e9; $vmax = -1e9
        foreach ($q in $pts) { $u = $q[0] * $c + $q[1] * $s; $v = - $q[0] * $s + $q[1] * $c
            if ($u -lt $umin) { $umin = $u }; if ($u -gt $umax) { $umax = $u }; if ($v -lt $vmin) { $vmin = $v }; if ($v -gt $vmax) { $vmax = $v } }
        $ar = ($umax - $umin) * ($vmax - $vmin)
        if (-not $best -or $ar -lt $best[0]) { $best = @($ar, $deg,($umax - $umin), ($vmax - $vmin)) }
    }
    $L = $best[2]; $W = $best[3]; $ang = $best[1]
    if ($W -gt $L) { $tmp = $L; $L = $W; $W = $tmp; $ang = $ang + 90 }
    $az = (90 - $ang) % 180; if ($az -lt 0) { $az += 180 }
    "{0}: nodes={1} area={2:F0} m2 perim={3:F0} m | min-area rect {4:F1} x {5:F1} m | long-axis azimuth {6:F2} deg (true N, cw) | rect fill ratio {7:F3}" -f $label, $n, [math]::Abs($area / 2), $P, $L, $W, $az, ([math]::Abs($area / 2) / ($L * $W))
}
foreach ($id in $ids.Split(',')) {
    $e = $j.elements | Where-Object { $_.id -eq [long]$id } | Select-Object -First 1
    if ($e.type -eq 'relation') { foreach ($m in $e.members) { Analyze (Get-Pts $m.geometry) ("rel $id {0} way {1}" -f $m.role, $m.ref) } }
    else { Analyze (Get-Pts $e.geometry) ("way $id " + ($e.tags | ConvertTo-Json -Compress)) }
}

