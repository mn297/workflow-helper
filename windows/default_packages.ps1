$pkgs = @(
    "Brave.Brave",
    "voidtools.Everything",
    "xanderfrangos.twinkletray",
    "Git.Git",
    "Codeium.Windsurf",
    "Microsoft.VisualStudioCode",
    "Microsoft.VisualStudio.2022.Community",
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
    "GIMP.GIMP.3"
)

foreach ($pkg in $pkgs) {
    Write-Host "Installing $pkg..."
    winget install --id $pkg --accept-package-agreements --accept-source-agreements --silent
}
