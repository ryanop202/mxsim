param([string]$dir, [double]$az = 25.5, [double]$gref = 0)
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture
$g = (Get-Content "$dir\grid.txt").Split(' '); $xmin = [double]$g[0]; $ymin = [double]$g[1]; $res = [double]$g[2]; $N = [int]$g[3]
$bs = [IO.File]::ReadAllBytes("$dir\MNS.bil"); $bt = [IO.File]::ReadAllBytes("$dir\MNT.bil")
$S = New-Object 'double[,]' $N, $N; $T = New-Object 'double[,]' $N, $N
for ($r = 0; $r -lt $N; $r++) { for ($c = 0; $c -lt $N; $c++) { $k = ($r * $N + $c) * 4; $S[$r, $c] = [BitConverter]::ToSingle($bs, $k); $T[$r, $c] = [BitConverter]::ToSingle($bt, $k) } }
# row 0 = north (ymax)
function XY($r, $c) { @(($xmin + ($c + 0.5) * $res), ($ymin + $N * $res - ($r + 0.5) * $res)) }
"MNS sample centre: {0}  MNT centre: {1}" -f $S[260, 260], $T[260, 260]
# terrain stats around
$tv = @(); for ($r = 0; $r -lt $N; $r += 10) { for ($c = 0; $c -lt $N; $c += 10) { $tv += $T[$r, $c] } }
$tm = $tv | Measure-Object -Min -Max -Average; "MNT range {0:F1}..{1:F1} avg {2:F1}" -f $tm.Minimum, $tm.Maximum, $tm.Average
# building mask: MNS - MNT > 12
$sx = 0; $sy = 0; $cnt = 0; $hmax = -1; $hmaxpos = $null
for ($r = 0; $r -lt $N; $r++) { for ($c = 0; $c -lt $N; $c++) { $h = $S[$r, $c] - $T[$r, $c]; if ($h -gt 20) { $p = XY $r $c; $sx += $p[0]; $sy += $p[1]; $cnt++ }; if ($S[$r, $c] -gt $hmax) { $hmax = $S[$r, $c]; $hmaxpos = @($r, $c) } } }
$cx = $sx / $cnt; $cy = $sy / $cnt
"mask(h>20m) area={0:F0} m2 centroid L93 {1:F1} {2:F1}" -f ($cnt * $res * $res), $cx, $cy
$p = XY $hmaxpos[0] $hmaxpos[1]; "max MNS {0:F2} at L93 {1:F1} {2:F1} (MNT there {3:F2})" -f $hmax, $p[0], $p[1], $T[$hmaxpos[0], $hmaxpos[1]]
# Note: L93 grid north differs from true north by meridian convergence; at lon 2.23 the convergence is about -0.58 deg (grid north is east of... handled approx)
$conv = -0.58
$t = (90 - ($az - $conv)) * [math]::PI / 180; $cu = [math]::Cos($t); $su = [math]::Sin($t)
function Sample($u, $v) { $x = $cx + $u * $cu - $v * $su; $y = $cy + $u * $su + $v * $cu; $c = [int][math]::Floor(($x - $xmin) / $res); $r = [int][math]::Floor(($ymin + $N * $res - $y) / $res); if ($r -lt 0 -or $c -lt 0 -or $r -ge $N -or $c -ge $N) { return @([double]::NaN, [double]::NaN) }; return @($S[$r, $c], $T[$r, $c]) }
"`n== Profile along long axis (u, v=0); u>0 toward azimuth $az ==="
for ($u = -120; $u -le 130; $u += 5) { $s = Sample $u 0; "u={0,5} MNS={1,7:F2} MNT={2,7:F2}" -f $u, $s[0], $s[1] }
"`n== Profile across (v, u=0); v>0 toward azimuth $($az-90) ==="
for ($v = -100; $v -le 100; $v += 5) { $s = Sample 0 $v; "v={0,5} MNS={1,7:F2} MNT={2,7:F2}" -f $v, $s[0], $s[1] }
# extents of mask in rotated frame
$umin = 1e9; $umax = -1e9; $vmin = 1e9; $vmax = -1e9
for ($r = 0; $r -lt $N; $r += 1) { for ($c = 0; $c -lt $N; $c += 1) { if ($S[$r, $c] - $T[$r, $c] -gt 15) { $p = XY $r $c; $dx = $p[0] - $cx; $dy = $p[1] - $cy; $u = $dx * $cu + $dy * $su; $v = - $dx * $su + $dy * $cu; if ([math]::Abs($u) -lt 140 -and [math]::Abs($v) -lt 110) { if ($u -lt $umin) { $umin = $u }; if ($u -gt $umax) { $umax = $u }; if ($v -lt $vmin) { $vmin = $v }; if ($v -gt $vmax) { $vmax = $v } } } } }
"`nmask(h>15) rotated extents u {0:F1}..{1:F1} (L={2:F1})  v {3:F1}..{4:F1} (W={5:F1})" -f $umin, $umax, ($umax - $umin), $vmin, $vmax, ($vmax - $vmin)
# Rim profile: walk around perimeter: for each angle from centroid, march outward, record last point with h>15 and the max MNS within the outer 15 m band
"`n== Rim (crown) profile by bearing from centroid (bearing = true azimuth) ==="
for ($b = 0; $b -lt 360; $b += 5) {
    $tb = (90 - ($b - $conv)) * [math]::PI / 180; $dxu = [math]::Cos($tb); $dyu = [math]::Sin($tb)
    $last = -1; $prof = @{}
    for ($d = 0; $d -le 130; $d += 0.5) { $x = $cx + $d * $dxu; $y = $cy + $d * $dyu; $c = [int][math]::Floor(($x - $xmin) / $res); $r = [int][math]::Floor(($ymin + $N * $res - $y) / $res); if ($r -lt 0 -or $c -lt 0 -or $r -ge $N -or $c -ge $N) { break }; $prof[$d] = $S[$r, $c]; if ($S[$r, $c] - $T[$r, $c] -gt 15) { $last = $d } }
    $bandmax = -1; $bandd = 0
    foreach ($k in $prof.Keys) { if ($k -ge $last - 15 -and $k -le $last -and $prof[$k] -gt $bandmax) { $bandmax = $prof[$k]; $bandd = $k } }
    "bearing {0,3}: edge at {1,6:F1} m from centroid; crown max MNS {2,7:F2} at {3,6:F1} m" -f $b, $last, $bandmax, $bandd
}
# Downsampled ASCII map of height above 54.6 (5 m cells), rotated frame
"`n== Height map (MNS - $gref), 6 m cells, rows = u (long axis, top = +u toward az), cols = v; values in metres/ 'digit' = floor(h/5) ==="
for ($u = 120; $u -ge -115; $u -= 6) { $line = ''; for ($v = -100; $v -le 100; $v += 4) { $s = Sample $u $v; $h = $s[0] - $gref; if ([double]::IsNaN($h)) { $line += ' ' } elseif ($h -lt 3) { $line += '.' } else { $q = [int][math]::Floor($h / 5); if ($q -gt 35) { $q = 35 }; $line += '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'[$q] } }; "{0,5} {1}" -f $u, $line }
