import platform
import subprocess
import json
from dataclasses import dataclass, field
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None

try:
    import wmi
except ImportError:
    wmi = None


@dataclass
class CPUInfo:
    name: str = "Unknown"
    cores_physical: int = 0
    cores_logical: int = 0
    max_ghz: float = 0.0


@dataclass
class GPUInfo:
    name: str = "Unknown"
    vram_mb: int = 0
    driver_version: str = "Unknown"


@dataclass
class MonitorInfo:
    name: str = "Unknown"
    width: int = 1920
    height: int = 1080
    refresh_hz: int = 60


@dataclass
class SystemInfo:
    os_name: str = ""
    os_version: str = ""
    ram_total_gb: float = 0.0
    ram_available_gb: float = 0.0
    cpu: CPUInfo = field(default_factory=CPUInfo)
    gpu: GPUInfo = field(default_factory=GPUInfo)
    monitor: MonitorInfo = field(default_factory=MonitorInfo)


class HardwareInfo:
    def __init__(self):
        self._cache: Optional[SystemInfo] = None

    def get_all(self, force: bool = False) -> SystemInfo:
        if self._cache and not force:
            return self._cache

        info = SystemInfo()
        info.os_name = platform.system()
        info.os_version = platform.version()

        self._fill_cpu(info)
        self._fill_ram(info)
        self._fill_gpu(info)
        self._fill_monitor(info)

        self._cache = info
        return info

    def _fill_cpu(self, info: SystemInfo):
        if psutil:
            freq = psutil.cpu_freq()
            info.cpu = CPUInfo(
                name=platform.processor() or "Unknown",
                cores_physical=psutil.cpu_count(logical=False) or 0,
                cores_logical=psutil.cpu_count(logical=True) or 0,
                max_ghz=round(freq.max / 1000, 2) if freq and freq.max else 0.0,
            )
        else:
            info.cpu = CPUInfo(name=platform.processor() or "Unknown")

    def _fill_ram(self, info: SystemInfo):
        if psutil:
            mem = psutil.virtual_memory()
            info.ram_total_gb = round(mem.total / (1024**3), 1)
            info.ram_available_gb = round(mem.available / (1024**3), 1)

    def _fill_gpu(self, info: SystemInfo):
        gpu = GPUInfo()
        try:
            if wmi:
                c = wmi.WMI(namespace="root\\cimv2")
                for item in c.Win32_VideoController():
                    gpu.name = item.Name or "Unknown"
                    adapter_ram = int(item.AdapterRAM or 0)
                    if adapter_ram > 0 and adapter_ram < 2147483647:
                        gpu.vram_mb = adapter_ram // (1024 * 1024)
                    gpu.driver_version = item.DriverVersion or "Unknown"
                    break
            else:
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-CimInstance Win32_VideoController | Select-Object Name, AdapterRAM, DriverVersion | ConvertTo-Json"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0 and result.stdout.strip():
                    data = json.loads(result.stdout)
                    if isinstance(data, list):
                        data = data[0]
                    gpu.name = data.get("Name", "Unknown")
                    adapter_ram = int(data.get("AdapterRAM", 0))
                    if adapter_ram > 0 and adapter_ram < 2147483647:
                        gpu.vram_mb = adapter_ram // (1024 * 1024)
                    gpu.driver_version = data.get("DriverVersion", "Unknown")

        except Exception:
            pass

        if gpu.vram_mb <= 0:
            gpu.vram_mb = self._get_vram_fallback()

        if gpu.vram_mb <= 0:
            gpu.vram_mb = self._get_vram_amd_fallback(gpu.name)

        info.gpu = gpu

    def _get_vram_fallback(self) -> int:
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return int(result.stdout.strip().split("\n")[0])
        except Exception:
            pass
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-CimInstance Win32_VideoController | Where-Object { $_.AdapterRAM -gt 0 }).AdapterRAM"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                val = int(result.stdout.strip().split("\n")[0].strip())
                if val > 0 and val < 2147483647:
                    return val // (1024 * 1024)
        except Exception:
            pass
        return 0

    def _get_vram_amd_fallback(self, gpu_name: str) -> int:
        if "amd" in gpu_name.lower() or "radeon" in gpu_name.lower():
            try:
                result = subprocess.run(
                    ["powershell", "-Command",
                     "Get-CimInstance Win32_VideoController | Select-Object AdapterRAM | ConvertTo-Json"],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and result.stdout.strip():
                    data = json.loads(result.stdout)
                    if isinstance(data, list):
                        for item in data:
                            ram = int(item.get("AdapterRAM", 0))
                            if ram > 0 and ram < 2147483647:
                                return ram // (1024 * 1024)
                    else:
                        ram = int(data.get("AdapterRAM", 0))
                        if ram > 0 and ram < 2147483647:
                            return ram // (1024 * 1024)
            except Exception:
                pass
        return 0

    def _fill_monitor(self, info: SystemInfo):
        monitor = MonitorInfo()
        try:
            import ctypes
            user32 = ctypes.windll.user32
            monitor.width = user32.GetSystemMetrics(0)
            monitor.height = user32.GetSystemMetrics(1)
        except Exception:
            pass

        if monitor.width <= 0 or monitor.height <= 0:
            try:
                import ctypes
                user32 = ctypes.windll.user32
                monitor.width = user32.GetSystemMetrics(0)
                monitor.height = user32.GetSystemMetrics(1)
            except Exception:
                pass

        try:
            import ctypes
            user32 = ctypes.windll.user32
            monitor.refresh_hz = 60
            try:
                dev_mode = ctypes.wintypes.DEVMODEW()
                dev_mode.dmSize = ctypes.sizeof(dev_mode)
                if user32.EnumDisplaySettingsW(None, -1, dev_mode):
                    if hasattr(dev_mode, 'dmDisplayFrequency') and dev_mode.dmDisplayFrequency > 0:
                        monitor.refresh_hz = dev_mode.dmDisplayFrequency
            except Exception:
                pass
        except Exception:
            pass

        info.monitor = monitor

    def get_summary(self) -> str:
        info = self.get_all()
        return (
            f"OS: {info.os_name} {info.os_version}\n"
            f"CPU: {info.cpu.name} ({info.cpu.cores_physical}C/{info.cpu.cores_logical}T @ {info.cpu.max_ghz} GHz)\n"
            f"RAM: {info.ram_total_gb} GB total, {info.ram_available_gb} GB available\n"
            f"GPU: {info.gpu.name} ({info.gpu.vram_mb} MB VRAM)\n"
            f"Driver: {info.gpu.driver_version}\n"
            f"Monitor: {info.monitor.width}x{info.monitor.height} @ {info.monitor.refresh_hz} Hz"
        )
