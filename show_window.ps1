Add-Type @"
using System;
using System.Runtime.InteropServices;
public class Win32 {
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr hWnd);
}
"@

$procs = @(Get-Process pythonw -ErrorAction SilentlyContinue)
foreach ($proc in $procs) {
    $handle = $proc.MainWindowHandle
    if ($handle -ne 0) {
        Write-Host "Showing window: $handle ($($proc.MainWindowTitle))"
        [Win32]::ShowWindow($handle, 9) | Out-Null  # SW_RESTORE
        [Win32]::BringWindowToTop($handle) | Out-Null
        [Win32]::SetForegroundWindow($handle) | Out-Null
    }
}
Write-Host "Done"
