param([string]$json)
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture
$j = Get-Content $json -Raw | ConvertFrom-Json
$lat0 = 48.8956; $lon0 = 2.2297; $R = 6378137
$kx = [math]::PI / 180 * $R * [math]::Cos($lat0 * [math]::PI / 180); $ky = [math]::PI / 180 * $R
foreach ($f in $j.features) {
    $ring = $f.geometry.coordinates[0][0]
    # detect axis order
    $a0 = [double]$ring[0][0]; $b0 = [double]$ring[0][1]
    $pts = New-Object System.Collections.ArrayList
    foreach ($c in $ring) {
        if ($a0 -gt 40) { $la = [double]$c[0]; $lo = [double]$c[1] } else { $lo = [double]$c[0]; $la = [double]$c[1] }
        [void]$pts.Add(@((($lo - $lon0) * $kx), (($la - $lat0) * $ky), $(if ($c.Count -gt 2) { [double]$c[2] } else { 0 })))
    }
    $n = $pts.Count; $area = 0.0
    for ($i = 0; $i -lt $n - 1; $i++) { $area += $pts[$i][0] * $pts[$i + 1][1] - $pts[$i + 1][0] * $pts[$i][1] }
    $best = $null
    for ($deg = 0.0; $deg -lt 180; $deg += 0.25) {
        $t = $deg * [math]::PI / 180; $cs = [math]::Cos($t); $sn = [math]::Sin($t)
        $umin = 1e9; $umax = -1e9; $vmin = 1e9; $vmax = -1e9
        foreach ($q in $pts) { $u = $q[0] * $cs + $q[1] * $sn; $v = - $q[0] * $sn + $q[1] * $cs
            if ($u -lt $umin) { $umin = $u }; if ($u -gt $umax) { $umax = $u }; if ($v -lt $vmin) { $vmin = $v }; if ($v -gt $vmax) { $vmax = $v } }
        $ar = ($umax - $umin) * ($vmax - $vmin)
        if (-not $best -or $ar -lt $best[0]) { $best = @($ar, $deg, ($umax - $umin), ($vmax - $vmin)) }
    }
    $L = $best[2]; $W = $best[3]; $ang = $best[1]
    if ($W -gt $L) { $tmp = $L; $L = $W; $W = $tmp; $ang += 90 }
    $az = (90 - $ang) % 180; if ($az -lt 0) { $az += 180 }
    $zs = $pts | ForEach-Object { $_[2] } | Measure-Object -Min -Max
    $cxm = ($pts | ForEach-Object { $_[0] } | Measure-Object -Average).Average; $cym = ($pts | ForEach-Object { $_[1] } | Measure-Object -Average).Average
    "{0} usage={1} h={2} | n={3} area={4:F0} m2 | rect {5:F1} x {6:F1} | az {7:F2} | z {8}..{9} | centre offset E{10:F0} N{11:F0}" -f $f.properties.cleabs, $f.properties.usage_1, $f.properties.hauteur, $n, [math]::Abs($area / 2), $L, $W, $az, $zs.Minimum, $zs.Maximum, $cxm, $cym
}
