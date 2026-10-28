using System;
using System.Drawing;
using System.Text;

public static class ImgProfile
{
    // For each column, find first y from top where the pixel deviates from the sky colour of the same row at x=5
    public static string Top(string path, int step, int thresh)
    {
        var bmp = new Bitmap(path); var sb = new StringBuilder();
        sb.AppendLine("size " + bmp.Width + "x" + bmp.Height);
        for (int x = 0; x < bmp.Width; x += step)
        {
            int found = -1;
            for (int y = 5; y < bmp.Height - 1; y++)
            {
                Color s = bmp.GetPixel(2, y); Color p = bmp.GetPixel(x, y);
                int d = Math.Abs(s.R - p.R) + Math.Abs(s.G - p.G) + Math.Abs(s.B - p.B);
                if (d > thresh) { found = y; break; }
            }
            sb.AppendLine(x + "\t" + found);
        }
        bmp.Dispose();
        return sb.ToString();
    }
    public static string Column(string path, int x)
    {
        var bmp = new Bitmap(path); var sb = new StringBuilder();
        for (int y = 0; y < bmp.Height; y += 2) { var p = bmp.GetPixel(x, y); sb.AppendLine(y + "\t" + p.R + "," + p.G + "," + p.B); }
        bmp.Dispose(); return sb.ToString();
    }
}
