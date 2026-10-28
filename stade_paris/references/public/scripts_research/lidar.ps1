param([string]$outdir)
[System.Threading.Thread]::CurrentThread.CurrentCulture = [System.Globalization.CultureInfo]::InvariantCulture
# Lambert-93 forward projection (GRS80)
function ToL93([double]$lat, [double]$lon) {
    $a = 6378137.0; $f = 1 / 298.257222101; $e = [math]::Sqrt(2 * $f - $f * $f)
    $d2r = [math]::PI / 180
    $phi1 = 44 * $d2r; $phi2 = 49 * $d2r; $phi0 = 46.5 * $d2r; $lam0 = 3 * $d2r; $x0 = 700000; $y0 = 6600000
    function m($p) { [math]::Cos($p) / [math]::Sqrt(1 - $e * $e * [math]::Sin($p) * [math]::Sin($p)) }
    function t($p) { [math]::Tan([math]::PI / 4 - $p / 2) / [math]::Pow((1 - $e * [math]::Sin($p)) / (1 + $e * [math]::Sin($p)), $e / 2) }
    $m1 = m $phi1; $m2 = m $phi2; $t1 = t $phi1; $t2 = t $phi2; $t0 = t $phi0
    $n = ([math]::Log($m1) - [math]::Log($m2)) / ([math]::Log($t1) - [math]::Log($t2))
    $F = $m1 / ($n * [math]::Pow($t1, $n)); $r0 = $a * $F * [math]::Pow($t0, $n)
    $tt = t ($lat * $d2r); $r = $a * $F * [math]::Pow($tt, $n); $th = $n * ($lon * $d2r - $lam0)
    return @(($x0 + $r * [math]::Sin($th)), ($y0 + $r0 - $r * [math]::Cos($th)))
}
$c = ToL93 48.8956 2.2297
"centre L93: {0:F1} {1:F1}" -f $c[0], $c[1]
$half = 130; $res = 0.5; $npx = [int](2 * $half / $res)
$xmin = [math]::Round($c[0] - $half); $ymin = [math]::Round($c[1] - $half); $xmax = $xmin + 2 * $half; $ymax = $ymin + 2 * $half
"bbox {0} {1} {2} {3} px={4}" -f $xmin, $ymin, $xmax, $ymax, $npx
foreach ($layer in @('MNS', 'MNT')) {
    $url = "https://data.geopf.fr/wms-r/wms?SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap&LAYERS=IGNF_LIDAR-HD_${layer}_ELEVATION.ELEVATIONGRIDCOVERAGE.LAMB93&STYLES=&CRS=EPSG:2154&BBOX=$xmin,$ymin,$xmax,$ymax&WIDTH=$npx&HEIGHT=$npx&FORMAT=image/x-bil;bits=32"
    & curl.exe -s -m 180 -A "research-script/1.0" $url -o "$outdir\$layer.bil"
    "{0}: {1} bytes (expected {2})" -f $layer, (Get-Item "$outdir\$layer.bil").Length, ($npx * $npx * 4)
}
"$xmin $ymin $res $npx" | Set-Content "$outdir\grid.txt"
