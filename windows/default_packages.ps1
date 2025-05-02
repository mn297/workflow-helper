$pkgs = @(
    "Brave.Brave",
    "voidtools.Everything",
    "xanderfrangos.twinkletray",
    "PDFsam.PDFsam",
    "JavadMotallebi.NeatDownloadManager",
    "VB-Audio.Voicemeeter.Banana",
    "Opera.Opera",
    "RARLab.WinRAR",
    "Gyan.FFmpeg",
    "Microsoft.Sysinternals",
    "Microsoft.PowerToys",
    "PrivateInternetAccess.PrivateInternetAccess",
    "qBittorrent.qBittorrent",
    "Oracle.VirtualBox",
    "Nvidia.CUDA",
    "MPC-BE.MPC-BE",
    # "Spotify.Spotify",
    "BlenderFoundation.Blender",
    "Unity.UnityHub",
    "Valve.Steam",
    "9NKSQGP7F2NH",
    "CPUID.HWMonitor",
    "CPUID.CPU-Z",
    "REALiX.HWiNFO",
    "Resplendence.LatencyMon",
    "TradingView.TradingViewDesktop",
    "geeksoftwareGmbH.PDF24Creator",
    "Creality.CrealityPrint",
    "SoftFever.OrcaSlicer",
    "GIMP.GIMP.3",
    # .NET Runtimes
    "Microsoft.DotNet.DesktopRuntime.5",
    "Microsoft.DotNet.DesktopRuntime.6",
    "Microsoft.DotNet.DesktopRuntime.7",
    "Microsoft.DotNet.DesktopRuntime.8",
    "Microsoft.DotNet.DesktopRuntime.9",
    "Microsoft.WindowsAppRuntime.1.7"
)

foreach ($pkg in $pkgs) {
    Write-Host "Installing $pkg..."
    winget install --id $pkg --accept-package-agreements --accept-source-agreements --silent
}
