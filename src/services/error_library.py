import json
import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class ErrorEntry:
    id: str
    name: str
    category: str
    severity: str
    description: str
    causes: list = field(default_factory=list)
    fixes: list = field(default_factory=list)
    search_terms: list = field(default_factory=list)
    related_dlls: list = field(default_factory=list)
    related_codes: list = field(default_factory=list)
    applies_to: str = "both"
    references: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "ErrorEntry":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


USER_ERRORS_FILE = Path(__file__).parent.parent.parent / "data" / "user_errors.json"
BUILTIN_ERRORS_FILE = Path(__file__).parent.parent.parent / "data" / "builtin_errors.json"


def _ensure_data_dir():
    USER_ERRORS_FILE.parent.mkdir(parents=True, exist_ok=True)


def _load_json_errors(path: Path) -> list[ErrorEntry]:
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return [ErrorEntry.from_dict(e) for e in data]
    except Exception:
        return []


def _save_json_errors(path: Path, errors: list[ErrorEntry]):
    _ensure_data_dir()
    with open(path, "w", encoding="utf-8") as f:
        json.dump([e.to_dict() for e in errors], f, indent=2, ensure_ascii=False)


BUILTIN_ERRORS = [
    # ============================================================
    # GPU / DRIVER CRASHES
    # ============================================================
    ErrorEntry(
        id="GPU_001", name="NVIDIA Driver Crash (nvlddmkm.sys / TDR)",
        category="GPU/Driver", severity="critical",
        description="NVIDIA display driver stopped responding and was reset (TDR event). Screen goes black, system becomes unresponsive, or MSFS crashes to desktop.",
        causes=["GPU overloaded by MSFS settings", "Corrupted or incompatible NVIDIA driver", "GPU overheating (thermal throttling)", "Unstable GPU overclock or undervolt", "Faulty GPU hardware (especially VRAM)", "Windows TDR timeout too short (default 2 seconds)", "Bad RAM causing GPU communication errors"],
        fixes=["Download latest NVIDIA Game Ready Driver from nvidia.com", "Use DDU (Display Driver Uninstaller) in Safe Mode to clean-install drivers", "Remove GPU overclocks and test at stock speeds", "Monitor GPU temps with HWiNFO - should stay below 85C", "Increase TDR timeout: Registry -> HKLM\\System\\CurrentControlSet\\Control\\GraphicsDrivers\\TdrDelay -> set to 8 (DWORD)", "Set TdrLevel to 0 to disable TDR (advanced)", "Lower MSFS texture resolution and render scale", "Disable Hardware-Accelerated GPU Scheduling (HAGS)", "Test with a different monitor", "Run Windows Memory Diagnostic to check for bad RAM"],
        search_terms=["nvlddmkm", "nvlddmkm.sys", "TDR", "video_tdr_failure", "display driver stopped", "Event ID 4101"],
        related_dlls=["nvlddmkm.sys", "nvwgf2umx.dll", "nvwgf2um.dll"], related_codes=["0x00000116", "0x000000ea"],
    ),
    ErrorEntry(
        id="GPU_002", name="AMD Driver Crash (atikmpag.sys / atidxx64.dll)",
        category="GPU/Driver", severity="critical",
        description="AMD display driver crashed during MSFS operation.",
        causes=["AMD driver bug or corruption", "GPU overheating", "Unstable overclock", "Incompatible driver version with MSFS"],
        fixes=["Update AMD Adrenalin drivers to latest version", "Use DDU in Safe Mode for clean driver install", "Remove GPU overclocks", "Check GPU temperature and cooling", "Try rolling back to previous stable driver version", "Disable AMD Frame Generation if using NVIDIA GPU"],
        search_terms=["atikmpag", "atidxx64", "amd driver crash", "amd display driver"],
        related_dlls=["atikmpag.sys", "atidxx64.dll", "atidxx32.dll"],
    ),
    ErrorEntry(
        id="GPU_003", name="DXGI_ERROR_DEVICE_HUNG (0x887a0006)",
        category="GPU/Driver", severity="critical",
        description="DirectX Graphics Infrastructure detected the GPU hung. MSFS loses communication with the graphics device.",
        causes=["GPU driver crash or timeout", "MSFS settings too high for GPU capabilities", "MSI Afterburner / RTSS conflict", "NVIDIA App RTX Dynamic Vibrance causing conflicts", "GPU overheating under sustained load", "Resizable BAR causing VRAM over-allocation", "HDR display issues with certain drivers"],
        fixes=["Disable MSI Afterburner and RivaTuner Statistics Server completely", "Disable NVIDIA RTX Dynamic Vibrance in NVIDIA App", "Lower MSFS graphics settings", "Clean-install GPU drivers using DDU in Safe Mode", "Disable Resizable BAR in BIOS", "Disable HAGS", "Increase TdrDelay registry value to 8", "Switch between DX11 and DX12", "Disable HDR in Windows display settings"],
        search_terms=["dxgi_error_device_hung", "0x887a0006", "DXGI_ERROR_DEVICE_Reset", "0x887a0007"],
        related_dlls=["dxgi.dll", "d3d12.dll"], related_codes=["0x887a0006", "0x887a0007"],
    ),
    ErrorEntry(
        id="GPU_004", name="DXGI_ERROR_DEVICE_REMOVED (0x887a0005)",
        category="GPU/Driver", severity="critical",
        description="The GPU device has been physically removed or the driver crashed so badly Windows lost the device.",
        causes=["GPU physically disconnected (laptop thermal shutdown)", "Severe driver crash", "Power supply insufficient for GPU", "Faulty GPU hardware"],
        fixes=["Check GPU power connections", "Ensure PSU has adequate wattage", "Lower graphics settings significantly", "Clean-install GPU drivers", "Test GPU with stress test (FurMark)", "For laptops: ensure cooling pad, clean vents"],
        search_terms=["dxgi_error_device_removed", "0x887a0005", "device removed"],
        related_dlls=["dxgi.dll"], related_codes=["0x887a0005"],
    ),
    ErrorEntry(
        id="GPU_005", name="DXGI_ERROR_UNSUPPORTED (0x887a0004)",
        category="GPU/Driver", severity="high",
        description="DirectX 12 device cannot be created. GPU does not support required Shader Model.",
        causes=["GPU too old - does not support Shader Model 6.7 (MSFS 2024 requirement)", "GPU drivers not installed", "DirectX not properly installed", "Integrated graphics being used instead of dedicated GPU"],
        fixes=["Check GPU compatibility: MSFS 2024 requires SM 6.7 (NVIDIA GTX 1080+ / AMD RX 5000+)", "Update GPU drivers", "Ensure dedicated GPU is selected", "Run dxdiag to check DirectX version", "For older GPUs: use MSFS 2020 instead"],
        search_terms=["dxgi_error_unsupported", "0x887a0004", "shader model 6.7", "D3D12Renderer_Z"],
        related_dlls=["dxgi.dll", "D3D12Core.dll"], related_codes=["0x887a0004"],
    ),
    ErrorEntry(
        id="GPU_006", name="NVIDIA nvwgf2umx.dll Crash",
        category="GPU/Driver", severity="high",
        description="Crash in the NVIDIA user-mode driver DLL nvwgf2umx.dll.",
        causes=["Corrupted NVIDIA driver", "GPU shader compilation failure", "VRAM corruption", "GPU overheating"],
        fixes=["Clean-install NVIDIA drivers with DDU", "Lower shader quality settings", "Check GPU temperature", "Disable GPU overclock", "Update to latest Game Ready driver"],
        search_terms=["nvwgf2umx", "nvwgf2umx.dll", "nvwgf2um.dll"],
        related_dlls=["nvwgf2umx.dll", "nvwgf2um.dll"],
    ),
    ErrorEntry(
        id="GPU_007", name="Intel GPU Incompatibility",
        category="GPU/Driver", severity="high",
        description="Intel integrated or Arc GPU cannot run MSFS 2024 properly.",
        causes=["Intel UHD/Iris not supported for MSFS 2024", "Intel Arc driver immaturity", "Missing Shader Model 6.7 support on older Intel GPUs"],
        fixes=["MSFS 2024 requires dedicated NVIDIA or AMD GPU", "Intel Arc A750/A770 may work with latest drivers", "Use MSFS 2020 for older Intel GPUs", "Ensure BIOS is set to use dedicated GPU if available"],
        search_terms=["intel gpu", "intel iris", "intel uhd", "intel arc"],
    ),

    # ============================================================
    # DIRECTX / RENDERING CRASHES
    # ============================================================
    ErrorEntry(
        id="DX_001", name="D3D11.dll Renderer_Z Crash",
        category="DirectX", severity="high",
        description="MSFS crashes in the DirectX 11 renderer. The d3d11.dll module failed during graphics rendering.",
        causes=["Corrupted DirectX 11 installation", "GPU driver incompatibility with DX11", "Monitor compatibility issue", "Overheating GPU", "Vulkan/DX12 fallback issues"],
        fixes=["Run sfc /scannow as administrator", "Run DISM /Online /Cleanup-Image /RestoreHealth", "Reinstall GPU drivers using DDU", "Try a different monitor (confirmed fix)", "Set page file to system-managed size", "Switch from DX12 to DX11 in MSFS settings"],
        search_terms=["d3d11.dll", "renderer_z", "d3d11 renderer", "d3d11 renderer_z fatal error"],
        related_dlls=["d3d11.dll", "d3d11_1sdklayers.dll"],
    ),
    ErrorEntry(
        id="DX_002", name="D3D12Core.dll Crash",
        category="DirectX", severity="high",
        description="MSFS crashes in the DirectX 12 core module.",
        causes=["Corrupted DX12 installation", "GPU driver incompatible with DX12", "GSX or add-on triggering DX12 crash", "Overlay apps hooking into DX12", "HAGS causing DX12 instability"],
        fixes=["Clean-install GPU drivers using DDU", "Disable Discord/Steam/MSI overlays", "Disable HAGS in Windows Graphics Settings", "Clear NCX OTA cache", "Switch to DX11 in MSFS settings", "Run sfc /scannow and DISM"],
        search_terms=["D3D12Core.dll", "d3d12", "dx12 crash"],
        related_dlls=["D3D12Core.dll", "d3d12.dll"], related_codes=["0xc0000005"],
    ),
    ErrorEntry(
        id="DX_003", name="dxgi.dll Crash",
        category="DirectX", severity="high",
        description="Crash in the DirectX Graphics Infrastructure module.",
        causes=["GPU driver issue", "Display mode change during rendering", "HDR conflict", "Multi-monitor issues"],
        fixes=["Update GPU drivers", "Disable HDR", "Try single-monitor mode", "Set display to native resolution before launch", "Disable VSync in MSFS"],
        search_terms=["dxgi.dll", "dxgi error"],
        related_dlls=["dxgi.dll"],
    ),
    ErrorEntry(
        id="DX_004", name="DXGI_ERROR_WAIT_TIMEOUT",
        category="DirectX", severity="medium",
        description="DXGI timed out waiting for the GPU to complete an operation.",
        causes=["GPU overloaded", "Driver timeout too short", "Background processes competing for GPU"],
        fixes=["Close background GPU-using apps", "Increase TdrDelay registry value", "Lower MSFS GPU settings", "Update GPU drivers"],
        search_terms=["dxgi wait timeout", "0x887a0020", "dxgi_timeout"],
        related_dlls=["dxgi.dll"], related_codes=["0x887a0020"],
    ),
    ErrorEntry(
        id="DX_005", name="D3D Device Lost",
        category="DirectX", severity="high",
        description="The Direct3D device was lost during rendering, typically from a driver crash.",
        causes=["GPU driver crash mid-frame", "VRAM exhaustion during scene load", "GPU thermal throttling causing timeout"],
        fixes=["Lower render scale and texture resolution", "Clean-install GPU drivers", "Monitor GPU temperature", "Disable ray tracing", "Set frame rate limit to reduce GPU load"],
        search_terms=["d3d device lost", "device lost", "d3d11_device_removed"],
    ),
    ErrorEntry(
        id="DX_006", name="Shader Compilation Error",
        category="DirectX", severity="medium",
        description="MSFS failed to compile a graphics shader. Can cause visual glitches or crash.",
        causes=["Corrupted shader cache", "GPU driver bug in shader compiler", "Hardware fault in GPU shader units"],
        fixes=["Clear DirectX shader cache (Disk Cleanup > DirectX Shader Cache)", "Update GPU drivers", "Delete MSFS cache folders", "Disable shader cache in NVIDIA Control Panel temporarily"],
        search_terms=["shader compilation", "shader compile error", "shader cache"],
    ),
    ErrorEntry(
        id="DX_007", name="Render Pipeline Crash",
        category="DirectX", severity="high",
        description="The MSFS render pipeline encountered a fatal error during frame submission.",
        causes=["Too many draw calls from complex scenery", "VRAM overflow during render", "Incompatible add-on injecting render calls"],
        fixes=["Reduce Object LOD and Terrain LOD", "Lower texture resolution", "Remove recently installed scenery add-ons", "Disable volumetric clouds temporarily"],
        search_terms=["render pipeline", "render crash", "frame submit"],
    ),

    # ============================================================
    # MEMORY / VRAM ERRORS
    # ============================================================
    ErrorEntry(
        id="MEM_001", name="Out of Memory (VRAM Exceeded)",
        category="Memory", severity="high",
        description="MSFS ran out of GPU VRAM. The simulator crashes when VRAM is exhausted.",
        causes=["Texture Resolution too high", "Terrain LOD and Object LOD too high", "Raytraced shadows enabled (eats 1-2GB VRAM)", "Resizable BAR over-allocating VRAM", "Too many add-ons loaded", "Rolling cache corrupted or too large"],
        fixes=["Reduce Texture Resolution by one tier", "Lower TLOD/OLOD to 100-150", "Disable Raytraced Shadows", "Disable Resizable BAR in BIOS", "Reduce Volumetric Clouds quality", "Enable Dynamic Settings", "Clear rolling cache", "Limit FPS to 30", "Close background GPU apps"],
        search_terms=["out of memory", "vram exceeded", "gpu memory", "resource usage exceeds gpu memory"],
    ),
    ErrorEntry(
        id="MEM_002", name="System RAM Exhaustion",
        category="Memory", severity="high",
        description="MSFS has run out of system RAM.",
        causes=["Less than 16GB RAM installed", "Too many background applications", "Page file disabled or too small", "Memory leak in add-on WASM module"],
        fixes=["Close unnecessary background apps", "Enable system-managed page file", "Test with empty Community folder", "Reduce Object LOD and Terrain LOD", "Restart Windows before long sessions", "Run Windows Memory Diagnostic"],
        search_terms=["memory resources getting low", "out of memory", "ram exhaustion"],
    ),
    ErrorEntry(
        id="MEM_003", name="Page File / Virtual Memory Issues",
        category="Memory", severity="medium",
        description="MSFS crashes when Windows virtual memory is misconfigured or disabled.",
        causes=["Page file completely disabled", "Page file on full drive", "Custom page file too small", "Page file on slow HDD"],
        fixes=["Set page file to System Managed Size", "Ensure page file drive has 50GB+ free", "Move page file to fastest SSD", "Never completely disable page file"],
        search_terms=["page file", "virtual memory", "paging file"],
    ),
    ErrorEntry(
        id="MEM_004", name="Memory Leak in Add-on",
        category="Memory", severity="medium",
        description="A Community folder add-on is leaking memory over time, causing eventual OOM crash.",
        causes=["WASM module not releasing memory", "Python add-on (e.g. SimConnect script) leaking", "Scenery add-on loading too many assets"],
        fixes=["Identify which add-on causes the leak by removing in halves", "Update all add-ons to latest versions", "Restart MSFS between long flights", "Report leak to add-on developer"],
        search_terms=["memory leak", "leaking memory", "gradual oom"],
    ),
    ErrorEntry(
        id="MEM_005", name="GPU Memory Fragmentation",
        category="Memory", severity="medium",
        description="GPU VRAM becomes fragmented over time, causing allocation failures even with free memory.",
        causes=["Long flight duration", "Frequent scenery changes (cross-country flight)", "High texture resolution with many add-ons"],
        fixes=["Restart MSFS periodically", "Lower texture resolution", "Reduce Object LOD", "Disable rolling cache if enabled", "Close other GPU-using apps"],
        search_terms=["vram fragmentation", "memory fragmentation", "gpu allocation failed"],
    ),

    # ============================================================
    # RUNTIME DLL ERRORS
    # ============================================================
    ErrorEntry(
        id="DLL_001", name="ucrtbase.dll Crash (0xc0000409)",
        category="Runtime DLL", severity="high",
        description="MSFS crashes in the Universal C Runtime. Two dominant causes: missing English language pack and non-English system locale.",
        causes=["Missing English (US) language pack", "Non-English system locale for non-Unicode programs", "Corrupted ucrtbase.dll", "Missing Visual C++ Redistributable", "Third-party app conflict (Nahimic, Corsair iCue, MSI Afterburner)"],
        fixes=["Install English (US) language pack in Windows Settings", "Set system locale to English (US): Control Panel > Region > Administrative", "Reinstall both x86 and x64 VC++ Redistributables", "Run sfc /scannow and DISM restorehealth", "Perform clean boot: msconfig -> hide Microsoft services -> disable rest", "Uninstall Nahimic audio driver, Corsair iCue, MSI Afterburner"],
        search_terms=["ucrtbase.dll", "0xc0000409", "universal c runtime"],
        related_dlls=["ucrtbase.dll"], related_codes=["0xc0000409"],
    ),
    ErrorEntry(
        id="DLL_002", name="VCRUNTIME140.dll Crash",
        category="Runtime DLL", severity="high",
        description="MSFS crashes due to missing or corrupted Visual C++ runtime library.",
        causes=["Missing VC++ Redistributable 2015-2022", "Corrupted VCRUNTIME140.dll", "Wrong version of VC++ runtime", "System file corruption"],
        fixes=["Download and install latest VC++ Redistributable from Microsoft (both x86 and x64)", "Direct download: aka.ms/vs/16/release/vc_redist.x86.exe and vc_redist.x64.exe", "Run sfc /scannow", "Reinstall MSFS if issue persists"],
        search_terms=["vcruntime140.dll", "vcruntime140_1.dll", "vc runtime"],
        related_dlls=["vcruntime140.dll", "vcruntime140_1.dll"], related_codes=["0xc0000005"],
    ),
    ErrorEntry(
        id="DLL_003", name="MSVCP140.dll Crash",
        category="Runtime DLL", severity="high",
        description="MSFS crashes due to missing Microsoft Visual C++ runtime library.",
        causes=["Missing Visual C++ Redistributable", "Corrupted MSVCP140.dll", "32/64 bit mismatch"],
        fixes=["Install both x86 and x64 VC++ Redistributables from Microsoft", "Run sfc /scannow", "Reinstall MSFS"],
        search_terms=["msvcp140.dll", "msvcp140"],
        related_dlls=["msvcp140.dll"],
    ),
    ErrorEntry(
        id="DLL_004", name="CoherentGTCore.dll Crash",
        category="Runtime DLL", severity="high",
        description="Crash in the Coherent GT web rendering engine used by MSFS for in-sim panels and UI.",
        causes=["Corrupted CoherentGTCore.dll", "Bad MSFS update installation", "Add-on interfering with web rendering", "Missing dependencies"],
        fixes=["Verify MSFS game files (Steam) or Repair app (Microsoft Store)", "Reinstall MSFS completely", "Remove Community folder content and test", "Run sfc /scannow"],
        search_terms=["coherentgtcore.dll", "coherent gt", "0xc000012f"],
        related_dlls=["CoherentGTCore.dll", "CoherentUIGT.dll"], related_codes=["0xc000012f"],
    ),
    ErrorEntry(
        id="DLL_005", name="clr.dll / .NET Runtime Crash",
        category="Runtime DLL", severity="medium",
        description="Crash in the .NET Common Language Runtime, often caused by GSX, FSUIPC.",
        causes=["GSX Pro (Couatl64_MSFS.exe) .NET runtime error", "Corrupted .NET Framework", "FSUIPC or other .NET add-on conflict"],
        fixes=["Run .NET Framework Repair Tool from Microsoft", "Update GSX Pro to latest version", "Reinstall .NET Framework 4.8", "Temporarily remove GSX/FSUIPC and test"],
        search_terms=["clr.dll", "couatl64", "gsx crash", ".net runtime error", "80131506"],
        related_dlls=["clr.dll", "Couatl64_MSFS.exe"], related_codes=["80131506"],
    ),
    ErrorEntry(
        id="DLL_006", name="msedge_webview2.dll Crash",
        category="Runtime DLL", severity="medium",
        description="Crash in Microsoft Edge WebView2 runtime used for some MSFS UI elements.",
        causes=["Corrupted WebView2 installation", "Edge browser conflict", "WebView2 version incompatibility"],
        fixes=["Update or repair Microsoft Edge WebView2 Runtime", "Reset WebView2: Settings > Apps > Microsoft Edge WebView2 > Reset", "Disable browser extensions", "Clear Edge cache"],
        search_terms=["msedge", "msedge_webview2", "webview2 crash", "edge webview"],
        related_dlls=["msedge_webview2.dll", "WebView2Loader.dll"],
    ),
    ErrorEntry(
        id="DLL_007", name="ntdll.dll Crash",
        category="Runtime DLL", severity="high",
        description="Crash in the NT Layer DLL - Windows kernel interface. Can indicate deep system issues.",
        causes=["Windows system file corruption", "Third-party software hooking system calls", "Memory corruption from faulty hardware", "Antivirus kernel filter driver issue"],
        fixes=["Run sfc /scannow and DISM", "Clean boot to identify conflicting software", "Update Windows to latest version", "Check RAM with Windows Memory Diagnostic", "Temporarily disable antivirus"],
        search_terms=["ntdll.dll", "ntdll!Rtl", "0xc0000005"],
        related_dlls=["ntdll.dll"],
    ),
    ErrorEntry(
        id="DLL_008", name="kernelbase.dll Crash",
        category="Runtime DLL", severity="high",
        description="Crash in the Windows Kernel Base library. Indicates a system-level failure.",
        causes=["Corrupted Windows system files", "Incompatible Windows update", "Third-party software conflict", "Hardware failure"],
        fixes=["Run sfc /scannow and DISM", "Uninstall recent Windows updates", "Perform clean boot", "Check Windows Event Viewer for preceding errors"],
        search_terms=["kernelbase.dll", "kernelbase!RaiseException"],
        related_dlls=["kernelbase.dll"],
    ),
    ErrorEntry(
        id="DLL_009", name="appcrash.dll / apphelp.dll",
        category="Runtime DLL", severity="medium",
        description="Application Compatibility shim crash.",
        causes=["Windows AppCompat layer interfering with MSFS", "Corrupted compatibility database", "Antivirus app compatibility filter"],
        fixes=["Disable application compatibility shim: gpedit.msc > Computer Config > Admin Templates > Windows Components > Application Compatibility > Turn off Application Compatibility Engine", "Run MSFS as administrator", "Add MSFS to antivirus exclusions"],
        search_terms=["appcrash.dll", "apphelp.dll", "appcompat"],
        related_dlls=["appcrash.dll", "apphelp.dll"],
    ),
    ErrorEntry(
        id="DLL_010", name="MSFSInternal-x64.dll Crash",
        category="Runtime DLL", severity="high",
        description="Crash in MSFS internal module. Indicates a bug in the simulator itself.",
        causes=["MSFS bug", "Corrupted installation", "Add-on triggering internal crash path"],
        fixes=["Verify MSFS files or Repair app", "Update MSFS to latest version", "Remove Community folder and test", "Reinstall MSFS as last resort"],
        search_terms=["MSFSInternal", "MSFSInternal-x64.dll"],
        related_dlls=["MSFSInternal-x64.dll"],
    ),

    # ============================================================
    # APPLICATION / EXCEPTION ERRORS
    # ============================================================
    ErrorEntry(
        id="APP_001", name="Access Violation (0xc0000005)",
        category="Application", severity="high",
        description="MSFS tried to read or write memory it doesn't have access to.",
        causes=["Third-party add-on conflict (most common)", "Corsair iCue, ASUS Armoury Crate, MSI Afterburner", "Corrupted MSFS files", "Missing English language pack", "GPU driver crash", "Memory corruption from bad RAM"],
        fixes=["Remove all Community folder add-ons and test", "If stable, add back in halves to find culprit", "Uninstall Corsair iCue, ASUS Armoury Crate, MSI Afterburner", "Install English (US) language pack", "Run sfc /scannow and DISM", "Clean-install GPU drivers with DDU", "Run Windows Memory Diagnostic"],
        search_terms=["0xc0000005", "access violation", "exception code"],
        related_codes=["0xc0000005"],
    ),
    ErrorEntry(
        id="APP_002", name="Breakpoint Reached (0x80000003)",
        category="Application", severity="high",
        description="MSFS hit an internal breakpoint, usually indicating a bug or CPU instability.",
        causes=["Intel 14th gen CPU instability (known issue)", "Corrupted MSFS installation", "Add-on triggering debug breakpoint", "Overclocked CPU instability"],
        fixes=["For Intel 14th gen: update BIOS to latest microcode", "Reduce CPU clock speed / remove overclock", "Verify MSFS game files", "Remove add-ons and test", "Reinstall MSFS"],
        search_terms=["0x80000003", "breakpoint", "breakpoint has been reached"],
        related_codes=["0x80000003"],
    ),
    ErrorEntry(
        id="APP_003", name="Bad Image (0xc000012f)",
        category="Application", severity="high",
        description="A DLL file is corrupted or not designed to run on Windows.",
        causes=["Corrupted MSFS update", "Corrupted system DLL files", "Virus/malware damage", "Incomplete file write during update"],
        fixes=["Run sfc /scannow as administrator", "Run DISM /Online /Cleanup-Image /RestoreHealth", "Verify MSFS game files or Repair app", "Reinstall MSFS", "Scan for malware"],
        search_terms=["bad image", "0xc000012f", "not designed to run"],
        related_codes=["0xc000012f"],
    ),
    ErrorEntry(
        id="APP_004", name="Stack Buffer Overrun (0xc0000409)",
        category="Application", severity="critical",
        description="MSFS triggered a stack buffer overrun security exception.",
        causes=["ucrtbase.dll language/locale issue", "Add-on causing memory corruption", "Security software interfering"],
        fixes=["Install English (US) language pack", "Set system locale to English (US)", "Remove add-ons and test", "Disable antivirus temporarily"],
        search_terms=["0xc0000409", "stack buffer overrun"],
        related_codes=["0xc0000409"],
    ),
    ErrorEntry(
        id="APP_005", name="Unhandled Exception (0xe0434352)",
        category="Application", severity="high",
        description="An unhandled .NET exception occurred in MSFS or a .NET-based add-on.",
        causes=[".NET Framework corruption", "GSX or FSUIPC .NET error", "Windows .NET update broke compatibility"],
        fixes=["Run .NET Framework Repair Tool", "Update or reinstall GSX/FSUIPC", "Reinstall .NET Framework 4.8"],
        search_terms=["0xe0434352", "unhandled exception", ".net exception"],
        related_codes=["0xe0434352"],
    ),
    ErrorEntry(
        id="APP_006", name="STATUS_STACK_BUFFER_OVERRUN (0xc0000409)",
        category="Application", severity="critical",
        description="Windows detected a stack buffer overrun and terminated MSFS for security.",
        causes=["Memory corruption from faulty hardware", "Add-on corrupting memory", "Antivirus driver conflict"],
        fixes=["Run Windows Memory Diagnostic", "Remove all add-ons", "Update antivirus or disable temporarily", "Check CPU/GPU stability"],
        search_terms=["status_stack_buffer_overrun", "0xc0000409"],
        related_codes=["0xc0000409"],
    ),
    ErrorEntry(
        id="APP_007", name="Application Hang (0x80000003)",
        category="Application", severity="high",
        description="MSFS became unresponsive and was terminated by Windows.",
        causes=["Deadlock in sim code or add-on", "Resource starvation (CPU/RAM/GPU)", "Infinite loop in add-on WASM module"],
        fixes=["Limit FPS to reduce CPU load", "Remove add-ons to test", "Update Windows and GPU drivers", "Check Task Manager for resource-hungry processes"],
        search_terms=["application hang", "not responding", "hung"],
    ),
    ErrorEntry(
        id="APP_008", name="Fatal Error Exit Code 1",
        category="Application", severity="high",
        description="MSFS terminated with a generic fatal error.",
        causes=["Corrupted installation files", "Missing configuration files", "Add-on conflict at startup"],
        fixes=["Verify MSFS files", "Delete UserCfg.opt and let MSFS regenerate", "Remove Community folder temporarily", "Reinstall MSFS"],
        search_terms=["exit code 1", "fatal error", "crash exit"],
    ),
    ErrorEntry(
        id="APP_009", name="EVENT_ID_1000 Application Error",
        category="Application", severity="medium",
        description="Windows Event Log recorded a generic application error (Event ID 1000).",
        causes=["Various application-level failures", "Faulting module indicates specific cause", "Exception code provides details"],
        fixes=["Check faulting module name in event details", "Search for specific faulting module in error library", "Update relevant drivers or reinstall affected component"],
        search_terms=["event id 1000", "event 1000", "application error"],
    ),
    ErrorEntry(
        id="APP_010", name="EVENT_ID_1002 Application Hang",
        category="Application", severity="medium",
        description="Windows recorded that MSFS stopped interacting with Windows (Event ID 1002).",
        causes=["MSFS frozen in an infinite loop", "GPU driver not responding", "System resource exhaustion"],
        fixes=["Check GPU driver version and update", "Monitor system resources during MSFS", "Lower graphics settings to reduce GPU load"],
        search_terms=["event id 1002", "event 1002", "application hang"],
    ),

    # ============================================================
    # WASM MODULE CRASHES
    # ============================================================
    ErrorEntry(
        id="WASM_001", name="WASM Module Crashed (Orange Screen)",
        category="WASM", severity="high",
        description="A WebAssembly module used by an add-on crashed. Instruments freeze, screens turn orange/red.",
        causes=["WASM module built for older MSFS version", "WASM cache corrupted after sim update", "Multiple WASM modules conflicting", "Incomplete add-on installation", "Nav database update triggering WASM bug (PMDG, iniBuilds)"],
        fixes=["Clear WASM cache folder completely:", "  MS Store: %LOCALAPPDATA%\\Packages\\Microsoft.Limitless_8wekyb3d8bbwe\\LocalState\\WASM", "  Steam: %APPDATA%\\Microsoft Flight Simulator 2024\\WASM", "Delete contents of WASM folder (sim rebuilds on next launch)", "Start MSFS in Safe Mode", "Remove Community folder, test, add back in halves", "Update affected add-ons to latest versions", "For PMDG: reinstall aircraft, re-update nav database"],
        search_terms=["wasm", "wasm module crashed", "wasm crash", "orange screen", "orange screen of death"],
    ),
    ErrorEntry(
        id="WASM_002", name="WASM Memory Leak / OOM",
        category="WASM", severity="medium",
        description="A WASM module is consuming increasing amounts of memory over time.",
        causes=["Bug in WASM module code", "Multiple WASM modules running simultaneously", "Long flight duration triggering leak"],
        fixes=["Limit flight duration if leak is confirmed", "Remove recently installed add-ons", "Report bug to add-on developer", "Restart MSFS between long flights"],
        search_terms=["wasm memory", "wasm oom", "wasm leak"],
    ),
    ErrorEntry(
        id="WASM_003", name="WASM Module Incompatible",
        category="WASM", severity="medium",
        description="An add-on WASM module is not compatible with the current MSFS version.",
        causes=["Add-on not updated for latest MSFS update", "Old WASM build tools used by developer", "SDK version mismatch"],
        fixes=["Check add-on developer website for MSFS 2024 compatible version", "Contact developer to request update", "Remove incompatible WASM add-on", "Check MSFS SDK version compatibility"],
        search_terms=["wasm incompatible", "wasm version", "wasm sdk mismatch"],
    ),
    ErrorEntry(
        id="WASM_004", name="WASM Gauge Error",
        category="WASM", severity="medium",
        description="A WASM gauge (instrument) in an add-on aircraft crashed.",
        causes=["Corrupted gauge configuration", "Missing texture or model file referenced by gauge", "Gauge code bug in specific flight phase"],
        fixes=["Reinstall the add-on aircraft", "Check for add-on updates", "Remove and re-download the add-on", "Report to developer with flight details"],
        search_terms=["wasm gauge", "gauge error", "gauge crash"],
    ),

    # ============================================================
    # SIMCONNECT ERRORS
    # ============================================================
    ErrorEntry(
        id="SIM_001", name="SimConnect Crash",
        category="SimConnect", severity="medium",
        description="The SimConnect interface used by add-ons to communicate with MSFS has crashed.",
        causes=["Third-party add-on using outdated SimConnect", "Beta SimConnect build causing conflicts", "Multiple add-ons fighting for SimConnect access"],
        fixes=["Update all add-ons to latest versions", "Reinstall SimConnect from MSFS SDK", "Remove Community folder add-ons and test in halves", "Install both x86 and x64 SimConnect redistributables"],
        search_terms=["simconnect", "simconnect crash", "simconnect error"],
    ),
    ErrorEntry(
        id="SIM_002", name="SimConnect Connection Lost",
        category="SimConnect", severity="medium",
        description="An add-on lost its SimConnect connection to MSFS.",
        causes=["MSFS restarting SimConnect subsystem", "Add-on not handling SimConnect reconnection", "Firewall blocking SimConnect pipe"],
        fixes=["Add MSFS and add-on to Windows Firewall exceptions", "Restart the add-on after MSFS fully loads", "Update add-on to latest version"],
        search_terms=["simconnect connection lost", "simconnect disconnect"],
    ),
    ErrorEntry(
        id="SIM_003", name="SimConnect Version Mismatch",
        category="SimConnect", severity="medium",
        description="Add-on requires a different SimConnect version than what MSFS provides.",
        causes=["Add-on built for MSFS 2020 SimConnect but running on 2024", "SDK version mismatch", "Multiple SimConnect versions installed"],
        fixes=["Install the specific SimConnect version the add-on requires", "Update add-on to MSFS 2024 compatible version", "Check add-on documentation for required SDK version"],
        search_terms=["simconnect version", "simconnect mismatch", "simconnect api"],
    ),

    # ============================================================
    # STARTUP / LAUNCH CRASHES
    # ============================================================
    ErrorEntry(
        id="START_001", name="MSFS Crashes on Launch",
        category="Startup", severity="high",
        description="MSFS crashes immediately or during loading screen before reaching the main menu.",
        causes=["Corrupted MSFS installation", "Corrupted UserCfg.opt or cloud save", "OneDrive syncing MSFS config files", "NVIDIA App causing DLL conflicts", "Missing VC++ redistributables", "Windows Game Mode / Game Bar interference", "Antivirus quarantining MSFS files"],
        fixes=["Repair MSFS: Settings > Apps > MSFS > Repair", "Delete cloud save and let it re-sync", "Disable OneDrive sync for Documents", "Uninstall NVIDIA App", "Install latest VC++ Redistributables", "Disable Windows Game Mode and Game Bar", "Add MSFS to antivirus exclusions", "Run MSFS as Administrator", "Delete Rolling Cache folder", "Perform clean boot (msconfig) and test"],
        search_terms=["crash on launch", "crash on startup", "wont start", "freeze on loading"],
    ),
    ErrorEntry(
        id="START_002", name="Stuck on Loading Screen",
        category="Startup", severity="high",
        description="MSFS gets stuck on the loading screen and never reaches the main menu.",
        causes=["Xbox Game Services issue (most common)", "Corrupted MSFS packages", "Internet connection problem during streaming", "OneDrive locking files", "Antivirus scanning MSFS files"],
        fixes=["Reset Xbox Game Services: Settings > Apps > Xbox Game Services > Advanced Options > Reset", "Clear MSFS rolling cache", "Disconnect OneDrive temporarily", "Add MSFS folders to antivirus exclusions", "Try launching in Safe Mode", "Repair MSFS from Settings > Apps"],
        search_terms=["stuck on loading", "loading screen freeze", "infinite loading"],
    ),
    ErrorEntry(
        id="START_003", name="Shader Model Not Supported",
        category="Startup", severity="critical",
        description="MSFS 2024 requires Shader Model 6.7 which your GPU does not support.",
        causes=["GPU too old (GTX 10 series and older)", "GPU drivers outdated", "Integrated graphics being used"],
        fixes=["MSFS 2024 requires: NVIDIA GTX 1080+ or AMD RX 5000+", "Update GPU drivers", "Ensure dedicated GPU is being used", "If GPU too old, use MSFS 2020 instead"],
        search_terms=["shader model 6.7", "shader model", "D3D12Renderer_Z"],
    ),
    ErrorEntry(
        id="START_004", name="Black Screen on Launch",
        category="Startup", severity="high",
        description="MSFS launches but shows a black screen indefinitely.",
        causes=["GPU driver not initialized properly", "HDR conflict", "Multi-monitor ordering issue", "Overlay application interfering"],
        fixes=["Alt+Tab out and back in", "Disable HDR in Windows", "Set single monitor before launch", "Disable Discord/Steam overlays", "Delete MSFS cache and restart"],
        search_terms=["black screen", "black screen launch", "blank screen"],
    ),
    ErrorEntry(
        id="START_005", name="MSFS Minimizes Immediately on Launch",
        category="Startup", severity="medium",
        description="MSFS window appears briefly then minimizes to taskbar.",
        causes=["Another application stealing focus", "Windows Game Mode issue", "Dual GPU system selecting wrong GPU"],
        fixes=["Close all other applications before launch", "Disable Windows Game Mode", "Set MSFS to use dedicated GPU in Windows Graphics Settings", "Check Task Manager for focus-stealing processes"],
        search_terms=["minimize on launch", "window minimizes", "focus stolen"],
    ),
    ErrorEntry(
        id="START_006", name="MSFS Opens in Windowed Mode Stuck",
        category="Startup", severity="low",
        description="MSFS launches but cannot switch to fullscreen mode.",
        causes=["Fullscreen setting not saved in UserCfg.opt", "Overlay preventing fullscreen exclusive", "Display driver issue"],
        fixes=["Edit UserCfg.opt directly to set fullscreen 1", "Disable all overlays", "Update GPU drivers", "Try Alt+Enter to toggle fullscreen"],
        search_terms=["windowed mode", "fullscreen stuck", "cant fullscreen"],
    ),
    ErrorEntry(
        id="START_007", name="Crash During Flight Loading",
        category="Startup", severity="high",
        description="MSFS crashes specifically when loading into a flight (after clicking Fly).",
        causes=["Corrupted scenery cache", "Airport add-on causing crash during load", "Insufficient VRAM for selected scenery area", "WASM module initializing during flight load"],
        fixes=["Try loading a different airport/area", "Remove scenery add-ons for the area", "Lower texture resolution before loading", "Clear WASM cache", "Delete SceneryIndexes folder"],
        search_terms=["crash loading flight", "crash when loading", "loading flight crash"],
    ),

    # ============================================================
    # ADD-ON / MOD ISSUES
    # ============================================================
    ErrorEntry(
        id="MOD_001", name="Community Folder Add-on Conflict",
        category="Add-ons", severity="high",
        description="An add-on in the Community folder is conflicting with MSFS or other add-ons.",
        causes=["Incompatible add-on version for current MSFS build", "Duplicate add-ons (same name, different versions)", "Add-on with broken package structure", "Marketplace add-on conflicting with Community add-on"],
        fixes=["Move ALL Community folder contents to backup", "Launch MSFS and test stability", "If stable, add back in halves (binary search)", "Use MSFS Addons Linker to manage add-on groups", "Update all add-ons to latest versions", "Check for duplicate add-on folders"],
        search_terms=["community folder", "add-on conflict", "mod crash", "mods causing crash"],
    ),
    ErrorEntry(
        id="MOD_002", name="Marketplace Add-on Auto-Install Issue",
        category="Add-ons", severity="medium",
        description="Marketplace add-ons auto-downloading and causing conflicts or CTDs.",
        causes=["Marketplace auto-install downloading incompatible content", "Streamed packages corrupting", "2020 items conflicting with 2024"],
        fixes=["Disable marketplace auto-install by creating empty placeholder folders", "Navigate to StreamedPackages folder and manage manually", "Create matching empty folder in Community folder to block download"],
        search_terms=["marketplace", "auto install", "streamed packages", "streamedpackages"],
    ),
    ErrorEntry(
        id="MOD_003", name="Missing layout.json Manifest",
        category="Add-ons", severity="low",
        description="An add-on folder is missing its layout.json manifest file.",
        causes=["Incomplete installation or corrupted download", "Developer forgot to include layout.json", "File extraction error"],
        fixes=["Re-download the add-on from original source", "Some mods work without layout.json but may cause issues", "Check if add-on requires specific installer"],
        search_terms=["layout.json missing", "missing manifest", "no layout.json"],
    ),
    ErrorEntry(
        id="MOD_004", name="Empty WASM Module (0 bytes)",
        category="Add-ons", severity="medium",
        description="A WASM file in the Community folder has zero bytes.",
        causes=["Corrupted download", "Incomplete file extraction", "Antivirus quarantined the file content"],
        fixes=["Re-download the add-on", "Check antivirus quarantine", "Verify file size after downloading"],
        search_terms=["empty wasm", "wasm 0 bytes", "wasm file empty"],
    ),
    ErrorEntry(
        id="MOD_005", name="Duplicate Add-on Detected",
        category="Add-ons", severity="low",
        description="Multiple folders with the same add-on name exist in the Community folder.",
        causes=["Accidental double installation", "Different versions installed simultaneously", "Addons Linker creating duplicate links"],
        fixes=["Remove the older or duplicate folder", "Keep only the latest version", "Verify they are actually the same add-on"],
        search_terms=["duplicate add-on", "duplicate mod", "duplicate folder"],
    ),
    ErrorEntry(
        id="MOD_006", name="Incompatible Add-on for MSFS 2024",
        category="Add-ons", severity="high",
        description="An add-on built for MSFS 2020 is not compatible with MSFS 2024.",
        causes=["Developer hasn't updated for MSFS 2024", "Package format changed between 2020 and 2024", "API changes breaking add-on functionality"],
        fixes=["Check add-on developer website for MSFS 2024 version", "Remove incompatible add-on from Community folder", "Use MSFS 2020 version of the add-on with MSFS 2020", "Contact developer to request update"],
        search_terms=["incompatible add-on", "msfs 2020 add-on", "not compatible"],
    ),
    ErrorEntry(
        id="MOD_007", name="Add-on Exceeds Package Size Limit",
        category="Add-ons", severity="medium",
        description="An add-on package exceeds MSFS package size limits or has too many files.",
        causes=["Overly detailed scenery add-on", "Too many high-resolution textures", "Developer packaged unnecessary files"],
        fixes=["Remove the add-on", "Contact developer to optimize package", "Check for a lite version of the add-on"],
        search_terms=["package size", "too many files", "package limit"],
    ),
    ErrorEntry(
        id="MOD_008", name="Broken Aircraft Add-on",
        category="Add-ons", severity="high",
        description="An aircraft add-on causes crashes or has broken instruments.",
        causes=["Missing required WASM module", "Incompatible panel configuration", "Missing liveries or textures", "Outdated aircraft systems code"],
        fixes=["Reinstall the aircraft add-on", "Check for updates from developer", "Remove and re-download", "Verify package structure with layout.json"],
        search_terms=["broken aircraft", "aircraft crash", "aircraft broken"],
    ),

    # ============================================================
    # PERFORMANCE ISSUES
    # ============================================================
    ErrorEntry(
        id="PERF_001", name="Low FPS / Stuttering",
        category="Performance", severity="medium",
        description="MSFS runs at very low FPS or stutters heavily despite adequate hardware.",
        causes=["Settings too high for hardware", "EXPO/XMP not enabled in BIOS", "Background apps consuming CPU/GPU", "Rolling cache corrupted", "Resizable BAR causing VRAM issues", "Threadripper CPU core count bug"],
        fixes=["Enable EXPO/XMP profile in BIOS", "Limit FPS to 30 or 60", "Disable ground displacement and raytraced shadows", "Set TLOD/OLOD to 100/100", "Use DLSS or FSR instead of TAA", "Clear rolling cache", "Disable Resizable BAR for 8-16GB GPUs", "Close all background apps", "Disable Windows Game Mode", "Set power plan to High Performance"],
        search_terms=["low fps", "stuttering", "micro freezes", "performance"],
    ),
    ErrorEntry(
        id="PERF_002", name="Post-Update Stuttering",
        category="Performance", severity="medium",
        description="Severe stuttering after a Sim Update, even with previously stable settings.",
        causes=["Stale WASM cache after update", "Corrupted scenery indexes", "Stale DirectX shader cache", "Content.xml needs regeneration"],
        fixes=["Clear WASM cache folder", "Delete SceneryIndexes and SceneryCache folders", "Delete Content.xml (sim regenerates it)", "Clear rolling cache", "Clear NVIDIA shader cache", "Start MSFS in Safe Mode for full recompile"],
        search_terms=["post update stutter", "stutter after update", "stuttering after su"],
    ),
    ErrorEntry(
        id="PERF_003", name="VRAM Critical Warning",
        category="Performance", severity="medium",
        description="MSFS displays VRAM Critical warning and performance degrades severely.",
        causes=["Texture Resolution too high", "TLOD too high", "Raytraced shadows enabled", "Resizable BAR over-allocating VRAM"],
        fixes=["Reduce Texture Resolution by one tier", "Lower TLOD to 100", "Disable Raytraced Shadows", "Disable Resizable BAR in BIOS", "Enable Dynamic Settings", "Use DLSS/FSR"],
        search_terms=["vram critical", "vram warning", "vram exceeded"],
    ),
    ErrorEntry(
        id="PERF_004", name="CPU Bottleneck",
        category="Performance", severity="medium",
        description="CPU is limiting FPS despite adequate GPU performance.",
        causes=["Object LOD too high", "Traffic settings too high", "Weather settings CPU-intensive", "Single-threaded bottleneck in MSFS"],
        fixes=["Lower Object LOD to 100", "Reduce AI traffic and airport traffic", "Lower weather update frequency", "Disable live weather temporarily", "Close CPU-heavy background apps"],
        search_terms=["cpu bottleneck", "cpu limited", "main thread limited"],
    ),
    ErrorEntry(
        id="PERF_005", name="Sim Stuttering Despite High FPS",
        category="Performance", severity="medium",
        description="MSFS shows 60+ FPS but feels choppy and stuttery.",
        causes=["Frame pacing issues", "VSync conflict", "Background process causing frame drops", "Rolling cache causing micro-hitches"],
        fixes=["Enable VSync or cap FPS to monitor refresh rate", "Disable background apps and overlays", "Clear rolling cache", "Set power plan to High Performance", "Disable HAGS if causing frame pacing issues"],
        search_terms=["frame pacing", "stuttering high fps", "frame time"],
    ),
    ErrorEntry(
        id="PERF_006", name="Long Loading Times",
        category="Performance", severity="medium",
        description="MSFS takes excessively long to load flights or scenery.",
        causes=["Slow HDD instead of SSD", "Too many Community add-ons", "Large rolling cache size", "Internet bandwidth limiting streaming", "Low RAM causing swapping"],
        fixes=["Install MSFS on SSD (mandatory for good performance)", "Reduce Community folder add-ons", "Clear rolling cache", "Use wired Ethernet", "Ensure 16GB+ RAM"],
        search_terms=["long loading", "slow loading", "loading time"],
    ),
    ErrorEntry(
        id="PERF_007", name="Texture Pop-in / Loading Late",
        category="Performance", severity="medium",
        description="Textures and scenery take too long to load, appearing low-res or popping in.",
        causes=["Internet bandwidth insufficient for streaming", "Texture Resolution setting too low", "Rolling cache not working properly", "Server congestion"],
        fixes=["Increase texture resolution if VRAM allows", "Clear and rebuild rolling cache", "Use wired Ethernet connection", "Try different time of day (server load)", "Pre-download offline scenery"],
        search_terms=["texture pop-in", "late loading textures", "blurry textures"],
    ),
    ErrorEntry(
        id="PERF_008", name="MSFS Not Using Full GPU",
        category="Performance", severity="medium",
        description="GPU utilization stays low (30-50%) while FPS is limited.",
        causes=["CPU bottleneck limiting frame submission", "VSync capping frame rate", "MSFS setting limiting GPU load", "Power settings throttling GPU"],
        fixes=["Lower CPU-bound settings (LOD, traffic)", "Disable VSync to test", "Set power plan to High Performance", "Ensure GPU is set to maximum performance in NVIDIA Control Panel"],
        search_terms=["gpu not used", "gpu utilization low", "gpu bottleneck"],
    ),

    # ============================================================
    # VR-SPECIFIC ISSUES
    # ============================================================
    ErrorEntry(
        id="VR_001", name="MSFS Crashes When Entering VR",
        category="VR", severity="high",
        description="MSFS crashes immediately when switching to VR mode (Ctrl+Tab).",
        causes=["Entering VR from main menu causes crash (known bug)", "OpenXR Toolkit Foveated Rendering conflict", "VR headset driver issue", "Insufficient GPU VRAM for VR rendering"],
        fixes=["Enter flight mode FIRST, THEN switch to VR", "Disable Foveated Rendering in OpenXR Toolkit", "Update VR headset drivers", "Lower VR-specific settings", "Disable motion reprojection temporarily"],
        search_terms=["vr crash", "vr mode crash", "ctrl+tab crash", "vr freeze"],
    ),
    ErrorEntry(
        id="VR_002", name="VR Performance Very Poor",
        category="VR", severity="high",
        description="MSFS in VR runs at very low framerate causing motion sickness.",
        causes=["VR requires 90fps for smooth experience", "Settings too high for VR rendering (2x resolution)", "OpenXR runtime not optimized", "Motion reprojection causing artifacts"],
        fixes=["Use OpenXR Toolkit for foveated rendering", "Lower VR render scale to 80-90%", "Use DLSS/FSR in VR mode", "Reduce Terrain LOD and Object LOD significantly", "Disable ray tracing in VR", "Ensure dedicated GPU is selected in Mixed Reality settings"],
        search_terms=["vr performance", "vr fps", "vr lag", "motion sickness"],
    ),
    ErrorEntry(
        id="VR_003", name="VR Headset Not Detected",
        category="VR", severity="medium",
        description="MSFS does not detect the VR headset for VR mode.",
        causes=["VR runtime not running", "Headset driver issue", "Mixed Reality Portal not installed", "OpenXR runtime not set"],
        fixes=["Ensure VR headset is connected and running", "Install/update Windows Mixed Reality Portal", "Set OpenXR as default runtime in SteamVR settings", "Restart VR runtime services"],
        search_terms=["vr not detected", "headset not found", "no vr"],
    ),
    ErrorEntry(
        id="VR_004", name="VR Controllers Not Working",
        category="VR", severity="low",
        description="VR controllers are not interactive in MSFS VR mode.",
        causes=["MSFS VR has limited controller support", "Controller tracking issue", "OpenXR input mapping problem"],
        fixes=["MSFS VR primarily uses mouse/controller for interaction", "Ensure controllers are tracked in WMR/SteamVR", "Try restarting VR runtime", "Check OpenXR input settings"],
        search_terms=["vr controller", "controller not working", "vr input"],
    ),
    ErrorEntry(
        id="VR_005", name="VR Causes CTD After Extended Use",
        category="VR", severity="high",
        description="MSFS in VR crashes after 30-60 minutes of play.",
        causes=["Memory leak in VR rendering path", "GPU overheating from dual-eye rendering", "VR runtime instability over time"],
        fixes=["Monitor GPU temperature during VR sessions", "Limit VR session length", "Restart MSFS between long VR flights", "Lower VR settings to reduce GPU load", "Check for VR runtime updates"],
        search_terms=["vr ctd", "vr crash after time", "vr extended crash"],
    ),

    # ============================================================
    # AUDIO ISSUES
    # ============================================================
    ErrorEntry(
        id="AUDIO_001", name="Audio Crackling / Stuttering",
        category="Audio", severity="medium",
        description="Audio in MSFS crackles, pops, or stutters during flight.",
        causes=["Audio buffer underrun (CPU overloaded)", "USB audio device conflict", "Audio driver issue", "Too many audio sources"],
        fixes=["Set audio to 44100Hz 16-bit in Windows Sound settings", "Increase audio buffer size in MSFS", "Update audio drivers", "Disable Windows audio enhancements", "Use motherboard audio instead of USB DAC"],
        search_terms=["audio crackling", "audio stuttering", "sound popping"],
    ),
    ErrorEntry(
        id="AUDIO_002", name="No Audio in MSFS",
        category="Audio", severity="medium",
        description="MSFS has no sound at all.",
        causes=["Wrong audio output device selected", "Audio service crashed", "MSFS audio settings muted", "Corrupted audio files"],
        fixes=["Check Windows audio output device", "Restart Windows Audio service", "Check MSFS audio settings and volume", "Repair MSFS installation", "Restart computer"],
        search_terms=["no audio", "no sound", "silent", "audio missing"],
    ),
    ErrorEntry(
        id="AUDIO_003", name="ATC Voice Missing",
        category="Audio", severity="low",
        description="ATC voice communication is not audible in MSFS.",
        causes=["ATC voice volume set to 0", "Text-to-Speech engine not installed", "ATC audio channel disabled"],
        fixes=["Check ATC volume in MSFS audio settings", "Install Windows Speech Synthesis voices", "Enable ATC audio in assistance settings"],
        search_terms=["atc voice", "atc audio", "atc silent"],
    ),

    # ============================================================
    # NETWORK / CONNECTIVITY
    # ============================================================
    ErrorEntry(
        id="NET_001", name="Streaming Content Loading Failure",
        category="Network", severity="medium",
        description="MSFS cannot stream scenery data, causing missing textures or loading failures.",
        causes=["Internet connection unstable", "Microsoft servers overloaded", "Firewall blocking MSFS network access", "Bandwidth insufficient"],
        fixes=["Use wired Ethernet instead of WiFi", "Lower data streaming quality in MSFS settings", "Disable rolling cache and re-enable it", "Check firewall settings for MSFS", "Try again during off-peak hours"],
        search_terms=["streaming", "loading failure", "missing textures", "server error"],
    ),
    ErrorEntry(
        id="NET_002", name="Xbox Live Connection Error",
        category="Network", severity="medium",
        description="MSFS cannot connect to Xbox Live services required for multiplayer and streaming.",
        causes=["Xbox Live services down", "NAT type restrictive", "Port blocking by router/firewall", "Microsoft account issue"],
        fixes=["Check Xbox Live status at status.xbox.com", "Enable UPnP on router", "Forward MSFS ports (3074, 88, 500, 3544, 4500)", "Sign out and sign back into Microsoft account", "Restart router"],
        search_terms=["xbox live", "xbox live error", "connection error", "login failed"],
    ),
    ErrorEntry(
        id="NET_003", name="Multiplayer / Live Traffic Not Working",
        category="Network", severity="low",
        description="Other players or live AI traffic are not visible despite being online.",
        causes=["Multiplayer settings disabled", "Data connection limited", "Server region mismatch", "Traffic settings too low"],
        fixes=["Enable multiplayer in MSFS settings", "Check Data tab settings are enabled", "Set Data Connection to maximum", "Verify Microsoft account has Xbox Game Pass / Live Gold if required"],
        search_terms=["multiplayer not working", "no players", "live traffic missing"],
    ),
    ErrorEntry(
        id="NET_004", name="MSFS Requires Internet Connection",
        category="Network", severity="low",
        description="MSFS requires periodic internet connection even for offline play.",
        causes=["Anti-piracy verification", "Content streaming requires connection", "License verification"],
        fixes=["Ensure periodic internet connection", "Pre-download content for offline use", "Use rolling cache for offline scenery"],
        search_terms=["internet required", "offline mode", "requires connection"],
    ),

    # ============================================================
    # THIRD-PARTY SOFTWARE CONFLICTS
    # ============================================================
    ErrorEntry(
        id="SW_001", name="MSI Afterburner / RTSS Conflict",
        category="Software Conflict", severity="high",
        description="MSI Afterburner and RivaTuner hooking into DirectX causing CTDs.",
        causes=["RTSS overlay hooking into DX12", "MSI Afterburner GPU monitoring conflicting", "On-Screen Display rendering interfering"],
        fixes=["Completely uninstall MSI Afterburner and RTSS", "Or disable RTSS overlay while running MSFS", "Add MSFS.exe to RTSS application list and set to none mode"],
        search_terms=["msi afterburner", "rtss", "rivatuner", "overlay crash"],
    ),
    ErrorEntry(
        id="SW_002", name="Corsair iCue / Nahimic Audio Conflict",
        category="Software Conflict", severity="medium",
        description="Corsair iCue or Nahimic audio drivers causing crashes.",
        causes=["Corsair iCue hooking into system processes", "Nahimic audio driver conflicting with MSFS audio"],
        fixes=["Uninstall Corsair iCue temporarily and test", "Uninstall Nahimic audio driver", "Disable audio enhancements in Windows Sound settings"],
        search_terms=["corsair icue", "nahimic", "audio crash"],
    ),
    ErrorEntry(
        id="SW_003", name="NVIDIA App Conflict",
        category="Software Conflict", severity="medium",
        description="NVIDIA App causing DLL conflicts and launch crashes.",
        causes=["NVIDIA App overlay interfering", "RTX Dynamic Vibrance causing DXGI errors", "NVIDIA App installing incompatible driver"],
        fixes=["Uninstall NVIDIA App completely", "Or disable NVIDIA App overlay and RTX Dynamic Vibrance", "Use NVIDIA Control Panel instead"],
        search_terms=["nvidia app", "nvidia app crash", "rtx dynamic vibrance"],
    ),
    ErrorEntry(
        id="SW_004", name="ASUS Armoury Crate / AI Suite Conflict",
        category="Software Conflict", severity="medium",
        description="ASUS motherboard software causing system instability with MSFS.",
        causes=["Armoury Crate background services consuming resources", "AI Suite fan control conflicting with GPU fan curves", "Aura Sync RGB software hooking into processes"],
        fixes=["Uninstall Armoury Crate and AI Suite", "Use BIOS for fan control instead", "Disable Aura Sync during MSFS sessions"],
        search_terms=["armoury crate", "ai suite", "asus software"],
    ),
    ErrorEntry(
        id="SW_005", name="Discord Overlay Conflict",
        category="Software Conflict", severity="medium",
        description="Discord overlay causing FPS drops or crashes in MSFS.",
        causes=["Discord overlay hooking into DirectX", "Screen sharing causing GPU overhead", "Rich presence conflicting with MSFS"],
        fixes=["Disable Discord overlay for MSFS", "Disable Hardware Acceleration in Discord settings", "Close Discord before launching MSFS", "Use Discord mobile during flights"],
        search_terms=["discord overlay", "discord crash", "discord fps"],
    ),
    ErrorEntry(
        id="SW_006", name="Windows Game Bar / Game Mode Conflict",
        category="Software Conflict", severity="medium",
        description="Windows Game Bar or Game Mode causing performance issues or crashes.",
        causes=["Game Bar overlay using GPU resources", "Game Mode incorrectly optimizing MSFS", "Game DVR recording in background"],
        fixes=["Disable Game Bar: Settings > Gaming > Xbox Game Bar > Off", "Disable Game Mode: Settings > Gaming > Game Mode > Off", "Disable Game DVR: Registry or Group Policy"],
        search_terms=["game bar", "game mode", "game dvr", "xbox game bar"],
    ),
    ErrorEntry(
        id="SW_007", name="Razer Synapse / Corsair iCue HW Control",
        category="Software Conflict", severity="low",
        description="RGB/peripheral software interfering with MSFS.",
        causes=["Background services polling hardware", "Macro software hooking inputs", "RGB control using GPU resources"],
        fixes=["Close peripheral software during MSFS", "Disable lighting effects during flight", "Use onboard peripheral memory profiles"],
        search_terms=["razer synapse", "peripheral software", "rgb software"],
    ),
    ErrorEntry(
        id="SW_008", name="Antivirus / Windows Defender Conflict",
        category="Software Conflict", severity="medium",
        description="Real-time antivirus scanning causing stuttering or CTDs.",
        causes=["AV scanning MSFS files mid-flight", "AV scanning WASM modules", "AV scanning Community folder"],
        fixes=["Add MSFS install folder to AV exclusions", "Add Community folder to exclusions", "Add WASM cache folder to exclusions", "Temporarily disable real-time scanning during flight"],
        search_terms=["antivirus", "windows defender", "av conflict", "defender scan"],
    ),

    # ============================================================
    # WINDOWS / SYSTEM ISSUES
    # ============================================================
    ErrorEntry(
        id="SYS_001", name="OneDrive Sync Conflict",
        category="System", severity="medium",
        description="OneDrive syncing MSFS config files causes file locks and CTDs.",
        causes=["Documents folder redirected to OneDrive (Windows 11 default)", "MSFS reading UserCfg.opt while OneDrive syncing", "Community folder in OneDrive-synced location"],
        fixes=["Stop OneDrive sync for Documents folder", "Move MSFS Community folder out of Documents", "Disable OneDrive entirely if not needed", "Use LocalAppData path for MSFS"],
        search_terms=["onedrive", "onedrive sync", "file lock"],
    ),
    ErrorEntry(
        id="SYS_002", name="Antivirus Quarantine Issue",
        category="System", severity="medium",
        description="Antivirus quarantines MSFS files mid-flight, causing CTD.",
        causes=["Real-time AV scanning .bgl or .ccc scenery files", "False positive on WASM modules", "AV scanning Community folder add-ons"],
        fixes=["Add MSFS install folder to AV exclusions", "Add Community folder to exclusions", "Add WASM cache folder to exclusions", "Check antivirus quarantine and restore files"],
        search_terms=["antivirus quarantine", "quarantine", "av false positive"],
    ),
    ErrorEntry(
        id="SYS_003", name="Windows Update Broke MSFS",
        category="System", severity="high",
        description="A Windows update caused MSFS to stop working properly.",
        causes=["Windows update overwrote GPU drivers", "Windows update broke DirectX", "Windows update changed system permissions", "Windows update incompatible with MSFS"],
        fixes=["Roll back Windows update", "Reinstall GPU drivers after Windows update", "Run sfc /scannow and DISM", "Check Microsoft support for known issues", "Wait for MSFS or Windows hotfix"],
        search_terms=["windows update", "update broke", "update issue"],
    ),
    ErrorEntry(
        id="SYS_004", name="Insufficient Disk Space",
        category="System", severity="medium",
        description="MSFS ran out of disk space during operation, causing crashes.",
        causes=["MSFS install drive full", "Rolling cache drive full", "Community folder drive full", "Windows temp folder full"],
        fixes=["Free up at least 50GB on MSFS install drive", "Reduce rolling cache size", "Move rolling cache to different drive", "Clear Windows temp folder", "Use disk cleanup utility"],
        search_terms=["disk space", "out of space", "no space", "disk full"],
    ),
    ErrorEntry(
        id="SYS_005", name="Corrupted Windows User Profile",
        category="System", severity="high",
        description="MSFS crashes due to corrupted Windows user profile or permissions.",
        causes=["Corrupted AppData folder", "Incorrect folder permissions", "Group Policy restrictions", "Domain-joined PC with restrictions"],
        fixes=["Create a new Windows user profile and test", "Take ownership of MSFS folders", "Run MSFS as administrator", "Check group policies for restrictions"],
        search_terms=["user profile", "permissions", "corrupted profile"],
    ),
    ErrorEntry(
        id="SYS_006", name="Hyper-V / WSL2 Conflict",
        category="System", severity="medium",
        description="Hyper-V or WSL2 virtualization causing GPU passthrough issues with MSFS.",
        causes=["Hyper-V GPU-PV partitioning conflicting", "WSL2 consuming GPU resources", "Virtualization-based security (VBS) affecting performance"],
        fixes=["Disable Hyper-V if not needed", "Disable WSL2 during MSFS sessions", "Disable VBS: Regedit -> HKLM\\System\\CurrentControlSet\\Control\\DeviceGuard -> EnableVirtualizationBasedSecurity = 0", "Disable Credential Guard"],
        search_terms=["hyper-v", "wsl2", "virtualization", "vbs", "credential guard"],
    ),
    ErrorEntry(
        id="SYS_007", name="Power Throttling",
        category="System", severity="medium",
        description="Windows power throttling is limiting MSFS CPU/GPU performance.",
        causes=["Power plan set to Balanced", "Battery saver mode on laptop", "Power throttling enabled in Windows"],
        fixes=["Set power plan to High Performance or Ultimate Performance", "Disable Power Throttling: Settings > System > Battery > Power Mode > Best Performance", "Plug in laptop for AC power", "Disable Battery Saver"],
        search_terms=["power throttling", "throttling", "power plan", "battery saver"],
    ),
    ErrorEntry(
        id="SYS_008", name="Clock Watchdog Timeout (0x101)",
        category="System", severity="critical",
        description="Windows detected a deadlocked CPU core (BSOD).",
        causes=["CPU instability from overclocking", "CPU voltage too low (undervolt)", "BIOS microcode bug (Intel 13th/14th gen)", "Faulty CPU hardware"],
        fixes=["Reset CPU to stock settings in BIOS", "Update BIOS to latest version", "Increase CPU voltage slightly", "For Intel 13th/14th gen: apply latest microcode update", "Run stress test (Prime95) to check CPU stability"],
        search_terms=["clock watchdog", "0x101", "whea uncorrectable"],
        related_codes=["0x00000101"],
    ),
    ErrorEntry(
        id="SYS_009", name="Machine Check Exception (0x9C)",
        category="System", severity="critical",
        description="Windows detected a hardware error (BSOD).",
        causes=["Faulty RAM", "Failing GPU hardware", "CPU instability", "Motherboard issue"],
        fixes=["Run Windows Memory Diagnostic", "Test GPU with FurMark", "Reset BIOS to defaults", "Check motherboard for blown capacitors", "Test with known-good hardware"],
        search_terms=["machine check exception", "0x9c", "hardware error"],
        related_codes=["0x0000009C"],
    ),
    ErrorEntry(
        id="SYS_010", name="IRQL NOT LESS OR EQUAL (0xA)",
        category="System", severity="critical",
        description="Windows kernel tried to access paged memory at too high an IRQL (BSOD).",
        causes=["Faulty device driver (often GPU or network)", "Faulty RAM", "Corrupted system files"],
        fixes=["Update all device drivers", "Run sfc /scannow", "Test RAM with Windows Memory Diagnostic", "Uninstall recently installed drivers or software"],
        search_terms=["irql not less or equal", "0xa", "bsod driver"],
        related_codes=["0x0000000A"],
    ),
    ErrorEntry(
        id="SYS_011", name="KERNEL SECURITY CHECK FAILURE (0x139)",
        category="System", severity="critical",
        description="Windows kernel detected a security violation (BSOD).",
        causes=["Corrupted system files", "Faulty driver", "Malware infection", "Disk corruption"],
        fixes=["Run sfc /scannow and DISM", "Update all drivers", "Run full antivirus scan", "Check disk for errors: chkdsk /f /r"],
        search_terms=["kernel security check", "0x139", "bsod kernel"],
        related_codes=["0x00000139"],
    ),
    ErrorEntry(
        id="SYS_012", name="PAGE FAULT IN NONPAGED AREA (0x50)",
        category="System", severity="critical",
        description="Windows tried to access invalid memory (BSOD).",
        causes=["Faulty RAM", "Corrupted NTFS volume", "Faulty driver", "Damaged page file"],
        fixes=["Run chkdsk /f /r", "Test RAM with Windows Memory Diagnostic", "Run sfc /scannow", "Reset page file: delete pagefile.sys and reboot"],
        search_terms=["page fault", "0x50", "nonpaged area"],
        related_codes=["0x00000050"],
    ),
    ErrorEntry(
        id="SYS_013", name="SYSTEM_SERVICE_EXCEPTION (0x3B)",
        category="System", severity="critical",
        description="A system service caused an exception (BSOD).",
        causes=["Faulty driver", "Corrupted system files", "Windows update issue"],
        fixes=["Run sfc /scannow", "Update Windows and all drivers", "Uninstall recent Windows updates", "Perform clean boot to identify culprit"],
        search_terms=["system service exception", "0x3b", "bsod service"],
        related_codes=["0x0000003B"],
    ),
    ErrorEntry(
        id="SYS_014", name="DPC WATCHDOG VIOLATION (0x133)",
        category="System", severity="critical",
        description="Windows detected a DPC routine taking too long (BSOD).",
        causes=["NVMe SSD firmware issue", "Storage driver conflict", "Network driver issue", "GPU driver issue"],
        fixes=["Update NVMe SSD firmware", "Update storage and network drivers", "Update GPU drivers", "Check SATA/NVMe cable connections"],
        search_terms=["dpc watchdog", "0x133", "dpc violation"],
        related_codes=["0x00000133"],
    ),
    ErrorEntry(
        id="SYS_015", name="SYSTEM_THREAD_EXCEPTION NOT HANDLED (0x7E)",
        category="System", severity="critical",
        description="A system thread generated an exception that was not handled (BSOD).",
        causes=["Faulty driver (most common cause)", "Corrupted system files", "Incompatible hardware"],
        fixes=["Boot into Safe Mode and uninstall recent drivers", "Run sfc /scannow", "Check Event Viewer for the specific faulting driver", "Update BIOS and chipset drivers"],
        search_terms=["system thread exception", "0x7e", "not handled"],
        related_codes=["0x0000007E"],
    ),

    # ============================================================
    # MSFS-SPECIFIC DLL CRASHES (from community research)
    # ============================================================
    ErrorEntry(
        id="MSFS_DLL_001", name="grammar.pggmod Crash",
        category="MSFS DLL", severity="high",
        description="MSFS 2024 crashes with the grammar.pggmod module as the faulting module. This is an internal MSFS content processing module.",
        causes=["Corrupted scenery package grammar file", "Bad sim update installation", "Add-on with broken grammar definition", "Stale content cache after update"],
        fixes=["Delete Content.xml and let MSFS regenerate it", "Clear SceneryIndexes and SceneryCache folders", "Verify MSFS files or Repair app", "Remove Community folder content and test", "Reinstall MSFS if persistent"],
        search_terms=["grammar.pggmod", "grammar", "pggmod"],
        related_dlls=["grammar.pggmod"],
    ),
    ErrorEntry(
        id="MSFS_DLL_002", name="CoherentGTJS.dll Crash",
        category="MSFS DLL", severity="high",
        description="Crash in the Coherent GT JavaScript engine used for HTML-based cockpit gauges and UI.",
        causes=["Corrupted CoherentGTJS.dll", "JavaScript gauge error in add-on aircraft", "Edge WebView conflict", "Incompatible browser runtime"],
        fixes=["Verify MSFS files or Repair app", "Update Microsoft Edge (provides WebView2 runtime)", "Remove add-on aircraft with HTML gauges and test", "Run sfc /scannow", "Reinstall MSFS"],
        search_terms=["coherentgtjs", "coherentgtjs.dll", "coherent gt js"],
        related_dlls=["CoherentGTJS.dll"],
    ),
    ErrorEntry(
        id="MSFS_DLL_003", name="190_E658703.dll Crash (NVIDIA NGX)",
        category="MSFS DLL", severity="high",
        description="Crash in an NVIDIA NGX (Neural Graphics Extension) DLL file. Used for DLSS and AI features.",
        causes=["NVIDIA App installed with incompatible NGX DLL", "NVIDIA App update corrupted NGX files", "DLSS version incompatibility", "GPU driver mismatch with NGX version"],
        fixes=["Uninstall NVIDIA App completely", "Reinstall GPU drivers using DDU", "Delete the NGX folder: C:\\ProgramData\\NVIDIA\\NGX\\models", "Let MSFS/driver reinstall NGX files", "Use older stable NVIDIA driver (566.03 recommended)"],
        search_terms=["190_e658703", "190_e658703.dll", "nvidia ngx", "ngx dll"],
        related_dlls=["190_E658703.dll"],
    ),
    ErrorEntry(
        id="MSFS_DLL_004", name="m29af25827efc9a3c_0.dll Crash (Mobiflight)",
        category="MSFS DLL", severity="medium",
        description="Crash in a Mobiflight event module WASM DLL used for hardware integration.",
        causes=["Outdated Mobiflight WASM module", "Mobiflight module incompatible with MSFS version", "WASM cache corrupted"],
        fixes=["Update Mobiflight connector and WASM module to latest version", "Delete WASM cache folder for Mobiflight", "Reinstall Mobiflight WASM module", "Check Mobiflight Discord for MSFS 2024 compatibility"],
        search_terms=["m29af25827efc9a3c", "mobiflight", "mobiflight event module"],
        related_dlls=["m29af25827efc9a3c_0.dll"],
    ),
    ErrorEntry(
        id="MSFS_DLL_005", name="navigraph-simbrief-dispatch DLL Crash",
        category="MSFS DLL", severity="medium",
        description="Crash in the Navigraph SimBrief Dispatch WASM module.",
        causes=["Outdated Navigraph module", "WASM cache corrupted", "SimBrief API change breaking module"],
        fixes=["Update Navigraph navigation data and SimBrief module", "Delete WASM cache for Navigraph", "Reinstall Navigraph add-on", "Check Navigraph support for MSFS 2024 updates"],
        search_terms=["navigraph", "simbrief dispatch", "navigraph dll"],
        related_dlls=["navigraph-simbrief-dispatch-2020"],
    ),
    ErrorEntry(
        id="MSFS_DLL_006", name="PiPlatformService_64.exe Crash",
        category="MSFS DLL", severity="medium",
        description="Crash in the PiPlatformService (likely Honeycomb or peripheral platform service) with ucrtbase.dll.",
        causes=["ucrtbase.dll language/locale issue", "Peripheral platform service bug", "Missing VC++ runtime"],
        fixes=["Install English (US) language pack", "Set system locale to English (US)", "Update peripheral drivers/software", "Reinstall VC++ Redistributables"],
        search_terms=["pipatformservice", "pipatformservice_64.exe"],
        related_dlls=["PiPlatformService_64.exe", "ucrtbase.dll"],
        related_codes=["0xc0000409"],
    ),

    # ============================================================
    # ADDITIONAL DXGI ERRORS
    # ============================================================
    ErrorEntry(
        id="DXGI_001", name="DXGI_ERROR_INVALID_CALL (0x887a0001)",
        category="DXGI", severity="high",
        description="An invalid call was made to the DXGI API. Common in VR mode when changing anti-aliasing settings.",
        causes=["Changing anti-aliasing settings in VR mode", "Overlay application interfering with DXGI", "GPU driver not handling DXGI calls properly", "Multi-monitor setup issue"],
        fixes=["Do not change anti-aliasing while in VR mode", "Disable overlays (Discord, Steam, MSI Afterburner)", "Update GPU drivers", "Disconnect additional monitors temporarily", "Delete NVIDIA App and use older driver (566.03)"],
        search_terms=["dxgi_error_invalid_call", "0x887a0001", "invalid call"],
        related_dlls=["dxgi.dll"], related_codes=["0x887a0001"],
    ),
    ErrorEntry(
        id="DXGI_002", name="DXGI_ERROR_DRIVER_INTERNAL_ERROR (0x887a0020)",
        category="DXGI", severity="critical",
        description="The GPU driver encountered an internal error. This is a driver-level failure.",
        causes=["GPU driver crash", "GPU overheating causing driver timeout", "NVIDIA App conflict", "GPU overclock unstable", "Multi-monitor configuration issue"],
        fixes=["Uninstall NVIDIA App and use driver 566.03", "Remove GPU overclock", "Disconnect additional monitors", "Clean-install GPU drivers with DDU", "Monitor GPU temperature", "Disable HAGS"],
        search_terms=["dxgi_driver_internal_error", "0x887a0020", "driver internal error"],
        related_dlls=["dxgi.dll"], related_codes=["0x887a0020"],
    ),
    ErrorEntry(
        id="DXGI_003", name="DXGI_ERROR_ACCESS_LOST (0x887a0026)",
        category="DXGI", severity="medium",
        description="The DXGI swap chain has lost access to its resources.",
        causes=["ALT+Tab during heavy rendering", "Another application taking exclusive fullscreen", "Display driver reset"],
        fixes=["Avoid ALT+Tab during heavy rendering", "Use borderless windowed mode instead of exclusive fullscreen", "Update GPU drivers", "Disable fullscreen optimizations in Windows"],
        search_terms=["dxgi_access_lost", "0x887a0026", "access lost"],
        related_dlls=["dxgi.dll"], related_codes=["0x887a0026"],
    ),
    ErrorEntry(
        id="DXGI_004", name="DXGI_ERROR_MODE_CHANGE_IN_PROGRESS (0x887a002a)",
        category="DXGI", severity="medium",
        description="A display mode change is already in progress when another was requested.",
        causes=["Rapid resolution switching", "Multi-monitor reconfiguration during flight", "HDR toggle during rendering"],
        fixes=["Avoid changing resolution during flight", "Set resolution before launching MSFS", "Disable HDR or set it before launch", "Use borderless windowed mode"],
        search_terms=["dxgi_mode_change", "0x887a002a", "mode change"],
        related_dlls=["dxgi.dll"], related_codes=["0x887a002a"],
    ),

    # ============================================================
    # MSFS 2024 SPECIFIC ISSUES
    # ============================================================
    ErrorEntry(
        id="MSFS24_001", name="MSFS 2024 Crashes Near Large Custom Airports",
        category="MSFS 2024", severity="high",
        description="MSFS 2024 becomes unresponsive or crashes when flying near large custom airports (e.g., iniBuilds, FlyTampa).",
        causes=["Custom airport scenery too complex for MSFS 2024 rendering engine", "Too many add-on scenery packages in area", "VRAM exhausted by high-res airport textures", "Ground traffic settings too high"],
        fixes=["Reduce Airport Traffic Quality to Low", "Lower Terrain LOD and Object LOD", "Remove complex custom airport add-ons", "Reduce texture resolution", "Disable ground vehicles and airport workers"],
        search_terms=["crash near airport", "custom airport crash", "large airport ctd", "airport freeze"],
    ),
    ErrorEntry(
        id="MSFS24_002", name="MSFS 2024 Hangs on Ready to Fly Screen",
        category="MSFS 2024", severity="high",
        description="MSFS 2024 freezes on the 'Ready to Fly' screen and cannot enter the sim.",
        causes=["Guide/tutorial overlay conflicting", "Third-party add-on blocking flight start", "WASM module initialization failure", "Cloud save corruption"],
        fixes=["Skip the Guide/tutorial if prompted", "Remove Community folder content", "Delete cloud save and let it re-sync", "Start MSFS in Safe Mode", "Verify MSFS files"],
        search_terms=["ready to fly hang", "ready to fly freeze", "ready to fly stuck", "guide hang"],
    ),
    ErrorEntry(
        id="MSFS24_003", name="MSFS 2024 Career Mode Crash",
        category="MSFS 2024", severity="medium",
        description="MSFS 2024 crashes specifically during Career Mode missions.",
        causes=["Career Mode bug in specific mission type", "Mission spawning logic error", "WASM module conflict with career systems", "Mission order data corruption"],
        fixes=["Try a different career mission type", "Clear WASM cache", "Verify MSFS files", "Report bug to Asobo via Zendesk", "Avoid career mode until patched"],
        search_terms=["career mode crash", "career crash", "mission crash", "career ctd"],
    ),
    ErrorEntry(
        id="MSFS24_004", name="MSFS 2024 Crashes When Escaping to Menu",
        category="MSFS 2024", severity="high",
        description="MSFS 2024 crashes to desktop when pressing ESC to return to the menu during flight.",
        causes=["Menu rendering resource leak", "WASM module not cleaning up on exit", "Cloud save write failure during pause", "Third-party add-on conflicting with menu transition"],
        fixes=["Reduce graphics settings before exiting", "Remove add-ons and test", "Clear WASM cache", "Verify MSFS files", "Run as Administrator"],
        search_terms=["escape crash", "menu crash", "esc crash", "pause crash"],
    ),
    ErrorEntry(
        id="MSFS24_005", name="MSFS 2024 Long Loading Times (10+ Minutes)",
        category="MSFS 2024", severity="medium",
        description="MSFS 2024 takes extremely long to load compared to MSFS 2020.",
        causes=["MSFS 2024 streams more content than 2020", "Slow internet connection", "Too many Community add-ons loading at startup", "HDD instead of SSD", "Insufficient RAM"],
        fixes=["Use wired Ethernet connection", "Reduce Community folder add-ons", "Install MSFS on NVMe SSD", "Ensure 32GB+ RAM", "Clear rolling cache and let it rebuild selectively"],
        search_terms=["long loading", "slow loading", "loading time", "loading 10 minutes"],
    ),
    ErrorEntry(
        id="MSFS24_006", name="MSFS 2024 Red Avatar / Identity Screen Crash",
        category="MSFS 2024", severity="high",
        description="MSFS 2024 crashes on the identity/avatar screen showing a red error avatar.",
        causes=["Cloud save corruption", "Microsoft account sync issue", "Xbox Live service problem", "Corrupted user profile data"],
        fixes=["Delete cloud save completely and let it re-sync", "Sign out and sign back into Microsoft account", "Check Xbox Live service status", "Reinstall MSFS and delete all local data"],
        search_terms=["red avatar", "identity crash", "avatar error", "red face crash"],
    ),
    ErrorEntry(
        id="MSFS24_007", name="MSFS 2024 Spawning Inside Buildings",
        category="MSFS 2024", severity="medium",
        description="MSFS 2024 spawns the aircraft inside buildings or underground at startup.",
        causes=["Scenery data loading error", "Airport elevation data corruption", "GPS position initialization failure", "Cloud save position data corrupted"],
        fixes=["Restart the flight", "Clear SceneryIndexes folder", "Delete cloud save position data", "Try a different departure airport", "Verify MSFS files"],
        search_terms=["spawn inside building", "underground spawn", "building spawn", "spawn error"],
    ),
    ErrorEntry(
        id="MSFS24_008", name="MSFS 2024 Checking for Updates Loop",
        category="MSFS 2024", severity="high",
        description="MSFS 2024 is stuck in an infinite 'Checking for Updates' loop.",
        causes=["Microsoft Store cache corruption", "Xbox Game Services stuck", "Internet connection issue during update check", "MSFS installation incomplete"],
        fixes=["Reset Xbox Game Services", "Clear Microsoft Store cache: wsreset.exe", "Sign out and sign back into Microsoft Store", "Repair MSFS from Settings > Apps", "Restart computer and try again"],
        search_terms=["checking for updates", "update loop", "infinite update", "updates loop"],
    ),
    ErrorEntry(
        id="MSFS24_009", name="MSFS 2024 Missing Aircraft from Library",
        category="MSFS 2024", severity="medium",
        description="Aircraft that should be available are missing from the in-game library.",
        causes=["Marketplace entitlement not syncing", "Xbox Game Pass content not loading", "Cloud save not reflecting purchases", "Installation incomplete"],
        fixes=["Sign out and sign back into Microsoft account", "Check Xbox Game Pass subscription status", "Repair MSFS from Settings > Apps", "Wait for Marketplace sync (can take hours)", "Contact Xbox support for entitlement issues"],
        search_terms=["missing aircraft", "aircraft not available", "library missing", "aircraft gone"],
    ),

    # ============================================================
    # LONG FLIGHT / EXTENDED SESSION ISSUES
    # ============================================================
    ErrorEntry(
        id="EXT_001", name="CTD After Extended Flight (2+ Hours)",
        category="Extended Flight", severity="high",
        description="MSFS crashes to desktop after flying for 2+ hours without warning.",
        causes=["Memory leak accumulating over time", "VRAM fragmentation causing allocation failure", "GPU overheating from sustained load", "Page file filling up", "Rolling cache corruption during long session"],
        fixes=["Set frame rate limit to 30 or 60", "Restart MSFS between long flights", "Monitor GPU temperature during flight", "Increase page file size", "Lower texture resolution to reduce VRAM pressure", "Disable rolling cache for long flights"],
        search_terms=["long flight crash", "2 hour crash", "extended flight ctd", "long haul crash"],
    ),
    ErrorEntry(
        id="EXT_002", name="MSFS Freezes but Sound Continues",
        category="Extended Flight", severity="high",
        description="MSFS display freezes completely but audio continues playing in the background.",
        causes=["GPU driver timeout (TDR)", "DXGI swap chain hang", "WASM module deadlock", "Render thread blocked by add-on"],
        fixes=["Wait 30 seconds for potential recovery", "ALT+Tab out and back in", "Disable overlays", "Update GPU drivers", "Remove add-ons and test in halves"],
        search_terms=["freeze sound continues", "audio continues freeze", "display freeze audio", "hang sound"],
    ),
    ErrorEntry(
        id="EXT_003", name="MSFS Stuck on Pause / Unresponsive After Menu Return",
        category="Extended Flight", severity="medium",
        description="MSFS becomes unresponsive after returning from pause menu mid-flight.",
        causes=["Menu overlay resource conflict", "WASM module not resuming properly", "Cloud sync during pause", "Third-party overlay conflicting"],
        fixes=["Wait 60 seconds for recovery", "ALT+Tab and return", "Disable overlays", "Reduce graphics settings", "Remove add-ons"],
        search_terms=["pause unresponsive", "menu return freeze", "pause menu crash"],
    ),

    # ============================================================
    # INPUT / PERIPHERAL ISSUES
    # ============================================================
    ErrorEntry(
        id="INPUT_001", name="Joystick/Controller Disconnects During Flight",
        category="Input", severity="medium",
        description="USB joystick or controller disconnects and reconnects randomly during flight.",
        causes=["USB power management turning off device", "Insufficient USB power", "USB hub issue", "Controller driver problem"],
        fixes=["Disable USB selective suspend: Power Options > Change plan settings > Change advanced > USB > Disable", "Plug controller directly into motherboard USB port (not hub)", "Update controller drivers", "Try different USB port", "Use powered USB hub for high-power devices"],
        search_terms=["joystick disconnect", "controller disconnect", "usb disconnect", "input lost"],
    ),
    ErrorEntry(
        id="INPUT_002", name="Throttle/Axis Calibration Drift",
        category="Input", severity="low",
        description="Analog axes (throttle, joystick) drift or don't respond correctly after calibration.",
        causes=["Dirty potentiometer in controller", "Windows calibration conflicting with MSFS calibration", "Deadzone settings incorrect", "Controller firmware issue"],
        fixes=["Calibrate in Windows Game Controllers first, then fine-tune in MSFS", "Increase deadzone in MSFS controls settings", "Clean potentiometer with contact cleaner", "Update controller firmware", "Create new MSFS control profile"],
        search_terms=["axis drift", "throttle drift", "calibration", "deadzone"],
    ),
    ErrorEntry(
        id="INPUT_003", name="Input Lag / Delayed Response",
        category="Input", severity="medium",
        description="Noticeable delay between physical input and MSFS response.",
        causes=["VSync causing input delay", "NVIDIA Reflex not enabled", "USB polling rate too low", "Frame rate too low causing perceived lag", "Background processes consuming CPU"],
        fixes=["Enable NVIDIA Reflex Low Latency in MSFS settings", "Disable VSync or use G-SYNC", "Set USB polling rate to 1000Hz in controller software", "Limit FPS to reduce frame time variance", "Close background CPU-heavy applications"],
        search_terms=["input lag", "delayed input", "controller delay", "responsiveness"],
    ),

    # ============================================================
    # VISUAL GLITCHES / RENDERING ISSUES
    # ============================================================
    ErrorEntry(
        id="VIS_001", name="Texture Flickering / Z-Fighting",
        category="Visual", severity="low",
        description="Textures flickering or fighting for display priority, especially on ground surfaces.",
        causes=["Terrain LOD too low causing distant texture conflicts", "Photogrammetry conflicting with default scenery", "Graphics driver bug", "MSFS rendering precision issue"],
        fixes=["Increase Terrain LOD to 150-200", "Enable Terrain Correction in NVIDIA Control Panel", "Update GPU drivers", "Disable photogrammetry for affected area", "Set Texture Supersampling to 4x4 or higher"],
        search_terms=["texture flickering", "z-fighting", "flickering textures", "ground flicker"],
    ),
    ErrorEntry(
        id="VIS_002", name="White / Black Textures Loading",
        category="Visual", severity="medium",
        description="Textures appear white or black instead of rendering correctly.",
        causes=["VRAM overflow causing texture load failure", "Streaming content not downloading", "Corrupted texture cache", "Internet connection issue during streaming"],
        fixes=["Lower texture resolution", "Clear rolling cache", "Check internet connection", "Pre-download scenery for the area", "Restart MSFS"],
        search_terms=["white texture", "black texture", "texture not loading", "missing texture"],
    ),
    ErrorEntry(
        id="VIS_003", name="Water Rendering Glitches",
        category="Visual", severity="low",
        description="Water appears with incorrect colors, patterns, or rendering artifacts.",
        causes=["Water Waves setting too high for GPU", "Reflection settings conflict", "Driver bug with water shaders", "Photogrammetry water mask conflict"],
        fixes=["Lower Water Waves setting", "Reduce Raymarched Reflections", "Update GPU drivers", "Disable photogrammetry near coastlines"],
        search_terms=["water glitch", "water render", "ocean glitch", "water artifact"],
    ),
    ErrorEntry(
        id="VIS_004", name="Cockpit Instruments Not Rendering",
        category="Visual", severity="high",
        description="Glass cockpit displays (PFD, ND, MCDU) show black, orange, or blank screens.",
        causes=["WASM module crashed (orange screen)", "Panel.cfg misconfiguration in add-on", "Coherent GT engine failure", "Display refresh rate issue"],
        fixes=["Restart the flight", "Clear WASM cache", "Update add-on to latest version", "Increase Glass Cockpit Refresh Rate setting", "Remove and reinstall add-on aircraft"],
        search_terms=["instrument black", "pfd blank", "nd blank", "glass cockpit", "mcdu blank"],
    ),
    ErrorEntry(
        id="VIS_005", name="Cloud Rendering Artifacts",
        category="Visual", severity="low",
        description="Volumetric clouds show banding, blocky patterns, or color artifacts.",
        causes=["Volumetric Clouds setting too low", "DLSS/FSR upscaling artifacts on clouds", "Driver bug with cloud shaders", "Weather data loading issue"],
        fixes=["Increase Volumetric Clouds quality", "Switch to TAA temporarily to test", "Update GPU drivers", "Try different weather preset", "Restart MSFS"],
        search_terms=["cloud artifact", "cloud banding", "cloud render", "cloud blocky"],
    ),
    ErrorEntry(
        id="VIS_006", name="Photogrammetry Buildings Floating / Misplaced",
        category="Visual", severity="medium",
        description="Photogrammetry 3D buildings appear floating above ground or misaligned.",
        causes=["Elevation data mismatch", "Streaming content incomplete", "GPS position error", "Terrain mesh corruption"],
        fixes=["Clear SceneryIndexes folder", "Restart MSFS to re-download scenery", "Disable photogrammetry for affected city", "Fly at higher altitude to force re-download"],
        search_terms=["photogrammetry floating", "building floating", "3d building misplaced", "photogrammetry error"],
    ),

    # ============================================================
    # AUDIO ISSUES (expanded)
    # ============================================================
    ErrorEntry(
        id="AUDIO_004", name="Engine Sound Cuts Out at Altitude",
        category="Audio", severity="low",
        description="Engine sounds disappear or become silent at high altitude.",
        causes=["Sound cone/directional settings", "Cockpit sound zone configuration", "Add-on aircraft sound file issue"],
        fixes=["Adjust cockpit camera position", "Check sound settings in assistances", "Update aircraft add-on", "Restart flight"],
        search_terms=["sound cuts out", "engine silent", "sound altitude", "sound disappears"],
    ),
    ErrorEntry(
        id="AUDIO_005", name="Wind Noise Too Loud / Overpowering",
        category="Audio", severity="low",
        description="Wind noise is excessively loud compared to other sounds.",
        causes=["MSFS 2024 sound mix issue", "Cockpit sound insulation setting", "Aircraft sound file configuration"],
        fixes=["Adjust environmental sound volume in MSFS audio settings", "Reduce wind volume slider", "Check add-on aircraft sound configuration", "Use different aircraft to test"],
        search_terms=["wind noise loud", "wind overpowering", "wind sound", "noise level"],
    ),

    # ============================================================
    # NETWORK / MULTIPLAYER (expanded)
    # ============================================================
    ErrorEntry(
        id="NET_005", name="Live Weather Not Loading",
        category="Network", severity="low",
        description="Live weather shows default clear sky instead of real weather data.",
        causes=["Weather data server issue", "Internet connection problem", "Weather API timeout", "MSFS data connection setting too low"],
        fixes=["Check internet connection", "Increase Data Connection bandwidth setting", "Restart MSFS", "Try switching between live weather and preset, then back", "Wait and retry (server issue)"],
        search_terms=["live weather not loading", "weather default", "no live weather", "weather stuck"],
    ),
    ErrorEntry(
        id="NET_006", name="Live Traffic / ATC Not Working",
        category="Network", severity="low",
        description="AI traffic and ATC services are not functioning despite being enabled.",
        causes=["Multiplayer settings not configured", "Data connection limited", "ATC voice synthesis not installed", "Server connectivity issue"],
        fixes=["Enable AI Traffic in MSFS settings", "Check Data Connection settings", "Install Windows Speech voices for ATC", "Verify Xbox Live connection"],
        search_terms=["live traffic", "atc not working", "ai traffic", "no traffic"],
    ),

    # ============================================================
    # ADDITIONAL ADD-ON ISSUES
    # ============================================================
    ErrorEntry(
        id="MOD_009", name="PMDG Aircraft WASM Crash (Orange Screens)",
        category="Add-ons", severity="high",
        description="PMDG aircraft (737, 777, 747) show orange screens and WASM module crashes.",
        causes=["PMDG WASM module needs recompilation after sim update", "Nav database outdated", "WASM cache corrupted", "PMDG version incompatible with current MSFS version"],
        fixes=["Delete WASM cache folder for the specific PMDG aircraft", "Update PMDG to latest version from PMDG Operations Center", "Update navigation data", "Start MSFS in Safe Mode for full WASM recompile", "Reinstall PMDG aircraft completely"],
        search_terms=["pmdg wasm", "pmdg orange", "pmdg crash", "pmdg 737 crash"],
    ),
    ErrorEntry(
        id="MOD_010", name="Fenix A320 Crash / Black Displays",
        category="Add-ons", severity="high",
        description="Fenix A320 shows black displays or crashes to desktop.",
        causes=["Fenix software version incompatible with MSFS version", "SimConnect connection failure", "Fenix background service not running", "WASM module crash"],
        fixes=["Update Fenix A320 to latest version", "Restart Fenix application", "Check Fenix requirements (separate installer)", "Clear WASM cache", "Reinstall Fenix completely"],
        search_terms=["fenix crash", "fenix a320", "fenix black displays", "fenix simconnect"],
    ),
    ErrorEntry(
        id="MOD_011", name="iniBuilds A350/A380 WASM Crash",
        category="Add-ons", severity="high",
        description="iniBuilds aircraft WASM module crashes, especially after sim updates.",
        causes=["iniBuilds WASM module incompatible with current MSFS version", "Nav data update required", "WASM cache stale"],
        fixes=["Clear WASM cache: delete microsoft-aircraft-a350 or a380 folder in WASM cache", "Update iniBuilds aircraft to latest version", "Start MSFS in Safe Mode", "Reinstall aircraft"],
        search_terms=["inibuilds wasm", "inibuilds crash", "a350 crash", "a380 crash"],
    ),
    ErrorEntry(
        id="MOD_012", name="GSX Pro Couatl64 Crash",
        category="Add-ons", severity="medium",
        description="GSX Pro (Couatl64_MSFS.exe) crashes with ntdll.dll or clr.dll errors.",
        causes=["Couatl64 .NET runtime error", "GSX version incompatible with MSFS", "GSX configuration corrupted", ".NET Framework issue"],
        fixes=["Update GSX Pro to latest version", "Run .NET Framework Repair Tool", "Clear GSX cache and reconfigure", "Reinstall GSX Pro", "Check GSX forum for MSFS 2024 compatibility"],
        search_terms=["gsx crash", "couatl64", "gsx pro", "couatl crash"],
    ),
    ErrorEntry(
        id="MOD_013", name="FBW (FlyByWire) A380X / A32NX Crash",
        category="Add-ons", severity="high",
        description="FlyByWire aircraft crashing or showing errors.",
        causes=["FBW version incompatible with MSFS version", "WASM module build mismatch", "SimBrief import failing", "Community folder conflict"],
        fixes=["Update FBW to latest dev or stable version", "Clear WASM cache for FBW", "Remove other add-ons that might conflict", "Check FBW Discord for known issues", "Reinstall FBW completely"],
        search_terms=["fbw crash", "flybywire", "a380x crash", "a32nx crash"],
    ),
    ErrorEntry(
        id="MOD_014", name="FSUIPC Crash / Conflict",
        category="Add-ons", severity="medium",
        description="FSUIPC causes crashes or conflicts with MSFS.",
        causes=["FSUIPC version incompatible", "FSUIPC WASM module issue", "Conflict with other SimConnect add-ons"],
        fixes=["Update FSUIPC to latest version", "Disable FSUIPC WASM module temporarily", "Check FSUIPC forum for MSFS 2024 compatibility", "Remove FSUIPC and test"],
        search_terms=["fsuipc crash", "fsuipc conflict", "fsuipc wasm"],
    ),
    ErrorEntry(
        id="MOD_015", name="VATSIM / IVAO Client Crash",
        category="Add-ons", severity="medium",
        description="VATSIM or IVAO online flying client causes MSFS to crash.",
        causes=["Client version incompatible with MSFS", "SimConnect conflict", "Network client hooking into sim incorrectly"],
        fixes=["Update VATSIM/IVAO client to latest version", "Check client compatibility with MSFS 2024", "Use vPilot or SWIFT as alternative", "Remove client and test"],
        search_terms=["vatsim crash", "ivao crash", "online flying crash", "vatsim ctd"],
    ),

    # ============================================================
    # ADDITIONAL DLL CRASHES (from web research)
    # ============================================================
    ErrorEntry(
        id="DLL_011", name="ntdll.dll Heap Corruption (0xc0000374)",
        category="Runtime DLL", severity="critical",
        description="Heap corruption in ntdll.dll causing crash. Very common in MSFS 2020/2024. Often triggered by add-ons or system memory issues.",
        causes=["Corrupted heap memory", "Incompatible add-on (CouATL64_MSFS.exe / GSX)", "Out of memory / pagefile too small", "Faulty RAM causing memory corruption", "Antivirus hooking into process memory", "DLL version mismatch"],
        fixes=["Increase pagefile size (set to system managed or 32GB+)", "Update GSX Pro to latest version", "Run Windows Memory Diagnostic (mdsched.exe)", "Disable antivirus real-time protection temporarily", "Run sfc /scannow and DISM repair", "Clear MSFS rolling cache", "Disable all Community add-ons and test"],
        search_terms=["ntdll.dll", "0xc0000374", "heap corruption", "couatl64", "heap alloc"],
        related_dlls=["ntdll.dll", "couatl64_MSFS.exe"], related_codes=["0xc0000374"],
    ),
    ErrorEntry(
        id="DLL_011", name="bad_module_info Crash",
        category="Application", severity="high",
        description="MSFS crashes with faulting module name 'bad_module_info'. This indicates a corrupted executable or Windows App package issue.",
        causes=["Corrupted MSFS installation files", "Windows Store / Xbox App cache corruption", "Incomplete Windows update", "Antivirus quarantining MSFS files", "User profile corruption"],
        fixes=["Repair MSFS via Windows Settings > Apps > Microsoft Flight Simulator > Advanced options > Repair", "Run wsreset.exe to reset Windows Store cache", "Re-register MSFS: PowerShell as admin: Get-AppxPackage Microsoft.Limitless | Reset-AppxPackage", "Uninstall and reinstall MSFS", "Create a new Windows user profile and test", "Add MSFS folder to antivirus exclusions"],
        search_terms=["bad_module_info", "bad module", "faulting module name bad_module_info"],
        related_dlls=["bad_module_info"],
    ),
    ErrorEntry(
        id="DLL_012", name="d2d1.dll Crash",
        category="Runtime DLL", severity="medium",
        description="Direct2D graphics library crash. Used for 2D rendering in MSFS UI elements.",
        causes=["GPU driver incompatibility with Direct2D", "Windows graphics subsystem corruption", "Multi-monitor DPI scaling conflict", "Corrupted MSFS UI resources"],
        fixes=["Update GPU drivers", "Set MSFS to run at native resolution", "Disable DPI scaling for MSFS.exe (Properties > Compatibility > Change high DPI settings)", "Run sfc /scannow to repair system files", "Disable fullscreen optimizations"],
        search_terms=["d2d1.dll", "d2d1", "direct2d crash"],
        related_dlls=["d2d1.dll"],
    ),
    ErrorEntry(
        id="DLL_013", name="wmphoto.dll / napinsp.dll Crash",
        category="Runtime DLL", severity="low",
        description="Windows Media Photo or Name Resolution DLL crash. Typically a Windows system file issue, not MSFS-specific.",
        causes=["Windows system file corruption", "Outdated Windows version", "Broken Windows feature installation"],
        fixes=["Run sfc /scannow as administrator", "Run DISM /Online /Cleanup-Image /RestoreHealth", "Install all Windows Updates", "Repair Visual C++ Redistributables"],
        search_terms=["wmphoto.dll", "napinsp.dll", "windows photo crash", "name resolution"],
        related_dlls=["wmphoto.dll", "napinsp.dll"],
    ),
    ErrorEntry(
        id="DLL_014", name="nvrtum64.dll Crash",
        category="GPU/Driver", severity="high",
        description="NVIDIA RTX Unified Module crash. Related to NVIDIA RTX features (ray tracing, DLSS).",
        causes=["NVIDIA driver corruption", "DLSS component issue", "Ray tracing settings too aggressive", "GPU VRAM exhaustion during RT operations"],
        fixes=["Clean-install NVIDIA drivers with DDU", "Disable ray tracing in MSFS temporarily", "Update DLSS via NVIDIA App or manually", "Lower render resolution", "Monitor VRAM usage"],
        search_terms=["nvrtum64.dll", "nvrtum", "nvidia rtx crash", "rtx module"],
        related_dlls=["nvrtum64.dll"],
    ),
    ErrorEntry(
        id="DLL_015", name="dwm.exe (Desktop Window Manager) Crash",
        category="System", severity="critical",
        description="Windows Desktop Window Manager crashes. Can be caused by MSFS pushing GPU beyond stable limits.",
        causes=["GPU driver crash propagating to DWM", "GPU unstable overclock/undervolt", "GPU hardware failure", "Windows composition issue", "HDR/Display configuration problem"],
        fixes=["Update GPU drivers", "Remove GPU overclocks", "Disable HDR in Windows Settings", "Set MSFS to borderless windowed mode", "Increase TDR timeout in registry", "Check GPU power connectors are secure", "Test with different monitor/cable"],
        search_terms=["dwm.exe", "desktop window manager", "dwm crash", "dwm stopped working"],
        related_dlls=["dwm.exe", "dwmcore.dll"],
    ),
    ErrorEntry(
        id="DLL_016", name="simprop.dll Crash",
        category="Application", severity="medium",
        description="MSFS simulation properties DLL crash. Handles aircraft configuration and simulation variables.",
        causes=["Corrupted aircraft configuration", "Add-on aircraft with invalid properties", "WASM module corruption", "SimUpdate changed simulation properties format"],
        fixes=["Clear WASM cache", "Reset MSFS usercfg.opt to defaults", "Remove recently installed add-ons", "Run MSFS in Safe Mode (hold Ctrl+Shift while starting)", "Reinstall MSFS"],
        search_terms=["simprop.dll", "simprop", "simulation properties"],
        related_dlls=["simprop.dll"],
    ),
    ErrorEntry(
        id="DLL_017", name="0xc00000fd Stack Overflow",
        category="Application", severity="high",
        description="Stack overflow exception (0xc00000fd). Usually indicates a recursive loop in code or add-on WASM module.",
        causes=["Add-on WASM module infinite loop", "Corrupted aircraft gauge code", "Recursive SimConnect callback", "Faulty scenery package triggering infinite recursion"],
        fixes=["Remove recently installed add-ons", "Clear WASM cache and let modules recompile", "Update all add-ons to latest versions", "Start MSFS in Safe Mode to test", "Check add-on developer forums for known issues"],
        search_terms=["0xc00000fd", "stack overflow", "exception 0xc00000fd"],
        related_codes=["0xc00000fd"],
    ),
    ErrorEntry(
        id="DLL_018", name="CoherentUIGT.dll / CoherentGT.dll Crash",
        category="Application", severity="high",
        description="Coherent GT JavaScript engine crash. Used for MSFS in-sim panels, checklists, and add-on UI. Known heap allocation bug in version 2.9.5.0.",
        causes=["Known Coherent GT 2.9.5.0 heap corruption bug", "Add-on corrupting Coherent memory allocation", "MSFS WASM module conflicting with Coherent", "Multiple add-ons loading Coherent panels simultaneously"],
        fixes=["Reduce number of add-ons using in-sim panels", "Clear WASM cache completely", "Update add-ons to latest versions (developers may have workarounds)", "Await Asobo fix for Coherent 2.9.5.0 heap bug", "Start MSFS in Safe Mode", "Report to MSFS DevSupport with crash logs"],
        search_terms=["CoherentUIGT", "CoherentGT", "coherentgtjs", "coherent crash", "coherent gt", "coherent dll"],
        related_dlls=["CoherentUIGT.dll", "CoherentGT.dll", "CoherentGTJS.dll"],
    ),
    ErrorEntry(
        id="DLL_019", name="Unknown Module with 0xffffffffffffffff Offset",
        category="Application", severity="high",
        description="MSFS crashes with 'unknown' faulting module and fault offset 0xffffffffffffffff. Indicates the crash is in MSFS's own code but symbol resolution failed.",
        causes=["MSFS internal engine crash", "Memory corruption from add-ons", "Out of memory", "Corrupted MSFS installation", "Flight at specific problematic airport/scenery"],
        fixes=["Clear MSFS rolling cache", "Lower texture resolution and render scale", "Increase pagefile size", "Remove all Community add-ons and test", "Reinstall MSFS", "Try a different departure/arrival airport", "Report to MSFS DevSupport with full crash log"],
        search_terms=["unknown module", "0xffffffffffffffff", "fault offset ffffffff", "unknown faulting module"],
        related_dlls=["unknown"], related_codes=["0xffffffffffffffff"],
    ),
    ErrorEntry(
        id="SYSTEM_009", name="LiveKernelEvent 193 (Hardware Error)",
        category="System", severity="critical",
        description="Windows LiveKernelEvent code 193 with parameter 810. Indicates a hardware-level GPU failure during MSFS operation.",
        causes=["GPU hardware failure", "GPU driver crash at kernel level", "Unstable GPU undervolt/overclock", "Failing GPU VRAM", "Insufficient GPU power delivery", "Unstable PBO (Precision Boost Overdrive) on CPU"],
        fixes=["Remove all GPU and CPU overclocks", "Update GPU drivers with DDU clean install", "Monitor GPU temperature and hotspot", "Run FurMark or 3DMark stress test", "Check GPU power connectors", "Test GPU in another system", "RMA GPU if persistent"],
        search_terms=["LiveKernelEvent", "193", "hardware error", "kernel event 193"],
        related_codes=["LiveKernelEvent 193", "Code 193"],
    ),
    ErrorEntry(
        id="DLL_020", name="DLSS Frame Generation + Avionics Pop-Out CTD",
        category="GPU/Driver", severity="high",
        description="MSFS crashes to desktop when popping out avionics/instruments to a second window while DLSS Frame Generation is enabled.",
        causes=["DLSS Frame Generation incompatible with pop-out windows", "NVIDIA driver bug with multi-window + FG", "GPU memory management issue with FG + additional render target"],
        fixes=["Disable DLSS Frame Generation before popping out instruments", "Use TAA instead of DLSS when using pop-out windows", "Update NVIDIA drivers to latest version", "Use a single monitor setup", "Pop out instruments before enabling FG"],
        search_terms=["dlss frame generation crash", "pop out crash", "avionics crash", "dlss fg ctd", "instrument popout"],
        related_dlls=["nvwgf2umx.dll"],
    ),
    ErrorEntry(
        id="SYSTEM_010", name="Intel HD Graphics Conflict (Dual GPU)",
        category="System", severity="high",
        description="MSFS crashes when both Intel HD Graphics (iGPU) and dedicated GPU are active. MSFS may try to use the iGPU for rendering.",
        causes=["MSFS detecting Intel HD Graphics and selecting it as render device", "BIOS set to auto-select GPU (not forcing dedicated GPU)", "Driver conflict between Intel and NVIDIA/AMD drivers"],
        fixes=["Disable Intel HD Graphics in Device Manager or BIOS", "Set BIOS to 'Discrete Graphics' or 'PCIe' mode", "In NVIDIA Control Panel, set MSFS to use high-performance GPU", "Update Intel Graphics drivers", "Disable iGPU in BIOS if not needed for display output"],
        search_terms=["intel hd graphics crash", "dual gpu", "igpu conflict", "intel graphics crash", "integrated gpu"],
        related_dlls=["igdumdim64.dll", "igd10um64.dll"],
    ),
    ErrorEntry(
        id="GPU_008", name="dxgkrnl.sys BSOD (VIDEO_DXGKRNL_FATAL_ERROR)",
        category="GPU/Driver", severity="critical",
        description="Blue Screen of Death with dxgkrnl.sys. DirectX Graphics Kernel detected a fatal violation. System crashes to blue screen and restarts.",
        causes=["NVIDIA driver crash at kernel level", "GPU hardware failure", "Unstable GPU overclock/undervolt", "GPU power delivery issue", "Faulty GPU VRAM"],
        fixes=["Clean-install NVIDIA drivers with DDU in Safe Mode", "Remove all GPU overclocks", "Update BIOS and chipset drivers", "Check GPU power connectors", "Run GPU stress test (FurMark) to isolate hardware vs driver", "Try previous stable driver version"],
        search_terms=["dxgkrnl", "dxgkrnl.sys", "video_dxgkrnl_fatal_error", "bugcheck 113"],
        related_dlls=["dxgkrnl.sys"], related_codes=["0x00000113"],
    ),
    ErrorEntry(
        id="GPU_009", name="watchdog.sys BSOD",
        category="GPU/Driver", severity="critical",
        description="Blue Screen of Death with watchdog.sys. Windows display watchdog detected the GPU stopped responding.",
        causes=["GPU driver hang/TDR timeout exceeded", "GPU hardware failure", "Unstable GPU clocks", "Power supply issue to GPU"],
        fixes=["Increase TDR timeout in registry (TdrDelay)", "Clean-install GPU drivers", "Remove GPU overclocks", "Check PSU wattage and GPU power cables", "Test GPU in another system"],
        search_terms=["watchdog.sys", "watchdog", "video_tdr_watchdog"],
        related_dlls=["watchdog.sys"],
    ),
    ErrorEntry(
        id="DLL_021", name="MSVCP140.dll / VCRUNTIME140.dll Missing",
        category="Runtime DLL", severity="high",
        description="MSFS fails to start because MSVCP140.dll or VCRUNTIME140.dll is missing. Common after Windows reset or fresh install.",
        causes=["Missing or corrupted Visual C++ Redistributable", "Windows reset/reinstall without restoring VC++ packages", "Corrupted VC++ installation", "Wrong architecture (32-bit vs 64-bit)"],
        fixes=["Install both x86 AND x64 Visual C++ Redistributable 2015-2022 from microsoft.com", "Repair existing VC++ installations via Programs & Features", "Download directly from: aka.ms/vs/17/release/vc_redist.x64.exe", "Run sfc /scannow to repair system files", "Reinstall MSFS after installing VC++ packages"],
        search_terms=["msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll", "msvcp140", "vcruntime missing"],
        related_dlls=["msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"],
    ),
    ErrorEntry(
        id="GPU_010", name="Event ID 14 nvlddmkm Display Driver Error",
        category="GPU/Driver", severity="high",
        description="NVIDIA display driver error Event ID 14. 'The description for this event cannot be found.' Usually followed by TDR crash or black screen.",
        causes=["NVIDIA driver corruption", "GPU hardware issue", "VRAM failure", "Driver version incompatible with Windows version", "Overheating GPU"],
        fixes=["Clean-install NVIDIA drivers using DDU in Safe Mode", "Check GPU temperature", "Run VRAM stress test (OCCT or MemtestG80)", "Update Windows to latest version", "Try previous NVIDIA driver version"],
        search_terms=["event id 14", "nvlddmkm event 14", "description for this event cannot be found nvlddmkm"],
        related_dlls=["nvlddmkm.sys"],
    ),

    # ============================================================
    # INSTALL / LAUNCH ISSUES
    # ============================================================
    ErrorEntry(
        id="INSTALL_001", name="Stuck on 'Checking for Updates' Loop",
        category="Install/Launch", severity="high",
        description="MSFS gets stuck in an infinite 'Checking for Updates' loop and never launches.",
        causes=["Corrupted content manager cache", "Stale Official packages", "Server connection issue", "Windows Store cache corruption"],
        fixes=["Delete leftover Official package folders older than the current update", "Run wsreset.exe to reset Windows Store cache", "Restart sim and PC", "Sign out and back into Microsoft account", "Check MSFS server status"],
        search_terms=["checking for updates", "update loop", "stuck updating", "checking updates"],
    ),
    ErrorEntry(
        id="INSTALL_002", name="Loading Screen Stuck at 97-98%",
        category="Install/Launch", severity="high",
        description="MSFS loading screen freezes at 97-98% without crashing. Non-crash error.",
        causes=["Clock/timezone desync", "Install on non-C: drive", "Corrupted content cache", "Server-side package state stuck"],
        fixes=["Sync Windows clock and region automatically", "Move install to C: drive", "Delete and rebuild rolling cache", "Wait and retry off-peak", "Force-close and relaunch"],
        search_terms=["stuck 97", "stuck 98", "loading stuck", "loading 97%", "loading 98%"],
    ),
    ErrorEntry(
        id="INSTALL_003", name="Sim Crashes/Hangs on Loading Screen",
        category="Install/Launch", severity="critical",
        description="MSFS crashes or hangs during the loading screen before reaching the main menu.",
        causes=["Background app interference", "Corrupted user profile", "Non-English Windows locale", "Corrupted fs-base package files"],
        fixes=["Restore to vanilla state (empty Community folder)", "Set system locale to English (US) in Control Panel > Region > Administrative", "Create a new Windows profile without special characters", "Run sfc /scannow and DISM", "Delete fs-base folders to force re-download"],
        search_terms=["crash loading screen", "hang loading", "loading screen crash", "stuck loading"],
    ),
    ErrorEntry(
        id="INSTALL_004", name="Deluxe/Premium Content Missing on First Launch",
        category="Install/Launch", severity="medium",
        description="Additional or deluxe edition content is missing when first launching MSFS 2024.",
        causes=["Entitlement sync delay", "Microsoft account not fully authenticated", "Content not yet downloaded"],
        fixes=["Close and relaunch the game", "Sign out and back into Microsoft account", "Check My Library for per-item enable/disable status", "Contact support if persistent"],
        search_terms=["deluxe content missing", "premium content missing", "edition content missing", "dlc missing"],
    ),
    ErrorEntry(
        id="INSTALL_005", name="Can't Type Login Info on First Launch (2024)",
        category="Install/Launch", severity="high",
        description="Unable to type login information on first launch of MSFS 2024.",
        causes=["USB peripheral conflict with login field", "Keyboard input not being captured"],
        fixes=["Disconnect all USB devices except mouse and keyboard", "Log in, then reconnect peripherals", "Try on-screen keyboard"],
        search_terms=["can't type login", "login keyboard", "login input not working", "login field"],
    ),
    ErrorEntry(
        id="INSTALL_006", name="Loading Issues from Old Google Mod (2020→2024)",
        category="Install/Launch", severity="medium",
        description="Loading issues traced to old 'Google Mod' from MSFS 2020 carried over to 2024.",
        causes=["Leftover hosts-file edits from 2020-era streaming mod", "Mod incompatible with 2024"],
        fixes=["Edit Windows hosts file (System32/drivers/etc/hosts) as admin and remove added entries", "Remove the mod from Community folder"],
        search_terms=["google mod", "hosts file mod", "streaming mod", "2020 mod conflict"],
    ),
    ErrorEntry(
        id="INSTALL_007", name="Install/Update Fails or Write Errors",
        category="Install/Launch", severity="high",
        description="MSFS installation or update fails with write permission errors.",
        causes=["Antivirus/Defender blocking", "Permission issues", "Disk full", "Corrupted download"],
        fixes=["Add install folder to AV exclusions", "Run installer as admin", "Check disk space", "Clear Windows Store cache"],
        search_terms=["install fail", "update fail", "write error", "permission error", "installation error"],
    ),
    ErrorEntry(
        id="INSTALL_008", name="3rd-Party 2020 Add-ons Block Entry After Port (2024)",
        category="Install/Launch", severity="high",
        description="Third-party MSFS 2020 add-ons block simulator entry after backward-compatibility port to 2024.",
        causes=["Incompatible legacy add-on content newly enabled in 2024", "Add-on not rebuilt for 2024"],
        fixes=["Temporarily disable/uninstall ported non-aircraft add-ons", "Use per-item content enable/disable in My Library", "Check vendor site for 2024-specific build"],
        search_terms=["2020 addon block", "legacy addon", "backward compatibility", "addon blocks entry"],
    ),
    ErrorEntry(
        id="INSTALL_009", name="Stuck at 'VFS Activating Packages' / 'Loading Languages' (2024)",
        category="Install/Launch", severity="high",
        description="MSFS 2024 stuck at X% 'VFS Activating Packages' or 'Loading Languages' on startup.",
        causes=["Server-side load at launch/major update", "Corrupted content cache", "Large number of add-ons"],
        fixes=["Wait and retry off-peak hours", "Sync system clock", "Avoid repeated restarts", "Clear rolling cache"],
        search_terms=["VFS activating", "loading languages", "stuck activating", "VFS packages"],
    ),
    ErrorEntry(
        id="INSTALL_010", name="Content Package Repeatedly Fails to Update",
        category="Install/Launch", severity="high",
        description="A specific content package (e.g. 'New Activities') repeatedly fails to update/download even after clean reinstall.",
        causes=["Server-side account/package state stuck", "Not fixable by local reinstall"],
        fixes=["Contact Microsoft/Zendesk support to reset package state", "Try on different network", "Sign out and back in"],
        search_terms=["content package fail", "update loop package", "download fails repeatedly", "package stuck"],
    ),
    ErrorEntry(
        id="INSTALL_011", name="Content Manager Stuck Downloading (2020)",
        category="Install/Launch", severity="high",
        description="Content Manager stuck downloading/looping on a specific file (e.g. pc-fs-base-bigfiles), or stuck on 'Please Wait' at launch week.",
        causes=["Content delivery/download-loop bug", "Server load at launch", "Corrupted download"],
        fixes=["Restart the app", "Delete last downloaded files in Official/OneStore folder and relaunch", "Download on second PC and copy locally", "Wait for server stabilization"],
        search_terms=["content manager stuck", "download loop", "stuck downloading", "please wait"],
    ),
    ErrorEntry(
        id="INSTALL_012", name="Silent Crash Launching from Desktop Shortcut (2020/Steam)",
        category="Install/Launch", severity="medium",
        description="MSFS silently crashes when launching directly from desktop shortcut without Steam client already open.",
        causes=["Steam client dependency", "Launch order issue"],
        fixes=["Open Steam first, then launch MSFS", "Always launch through Steam"],
        search_terms=["silent crash launch", "desktop shortcut crash", "steam launch crash"],
    ),
    ErrorEntry(
        id="INSTALL_013", name="Duplicated Community Packages After Update (2024)",
        category="Install/Launch", severity="medium",
        description="Duplicated Community packages appearing after certain update/install sequences in MSFS 2024.",
        causes=["Package-management bug", "Update sequence issue"],
        fixes=["Manually remove duplicate packages from Community folder", "Verify/repair install"],
        search_terms=["duplicated packages", "duplicate community", "packages duplicated"],
    ),
    ErrorEntry(
        id="INSTALL_014", name="Infinite Loading with WASM Aircraft After Cancel (2024)",
        category="Install/Launch", severity="high",
        description="Infinite loading screen when loading a flight with a WASM-containing aircraft after cancelling a previous WASM aircraft load.",
        causes=["WASM load/cancel state bug"],
        fixes=["Force-close and relaunch", "Clear WASM cache", "Don't cancel WASM aircraft loads"],
        search_terms=["infinite loading wasm", "wasm load cancel", "wasm aircraft stuck"],
    ),
    ErrorEntry(
        id="INSTALL_015", name="MSFS 2024 Fails on Steam Deck / Linux Proton",
        category="Install/Launch", severity="high",
        description="MSFS 2024 (Steam version) fails to launch or crashes with shader errors on Steam Deck / Linux via Proton.",
        causes=["Proton compatibility gaps with shader compilation", "Steam Deck hardware insufficient"],
        fixes=["Switch to Proton Experimental Bleeding Edge", "Add launch option DXVK_HDR=0 %command% on OLED", "Expect limited performance on Steam Deck"],
        search_terms=["steam deck", "proton", "linux crash", "shader error steam deck"],
    ),
    ErrorEntry(
        id="INSTALL_016", name="MSFS Crashes After Windows Update (2020)",
        category="Install/Launch", severity="high",
        description="MSFS crashes/hangs at ~50% load specifically after a recent Windows update. Reinstalling doesn't fix it.",
        causes=["Windows update breaking compatibility", "Driver conflict after update"],
        fixes=["Roll back Windows update", "Update GPU drivers after Windows update", "Run sfc /scannow", "Check MSFS forums for known Windows update conflicts"],
        search_terms=["crash after windows update", "windows update crash", "update broke msfs"],
    ),
    ErrorEntry(
        id="INSTALL_017", name="MS Store/Xbox App Crash at Launch Only (2024)",
        category="Install/Launch", severity="high",
        description="MSFS crashes at launch only when launched via Store/Xbox App shortcut.",
        causes=["Store launcher permission issue"],
        fixes=["Run the app as Administrator", "Try launching from Start Menu instead", "Repair MSFS via Windows Settings > Apps"],
        search_terms=["store crash", "xbox app crash", "ms store launch", "store shortcut crash"],
    ),
    ErrorEntry(
        id="INSTALL_018", name="MSFS2020 Content Fails to Transfer to MSFS 2024",
        category="Install/Launch", severity="high",
        description="Previously-owned Deluxe/Premium aircraft or MSFS2020 content fails to appear in MSFS 2024 after fresh install.",
        causes=["Backward-compatibility content porting/entitlement sync issue", "Cross-platform purchase isolation"],
        fixes=["Verify entitlements by signing into same platform/account", "Check My Library for per-item enable/disable", "Contact support if persistent"],
        search_terms=["content transfer", "2020 content missing", "premium missing 2024", "dlc transfer"],
    ),

    # ============================================================
    # CAREER MODE / MISSIONS
    # ============================================================
    ErrorEntry(
        id="CAREER_001", name="Error 308-400-00209 Crash During Career Missions (2024)",
        category="Career Mode", severity="critical",
        description="MSFS crashes with error 308-400-00209 during freelance/career missions.",
        causes=["In-flight refueling logic bug tied to mission mechanics", "308-400-00209 error code"],
        fixes=["Fully fuel before accepting mission", "Avoid combined 'repair and refuel' action", "Use fuel-only keybind instead", "Workaround documented as long-standing, no fix yet"],
        search_terms=["308-400-00209", "career crash", "freelance crash", "mission error 308"],
        related_codes=["308-400-00209"],
    ),
    ErrorEntry(
        id="CAREER_002", name="Mission Bugs After Repair and Refuel (2024)",
        category="Career Mode", severity="medium",
        description="Mission errors after using 'repair and refuel' mid-flight. Income can go negative.",
        causes=["Same refuel/repair logic bug", "Economy/reward calculation bug"],
        fixes=["Use fuel-only key bind, never the combined repair+refuel action", "Avoid combined repair+refuel during missions"],
        search_terms=["repair refuel bug", "income negative", "mission error refuel"],
    ),
    ErrorEntry(
        id="CAREER_003", name="Aircraft Fails to Spawn After 'Skip to Final' (2024)",
        category="Career Mode", severity="medium",
        description="Aircraft fails to spawn correctly after using 'skip to final' shortcut in career mode.",
        causes=["Mission-state scripting bug"],
        fixes=["Avoid the skip-to-final shortcut", "Fly the leg manually"],
        search_terms=["skip to final", "aircraft spawn fail", "career spawn"],
    ),
    ErrorEntry(
        id="CAREER_004", name="Landing Challenge Target Box at Wrong End of Runway (2024)",
        category="Career Mode", severity="medium",
        description="Landing Challenge target box appears at the wrong end of the runway, forcing an unnecessary detour.",
        causes=["Landing-target placement data regression"],
        fixes=["Fly the actual approach implied by the misplaced box", "Report airport ICAO to bug tracker"],
        search_terms=["landing challenge wrong", "target box wrong", "landing target misplaced"],
    ),
    ErrorEntry(
        id="CAREER_005", name="Landing Challenge Always Fails on Xbox",
        category="Career Mode", severity="high",
        description="Every Landing Challenge ends in Failure 100% of the time on Xbox, even landing correctly.",
        causes=["Challenge pass/fail evaluation logic bug on Xbox"],
        fixes=["No user-side fix - platform-specific evaluation bug", "Track official patch notes for Xbox-specific fix"],
        search_terms=["landing challenge fail xbox", "challenge always fails", "landing challenge broken xbox"],
    ),
    ErrorEntry(
        id="CAREER_006", name="PPL Certification Mission Soft-Lock (2024)",
        category="Career Mode", severity="critical",
        description="PPL certification mission soft-locks the entire career mode. Instructor voice loops garbled audio, HUD disappears, forced to force-quit.",
        causes=["Severe state-corruption bug tied to PPL certification mission completion/cutscene logic"],
        fixes=["No confirmed working fix - escalation-only via support ticket", "Back up save data before attempting career reset", "Career reset did not resolve for reporting user"],
        search_terms=["PPL certification", "career soft lock", "instructor voice", "career mode locked"],
    ),
    ErrorEntry(
        id="CAREER_007", name="Career Mode Immersion Bugs at Launch (2024)",
        category="Career Mode", severity="high",
        description="Cluster of career-mode bugs: NPCs clipping through aircraft, lips not moving, ATC talking over itself, penalties for implausible reasons.",
        causes=["Multiple independent launch-period bugs in career/NPC/scoring systems"],
        fixes=["No single fix - improved gradually via Sim Updates", "Expect incremental refinement via patches"],
        search_terms=["career mode bugs", "npc clipping", "npc lips", "career penalties"],
    ),
    ErrorEntry(
        id="CAREER_008", name="Airports Greyed Out in Career Mode (2024)",
        category="Career Mode", severity="low",
        description="Airports appear greyed out/unselectable when trying to start a new career.",
        causes=["Career-mode airport eligibility filter - restricted by career level/certification progress"],
        fixes=["Select from smaller/eligible airports first", "Larger airports unlock as career level progresses"],
        search_terms=["airports greyed out career", "career airport locked", "career airport unavailable"],
    ),
    ErrorEntry(
        id="CAREER_009", name="Bush Trip Achievements Broken (2020/2024)",
        category="Career Mode", severity="medium",
        description="Bush trip achievements remain broken/won't unlock even after specific patches claimed to fix them.",
        causes=["Bush-trip achievement tracking bug that has resurfaced across multiple patches"],
        fixes=["No confirmed permanent fix - check specific achievement status on current patch", "Community-maintained achievement bug list exists"],
        search_terms=["bush trip achievement", "achievement broken", "bush trip unlock"],
    ),
    ErrorEntry(
        id="CAREER_010", name="Achievement Progress Rolls Backward (Xbox)",
        category="Career Mode", severity="high",
        description="Total flight hours and achievement progress silently roll backward after certain updates, especially with Xbox Quick Resume.",
        causes=["Save-state desync between achievement tracker and actual flight-hour accumulation", "Quick Resume worsening the issue"],
        fixes=["Avoid using Xbox Quick Resume for MSFS sessions", "Fully close and reopen the sim instead", "Progress may gradually 'catch back up' over subsequent sessions"],
        search_terms=["achievement rollback", "hours rollback", "progress backward", "quick resume bug"],
    ),
    ErrorEntry(
        id="CAREER_011", name="ATC Window Doesn't Register Voice Input in Career (2024)",
        category="Career Mode", severity="high",
        description="Career mode ATC window doesn't register voice/response input, causing penalties.",
        causes=["ATC response-input handling bug in career mode"],
        fixes=["Open the ATC menu window explicitly and respond from there", "Don't rely on voice/quick-response prompts"],
        search_terms=["career atc input", "atc voice not working career", "atc response career"],
    ),
    ErrorEntry(
        id="CAREER_012", name="Aircraft Runs Out of Fuel Despite Gauge Showing Adequate (2024)",
        category="Career Mode", severity="high",
        description="Aircraft runs out of fuel mid-mission despite instruments/fuel gauge showing adequate fuel remaining.",
        causes=["Multiple contributing bugs: fuel selector defaulting to single tank, missions assigned with insufficient fuel, fuel-calculation bug from SU3"],
        fixes=["Check fuel tank selector is set to BOTH/ALL", "Manually add fuel before departure", "Bind and use 'Add Fuel' key as in-flight workaround"],
        search_terms=["fuel bug career", "fuel runs out", "fuel gauge wrong", "mission fuel"],
    ),
    ErrorEntry(
        id="CAREER_013", name="Career Mode Crashes and Visualization Errors at Launch (2024)",
        category="Career Mode", severity="high",
        description="Career-mode crashes and visualization errors during missions/activities present at launch.",
        causes=["Multiple career-mode-specific stability bugs from launch"],
        fixes=["Updated via Sim Update 1 (1.3.23.0)", "Ensure sim is on latest patch"],
        search_terms=["career crash", "career visualization", "mission crash"],
    ),
    ErrorEntry(
        id="CAREER_014", name="ATR Engine Shuts Down with 'Skip to Takeoff' in Career (2024)",
        category="Career Mode", severity="medium",
        description="ATR 42-600/72-600 engine shuts down unexpectedly when using 'Skip to Takeoff' in career mode.",
        causes=["Skip-to-X shortcut logic bug affecting engine-state initialization"],
        fixes=["Avoid using Skip to Takeoff shortcut on ATR aircraft", "Start from cold & dark manually"],
        search_terms=["atr engine shutdown", "skip to takeoff engine", "atr career engine"],
    ),
    ErrorEntry(
        id="CAREER_015", name="'My Way' Achievement Doesn't Unlock (2020)",
        category="Career Mode", severity="medium",
        description="'My Way' achievement (300+ miles, no assists) does not unlock despite multiple confirmed completions.",
        causes=["Achievement-trigger logic bug affecting this specific achievement"],
        fixes=["No user-side fix - officially logged as BUG LOGGED", "Ensure Community folder empty and Developer Mode untouched"],
        search_terms=["my way achievement", "achievement not unlocking", "my way bug"],
    ),

    # ============================================================
    # ATC / GROUND
    # ============================================================
    ErrorEntry(
        id="ATC_001", name="ATC Assigns Wrong Runway vs Wind",
        category="ATC/Ground", severity="medium",
        description="ATC assigns a runway that puts the aircraft downwind/wrong vs actual wind.",
        causes=["ATC active-runway-selection logic bug", "Specific METAR edge case", "Update regression"],
        fixes=["Manually request correct runway via ATC menu", "Report with METAR that triggered it", "No reliable user fix"],
        search_terms=["atc wrong runway", "atc downwind", "runway assignment wrong"],
    ),
    ErrorEntry(
        id="ATC_002", name="Aircraft Spawns at Wrong Runway Despite Selection",
        category="ATC/Ground", severity="medium",
        description="Aircraft spawns at the wrong runway despite selecting the correct one in Flight Setup.",
        causes=["Spawn-position logic not respecting user's runway selection"],
        fixes=["Manually taxi to the correct runway after spawning", "No consistent settings fix"],
        search_terms=["spawn wrong runway", "wrong runway spawn", "aircraft position wrong"],
    ),
    ErrorEntry(
        id="ATC_003", name="ATC Repeatedly Asks to 'Reset Transponder' / Squawk Code",
        category="ATC/Ground", severity="low",
        description="ATC repeatedly asks to 'reset transponder' or squawk code issue after starting mid-air or on runway.",
        causes=["Transponder/squawk assignment only set during full ATC clearance flow, skipped when starting mid-flight"],
        fixes=["Start from a gate/parking with full ATC flow (cold & dark)", "Manually cycle transponder if option is bound"],
        search_terms=["transponder reset", "squawk code", "atc transponder"],
    ),
    ErrorEntry(
        id="ATC_004", name="Pushback Stalls / Aircraft Won't Move After Pushback",
        category="ATC/Ground", severity="medium",
        description="Pushback stalls or aircraft won't move after pushback completes.",
        causes=["Ground-physics/brake-state desync", "Unbound brake axis read as 'ON'"],
        fixes=["Confirm chocks/parking brake are released", "Bind BOTH left and right brake axes explicitly", "Try different parking stand"],
        search_terms=["pushback stall", "won't move pushback", "pushback stuck", "aircraft won't move"],
    ),
    ErrorEntry(
        id="ATC_005", name="Aircraft Slides/Slips Unrealistically on Ground",
        category="ATC/Ground", severity="medium",
        description="Aircraft slides/slips unrealistically on the ground during taxi, takeoff roll, and landing rollout.",
        causes=["Long-standing ground-friction/inertia model limitation"],
        fixes=["No user-side fix - acknowledged long-running community request for ground physics overhaul", "Partial improvement per sim generation via patches only"],
        search_terms=["ground slide", "unrealistic ground", "taxi slide", "ground physics"],
    ),
    ErrorEntry(
        id="ATC_006", name="Rudder Auto-Recenters on Ground During Taxi",
        category="ATC/Ground", severity="medium",
        description="Rudder auto-recenters on the ground during taxi despite full pedal/stick input.",
        causes=["Control-binding/centering-spring logic bug", "Often appears after an update"],
        fixes=["Re-assign the rudder axis binding even if already set", "Reset flight to departure to test if session-specific"],
        search_terms=["rudder recenters", "rudder auto center", "rudder taxi bug"],
    ),
    ErrorEntry(
        id="ATC_007", name="GSX Ground Service Vehicle Bugs",
        category="ATC/Ground", severity="medium",
        description="GSX ground service vehicles clip/slide through aircraft, passengers walking on cockpit, marshaller wanders onto runway.",
        causes=["Multiple animation/pathing bugs in GSX initial MSFS release"],
        fixes=["Update GSX to latest version", "Report to FSDT support if persistent", "No user-side fix for underlying animation bugs"],
        search_terms=["gsx vehicle clip", "gsx passenger", "gsx marshaller", "ground service bug"],
    ),
    ErrorEntry(
        id="ATC_008", name="Brakes Completely Stuck on All Aircraft (2024)",
        category="ATC/Ground", severity="high",
        description="Brakes completely stuck/won't release on ALL aircraft. Only parking brake works. Appeared as a new issue.",
        causes=["Control-binding conflict - lost/duplicated binding after update", "Multiple commands bound to same key/axis for brakes"],
        fixes=["Open Controls setup and check for duplicate brake bindings", "Rebind brakes cleanly", "This recurs after updates that silently reset bindings"],
        search_terms=["brakes stuck", "brakes won't release", "stuck brakes all aircraft"],
    ),
    ErrorEntry(
        id="ATC_009", name="Taxi/IFR Clearance Request Broken in Career (2024)",
        category="ATC/Ground", severity="high",
        description="ATC demands an IFR clearance with no flight plan filed even in clear VFR conditions, blocking takeoff in career mode.",
        causes=["ATC clearance-state logic bug, worse in career mode"],
        fixes=["File then explicitly cancel a dummy flight plan", "Restart the flight/mission from clean state", "Switch to Free Flight avoids career-mode trigger"],
        search_terms=["ifr clearance broken", "taxi clearance", "atc clearance career"],
    ),
    ErrorEntry(
        id="ATC_010", name="Rudder Pedals Not Working at 2024 Launch",
        category="ATC/Ground", severity="high",
        description="Rudder pedals (Thrustmaster, Logitech, MFG, CH Products) register in device list but produce no rudder response.",
        causes=["2024 uses different axis-naming/detection scheme than 2020", "Sim-side axis-mapping change"],
        fixes=["Explicitly assign specific named axes (Rudder Axis, Left/Right Brake Axis)", "Check Sensitivities page confirms full range of motion", "CH Pro pedals need sensitivity set to -50%"],
        search_terms=["rudder pedals not working", "rudder no response", "pedals detected no input"],
    ),

    # ============================================================
    # REPLAY / CAMERA
    # ============================================================
    ErrorEntry(
        id="CAMERA_001", name="Drone Camera Erratic on Multiplayer Aircraft Lock (2024)",
        category="Replay/Camera", severity="medium",
        description="Drone camera view becomes completely erratic/haywire when locking onto another multiplayer aircraft.",
        causes=["Multiplayer aircraft-lock camera targeting bug, long-standing since launch"],
        fixes=["Avoid locking drone camera onto other multiplayer aircraft", "Use it on your own aircraft or static scenery"],
        search_terms=["drone camera multiplayer", "drone erratic", "drone lock aircraft"],
    ),
    ErrorEntry(
        id="CAMERA_002", name="Drone Camera Toggle One-Way / Can't Exit (2024)",
        category="Replay/Camera", severity="medium",
        description="Drone Camera Toggle keybind enters Drone mode but then can't exit. Cockpit/External View toggle keys fail.",
        causes=["Camera-mode state bug where toggle becomes one-directional"],
        fixes=["Marked Resolved on official tracker - verify sim is current", "Use Camera menu UI instead of direct keybind"],
        search_terms=["drone camera stuck", "can't exit drone", "drone toggle broken"],
    ),
    ErrorEntry(
        id="CAMERA_003", name="FlyBy Camera Greyed Out / Unavailable",
        category="Replay/Camera", severity="low",
        description="FlyBy Camera greyed out / unavailable during live flight.",
        causes=["FlyBy Camera only works during Replay mode, not Live Flight, by design"],
        fixes=["Start a Recording session first - FlyBy Camera activates only once in Replay mode"],
        search_terms=["flyby camera", "flyby unavailable", "flyby greyed"],
    ),
    ErrorEntry(
        id="CAMERA_004", name="Replay Performance Drop with Stress and Damage (2024)",
        category="Replay/Camera", severity="low",
        description="Display artifacts and performance drop while using Replay with Stress and Damage enabled.",
        causes=["Known conflict between Stress and Damage system and replay renderer"],
        fixes=["Disable Stress and Damage option before using Replay"],
        search_terms=["replay performance", "stress damage replay", "replay artifacts"],
    ),
    ErrorEntry(
        id="CAMERA_005", name="Cockpit Camera Unstable / Shaking on Its Own (2024)",
        category="Replay/Camera", severity="medium",
        description="Cockpit camera view unstable/shaking/moving on its own when sitting in pilot's seat in Free Flight.",
        causes=["Camera stabilization bug"],
        fixes=["Try resetting camera view to default keybind", "Check for FreeTrack/TrackIR software running in background"],
        search_terms=["cockpit camera shake", "camera unstable", "camera moving alone"],
    ),
    ErrorEntry(
        id="CAMERA_006", name="Drone Mode Shows Water / Aircraft Falls from Sky (2024)",
        category="Replay/Camera", severity="medium",
        description="Activating drone mode briefly shows strange water-surface image, and upon exiting drone mode the aircraft is found falling out of the sky.",
        causes=["Drone-mode entry/exit state bug affecting the aircraft's own flight state"],
        fixes=["Avoid using drone mode in critical flight phases", "Report to bug tracker"],
        search_terms=["drone water", "aircraft falls drone", "drone exit crash"],
    ),

    # ============================================================
    # DEV MODE / SDK
    # ============================================================
    ErrorEntry(
        id="SDK_001", name="Scenery Editor Crash Loading BGL/Project",
        category="Dev Mode/SDK", severity="high",
        description="MSFS crashes to desktop when loading a BGL/project in the Scenery Editor.",
        causes=["Corrupted BGL", "Stale SDK/content mismatch after update"],
        fixes=["Reinstall the SDK", "Re-verify/re-copy sim's Official folder", "Reboot after clean relaunch"],
        search_terms=["scenery editor crash", "bgl crash", "sdk scenery crash"],
    ),
    ErrorEntry(
        id="SDK_002", name="fspackagetool / Build Package Crash",
        category="Dev Mode/SDK", severity="high",
        description="fspackagetool/SDK crashes specifically when clicking 'Build Package'.",
        causes=["Too many custom objects (~125+)", "Corrupted texture in build queue"],
        fixes=["Split scenery project into smaller packages", "Verify each object/texture individually", "Reinstall SDK"],
        search_terms=["build package crash", "fspackagetool crash", "package build error"],
    ),
    ErrorEntry(
        id="SDK_003", name="SDK Crash on Value '12' in Release Notes (2024)",
        category="Dev Mode/SDK", severity="medium",
        description="SDK crash on scenery build triggered by the value '12' in release notes/project metadata.",
        causes=["Confirmed SDK parsing bug: value '12' in release notes field triggers crash"],
        fixes=["Avoid using '12' in release notes field until patched", "Officially acknowledged, fix pending"],
        search_terms=["sdk crash 12", "release notes crash", "value 12 crash"],
    ),
    ErrorEntry(
        id="SDK_004", name="Dev Mode Freezes Loading Airport Project",
        category="Dev Mode/SDK", severity="high",
        description="Dev Mode freezes/locks up when loading an airport project.",
        causes=["Rendering the full airport scene overloads Dev Mode's renderer"],
        fixes=["Move camera/avatar away from airport to remote area before loading", "Confirmed reproducible workaround"],
        search_terms=["dev mode freeze", "airport project freeze", "dev mode locked"],
    ),
    ErrorEntry(
        id="SDK_005", name="Dev Mode Completely Inoperable (2024)",
        category="Dev Mode/SDK", severity="critical",
        description="Dev Mode completely inoperable - any Dev/File/Editor menu click causes immediate crash.",
        causes=["SDK/install corruption not resolved by SDK reinstall alone"],
        fixes=["Full sim + SDK reinstall", "Report to MSFS DevSupport with RAI crash logs"],
        search_terms=["dev mode crash", "dev mode broken", "dev mode inoperable"],
    ),

    # ============================================================
    # FLIGHT PLANNING / FMS
    # ============================================================
    ErrorEntry(
        id="FPL_001", name="EFB Flight Plan Doesn't Load into Avionics (2024)",
        category="Flight Planning/FMS", severity="high",
        description="Flight plan created in EFB/World Map doesn't load into aircraft avionics (G1000/MFD), or loads incomplete.",
        causes=["Sync bug between EFB/World Map planner and aircraft avionics", "Server load", "Aircraft-dependent"],
        fixes=["Send to Avionics/ATC from EFB, then explicitly press Activate on MFD", "Start flight first, then send plan in-flight", "Report with aircraft + build number"],
        search_terms=["efb flight plan", "flight plan not loading", "plan not sync", "avionics flight plan"],
    ),
    ErrorEntry(
        id="FPL_002", name="IFR Flight Plan Reverts to VFR After Send to Avionics (2024)",
        category="Flight Planning/FMS", severity="medium",
        description="IFR flight plan reverts to/displays as VFR after being sent to avionics.",
        causes=["Flight-rule flag not persisting through EFB-to-avionics handoff"],
        fixes=["Re-select IFR explicitly after sending to avionics", "Verify in aircraft's own FMS/GPS menu"],
        search_terms=["ifr reverts vfr", "ifr flight plan bug", "flight plan type wrong"],
    ),
    ErrorEntry(
        id="FPL_003", name="Autopilot Ignores Flight Plan After NAV Engaged (2024)",
        category="Flight Planning/FMS", severity="high",
        description="Autopilot ignores the loaded flight plan and flies a different heading (e.g. straight north) after NAV engaged.",
        causes=["Flight plan not actually committed to autopilot/FMS despite appearing loaded"],
        fixes=["Load and send flight plan after starting the flight (not from pre-flight planner)", "Verify NAV source is set correctly before engaging"],
        search_terms=["autopilot ignores plan", "nav not following", "autopilot wrong heading"],
    ),
    ErrorEntry(
        id="FPL_004", name="SimBrief Import Fails / FMC Empty (2024)",
        category="Flight Planning/FMS", severity="high",
        description="SimBrief-imported flight plans fail to load: Import button does nothing, waypoints missing, FMC ends up empty.",
        causes=["Import pathway between SimBrief and in-sim EFB/FMC breaking in several ways", "Aircraft-specific (PMDG, Fenix)"],
        fixes=["Reboot sim after importing", "Ensure navdata is up to date and matches sim's AIRAC cycle", "Consult aircraft-specific import guide"],
        search_terms=["simbrief import", "simbrief not working", "fmc empty", "flight plan import fail"],
    ),
    ErrorEntry(
        id="FPL_005", name="EFB Weight & Balance Non-Interactive (2024)",
        category="Flight Planning/FMS", severity="high",
        description="EFB Weight & Balance screen entirely non-interactive - Seats/Cargo/Fuel/CG fields can't be modified.",
        causes=["EFB load-state lock bug", "Blocks weight & balance changes both in menu and in-flight"],
        fixes=["Try loading weight & balance before first engine start", "Reload the flight if lock persists", "Report to official bug tracker"],
        search_terms=["efb weight balance", "weight balance locked", "efb not interactive"],
    ),
    ErrorEntry(
        id="FPL_006", name="EFB Trip Fuel Shows 0lbs (2024)",
        category="Flight Planning/FMS", severity="medium",
        description="EFB Weight & Balance screen: Trip Fuel field shows 0lbs and cannot be edited.",
        causes=["EFB fuel-field editability regression introduced by Sim Update 3"],
        fixes=["Use in-cockpit fuel controls/refuel command directly", "Don't trust EFB trip fuel field until patched"],
        search_terms=["efb fuel 0", "trip fuel zero", "efb fuel field"],
    ),
    ErrorEntry(
        id="FPL_007", name="Global Units Don't Update Aircraft EFB",
        category="Flight Planning/FMS", severity="medium",
        description="Changing global units (Metric/US/Hybrid) doesn't update aircraft's own EFB, causing fuel/payload values to be misinterpreted.",
        causes=["Many aircraft maintain separate unit preference that doesn't inherit global setting"],
        fixes=["Always verify unit labels in loading panel/EFB after changing global setting", "Set aircraft's own EFB unit preference separately", "Don't enter data through both sim loading panel and aircraft EFB"],
        search_terms=["units wrong", "efb units", "metric us hybrid", "fuel units mismatch"],
    ),
    ErrorEntry(
        id="FPL_008", name="PMDG 777 SimBrief Plan Shows Red / Winds Don't Populate (2024)",
        category="Flight Planning/FMS", severity="medium",
        description="PMDG 777: SimBrief flight plan shows red on FMC (not loading) or loads but winds don't populate.",
        causes=["Aircraft-specific SimBrief integration bug", "Intermittent"],
        fixes=["Uninstalling other PMDG aircraft installed alongside as isolation step", "Track PMDG support forum for fix"],
        search_terms=["pmdg 777 simbrief", "pmdg winds", "pmdg fmc red"],
    ),

    # ============================================================
    # MARKETPLACE / PURCHASES
    # ============================================================
    ErrorEntry(
        id="MARKET_001", name="Marketplace Tile Greyed Out / Inaccessible",
        category="Marketplace", severity="medium",
        description="Marketplace tile greyed out or inaccessible.",
        causes=["Online Services session stuck", "Community folder conflict"],
        fixes=["Verify game files", "Sign out/in of Microsoft accounts", "Contact platform support if persistent"],
        search_terms=["marketplace greyed", "marketplace inaccessible", "marketplace tile"],
    ),
    ErrorEntry(
        id="MARKET_002", name="Purchase Stuck on 'Pending' / Transaction Failed But Charged",
        category="Marketplace", severity="high",
        description="Purchase stuck on 'pending' or transaction failed but charged.",
        causes=["Payment confirmation desync between store backend and sim"],
        fixes=["Retry later", "Verify account region settings", "Report via official bug forum if persistent"],
        search_terms=["purchase pending", "transaction failed", "charged but not delivered"],
    ),
    ErrorEntry(
        id="MARKET_003", name="Marketplace Locks Up / Can't Complete Purchase (2024)",
        category="Marketplace", severity="medium",
        description="Marketplace locks up and can't complete a purchase in MSFS 2024.",
        causes=["Session/backend bug"],
        fixes=["Force-close and relaunch", "Try purchasing from web marketplace instead"],
        search_terms=["marketplace lock", "purchase stuck", "marketplace freeze"],
    ),

    # ============================================================
    # SAVES / LOGBOOK
    # ============================================================
    ErrorEntry(
        id="SAVE_001", name="Logbook Stuck / Not Updating / Missing Flight History",
        category="Saves/Logbook", severity="medium",
        description="Logbook stuck/not updating, missing flight history.",
        causes=["Cloud save not uploaded on quit", "Dev mode/mods disabling tracking"],
        fixes=["Always quit via in-game Quit option", "Disable dev mode and remove mods that suppress logbook tracking"],
        search_terms=["logbook stuck", "logbook not updating", "flight history missing"],
    ),
    ErrorEntry(
        id="SAVE_002", name="Corrupted Profile Causing Crashes on Identity Screen",
        category="Saves/Logbook", severity="high",
        description="Corrupted profile causing crashes on identity screen, spawning inside buildings, or stuck loading.",
        causes=["Corrupted cloud save/profile data"],
        fixes=["Delete the cloud save (irversibly wipes logbook, control profiles, settings)", "Contact support"],
        search_terms=["corrupted profile", "identity crash", "profile corrupted", "spawn inside building"],
    ),
    ErrorEntry(
        id="SAVE_003", name="Want to Reset Logbook / Flight Hours to Zero",
        category="Saves/Logbook", severity="low",
        description="User wants to reset logbook/flight hours to zero.",
        causes=["No in-sim command exists for partial/row-level reset"],
        fixes=["Full cloud save deletion is the only method - resets everything (logbook, career, settings)", "Not reversible"],
        search_terms=["reset logbook", "reset flight hours", "clear logbook"],
    ),
    ErrorEntry(
        id="SAVE_004", name="CTD When Clicking Mouse Options in Settings (2024)",
        category="Saves/Logbook", severity="high",
        description="CTD tied to opening Settings, specifically clicking Mouse options. Traced to corrupted cloud save.",
        causes=["Corrupted 2024 cloud save carried over even after reinstall"],
        fixes=["Delete cloud save via command line: start Shell:AppsFolder\\Microsoft.Limitless_8wekyb3d8bbwe!App -DeleteCloudSaves", "MS Store version"],
        search_terms=["settings crash mouse", "cloud save corrupt", "settings ctd"],
    ),

    # ============================================================
    # HELICOPTER PHYSICS
    # ============================================================
    ErrorEntry(
        id="HELI_001", name="Helicopter Ground Effect Transition Broken (2024)",
        category="Helicopter Physics", severity="high",
        description="Helicopter ground effect transition is abrupt/broken - airflow model doesn't react correctly to proximity of rotor disc to ground.",
        causes=["Ground-effect aerodynamic model bug, same root issue from MSFS 2020, only partially improved in SU1 beta"],
        fixes=["No user-side fix - officially logged bug (Severity: Blocker on dev forum)", "Improves incrementally per Sim Update"],
        search_terms=["helicopter ground effect", "ground effect broken", "helicopter ground proximity"],
    ),
    ErrorEntry(
        id="HELI_002", name="Helicopter Spins Uncontrollably When Raising Collective (2024)",
        category="Helicopter Physics", severity="high",
        description="Helicopter spins uncontrollably (pirouettes) when raising collective, especially near the ground.",
        causes=["Usually NOT a bug - most cases trace to insufficient/absent pedal (anti-torque) input", "Unbound/reversed/duplicated Tail Rotor Axis binding", "Low rotor RPM"],
        fixes=["Verify Tail Rotor Axis is bound correctly (not reversed/duplicated)", "Apply proportional pedal as collective increases", "Keep rotor RPM in green", "Disable Assisted Tail Rotor/Assisted Cyclic to check"],
        search_terms=["helicopter spinning", "helicopter pirouette", "collective spin", "anti-torque"],
    ),
    ErrorEntry(
        id="HELI_003", name="Helicopter Flight Model Feels Wrong / Floaty (2024)",
        category="Helicopter Physics", severity="high",
        description="Helicopter flight model feels 'wrong'/floaty/unrealistic even with assists off.",
        causes=["Community-found bug where sim silently falls back to legacy flight model instead of applying new 'Modern' one"],
        fixes=["Set Flight Model to Legacy + Global Preset to Realistic, apply, start flight, then switch back to Modern - forces new model to load"],
        search_terms=["helicopter flight model", "helicopter floaty", "flight model wrong"],
    ),
    ErrorEntry(
        id="HELI_004", name="Rotor Clutch/Engagement Behaves Incorrectly (2024)",
        category="Helicopter Physics", severity="medium",
        description="Rotor clutch/engagement behaves incorrectly - doesn't disengage/engage as expected, RPM behavior wrong at spool-up.",
        causes=["Rotor clutch simulation bug in engine/rotor coupling logic"],
        fixes=["Bring throttle up gradually rather than abruptly during spool-up", "Avoid relying on clutch disengagement for autorotation practice until patched"],
        search_terms=["rotor clutch", "clutch engagement", "rotor rpm wrong", "spool up bug"],
    ),
    ErrorEntry(
        id="HELI_005", name="Main/Tail Rotor Shadow Disappears at Flying RPM (2024)",
        category="Helicopter Physics", severity="low",
        description="Main/tail rotor shadow disappears once rotor reaches flying RPM (present only during spool-up).",
        causes=["Rotor shadow rendering only implemented/working at low RPM on most stock helicopters"],
        fixes=["No official fix - pilots who rely on shadow for height judgment have no workaround", "Third-party add-ons exist that restore it"],
        search_terms=["rotor shadow", "shadow disappears", "rotor shadow missing"],
    ),

    # ============================================================
    # SEAPLANE / GLIDER PHYSICS
    # ============================================================
    ErrorEntry(
        id="SEAPLANE_001", name="Float Planes Nearly Impossible to Steer on Water",
        category="Seaplane Physics", severity="medium",
        description="Float planes nearly impossible to steer on water, especially with wind. Water rudders have little effect.",
        causes=["Long-standing water-contact-point/steering physics limitation"],
        fixes=["No user-side fix - extend water rudders and use differential power/braking as partial workaround", "Full fix requires engine-level rework"],
        search_terms=["float plane steering", "water rudder", "seaplane steering"],
    ),
    ErrorEntry(
        id="SEAPLANE_002", name="Float Plane Bounces on Water Takeoff Instead of Planing",
        category="Seaplane Physics", severity="medium",
        description="Float plane won't get 'on step' / bounces repeatedly on water during takeoff instead of planing smoothly.",
        causes=["Water buoyancy/contact-point model doesn't accurately estimate float shape/buoyancy distribution"],
        fixes=["No user-side fix - trim/pitch technique can reduce bouncing somewhat", "Cannot fully compensate for underlying model limitation"],
        search_terms=["float plane bounce", "water takeoff bounce", "float step"],
    ),
    ErrorEntry(
        id="SEAPLANE_003", name="No Pitch Control on Water for Float Planes",
        category="Seaplane Physics", severity="medium",
        description="No pitch control on the water for float planes - can't simulate plow/step taxi transitions.",
        causes=["Water physics model lacks a pitch-control axis simulation specific to float taxiing"],
        fixes=["No user-side fix - officially requested feature/fix, not yet implemented"],
        search_terms=["float plane pitch", "water pitch control", "plow step taxi"],
    ),
    ErrorEntry(
        id="SEAPLANE_004", name="Thermals Too Dense / Unrealistic for Gliding",
        category="Seaplane Physics", severity="low",
        description="Thermals for gliding are spaced too closely together / unrealistically dense.",
        causes=["Thermal generation algorithm tuning issue"],
        fixes=["No user-side fix - officially logged bug on forums (marked Resolved at time of report)", "Re-verify on current patch"],
        search_terms=["thermals dense", "thermals unrealistic", "gliding thermals"],
    ),
    ErrorEntry(
        id="SEAPLANE_005", name="Glider Mods Hard-Crash on Water Landing",
        category="Seaplane Physics", severity="high",
        description="Some payware/freeware glider mods hard-crash the entire sim if you land/crash into water.",
        causes=["Add-on-specific wing-tilt geometry incompatible with sim's water-contact collision handling"],
        fixes=["No fix - developer-acknowledged as unfixable for that model", "Avoid water contact with affected glider add-ons entirely"],
        search_terms=["glider water crash", "water landing crash", "glider crash water"],
    ),

    # ============================================================
    # CONNECTIVITY / ONLINE
    # ============================================================
    ErrorEntry(
        id="NET_005", name="Bandwidth Too Low for Data Streaming (2024)",
        category="Network", severity="medium",
        description="'Your bandwidth is too low for data streaming, you have been switched to offline mode' error.",
        causes=["Insufficient sustained bandwidth for live data streaming"],
        fixes=["Switch to wired connection", "Close other bandwidth-heavy apps/devices", "Adjust rolling cache size"],
        search_terms=["bandwidth too low", "low bandwidth", "offline mode bandwidth"],
    ),
    ErrorEntry(
        id="NET_006", name="Content Servers Unavailable - Login Loop After Patch",
        category="Network", severity="high",
        description="'Access to the content servers is currently unavailable' repeating login loop after a patch.",
        causes=["Xbox/online login handshake failure after update"],
        fixes=["Alt+Tab/resize login window if unresponsive", "Verify Xbox Live status", "Retry login", "Check firewall"],
        search_terms=["content servers unavailable", "login loop", "server unavailable"],
    ),
    ErrorEntry(
        id="NET_007", name="Online Services Broken While Base Sim Works",
        category="Network", severity="medium",
        description="Online services (live weather, multiplayer) broken while base sim works fine.",
        causes=["Online Functionality/Data Connection service needs a reset"],
        fixes=["Toggle Online Functionality off/on", "Restart Online Services in-sim", "Sign out/in of Microsoft account"],
        search_terms=["online services broken", "live weather not working", "multiplayer not working"],
    ),
    ErrorEntry(
        id="NET_008", name="Rolling Cache Full / Scenery Fails to Stream",
        category="Network", severity="medium",
        description="Rolling cache full or scenery fails to stream, causing blurry textures.",
        causes=["Cache size too small or on slow storage", "Live-traffic server load"],
        fixes=["Increase rolling cache size", "Move to SSD", "Delete and rebuild periodically"],
        search_terms=["rolling cache full", "scenery not streaming", "blurry scenery"],
    ),

    # ============================================================
    # REMAINING CRASH / CTD ERRORS
    # ============================================================
    ErrorEntry(
        id="CTD_010", name="Crash Caused by NVIDIA Driver (2024)",
        category="Crash/CTD", severity="high",
        description="MSFS 2024 crashes specifically caused by a recent NVIDIA driver update.",
        causes=["Corrupted NGX OTA cache (DLSS-related)", "Driver incompatibility"],
        fixes=["Delete C:\\ProgramData\\NVIDIA\\NGX folder and reboot", "Roll back to previous driver", "Check MSFS forums for current known-bad driver version"],
        search_terms=["nvidia driver crash", "driver crash 2024", "nvidia crash msfs"],
    ),
    ErrorEntry(
        id="CTD_011", name="Crash on CPUs with More Than 32 Cores (2024)",
        category="Crash/CTD", severity="critical",
        description="Sim crashes on CPUs with more than 32 cores (Threadripper, high-end Xeon) at 87-90% loading stage.",
        causes=["Thread-count handling bug", "Patched in 1.2.7.0"],
        fixes=["Disable extra cores, cap active cores at 32 in BIOS/Task Manager affinity", "Update to 1.2.7.0 or later"],
        search_terms=["32 cores crash", "threadripper crash", "cpu cores crash", "more than 32 cores"],
    ),
    ErrorEntry(
        id="CTD_012", name="DX12 Error on Radeon RX580 or Lower (2024)",
        category="Crash/CTD", severity="high",
        description="DX12 error on Radeon RX580 or lower-tier GPUs.",
        causes=["GPU below minimum supported performance tier for DX12"],
        fixes=["None - GPU upgrade required", "Use DX11 if available"],
        search_terms=["dx12 radeon", "rx580 crash", "dx12 error lower gpu"],
    ),
    ErrorEntry(
        id="CTD_013", name="Out-of-Memory (OOM) Crash with High Settings/Heavy Add-ons",
        category="Crash/CTD", severity="high",
        description="Out-of-memory crash with high settings and heavy add-ons.",
        causes=["VRAM/RAM exhaustion, especially 8GB VRAM cards"],
        fixes=["Lower Terrain/Object LOD and texture resolution", "Reduce concurrent add-ons", "Increase pagefile"],
        search_terms=["out of memory", "oom crash", "memory crash", "vram exhaustion"],
    ),
    ErrorEntry(
        id="CTD_014", name="Silent CTD with No Error Dialog",
        category="Crash/CTD", severity="medium",
        description="Silent CTD with no error dialog shown.",
        causes=["Conflicting Community folder add-on"],
        fixes=["Binary-search the Community folder (move half out, test, repeat)", "Check Event Viewer for faulting module"],
        search_terms=["silent ctd", "crash no error", "ctd no dialog"],
    ),
    ErrorEntry(
        id="CTD_015", name="Crash Under Sustained Load / Long Sessions",
        category="Crash/CTD", severity="high",
        description="Crash during mid-flight or long sessions (sustained load).",
        causes=["PSU underpowered for full system load", "Thermal throttling", "Memory leak"],
        fixes=["Verify PSU headroom for full system draw", "Check GPU/CPU temps", "Monitor RAM/VRAM usage during flight"],
        search_terms=["crash mid flight", "crash long session", "sustained load crash"],
    ),
    ErrorEntry(
        id="CTD_016", name="Crash When Clicking 'Fly'",
        category="Crash/CTD", severity="high",
        description="Sim crashes specifically when clicking the 'Fly' button to start a flight.",
        causes=["Corrupted user profile/save data"],
        fixes=["Reset pagefile to custom min/max size matching system RAM", "Check for corrupted profile", "Create new Windows profile"],
        search_terms=["crash click fly", "fly button crash", "start flight crash"],
    ),
    ErrorEntry(
        id="CTD_017", name="Crash Tied to Realtek Audio / Nahimic",
        category="Crash/CTD", severity="high",
        description="CTD tied to Realtek audio or Nahimic sound enhancement software.",
        causes=["Nahimic service conflicts with sim audio engine"],
        fixes=["Disable Nahimic service", "Uninstall/replace Realtek audio driver package with generic HD Audio driver"],
        search_terms=["nahimic crash", "realtek audio crash", "nahimic msfs", "sound crash"],
    ),
    ErrorEntry(
        id="CTD_018", name="Crash When Peripherals Plugged/Unplugged After Launch",
        category="Crash/CTD", severity="medium",
        description="CTD when peripherals are plugged or unplugged after launch.",
        causes=["Hot-plug peripheral handling bug"],
        fixes=["Connect all peripherals before launching the sim", "Avoid hot-plugging mid-session"],
        search_terms=["peripheral crash", "usb crash", "hot plug crash", "unplug crash"],
    ),
    ErrorEntry(
        id="CTD_019", name="Crash Tied to Background Utilities",
        category="Crash/CTD", severity="medium",
        description="Crash tied to background utilities (backup software, tune-up utilities, RGB/lighting software).",
        causes=["Resource/hook conflicts"],
        fixes=["Close backup, tune-up, and resource-management software before launching"],
        search_terms=["background utility crash", "rgb crash", "tune-up crash", "software conflict crash"],
    ),
    ErrorEntry(
        id="CTD_020", name="OneDrive Syncing Documents Folder Causes Crash (2024)",
        category="Crash/CTD", severity="high",
        description="MSFS 2024 crashes only when OneDrive is syncing the Documents folder.",
        causes=["OneDrive locks/rewrites files (like UserCfg.opt) while sim is actively reading/writing them"],
        fixes=["Stop syncing Documents folder in OneDrive", "Move Community folder and add-on paths out of Documents", "Default LocalAppData install path is unaffected"],
        search_terms=["onedrive crash", "onedrive sync crash", "documents onedrive"],
    ),
    ErrorEntry(
        id="CTD_021", name="Antivirus Quarantining Scenery Files Causes CTD (2024)",
        category="Crash/CTD", severity="high",
        description="Stutters and occasional CTDs from a streamed scenery .bgl/.ccc file getting quarantined mid-read by third-party antivirus.",
        causes=["Real-time AV scanning interfering with sim's live file streaming"],
        fixes=["Add MSFS install directory, Packages folder, and Community folder to AV exclusion list", "Windows Defender is well-behaved; third-party AVs (Norton, McAfee, Bitdefender, Kaspersky) are more common offenders"],
        search_terms=["antivirus crash", "av quarantine", "defender crash", "bitdefender crash"],
    ),
    ErrorEntry(
        id="CTD_022", name="VRAM Exhaustion Crash Pattern (2024)",
        category="Crash/CTD", severity="high",
        description="VRAM-exhaustion crash pattern: happens minutes into a flight (not at launch), at busy airports/complex weather.",
        causes=["Sim does not gracefully degrade when VRAM runs out - crashes rather than throttling quality"],
        fixes=["Texture Resolution and Terrain LOD are two settings driving VRAM hardest", "Ultra textures need ~8GB VRAM minimum", "Drop Texture Resolution one tier first on 6-8GB cards"],
        search_terms=["vram crash", "vram exhaustion", "vram full crash", "out of vram"],
    ),
    ErrorEntry(
        id="CTD_023", name="Crash/Freeze Enabling DLSS Frame Generation on DX11",
        category="Crash/CTD", severity="high",
        description="Crash/freeze when enabling NVIDIA DLSS Frame Generation while sim is running under DirectX 11.",
        causes=["DLSS Frame Generation requires DirectX 12 - not supported under DX11 renderer"],
        fixes=["Switch sim's Graphics API to DirectX 12 before enabling DLSS Frame Generation", "MSFS 2024 runs DX12 by default"],
        search_terms=["dlss frame generation crash", "dlss dx11", "frame gen crash", "dx11 dlss"],
    ),
    ErrorEntry(
        id="CTD_024", name="Freeze on Fullscreen Launch with DLSS FG (2024)",
        category="Crash/CTD", severity="high",
        description="Freeze on launching a flight in fullscreen mode specifically with DLSS Frame Generation on.",
        causes=["Fullscreen exclusive mode conflicts with Frame Generation initialization"],
        fixes=["Use windowed/borderless mode instead of true fullscreen", "Alt+Enter after freeze can sometimes recover"],
        search_terms=["fullscreen freeze", "dlss fullscreen", "frame gen fullscreen"],
    ),
    ErrorEntry(
        id="CTD_025", name="DLSS FG 3x/4x Multiplier Instability (2024)",
        category="Crash/CTD", severity="high",
        description="Application instability specifically when selecting 3x or 4x DLSS Frame Generation multiplier.",
        causes=["DLSS multi-frame-gen multiplier bug"],
        fixes=["Use NVIDIA App's DLSS Override to enable DLSS Multi-Frame Generation instead of in-sim 3x/4x option", "Ensure GeForce Game Ready Driver 576.40+"],
        search_terms=["dlss 3x", "dlss 4x", "multi frame gen", "dlss multiplier crash"],
    ),
    ErrorEntry(
        id="CTD_026", name="Crash Near Keflavik Airport (BIKF) - MSFS 2020",
        category="Crash/CTD", severity="high",
        description="Guaranteed CTD flying, departing, or arriving near Keflavik International Airport (BIKF), Iceland.",
        causes=["Specific scenery/terrain data bug at this airport, officially acknowledged at launch"],
        fixes=["No user-side fix - avoid BIKF until patched", "Subsequently patched in later updates"],
        search_terms=["keflavik crash", "bikf crash", "iceland crash", "keflavik ctd"],
    ),
    ErrorEntry(
        id="CTD_027", name="Running Low on Memory - Avionics Disabled (Xbox/2020)",
        category="Crash/CTD", severity="critical",
        description="'Running low on memory, disabling avionics' warning on Xbox after Sim Update 5, leaving glass cockpits with black screens.",
        causes=["Confirmed memory-management regression introduced specifically by Sim Update 5 on console"],
        fixes=["Officially confirmed fix coming in patch", "Restart sim between flights to clear accumulated memory pressure", "Avoid large glass-cockpit aircraft at complex airports"],
        search_terms=["low memory avionics", "memory warning xbox", "avionics disabled", "orange wasm error"],
    ),
    ErrorEntry(
        id="CTD_028", name="Crash with Event Viewer 'ucrtbase.dll' (2024)",
        category="Crash/CTD", severity="high",
        description="CTD with Event Viewer faulting module 'ucrtbase.dll' (Universal C Runtime).",
        causes=["Missing English (US) language pack", "Non-English system locale for non-Unicode programs"],
        fixes=["Add English (United States) as full language pack", "Set system locale to English (US) in Control Panel > Region > Administrative", "Reinstall both x86 and x64 Visual C++ Redistributables"],
        search_terms=["ucrtbase.dll", "ucrtbase crash", "universal c runtime"],
        related_dlls=["ucrtbase.dll"],
    ),
    ErrorEntry(
        id="CTD_029", name="Crash with 'nvwgf2umx.dll' or 'atidxx64.dll' (2024)",
        category="Crash/CTD", severity="high",
        description="CTD with Event Viewer faulting module 'nvwgf2umx.dll' (NVIDIA) or 'atidxx64.dll' (AMD).",
        causes=["GPU display driver itself crashed - a driver problem, not a sim bug"],
        fixes=["Check MSFS forums for current known-bad driver version", "Swap to matching Studio Driver", "Use DDU in Safe Mode to roll back"],
        search_terms=["nvwgf2umx crash", "atidxx64 crash", "gpu driver crash dll"],
        related_dlls=["nvwgf2umx.dll", "atidxx64.dll"],
    ),
    ErrorEntry(
        id="CTD_030", name="Safe Mode Prompt After CTD (2024)",
        category="Crash/CTD", severity="low",
        description="After a CTD, leftover 'running.lock' file triggers Safe Mode prompt on next launch.",
        causes=["Sim's built-in crash-recovery mechanism - lacks manual trigger"],
        fixes=["Let Safe Mode load once to quickly confirm if add-ons are cause", "Community tool MSFS-Safe-Mode-Switch on GitHub can force Safe Mode on demand"],
        search_terms=["safe mode", "safe mode prompt", "running.lock"],
    ),
    ErrorEntry(
        id="CTD_031", name="Add-on Aircraft Ported from 2020 Crashes in 2024",
        category="Crash/CTD", severity="high",
        description="Add-on aircraft ported from MSFS2020 to 2024 crashes or behaves unreliably despite working fine in 2020.",
        causes=["Stale dependencies - 2020-built add-on running inside 2024 without 2024-specific rebuild"],
        fixes=["Check vendor site after every Sim Update for 2024-specific build", "Don't assume 2020 version will keep working", "Go to vendor's own support hub once isolated"],
        search_terms=["port addon crash", "2020 addon 2024 crash", "ported aircraft crash"],
    ),
    ErrorEntry(
        id="CTD_032", name="Multiple Crashes on Xbox/PS5 Tied to Certain Aircraft (2024)",
        category="Crash/CTD", severity="critical",
        description="Multiple crashes and low-memory/avionics failures specifically on Xbox Series X|S and PlayStation 5 tied to certain aircraft.",
        causes=["Console memory-management issues persisting into mid-2026 for specific aircraft"],
        fixes=["Patched/reduced in AAU4 release", "Reduce AI traffic and scenery/graphics load to relieve memory pressure"],
        search_terms=["xbox crash aircraft", "ps5 crash", "console crash avionics"],
    ),
    ErrorEntry(
        id="CTD_033", name="Crash with 32870 Exception Code (Event ID 1000)",
        category="Crash/CTD", severity="high",
        description="Repeated CTD with Event ID 1000 and exception 0xc0000005 in Windows Event Viewer.",
        causes=["Generic access-violation fault - GPU driver, audio driver, or 3rd-party module most common"],
        fixes=["Check Event Viewer 'Faulting module' name for the real culprit DLL", "Update/replace that driver or remove that add-on"],
        search_terms=["event id 1000", "0xc0000005", "exception code", "access violation"],
        related_codes=["0xc0000005"],
    ),

    # ============================================================
    # TCAS ERRORS
    # ============================================================
    ErrorEntry(
        id="TCAS_001", name="TCAS False Alerts on iniBuilds Airbus (2024)",
        category="Aircraft Systems", severity="high",
        description="Erroneous TCAS Resolution/Traffic Advisories triggered with no real nearby traffic on iniBuilds Airbus aircraft.",
        causes=["Distinct TCAS logic fault across different aircraft/updates", "iniBuilds-specific"],
        fixes=["Turn transponder off as workaround", "Track iniBuilds forum directly for fix", "Not core sim bug"],
        search_terms=["tcas false alert", "tcas iniBuilds", "tcas traffic advisory"],
    ),
    ErrorEntry(
        id="TCAS_002", name="TCAS Ground Inhibit Bug (Fixed in SU3)",
        category="Aircraft Systems", severity="medium",
        description="TCAS gives 'Traffic, Traffic...Clear of conflict' callouts on the ground after landing.",
        causes=["TCAS ground-inhibit logic bug - TCAS should be automatically inhibited on ground but wasn't"],
        fixes=["Fixed in Sim Update 3 (1.5.27.0)", "Ensure sim is updated"],
        search_terms=["tcas ground", "tcas traffic ground", "tcas ground inhibit"],
    ),
    ErrorEntry(
        id="TCAS_003", name="TCAS Display Shows STANDBY Despite Being ON",
        category="Aircraft Systems", severity="medium",
        description="TCAS display shows 'STANDBY' status despite mode selector being set to ON/TA/TA-RA.",
        causes=["TCAS mode-display sync bug"],
        fixes=["Fixed in Sim Update 3 (1.5.27.0)", "Ensure sim is updated"],
        search_terms=["tcas standby", "tcas display wrong", "tcas mode stuck"],
    ),
    ErrorEntry(
        id="TCAS_004", name="TCAS Shows No Traffic Despite Being ON",
        category="Aircraft Systems", severity="medium",
        description="TCAS doesn't display any other traffic at all even when explicitly selected ON with TA or TA/RA mode active.",
        causes=["TCAS traffic-display rendering bug"],
        fixes=["Fixed in Sim Update 3 (1.5.27.0)", "Ensure sim is updated"],
        search_terms=["tcas no traffic", "tcas empty", "tcas not showing traffic"],
    ),
    ErrorEntry(
        id="TCAS_005", name="TCAS Inaccurate with Non-MSFS Aircraft on VATSIM",
        category="Aircraft Systems", severity="low",
        description="TCAS/relative-altitude calculations can be inaccurate when flying alongside non-MSFS aircraft on shared network (VATSIM).",
        causes=["Cross-simulator altitude mismatch - other sims may compute altitude differently"],
        fixes=["Not fixable from MSFS side - discrepancy originates in how other sims compute altitude", "Be aware TCAS readings involving non-MSFS traffic may be less reliable"],
        search_terms=["tcas vatSIM", "tcas altitude wrong", "cross simulator tcas"],
    ),

    # ============================================================
    # TEXTURES / GRAPHICS
    # ============================================================
    ErrorEntry(
        id="GFX_001", name="Pink/Magenta Checkerboard Textures",
        category="Textures/Graphics", severity="high",
        description="Pink/magenta checkerboard textures on aircraft or scenery.",
        causes=["Corrupted texture files", "Incompatible legacy livery (2020 BC1/BC3 format vs 2024)", "Interrupted download"],
        fixes=["Delete/rebuild rolling cache", "Verify livery is built for correct sim version", "Delete corrupted fs-base folders in Packages to force re-download"],
        search_terms=["pink textures", "magenta textures", "checkerboard textures", "pink aircraft"],
    ),
    ErrorEntry(
        id="GFX_002", name="Pink Textures from MSFS2020-Only Liveries (2024)",
        category="Textures/Graphics", severity="medium",
        description="Pink textures from MSFS2020-only liveries in MSFS 2024.",
        causes=["Older BC1/BC3 texture compression unsupported in 2024 renderer"],
        fixes=["Remove livery", "Use a 2024-compatible re-release if available"],
        search_terms=["pink livery", "2020 livery pink", "livery texture pink"],
    ),
    ErrorEntry(
        id="GFX_003", name="Poor/Blurry Photogrammetry",
        category="Textures/Graphics", severity="medium",
        description="Poor or blurry photogrammetry in MSFS.",
        causes=["Corrupted online cache", "Streaming interruption"],
        fixes=["Toggle Online Functionality/Bing Data/Photogrammetry off then on", "Delete rolling + manual cache for affected region"],
        search_terms=["blurry photogrammetry", "photogrammetry quality", "poor photogrammetry"],
    ),
    ErrorEntry(
        id="GFX_004", name="Whole Screen Pink/Magenta Tint",
        category="Textures/Graphics", severity="medium",
        description="Whole screen shifted pink/magenta tint (not object-specific).",
        causes=["HDR display conflict, not a texture bug"],
        fixes=["Disable HDR", "Update/reset GPU driver"],
        search_terms=["pink tint", "magenta tint", "screen tint pink", "hdr pink"],
    ),
    ErrorEntry(
        id="GFX_005", name="No Rain Visible on Windshield (2024 Launch)",
        category="Textures/Graphics", severity="medium",
        description="No rain visible on the windshield/canopy at all despite flying through heavy precipitation.",
        causes=["Windshield rain-effect rendering bug, directly acknowledged by developer"],
        fixes=["Track linked official forum bug thread for resolution status", "Officially logged same day as reported"],
        search_terms=["no rain", "rain not visible", "windshield rain missing"],
    ),
    ErrorEntry(
        id="GFX_006", name="Windshield Rain/Snow Reverts to Medium Quality (2024)",
        category="Textures/Graphics", severity="low",
        description="Windshield rain/snow effects intermittently revert to Medium quality regardless of Ultra setting.",
        causes=["Windshield-effects quality setting not persisting correctly"],
        fixes=["Set overall graphics preset to Ultra first, then adjust individual settings back down", "Changing windshield effect setting in isolation doesn't take effect"],
        search_terms=["rain quality medium", "snow quality medium", "windshield effect revert"],
    ),
    ErrorEntry(
        id="GFX_007", name="Cockpit Texture Popping / LOD Artifacts (2024)",
        category="Textures/Graphics", severity="medium",
        description="Cockpit texture and LOD popping, distant shadow rendering artifacts, occasional flickering during terrain LOD transitions.",
        causes=["Rendering pipeline bugs present pre-SimUpdate-6"],
        fixes=["Patched in Sim Update 6 (1.8.14.0)", "Ensure sim is updated"],
        search_terms=["texture popping", "lod artifacts", "shadow artifacts", "cockpit texture"],
    ),

    # ============================================================
    # PERFORMANCE
    # ============================================================
    ErrorEntry(
        id="PERF_006", name="Periodic Stutter Every 15-30s with CPU Clock Drop",
        category="Performance", severity="high",
        description="Periodic stutter every 15-30s with CPU clock dropping sharply (e.g. 4.9GHz to 0.4GHz), started after a Windows update.",
        causes=["Windows 11 25H2 power-management regression affecting the sim specifically"],
        fixes=["Roll back to Windows 11 23H2/24H2", "Confirmed by multiple users to fully resolve it"],
        search_terms=["cpu clock drop", "periodic stutter", "stutter 15 seconds", "cpu throttle"],
    ),
    ErrorEntry(
        id="PERF_007", name="Screen Tearing During Flight",
        category="Performance", severity="low",
        description="Screen tearing during flight.",
        causes=["VSync/frame pacing mismatch with monitor refresh", "Frame-gen mod conflicts"],
        fixes=["Enable VSync or cap frame rate below monitor refresh in Nvidia/AMD panel", "Disable third-party frame-generation mods"],
        search_terms=["screen tearing", "tearing flight", "vsync tearing"],
    ),
    ErrorEntry(
        id="PERF_008", name="Limited by Main Thread Warning (2024)",
        category="Performance", severity="low",
        description="'Limited by main thread' warning in Developer Mode FPS display.",
        causes=["CPU's main simulation thread taking longer per frame than GPU - this is a diagnostic indicator, not a bug"],
        fixes=["Lower Terrain LOD, Objects LOD, and AI traffic density first", "Test with simpler default aircraft and no add-ons"],
        search_terms=["limited main thread", "cpu bottleneck", "main thread warning"],
    ),
    ErrorEntry(
        id="PERF_009", name="Severe Post-Patch Regression Cluster (2024)",
        category="Performance", severity="critical",
        description="Severe post-patch regression: slideshow-level stutters, VRAM/RAM leak, CTDs, all appearing together right after a specific update.",
        causes=["A poorly-tested patch introducing multiple simultaneous regressions"],
        fixes=["Clear shader cache, verify files, empty Community folder", "Wait for follow-up hotfix", "Monitor official forums for hotfix ETA"],
        search_terms=["post patch regression", "slideshow stutter", "patch regression"],
    ),
    ErrorEntry(
        id="PERF_010", name="Boot/Loading Times Slow, DLSS Not Applied, WASM Leaks (2024 pre-SU3)",
        category="Performance", severity="high",
        description="Boot/loading times slow, DLSS x3/x4 not correctly applied, WASM memory leaks, high VRAM usage, weak VR render performance pre-Sim Update 3.",
        causes=["Multiple performance bottlenecks bundled together"],
        fixes=["Patched in Sim Update 3 (1.5.27.0) - optimized boot/loading, corrected DLSS, fixed WASM leaks and VRAM usage"],
        search_terms=["slow boot", "dlss not applied", "wasm leak", "vram high"],
    ),
    ErrorEntry(
        id="PERF_011", name="Performance Regression with Live Weather in Dense Airport Areas (2024)",
        category="Performance", severity="medium",
        description="Performance regression using live weather in areas with high density of airports/helipads.",
        causes=["Live weather processing overhead scaling poorly with airport/helipad density"],
        fixes=["Reduce live weather detail settings", "Report via Weather bug forum"],
        search_terms=["performance live weather", "dense airports stutter", "weather performance"],
    ),
    ErrorEntry(
        id="PERF_012", name="Frame Rate Cap Slows Boot Sequence (2024)",
        category="Performance", severity="low",
        description="Frame rate cap not properly ignored during initial boot, slowing down the boot sequence itself.",
        causes=["Boot-sequence and building-load performance bugs"],
        fixes=["Patched in Sim Update 6 (1.8.14.0)", "Ensure sim is updated"],
        search_terms=["boot slow", "frame rate cap boot", "loading slow"],
    ),

    # ============================================================
    # AIRCRAFT SYSTEMS (Additional)
    # ============================================================
    ErrorEntry(
        id="AIR_020", name="ILS Doesn't Activate on Final Approach (2024)",
        category="Aircraft Systems", severity="high",
        description="ILS system doesn't activate at all on final approach in MSFS 2024 (worked fine in 2020).",
        causes=["Genuine cross-generation regression", "Procedure error (arming APPR before valid LOC/GS signals received)"],
        fixes=["Verify NAV radio tuned to correct ILS frequency", "Confirm CDI set to NAV not GPS", "Arm APPR only after receiving valid LOC/GS signals", "If all correct - logged 2024-specific regression"],
        search_terms=["ils not working", "ils approach fail", "ils not activating", "approach button broken"],
    ),
    ErrorEntry(
        id="AIR_021", name="ILS/Glideslope Misaligned at Specific Airports",
        category="Aircraft Systems", severity="medium",
        description="ILS/glideslope and PAPI genuinely misaligned/offset at specific airports - following glideslope leads to high unstable approach.",
        causes=["Long-standing navdata/scenery placement bug traced to legacy code"],
        fixes=["Cross-check PAPI visually against glideslope indication", "Trust PAPI/visual references over electronic glideslope if they clearly disagree", "Check payware scenery developer for navdata correction patch"],
        search_terms=["ils misaligned", "glideslope offset", "papi misaligned", "ils wrong airport"],
    ),
    ErrorEntry(
        id="AIR_022", name="Engine Won't Stay Running with Auto Start (2024)",
        category="Aircraft Systems", severity="high",
        description="Engine won't stay running even using the Engine Auto Start command (reported on C172 and Vision Jet).",
        causes=["Engine-start/keep-alive logic bug affecting Auto Start command"],
        fixes=["Try full manual cold-and-dark start sequence instead", "Verify mixture/fuel pump state immediately after engine catches"],
        search_terms=["engine auto start", "engine won't start", "engine shutdown auto start"],
    ),
    ErrorEntry(
        id="AIR_023", name="FADEC Enters Start Modes Mid-Flight (2024)",
        category="Aircraft Systems", severity="high",
        description="FADEC incorrectly enters engine start modes (READY/LIGHT-OFF/START) mid-flight when engine performance drops.",
        causes=["FADEC state-machine bug misreading fuel starvation as a start condition"],
        fixes=["Patched in Sim Update 3 (1.5.27.0)", "Ensure sim is updated"],
        search_terms=["fadec start mid flight", "fadec modes wrong", "engine start modes"],
    ),
    ErrorEntry(
        id="AIR_024", name="Autothrottle Silently Disengages at Cruise (2024)",
        category="Aircraft Systems", severity="high",
        description="Autothrottle (ATHR) mode silently disengages at cruise altitude with throttles in CLB.",
        causes=["Autothrottle mode-management logic bug at climb-to-cruise transition"],
        fixes=["No user-side fix at time of report - logged as known open issue", "Monitor patch notes for fix"],
        search_terms=["autothrottle disengage", "athr disengage", "autothrottle cruise"],
    ),
    ErrorEntry(
        id="AIR_025", name="Throttle Lever Doesn't Move Engine Power",
        category="Aircraft Systems", severity="high",
        description="Throttle lever doesn't move engine power at all, or moves then snaps back to a different position.",
        causes=["Duplicate/conflicting axis binding", "Autothrottle or AI-assist fighting manual input", "Wrong axis bound"],
        fixes=["Disable autothrottle and AI piloting assistance to test manually", "Check for duplicate throttle bindings", "Verify correct axis per engine on multi-engine"],
        search_terms=["throttle not working", "throttle no power", "throttle snaps back"],
    ),
    ErrorEntry(
        id="AIR_026", name="Payware Airbus Idle Throttle Engine Shutdown (2024)",
        category="Aircraft Systems", severity="high",
        description="Payware Airbus add-ons (iniBuilds) experience unexpected engine shutdown when idling throttle during taxi or landing.",
        causes=["Add-on-specific idle-throttle handling bug"],
        fixes=["Avoid fully idling throttle during taxi/rollout on affected add-ons", "Keep slightly above idle"],
        search_terms=["inibuilds engine shutdown", "idle throttle engine", "airbus engine trip"],
    ),
    ErrorEntry(
        id="AIR_027", name="Cockpit Click-Interaction Not Responding (2024)",
        category="Aircraft Systems", severity="high",
        description="Cockpit click-interaction system bug - switches/knobs not responding correctly to mouse/VR pointer clicks.",
        causes=["Interaction-volume/hitbox logic bug", "Aircraft- or build-dependent"],
        fixes=["Try adjusting interaction mode (Lock vs Legacy)", "In VR, exiting and re-entering VR mode reliably restores click-interaction", "Report with aircraft + build number"],
        search_terms=["cockpit click", "switch not responding", "click interaction", "knob not working"],
    ),
    ErrorEntry(
        id="AIR_028", name="'You Overstressed the Aircraft' False Trigger (2024)",
        category="Aircraft Systems", severity="medium",
        description="Erroneous 'You overstressed the aircraft' failure triggered during normal rotation/takeoff.",
        causes=["Stress and Damage model miscalculating G-load/structural stress at specific pitch rates"],
        fixes=["Disable the Stress and Damage option in Assistance settings", "Report with exact pitch/speed/aircraft to bug tracker"],
        search_terms=["overstressed aircraft", "stress damage false", "false failure stress"],
    ),
    ErrorEntry(
        id="AIR_029", name="2020 Aircraft Trigger Wear and Tear Faults in Normal Flight (2024)",
        category="Aircraft Systems", severity="medium",
        description="MSFS2020-era light aircraft trigger Wear and Tear faults in completely normal flight after being ported to 2024.",
        causes=["2024's Wear and Tear system applies stress calculations these older aircraft weren't modeled to handle"],
        fixes=["Disable Wear and Tear / Stress and Damage assistance options for affected legacy aircraft"],
        search_terms=["wear and tear", "legacy aircraft faults", "2020 aircraft wear"],
    ),
    ErrorEntry(
        id="AIR_030", name="AI Aircraft Fail to Maintain Stable Altitude",
        category="Aircraft Systems", severity="medium",
        description="AI aircraft fail to maintain a stable altitude (visibly climbing/descending erratically).",
        causes=["AI traffic altitude-hold logic bug"],
        fixes=["None confirmed - report via AI traffic bug forum"],
        search_terms=["ai aircraft altitude", "ai unstable", "ai climbing descending"],
    ),
    ErrorEntry(
        id="AIR_031", name="PMDG 737 Stops Following Flight Plan After Update (2020)",
        category="Aircraft Systems", severity="high",
        description="Third-party airliner (e.g. PMDG 737) stops following the loaded flight plan after an MSFS core update.",
        causes=["Usually a Community folder conflict introduced or exposed by the update"],
        fixes=["Remove other mods from Community folder one at a time to isolate", "Test same aircraft on second, cleaner install/PC"],
        search_terms=["pmdg flight plan", "pmdg not following", "pmdg broken update"],
    ),
    ErrorEntry(
        id="AIR_032", name="Brakes Stuck After Landing (Rudder Pedals Specific)",
        category="Aircraft Systems", severity="medium",
        description="Rudder pedal brakes get 'stuck' fully on after landing/braking, only releasable by toggling parking brake.",
        causes=["Brake-axis center-position/half-applied-at-rest handling bug specific to certain pedal models"],
        fixes=["No universal confirmed fix - verify pedals bound as Axis controls (not Toggle)", "Cycle parking brake as workaround"],
        search_terms=["pedal brakes stuck", "brake pedal stuck", "rudder brake stuck"],
    ),
]


def _load_all_builtin() -> list[ErrorEntry]:
    return list(BUILTIN_ERRORS)


class ErrorLibrary:
    def __init__(self):
        self._builtin = _load_all_builtin()
        self._user = _load_json_errors(USER_ERRORS_FILE)
        self._rebuilt = False

    def _all(self) -> list[ErrorEntry]:
        return self._builtin + self._user

    def get_all(self) -> list[ErrorEntry]:
        return self._all()

    def get_by_id(self, error_id: str) -> Optional[ErrorEntry]:
        for e in self._all():
            if e.id == error_id:
                return e
        return None

    def search(self, query: str) -> list[ErrorEntry]:
        query_lower = query.lower()
        results = []
        for e in self._all():
            searchable = " ".join([
                e.name.lower(), e.description.lower(), e.category.lower(),
                " ".join(e.search_terms).lower(), " ".join(e.related_dlls).lower(),
                " ".join(e.related_codes).lower(),
            ])
            if query_lower in searchable or any(term in searchable for term in query_lower.split()):
                results.append(e)
        return results

    def get_by_category(self, category: str) -> list[ErrorEntry]:
        return [e for e in self._all() if e.category.lower() == category.lower()]

    def get_by_severity(self, severity: str) -> list[ErrorEntry]:
        return [e for e in self._all() if e.severity.lower() == severity.lower()]

    def get_categories(self) -> list[str]:
        return list(sorted(set(e.category for e in self._all())))

    def add_user_error(self, entry: ErrorEntry) -> bool:
        existing = self.get_by_id(entry.id)
        if existing:
            return False
        self._user.append(entry)
        self._save_user_errors()
        return True

    def update_user_error(self, entry: ErrorEntry) -> bool:
        for i, e in enumerate(self._user):
            if e.id == entry.id:
                self._user[i] = entry
                self._save_user_errors()
                return True
        return False

    def remove_user_error(self, error_id: str) -> bool:
        for i, e in enumerate(self._user):
            if e.id == error_id:
                self._user.pop(i)
                self._save_user_errors()
                return True
        return False

    def register_error(self, error_id: str, name: str, category: str, severity: str,
                       description: str, causes: list = None, fixes: list = None,
                       search_terms: list = None, related_dlls: list = None,
                       related_codes: list = None, references: list = None) -> ErrorEntry:
        entry = ErrorEntry(
            id=error_id, name=name, category=category, severity=severity,
            description=description, causes=causes or [], fixes=fixes or [],
            search_terms=search_terms or [], related_dlls=related_dlls or [],
            related_codes=related_codes or [], references=references or [],
        )
        existing = self.get_by_id(error_id)
        if existing:
            for i, e in enumerate(self._user):
                if e.id == error_id:
                    self._user[i] = entry
                    self._save_user_errors()
                    return entry
            return entry
        self._user.append(entry)
        self._save_user_errors()
        return entry

    def import_from_json(self, json_path: Path) -> int:
        errors = _load_json_errors(json_path)
        count = 0
        for e in errors:
            if not self.get_by_id(e.id):
                self._user.append(e)
                count += 1
        if count > 0:
            self._save_user_errors()
        return count

    def export_all(self, json_path: Path) -> int:
        all_errors = self._all()
        _save_json_errors(json_path, all_errors)
        return len(all_errors)

    def get_stats(self) -> dict:
        all_errors = self._all()
        cats = {}
        sevs = {}
        for e in all_errors:
            cats[e.category] = cats.get(e.category, 0) + 1
            sevs[e.severity] = sevs.get(e.severity, 0) + 1
        return {
            "total": len(all_errors),
            "builtin": len(self._builtin),
            "user_defined": len(self._user),
            "categories": cats,
            "severities": sevs,
            "all_categories": self.get_categories(),
        }

    def _save_user_errors(self):
        _save_json_errors(USER_ERRORS_FILE, self._user)


_library_instance: Optional[ErrorLibrary] = None


def get_library() -> ErrorLibrary:
    global _library_instance
    if _library_instance is None:
        _library_instance = ErrorLibrary()
    return _library_instance


def search_errors(query: str) -> list[ErrorEntry]:
    return get_library().search(query)


def get_error_by_id(error_id: str) -> Optional[ErrorEntry]:
    return get_library().get_by_id(error_id)


def get_all_errors() -> list[ErrorEntry]:
    return get_library().get_all()


def get_all_categories() -> list[str]:
    return get_library().get_categories()
