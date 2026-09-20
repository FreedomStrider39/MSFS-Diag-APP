import os
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class ConfigSettings:
    """Parsed MSFS UserCfg.opt settings."""
    ultra_quality: bool = False
    render_scale: int = 100
    terrain_lod: int = 200
    object_lod: int = 200
    volumetric_clouds: int = 200
    texture_res: int = 2048
    anisotropic: int = 16
    shadows: int = 2048
    reflection: int = 2048
    grass: int = 200
    raymarching: int = 200
    ambient_occlusion: bool = True
    motion_blur: bool = True
    depth_of_field: bool = True
    bloom: bool = True
    vsync: int = 1
    frame_rate_limit: int = 0
    fullscreen: bool = True
    raw_lines: list = field(default_factory=list)


class ConfigParser:
    USERCFG_FILENAME = "UserCfg.opt"

    def __init__(self):
        self._config_path: Optional[Path] = None
        self._msfs_path: Optional[Path] = None
        self._community_path: Optional[Path] = None

    def _get_search_paths(self) -> list[Path]:
        paths = []
        local = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")
        home = os.path.expanduser("~")

        paths.append(Path(local) / "Packages" / "Microsoft.FlightSimulator_8wekyb3d8bbwe" / "LocalCache")
        paths.append(Path(local) / "Packages" / "Microsoft.FlightSimulator2024_8wekyb3d8bbwe" / "LocalCache")
        paths.append(Path(appdata) / "Microsoft Flight Simulator")
        paths.append(Path(appdata) / "Microsoft Flight Simulator 2024")
        paths.append(Path(local) / "Microsoft Flight Simulator")
        paths.append(Path(local) / "Microsoft Flight Simulator 2024")
        paths.append(Path(home) / "AppData" / "Local" / "Microsoft Flight Simulator")
        paths.append(Path(home) / "AppData" / "Local" / "Microsoft Flight Simulator 2024")

        steam_common_paths = []
        for drive in "CDEFGH":
            steam_common_paths.append(Path(f"{drive}:/Program Files (x86)/Steam/steamapps/common"))
            steam_common_paths.append(Path(f"{drive}:/Steam/steamapps/common"))
            steam_common_paths.append(Path(f"{drive}:/Games/Steam/steamapps/common"))
            steam_common_paths.append(Path(f"{drive}:/SteamLibrary/steamapps/common"))

        for common in steam_common_paths:
            for sim_dir in ["FlightSimulator", "MicrosoftFlightSimulator", "Microsoft Flight Simulator"]:
                paths.append(common / sim_dir)

        libraryfolders = Path("C:/Program Files (x86)/Steam/steamapps/libraryfolders.vdf")
        if libraryfolders.exists():
            try:
                import re as _re
                content = libraryfolders.read_text(encoding="utf-8", errors="ignore")
                for match in _re.finditer(r'"path"\s+"([^"]+)"', content):
                    lib_path = Path(match.group(1).replace("\\\\", "/"))
                    steamapps = lib_path / "steamapps" / "common"
                    if steamapps.exists():
                        for sim_dir in ["FlightSimulator", "MicrosoftFlightSimulator", "Microsoft Flight Simulator"]:
                            paths.append(steamapps / sim_dir)
            except Exception:
                pass

        ms_store_base = Path(local) / "Packages"
        if ms_store_base.exists():
            for item in ms_store_base.iterdir():
                if item.is_dir():
                    name_lower = item.name.lower()
                    if ("flight" in name_lower and "simulator" in name_lower) or "flightsimulator" in name_lower:
                        paths.append(item / "LocalCache")

        return paths

    def find_msfs_path(self, clear_cache: bool = False) -> Optional[Path]:
        if clear_cache:
            self._msfs_path = None
            self._config_path = None

        if self._msfs_path and self._msfs_path.exists():
            usercfg = self._msfs_path / self.USERCFG_FILENAME
            if usercfg.exists():
                self._config_path = usercfg
                return self._msfs_path

        for p in self._get_search_paths():
            if p.exists():
                usercfg = p / self.USERCFG_FILENAME
                if usercfg.exists():
                    self._msfs_path = p
                    self._config_path = usercfg
                    return p

        return None

    def set_custom_path(self, path: Path) -> bool:
        if path.exists():
            usercfg = path / self.USERCFG_FILENAME
            self._msfs_path = path
            if usercfg.exists():
                self._config_path = usercfg
            return True
        return False

    def set_custom_community_path(self, path: Path) -> bool:
        if path.exists():
            self._community_path = path
            return True
        return False

    def find_usercfg(self) -> Optional[Path]:
        if self._config_path and self._config_path.exists():
            return self._config_path
        self.find_msfs_path()
        return self._config_path

    def find_community_folder(self) -> Optional[Path]:
        if hasattr(self, '_community_path') and self._community_path and self._community_path.exists():
            return self._community_path
        msfs = self.find_msfs_path()
        if msfs:
            community = msfs / "Community"
            if community.exists():
                return community
        return None

    def create_backup(self) -> Optional[Path]:
        usercfg = self.find_usercfg()
        if not usercfg or not usercfg.exists():
            return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = usercfg.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        backup_path = backup_dir / f"UserCfg_{timestamp}.opt"
        shutil.copy2(usercfg, backup_path)
        return backup_path

    def parse(self, path: Optional[Path] = None) -> ConfigSettings:
        if path is None:
            path = self.find_usercfg()
        if not path or not path.exists():
            return ConfigSettings()

        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        settings = ConfigSettings(raw_lines=lines)

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("//") or not stripped:
                continue

            settings.ultra_quality = "Ultra" in stripped

            m = re.match(r"renderScale\s+(\d+)", stripped)
            if m:
                settings.render_scale = int(m.group(1))

            m = re.match(r"terrainLod\s+(\d+)", stripped)
            if m:
                settings.terrain_lod = int(m.group(1))

            m = re.match(r"objectLod\s+(\d+)", stripped)
            if m:
                settings.object_lod = int(m.group(1))

            m = re.match(r"volumetricClouds\s+(\d+)", stripped)
            if m:
                settings.volumetric_clouds = int(m.group(1))

            m = re.match(r"textureRes\s+(\d+)", stripped)
            if m:
                settings.texture_res = int(m.group(1))

            m = re.match(r"anisotropic\s+(\d+)", stripped)
            if m:
                settings.anisotropic = int(m.group(1))

            m = re.match(r"shadows\s+(\d+)", stripped)
            if m:
                settings.shadows = int(m.group(1))

            m = re.match(r"reflection\s+(\d+)", stripped)
            if m:
                settings.reflection = int(m.group(1))

            m = re.match(r"grass\s+(\d+)", stripped)
            if m:
                settings.grass = int(m.group(1))

            m = re.match(r"raymarching\s+(\d+)", stripped)
            if m:
                settings.raymarching = int(m.group(1))

            if "ambientOcclusion" in stripped:
                settings.ambient_occlusion = "1" in stripped or "true" in stripped.lower()
            if "motionBlur" in stripped:
                settings.motion_blur = "1" in stripped or "true" in stripped.lower()
            if "depthOfField" in stripped:
                settings.depth_of_field = "1" in stripped or "true" in stripped.lower()
            if "bloom" in stripped:
                settings.bloom = "1" in stripped or "true" in stripped.lower()

            m = re.match(r"vsync\s+(\d+)", stripped)
            if m:
                settings.vsync = int(m.group(1))

            m = re.match(r"frameRateLimit\s+(\d+)", stripped)
            if m:
                settings.frame_rate_limit = int(m.group(1))

            if "fullscreen" in stripped:
                settings.fullscreen = "1" in stripped or "true" in stripped.lower()

        return settings

    def write_config(self, settings: ConfigSettings, path: Optional[Path] = None) -> bool:
        if path is None:
            path = self.find_usercfg()
        if not path:
            return False

        new_lines = []
        for line in settings.raw_lines:
            stripped = line.strip()
            if stripped.startswith("//"):
                new_lines.append(line)
                continue

            modified = line
            if re.match(r"renderScale\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.render_scale), line)
            elif re.match(r"terrainLod\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.terrain_lod), line)
            elif re.match(r"objectLod\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.object_lod), line)
            elif re.match(r"volumetricClouds\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.volumetric_clouds), line)
            elif re.match(r"textureRes\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.texture_res), line)
            elif re.match(r"anisotropic\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.anisotropic), line)
            elif re.match(r"shadows\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.shadows), line)
            elif re.match(r"reflection\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.reflection), line)
            elif re.match(r"grass\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.grass), line)
            elif re.match(r"raymarching\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.raymarching), line)
            elif re.match(r"vsync\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.vsync), line)
            elif re.match(r"frameRateLimit\s+", stripped):
                modified = re.sub(r"\d+$", str(settings.frame_rate_limit), line)
            elif re.match(r"ambientOcclusion\s+", stripped):
                modified = re.sub(r"[01]$", "1" if settings.ambient_occlusion else "0", line)
            elif re.match(r"motionBlur\s+", stripped):
                modified = re.sub(r"[01]$", "1" if settings.motion_blur else "0", line)
            elif re.match(r"depthOfField\s+", stripped):
                modified = re.sub(r"[01]$", "1" if settings.depth_of_field else "0", line)
            elif re.match(r"bloom\s+", stripped):
                modified = re.sub(r"[01]$", "1" if settings.bloom else "0", line)
            elif re.match(r"fullscreen\s+", stripped):
                modified = re.sub(r"[01]$", "1" if settings.fullscreen else "0", line)

            new_lines.append(modified)

        try:
            path.write_text("\n".join(new_lines), encoding="utf-8")
            return True
        except Exception:
            return False

    def restore_backup(self, backup_path: Path) -> bool:
        usercfg = self.find_usercfg()
        if not usercfg or not backup_path.exists():
            return False
        try:
            shutil.copy2(backup_path, usercfg)
            return True
        except Exception:
            return False

    def list_backups(self) -> list[Path]:
        usercfg = self.find_usercfg()
        if not usercfg:
            return []
        backup_dir = usercfg.parent / "backups"
        if not backup_dir.exists():
            return []
        return sorted(backup_dir.glob("UserCfg_*.opt"), reverse=True)
