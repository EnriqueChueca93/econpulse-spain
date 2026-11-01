// EconPulse.exe: double-click it in the project folder to build the site and open it in the browser.
//
// It runs the project's own Python (.venv), so it always shows the current code and data:
//     .venv\Scripts\python.exe -m econpulse serve [arguments]
// Arguments are passed on, e.g. "EconPulse.exe --update" fetches fresh data first.
// Built by scripts/build_launcher.py with the C# compiler that comes with Windows.

using System;
using System.Diagnostics;
using System.IO;
using System.Linq;

class EconPulse
{
    static int Main(string[] args)
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        string python = Path.Combine(root, ".venv", "Scripts", "python.exe");
        Console.Title = "EconPulse Spain";
        if (!File.Exists(Path.Combine(root, "econpulse", "__main__.py")))
        {
            return Fail("EconPulse.exe must be in the project folder (the one that holds the econpulse folder).");
        }
        if (!File.Exists(python))
        {
            return Fail("The project's Python environment is missing. Create it first, from the project folder:\n" +
                        "    py -3 -m venv .venv\n    .venv\\Scripts\\python.exe -m pip install -r requirements.txt");
        }

        string passed = string.Join(" ", args.Select(a => a.Contains(" ") ? "\"" + a + "\"" : a));
        var start = new ProcessStartInfo(python, ("-m econpulse serve " + passed).Trim())
        {
            WorkingDirectory = root,
            UseShellExecute = false,
        };
        start.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
        Console.WriteLine(args.Contains("--update")
            ? "Fetching the latest data and building the site (this takes a few minutes)..."
            : "Building the site from the saved data...");
        using (Process child = Process.Start(start))
        {
            child.WaitForExit();
            if (child.ExitCode != 0)
            {
                return Fail("EconPulse stopped with an error (see above).", child.ExitCode);
            }
            return 0;
        }
    }

    static int Fail(string message, int code = 1)
    {
        Console.Error.WriteLine("\n" + message);
        Console.Error.WriteLine("\nPress Enter to close this window.");
        Console.ReadLine();
        return code;
    }
}
