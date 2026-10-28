using System;
using System.IO;
using System.Text;
using System.Globalization;

public static class EdgeAnalysis
{
    static double xmin, ymin, res; static int N; static float[] S, T;
    static double cx, cy, cu, su;
    static float Get(float[] a, double x, double y)
    {
        int c = (int)Math.Floor((x - xmin) / res); int r = (int)Math.Floor((ymin + N * res - y) / res);
        if (r < 0 || c < 0 || r >= N || c >= N) return float.NaN; return a[r * N + c];
    }
    static double H(double u, double v, double gref) { double x = cx + u * cu - v * su, y = cy + u * su + v * cu; return Get(S, x, y) - gref; }
    static float[] Load(string p) { var b = File.ReadAllBytes(p); var a = new float[b.Length / 4]; for (int i = 0; i < a.Length; i++) a[i] = BitConverter.ToSingle(b, i * 4); return a; }

    public static string Run(string dir, double azTrue, double conv, double gref, double ccx, double ccy)
    {
        var inv = CultureInfo.InvariantCulture; var sb = new StringBuilder();
        var g = File.ReadAllText(Path.Combine(dir, "grid.txt")).Trim().Split(' ');
        xmin = double.Parse(g[0], inv); ymin = double.Parse(g[1], inv); res = double.Parse(g[2], inv); N = int.Parse(g[3], inv);
        S = Load(Path.Combine(dir, "MNS.bil")); T = Load(Path.Combine(dir, "MNT.bil"));
        cx = ccx; cy = ccy; double ang = (90 - (azTrue - conv)) * Math.PI / 180; cu = Math.Cos(ang); su = Math.Sin(ang);
        // marching outward from axis; first point where h < 12 = edge
        sb.AppendLine("Long sides: per u, edge v (first drop below 12 m going outward), and height at 0.5/2/5/10/20 m inside edge; also max h in outer 30 m");
        for (double u = -95; u <= 120; u += 5)
        {
            var line = new StringBuilder(string.Format(inv, "u={0,5}", u));
            foreach (int sgn in new[] { 1, -1 })
            {
                double e = double.NaN;
                for (double v = 0; v <= 110; v += 0.25) { if (H(u, sgn * v, gref) < 12) { e = v; break; } }
                if (double.IsNaN(e) || e < 1) { line.Append(" | --"); continue; }
                double mx = -99; for (double v = Math.Max(0, e - 30); v < e; v += 0.25) mx = Math.Max(mx, H(u, sgn * v, gref));
                line.Append(string.Format(inv, " | {0}edge {1,6:F1}: h@-0.5={2,5:F1} -2={3,5:F1} -5={4,5:F1} -10={5,5:F1} -20={6,5:F1} max30={7,5:F1}",
                    sgn > 0 ? "+v" : "-v", sgn * e, H(u, sgn * (e - 0.5), gref), H(u, sgn * (e - 2), gref), H(u, sgn * (e - 5), gref), H(u, sgn * (e - 10), gref), H(u, sgn * (e - 20), gref), mx));
            }
            sb.AppendLine(line.ToString());
        }
        sb.AppendLine("Ends: per v, edge u going outward (+u north end, -u south end)");
        for (double v = -90; v <= 85; v += 5)
        {
            var line = new StringBuilder(string.Format(inv, "v={0,5}", v));
            foreach (int sgn in new[] { 1, -1 })
            {
                double e = double.NaN;
                for (double u = 0; u <= 140; u += 0.25) { if (H(sgn * u, v, gref) < 12) { e = u; break; } }
                if (double.IsNaN(e) || e < 1) { line.Append(" | --"); continue; }
                line.Append(string.Format(inv, " | {0}edge {1,6:F1}: h@-0.5={2,5:F1} -2={3,5:F1} -5={4,5:F1} -10={5,5:F1} -20={6,5:F1}",
                    sgn > 0 ? "+u" : "-u", sgn * e, H(sgn * (e - 0.5), v, gref), H(sgn * (e - 2), v, gref), H(sgn * (e - 5), v, gref), H(sgn * (e - 10), v, gref), H(sgn * (e - 20), v, gref)));
            }
            sb.AppendLine(line.ToString());
        }
        // plateau
        int n44 = 0, n40 = 0; double u0 = 1e9, u1 = -1e9, v0 = 1e9, v1 = -1e9;
        for (double u = -100; u <= 130; u += 1) for (double v = -95; v <= 95; v += 1)
            { double h = H(u, v, gref); if (h > 40) n40++; if (h > 44) { n44++; u0 = Math.Min(u0, u); u1 = Math.Max(u1, u); v0 = Math.Min(v0, v); v1 = Math.Max(v1, v); } }
        sb.AppendLine(string.Format(inv, "area h>40: {0} m2 ; area h>44: {1} m2, extents u {2}..{3} v {4}..{5}", n40, n44, u0, u1, v0, v1));
        return sb.ToString();
    }
}
