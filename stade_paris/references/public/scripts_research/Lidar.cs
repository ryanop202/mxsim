using System;
using System.IO;
using System.Text;
using System.Globalization;

public static class LidarAnalysis
{
    static double xmin, ymin, res; static int N;
    static float[] S, T;
    static double cx, cy, cu, su;

    static float Get(float[] a, double x, double y)
    {
        int c = (int)Math.Floor((x - xmin) / res);
        int r = (int)Math.Floor((ymin + N * res - y) / res);
        if (r < 0 || c < 0 || r >= N || c >= N) return float.NaN;
        return a[r * N + c];
    }
    static double X(int c) { return xmin + (c + 0.5) * res; }
    static double Y(int r) { return ymin + N * res - (r + 0.5) * res; }
    // rotated frame -> L93
    static void UV2XY(double u, double v, out double x, out double y) { x = cx + u * cu - v * su; y = cy + u * su + v * cu; }

    public static string Run(string dir, double azTrue, double conv, double gref)
    {
        var inv = CultureInfo.InvariantCulture;
        var sb = new StringBuilder();
        var g = File.ReadAllText(Path.Combine(dir, "grid.txt")).Trim().Split(' ');
        xmin = double.Parse(g[0], inv); ymin = double.Parse(g[1], inv); res = double.Parse(g[2], inv); N = int.Parse(g[3], inv);
        S = Load(Path.Combine(dir, "MNS.bil")); T = Load(Path.Combine(dir, "MNT.bil"));
        // mask & centroid
        double sx = 0, sy = 0; int cnt = 0; float hmax = -1; int hr = 0, hc = 0;
        for (int r = 0; r < N; r++) for (int c = 0; c < N; c++)
        {
            float s = S[r * N + c], t = T[r * N + c];
            if (s - t > 15) { sx += X(c); sy += Y(r); cnt++; }
            if (s > hmax) { hmax = s; hr = r; hc = c; }
        }
        cx = sx / cnt; cy = sy / cnt;
        sb.AppendLine(string.Format(inv, "mask(MNS-MNT>15m) area={0:F0} m2, centroid L93 {1:F1} {2:F1}", cnt * res * res, cx, cy));
        sb.AppendLine(string.Format(inv, "max MNS {0:F2} m NGF at L93 {1:F1} {2:F1}; MNT there {3:F2}", hmax, X(hc), Y(hr), T[hr * N + hc]));
        // min-area rectangle of mask
        double best = 1e18, bestA = 0, bL = 0, bW = 0;
        for (double a = 0; a < 180; a += 0.25)
        {
            double t = a * Math.PI / 180, c1 = Math.Cos(t), s1 = Math.Sin(t);
            double u0 = 1e9, u1 = -1e9, v0 = 1e9, v1 = -1e9;
            for (int r = 0; r < N; r += 1) for (int c = 0; c < N; c += 1)
            {
                if (S[r * N + c] - T[r * N + c] <= 15) continue;
                double dx = X(c) - cx, dy = Y(r) - cy;
                if (Math.Abs(dx) > 125 || Math.Abs(dy) > 125) continue;
                double u = dx * c1 + dy * s1, v = -dx * s1 + dy * c1;
                if (u < u0) u0 = u; if (u > u1) u1 = u; if (v < v0) v0 = v; if (v > v1) v1 = v;
            }
            double ar = (u1 - u0) * (v1 - v0);
            if (ar < best) { best = ar; bestA = a; bL = u1 - u0; bW = v1 - v0; }
        }
        if (bW > bL) { double tmp = bL; bL = bW; bW = tmp; bestA += 90; }
        double azGrid = ((90 - bestA) % 180 + 180) % 180;
        sb.AppendLine(string.Format(inv, "mask min-area rect: {0:F1} x {1:F1} m, long axis grid-azimuth {2:F2} deg => true azimuth {3:F2} deg", bL, bW, azGrid, azGrid + conv));

        double ang = (90 - (azTrue - conv)) * Math.PI / 180; cu = Math.Cos(ang); su = Math.Sin(ang);
        // terrain around building: ring 5-25 m outside mask
        sb.AppendLine("\n== Long-axis profiles (u toward true az " + azTrue + "), MNS-gref, at v offsets ==");
        sb.Append("   u  |");
        double[] voffs = { -70, -50, -25, 0, 25, 50, 70 };
        foreach (var vo in voffs) sb.Append(string.Format(inv, " v={0,4} ", vo)); sb.AppendLine(" | MNT(v=0)");
        for (double u = -115; u <= 125; u += 5)
        {
            sb.Append(string.Format(inv, "{0,5} |", u));
            foreach (var vo in voffs) { double x, y; UV2XY(u, vo, out x, out y); sb.Append(string.Format(inv, " {0,6:F1} ", Get(S, x, y) - gref)); }
            { double x, y; UV2XY(u, 0, out x, out y); sb.AppendLine(string.Format(inv, " | {0,6:F1}", Get(T, x, y))); }
        }
        sb.AppendLine("\n== Cross-axis profiles (v>0 toward true az " + (azTrue - 90) + "), MNS-gref, at u offsets ==");
        double[] uoffs = { -80, -60, -30, 0, 30, 60, 80, 100 };
        sb.Append("   v  |"); foreach (var uo in uoffs) sb.Append(string.Format(inv, " u={0,4} ", uo)); sb.AppendLine();
        for (double v = -100; v <= 100; v += 5)
        {
            sb.Append(string.Format(inv, "{0,5} |", v));
            foreach (var uo in uoffs) { double x, y; UV2XY(uo, v, out x, out y); sb.Append(string.Format(inv, " {0,6:F1} ", Get(S, x, y) - gref)); }
            sb.AppendLine();
        }
        // perimeter crown: along long sides (scan v outward), along ends (scan u outward)
        sb.AppendLine("\n== Perimeter: edge position & crown top (max MNS-gref in outer 25 m band) ==");
        sb.AppendLine("Side +v (true az " + (azTrue - 90) + " side) and -v side, per u:");
        for (double u = -110; u <= 125; u += 5)
        {
            string line = string.Format(inv, "u={0,5}", u);
            foreach (int sgn in new[] { 1, -1 })
            {
                double edge = double.NaN;
                for (double v = 0; v <= 120; v += 0.5) { double x, y; UV2XY(u, sgn * v, out x, out y); if (Get(S, x, y) - Get(T, x, y) > 15) edge = v; }
                double mx = double.NaN, mv = 0;
                if (!double.IsNaN(edge)) for (double v = edge - 25; v <= edge; v += 0.5) { double x, y; UV2XY(u, sgn * v, out x, out y); double h = Get(S, x, y) - gref; if (double.IsNaN(mx) || h > mx) { mx = h; mv = v; } }
                line += string.Format(inv, " | {0}: edge {1,6:F1} crownTop {2,6:F1} at {3,6:F1}", sgn > 0 ? "+v" : "-v", sgn * edge, mx, sgn * mv);
            }
            sb.AppendLine(line);
        }
        sb.AppendLine("Ends (+u toward az " + azTrue + ", -u opposite), per v:");
        for (double v = -95; v <= 95; v += 5)
        {
            string line = string.Format(inv, "v={0,5}", v);
            foreach (int sgn in new[] { 1, -1 })
            {
                double edge = double.NaN;
                for (double u = 0; u <= 140; u += 0.5) { double x, y; UV2XY(sgn * u, v, out x, out y); if (Get(S, x, y) - Get(T, x, y) > 15) edge = u; }
                double mx = double.NaN, mu = 0;
                if (!double.IsNaN(edge)) for (double u = edge - 25; u <= edge; u += 0.5) { double x, y; UV2XY(sgn * u, v, out x, out y); double h = Get(S, x, y) - gref; if (double.IsNaN(mx) || h > mx) { mx = h; mu = u; } }
                line += string.Format(inv, " | {0}: edge {1,6:F1} crownTop {2,6:F1} at {3,6:F1}", sgn > 0 ? "+u" : "-u", sgn * edge, mx, sgn * mu);
            }
            sb.AppendLine(line);
        }
        // ASCII map
        sb.AppendLine("\n== Height map MNS-gref, 4 m cells; rows: u from +125 (top, toward az) to -115; cols: v from +100 (left) to -100 (right); char = floor(h/2.5) in 0-9A-Z ==");
        string digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ";
        for (double u = 125; u >= -115; u -= 4)
        {
            var l = new StringBuilder(string.Format(inv, "{0,5} ", u));
            for (double v = 100; v >= -100; v -= 2.5)
            {
                double x, y; UV2XY(u, v, out x, out y); double h = Get(S, x, y) - gref;
                if (double.IsNaN(h)) l.Append(' '); else if (h < 3) l.Append('.'); else { int q = (int)Math.Floor(h / 2.5); if (q > 35) q = 35; l.Append(digits[q]); }
            }
            sb.AppendLine(l.ToString());
        }
        return sb.ToString();
    }
    static float[] Load(string p)
    {
        var b = File.ReadAllBytes(p); var a = new float[b.Length / 4];
        for (int i = 0; i < a.Length; i++) a[i] = BitConverter.ToSingle(b, i * 4);
        return a;
    }
}
