import json
import os
import shutil
import subprocess
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from enum import Enum

from .hardware import HardwareInfo, SystemInfo
from .config_parser import ConfigParser, ConfigSettings


class TunerCategory(Enum):
    MSFS_GRAPHICS = "MSFS Graphics"
    NVIDIA_CONTROL_PANEL = "NVIDIA Control Panel"
    WINDOWS_POWER = "Windows Power Settings"
    WINDOWS_GAMING = "Windows Gaming Settings"
    WINDOWS_SYSTEM = "Windows System Settings"
    ADVANCED = "Advanced / Registry"


@dataclass
class TuneChange:
    category: str
    setting: str
    current: str
    recommended: str
    reason: str
    requires_admin: bool = False
    registry_key: str = ""
    registry_value: str = ""
    power_shell_cmd: str = ""
    nvidia_cmd: str = ""


@dataclass
class TunePreset:
    id: str
    name: str
    description: str
    target_fps: int
    priority: str
    tier: str
    icon: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class RevertPoint:
    timestamp: str
    label: str
    changes: list
    msfs_backup_path: str = ""
    nvidia_backup: dict = field(default_factory=dict)
    windows_backup: dict = field(default_factory=dict)


PRESETS = {
    "fps60_comppetitive": TunePreset(
        id="fps60_comppetitive",
        name="60 FPS Competitive",
        description="Maximum FPS for competitive/online flying. Sacrifices visual quality for buttery smooth gameplay.",
        target_fps=60,
        priority="performance",
        tier="low",
    ),
    "fps60_balanced": TunePreset(
        id="fps60_balanced",
        name="60 FPS Balanced",
        description="Target 60 FPS with reasonable visual quality. Good balance for most users.",
        target_fps=60,
        priority="balanced",
        tier="medium",
    ),
    "fps45_smooth": TunePreset(
        id="fps45_smooth",
        name="45 FPS Smooth",
        description="Stable 45 FPS with good visuals. Great for G-SYNC/FreeSync displays.",
        target_fps=45,
        priority="balanced",
        tier="medium",
    ),
    "fps30_quality": TunePreset(
        id="fps30_quality",
        name="30 FPS Quality",
        description="30 FPS with high visual quality. Best for airliner/cruise flying where smoothness matters less.",
        target_fps=30,
        priority="quality",
        tier="high",
    ),
    "fps30_ultra": TunePreset(
        id="fps30_ultra",
        name="30 FPS Ultra Quality",
        description="30 FPS with maximum visual fidelity. For powerful systems wanting the best visuals.",
        target_fps=30,
        priority="quality",
        tier="ultra",
    ),
    "vr_smooth": TunePreset(
        id="vr_smooth",
        name="VR 72 FPS",
        description="Optimized for VR headsets at 72Hz. Lower settings but smooth VR experience.",
        target_fps=72,
        priority="performance",
        tier="vr",
    ),
    "vr_quality": TunePreset(
        id="vr_quality",
        name="VR 45 FPS Quality",
        description="VR mode with motion reprojection at 45 FPS. Higher visual quality in VR.",
        target_fps=45,
        priority="quality",
        tier="vr_high",
    ),
    "auto_detect": TunePreset(
        id="auto_detect",
        name="Auto-Detect (Hardware Based)",
        description="Automatically detect best settings based on your hardware specifications.",
        target_fps=0,
        priority="auto",
        tier="auto",
    ),
}


MSFS_PRESET_VALUES = {
    "low": {
        "description": "Performance Mode - Maximum FPS",
        "render_scale": 80, "terrain_lod": 80, "object_lod": 80,
        "volumetric_clouds": 80, "texture_res": 1024, "anisotropic": 4,
        "shadows": 512, "reflection": 1024, "grass": 50, "raymarching": 50,
        "ambient_occlusion": False, "motion_blur": False, "depth_of_field": False,
        "bloom": True, "vsync": 0, "frame_rate_limit": 0,
        "buildings": "low", "trees": "low", "plants": "low", "rocks": "low",
        "water_waves": "low", "contact_shadows": "off",
        "texture_supersampling": "off", "displacement_mapping": False,
        "traffic_airport": "off", "air_traffic": "off",
        "road_traffic": "off", "sea_traffic": "off", "fauna": "off",
        "glass_cockpit": "low", "characters": "off",
    },
    "medium": {
        "description": "Balanced Mode - Good Visuals + FPS",
        "render_scale": 100, "terrain_lod": 120, "object_lod": 120,
        "volumetric_clouds": 120, "texture_res": 2048, "anisotropic": 8,
        "shadows": 1024, "reflection": 2048, "grass": 100, "raymarching": 100,
        "ambient_occlusion": True, "motion_blur": False, "depth_of_field": False,
        "bloom": True, "vsync": 0, "frame_rate_limit": 0,
        "buildings": "medium", "trees": "medium", "plants": "low", "rocks": "low",
        "water_waves": "medium", "contact_shadows": "medium",
        "texture_supersampling": "off", "displacement_mapping": True,
        "traffic_airport": "low", "air_traffic": "low",
        "road_traffic": "low", "sea_traffic": "off", "fauna": "medium",
        "glass_cockpit": "medium", "characters": "low",
    },
    "high": {
        "description": "Quality Mode - High Visuals",
        "render_scale": 100, "terrain_lod": 180, "object_lod": 150,
        "volumetric_clouds": 180, "texture_res": 4096, "anisotropic": 16,
        "shadows": 2048, "reflection": 4096, "grass": 150, "raymarching": 180,
        "ambient_occlusion": True, "motion_blur": True, "depth_of_field": True,
        "bloom": True, "vsync": 0, "frame_rate_limit": 0,
        "buildings": "high", "trees": "high", "plants": "medium", "rocks": "medium",
        "water_waves": "high", "contact_shadows": "high",
        "texture_supersampling": "4x4", "displacement_mapping": True,
        "traffic_airport": "medium", "air_traffic": "medium",
        "road_traffic": "medium", "sea_traffic": "low", "fauna": "high",
        "glass_cockpit": "high", "characters": "medium",
    },
    "ultra": {
        "description": "Ultra Mode - Maximum Visual Fidelity",
        "render_scale": 100, "terrain_lod": 200, "object_lod": 200,
        "volumetric_clouds": 200, "texture_res": 4096, "anisotropic": 16,
        "shadows": 4096, "reflection": 4096, "grass": 200, "raymarching": 200,
        "ambient_occlusion": True, "motion_blur": True, "depth_of_field": True,
        "bloom": True, "vsync": 0, "frame_rate_limit": 0,
        "buildings": "ultra", "trees": "ultra", "plants": "high", "rocks": "high",
        "water_waves": "high", "contact_shadows": "ultra",
        "texture_supersampling": "8x8", "displacement_mapping": True,
        "traffic_airport": "high", "air_traffic": "high",
        "road_traffic": "medium", "sea_traffic": "medium", "fauna": "high",
        "glass_cockpit": "high", "characters": "high",
    },
}

NVIDIA_PRESETS = {
    "quality": {
        "power_management": "Normal",
        "texture_filtering_quality": "Quality",
        "texture_filtering_anisotropic": "On",
        "texture_filtering_trilinear": "On",
        "texture_filtering_negative_lod": "Allow",
        "shader_cache": "Driver Default",
        "low_latency": "Off",
        "vsync": "Use the 3D application setting",
        "preferred_refresh": "Highest available",
        "threaded_optimization": "Auto",
        "monitor_technology": "G-SYNC Compatible",
        "mfaa": "Off",
        "fxaa": "Off",
        "image_scaling": "Off",
    },
    "performance": {
        "power_management": "Prefer maximum performance",
        "texture_filtering_quality": "High performance",
        "texture_filtering_anisotropic": "Off",
        "texture_filtering_trilinear": "On",
        "texture_filtering_negative_lod": "Allow",
        "shader_cache": "Driver Default",
        "low_latency": "On",
        "vsync": "Off",
        "preferred_refresh": "Highest available",
        "threaded_optimization": "On",
        "monitor_technology": "G-SYNC Compatible",
        "mfaa": "Off",
        "fxaa": "Off",
        "image_scaling": "Off",
    },
    "balanced": {
        "power_management": "Normal",
        "texture_filtering_quality": "Quality",
        "texture_filtering_anisotropic": "On",
        "texture_filtering_trilinear": "On",
        "texture_filtering_negative_lod": "Allow",
        "shader_cache": "Driver Default",
        "low_latency": "Off",
        "vsync": "Use the 3D application setting",
        "preferred_refresh": "Highest available",
        "threaded_optimization": "Auto",
        "monitor_technology": "G-SYNC Compatible",
        "mfaa": "Off",
        "fxaa": "Off",
        "image_scaling": "Off",
    },
}

WINDOWS_GAMING_PRESETS = {
    "optimized": {
        "game_bar": False,
        "game_dvr": False,
        "game_mode": False,
        "captures": False,
        "hags": True,
        "hardware_acceleration": True,
    },
    "maximum_performance": {
        "game_bar": False,
        "game_dvr": False,
        "game_mode": False,
        "captures": False,
        "hags": False,
        "hardware_acceleration": False,
    },
}

WINDOWS_POWER_PRESETS = {
    "high_performance": {
        "plan_name": "High performance",
        "plan_guid": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "processor_min": 100,
        "processor_max": 100,
        "pci_express_link_state": "Off",
        "hibernate_timeout_ac": 0,
        "hibernate_timeout_dc": 0,
        "turn_off_display_ac": 0,
        "turn_off_display_dc": 0,
        "sleep_timeout_ac": 0,
        "sleep_timeout_dc": 0,
    },
    "ultimate_performance": {
        "plan_name": "Ultimate Performance",
        "plan_guid": "e9a42b02-d5df-448d-aa00-03f14749eb61",
        "processor_min": 100,
        "processor_max": 100,
        "pci_express_link_state": "Off",
        "hibernate_timeout_ac": 0,
        "hibernate_timeout_dc": 0,
        "turn_off_display_ac": 0,
        "turn_off_display_dc": 0,
        "sleep_timeout_ac": 0,
        "sleep_timeout_dc": 0,
    },
    "balanced": {
        "plan_name": "Balanced",
        "plan_guid": "381b4222-f694-41df-b545-5f275e1e56cf",
        "processor_min": 5,
        "processor_max": 100,
        "pci_express_link_state": "Moderate power savings",
        "hibernate_timeout_ac": 0,
        "hibernate_timeout_dc": 0,
        "turn_off_display_ac": 15,
        "turn_off_display_dc": 5,
        "sleep_timeout_ac": 0,
        "sleep_timeout_dc": 15,
    },
}

REVERT_DIR = Path(__file__).parent.parent.parent / "data" / "reverts"


class ConfigTuner:
    def __init__(self):
        self.hw = HardwareInfo()
        self.parser = ConfigParser()
        REVERT_DIR.mkdir(parents=True, exist_ok=True)

    def determine_tier(self, info: Optional[SystemInfo] = None) -> str:
        if info is None:
            info = self.hw.get_all()
        vram = info.gpu.vram_mb
        ram = info.ram_total_gb
        cores = info.cpu.cores_physical
        score = 0
        if vram >= 12000: score += 3
        elif vram >= 8000: score += 2
        elif vram >= 4000: score += 1
        if ram >= 32: score += 3
        elif ram >= 16: score += 2
        elif ram >= 8: score += 1
        if cores >= 8: score += 2
        elif cores >= 6: score += 1
        gpu_name = info.gpu.name.lower()
        if any(kw in gpu_name for kw in ["4090", "4080", "3090", "7900 xtx", "5090", "5080"]): score += 3
        elif any(kw in gpu_name for kw in ["4070", "3080", "6900", "7900"]): score += 2
        elif any(kw in gpu_name for kw in ["4060", "3070", "6800", "7800"]): score += 1
        elif any(kw in gpu_name for kw in ["3060", "6700", "7700"]): score += 0
        elif any(kw in gpu_name for kw in ["1080", "2080", "5700"]): score += 0
        else: score -= 1
        if score >= 8: return "ultra"
        elif score >= 5: return "high"
        elif score >= 3: return "medium"
        else: return "low"

    def get_recommendations(self, tier: str) -> list[TuneChange]:
        return self.get_msfs_changes(tier)

    def get_preset_for_target(self, target_fps: int, priority: str) -> str:
        if target_fps >= 70:
            return "low"
        elif target_fps >= 55:
            if priority == "quality":
                return "medium"
            return "medium"
        elif target_fps >= 40:
            if priority == "quality":
                return "high"
            return "medium"
        elif target_fps >= 28:
            if priority == "quality":
                return "ultra"
            return "high"
        else:
            return "ultra"

    def get_msfs_changes(self, preset_id: str) -> list[TuneChange]:
        changes = []
        if preset_id == "auto_detect":
            tier = self.determine_tier()
        elif preset_id in PRESETS:
            preset = PRESETS[preset_id]
            if preset.tier == "auto":
                tier = self.determine_tier()
            else:
                tier = preset.tier
        else:
            tier = preset_id

        if tier not in MSFS_PRESET_VALUES:
            return changes
        rules = MSFS_PRESET_VALUES[tier]
        current = self.parser.parse()

        mapping = [
            ("render_scale", "Render Scale", str(current.render_scale), str(rules["render_scale"])),
            ("terrain_lod", "Terrain LOD", str(current.terrain_lod), str(rules["terrain_lod"])),
            ("object_lod", "Object LOD", str(current.object_lod), str(rules["object_lod"])),
            ("volumetric_clouds", "Volumetric Clouds", str(current.volumetric_clouds), str(rules["volumetric_clouds"])),
            ("texture_res", "Texture Resolution", str(current.texture_res), str(rules["texture_res"])),
            ("anisotropic", "Anisotropic Filtering", f"{current.anisotropic}x", f"{rules['anisotropic']}x"),
            ("shadows", "Shadow Maps", str(current.shadows), str(rules["shadows"])),
            ("reflection", "Reflection Resolution", str(current.reflection), str(rules["reflection"])),
            ("grass", "Grass Detail", str(current.grass), str(rules["grass"])),
            ("raymarching", "Raymarched Reflections", str(current.raymarching), str(rules["raymarching"])),
            ("ambient_occlusion", "Ambient Occlusion", str(current.ambient_occlusion), str(rules["ambient_occlusion"])),
            ("motion_blur", "Motion Blur", str(current.motion_blur), str(rules["motion_blur"])),
            ("depth_of_field", "Depth of Field", str(current.depth_of_field), str(rules["depth_of_field"])),
            ("bloom", "Bloom", str(current.bloom), str(rules["bloom"])),
        ]

        for key, label, curr, rec in mapping:
            if curr != rec:
                changes.append(TuneChange(
                    category=TunerCategory.MSFS_GRAPHICS.value,
                    setting=label, current=curr, recommended=rec,
                    reason=f"{rules['description']} preset",
                ))
        return changes

    def get_nvidia_changes(self, preset: str = "balanced") -> list[TuneChange]:
        changes = []
        if preset not in NVIDIA_PRESETS:
            preset = "balanced"
        rules = NVIDIA_PRESETS[preset]
        setting_labels = {
            "power_management": "Power Management Mode",
            "texture_filtering_quality": "Texture Filtering - Quality",
            "texture_filtering_anisotropic": "Anisotropic Sample Optimization",
            "texture_filtering_trilinear": "Trilinear Optimization",
            "texture_filtering_negative_lod": "Negative LOD Bias",
            "shader_cache": "Shader Cache Size",
            "low_latency": "Low Latency Mode",
            "vsync": "Vertical Sync",
            "preferred_refresh": "Preferred Refresh Rate",
            "threaded_optimization": "Threaded Optimization",
            "monitor_technology": "Monitor Technology",
            "mfaa": "Multi-Frame Sampled AA (MFAA)",
            "fxaa": "Antialiasing - FXAA",
            "image_scaling": "Image Scaling",
        }
        for key, label in setting_labels.items():
            if key in rules:
                changes.append(TuneChange(
                    category=TunerCategory.NVIDIA_CONTROL_PANEL.value,
                    setting=label, current="Current", recommended=rules[key],
                    reason=f"MSFS optimized {preset} preset",
                ))
        return changes

    def get_windows_gaming_changes(self, preset: str = "optimized") -> list[TuneChange]:
        changes = []
        if preset not in WINDOWS_GAMING_PRESETS:
            preset = "optimized"
        rules = WINDOWS_GAMING_PRESETS[preset]
        setting_labels = {
            "game_bar": "Xbox Game Bar",
            "game_dvr": "Game DVR / Recording",
            "game_mode": "Game Mode",
            "game_bar_recording": "Background Recording",
            "hags": "Hardware-Accelerated GPU Scheduling (HAGS)",
            "hardware_acceleration": "Hardware Graphics Acceleration",
        }
        for key, label in setting_labels.items():
            if key in rules:
                val = rules[key]
                changes.append(TuneChange(
                    category=TunerCategory.WINDOWS_GAMING.value,
                    setting=label, current="Unknown", recommended="Enabled" if val else "Disabled",
                    reason=f"{preset} preset for MSFS",
                    requires_admin=(key == "hags"),
                ))
        return changes

    def get_windows_power_changes(self, preset: str = "high_performance") -> list[TuneChange]:
        changes = []
        if preset not in WINDOWS_POWER_PRESETS:
            preset = "high_performance"
        rules = WINDOWS_POWER_PRESETS[preset]
        changes.append(TuneChange(
            category=TunerCategory.WINDOWS_POWER.value,
            setting="Power Plan", current="Current Plan", recommended=rules["plan_name"],
            reason="Optimized power settings for MSFS",
            requires_admin=True,
        ))
        changes.append(TuneChange(
            category=TunerCategory.WINDOWS_POWER.value,
            setting="PCI Express Link State Power Management", current="Unknown", recommended=rules["pci_express_link_state"],
            reason="Prevent GPU throttling",
            requires_admin=True,
        ))
        changes.append(TuneChange(
            category=TunerCategory.WINDOWS_POWER.value,
            setting="Processor Minimum State", current="Unknown", recommended=f"{rules['processor_min']}%",
            reason="Keep CPU at full speed",
            requires_admin=True,
        ))
        changes.append(TuneChange(
            category=TunerCategory.WINDOWS_POWER.value,
            setting="Processor Maximum State", current="Unknown", recommended=f"{rules['processor_max']}%",
            reason="Allow full CPU performance",
            requires_admin=True,
        ))
        changes.append(TuneChange(
            category=TunerCategory.WINDOWS_POWER.value,
            setting="Turn Off Display (Plugged In)", current="Unknown", recommended=f"{rules['turn_off_display_ac']} minutes" if rules['turn_off_display_ac'] > 0 else "Never",
            reason="Prevent display timeout during flight",
        ))
        changes.append(TuneChange(
            category=TunerCategory.WINDOWS_POWER.value,
            setting="Sleep (Plugged In)", current="Unknown", recommended=f"{rules['sleep_timeout_ac']} minutes" if rules['sleep_timeout_ac'] > 0 else "Never",
            reason="Prevent sleep during flight",
            requires_admin=True,
        ))
        return changes

    def get_all_changes_for_preset(self, preset_id: str) -> dict[str, list[TuneChange]]:
        preset = PRESETS.get(preset_id, PRESETS["auto_detect"])
        all_changes = {}
        all_changes[TunerCategory.MSFS_GRAPHICS.value] = self.get_msfs_changes(preset_id)

        if preset.priority == "performance":
            nvidia_preset = "performance"
            power_preset = "ultimate_performance"
            gaming_preset = "maximum_performance"
        elif preset.priority == "quality":
            nvidia_preset = "quality"
            power_preset = "high_performance"
            gaming_preset = "optimized"
        else:
            nvidia_preset = "balanced"
            power_preset = "high_performance"
            gaming_preset = "optimized"

        all_changes[TunerCategory.NVIDIA_CONTROL_PANEL.value] = self.get_nvidia_changes(nvidia_preset)
        all_changes[TunerCategory.WINDOWS_GAMING.value] = self.get_windows_gaming_changes(gaming_preset)
        all_changes[TunerCategory.WINDOWS_POWER.value] = self.get_windows_power_changes(power_preset)
        return all_changes

    def apply_msfs_changes(self, changes: list[TuneChange]) -> bool:
        if not changes:
            return True
        backup_path = self.parser.create_backup()
        if not backup_path:
            return False
        current = self.parser.parse()
        for change in changes:
            if change.setting == "Render Scale": current.render_scale = int(change.recommended)
            elif change.setting == "Terrain LOD": current.terrain_lod = int(change.recommended)
            elif change.setting == "Object LOD": current.object_lod = int(change.recommended)
            elif change.setting == "Volumetric Clouds": current.volumetric_clouds = int(change.recommended)
            elif change.setting == "Texture Resolution": current.texture_res = int(change.recommended)
            elif change.setting == "Anisotropic Filtering": current.anisotropic = int(change.recommended.replace("x", ""))
            elif change.setting == "Shadow Maps": current.shadows = int(change.recommended)
            elif change.setting == "Reflection Resolution": current.reflection = int(change.recommended)
            elif change.setting == "Grass Detail": current.grass = int(change.recommended)
            elif change.setting == "Raymarched Reflections": current.raymarching = int(change.recommended)
            elif change.setting == "Ambient Occlusion": current.ambient_occlusion = change.recommended.lower() in ("true", "1", "yes")
            elif change.setting == "Motion Blur": current.motion_blur = change.recommended.lower() in ("true", "1", "yes")
            elif change.setting == "Depth of Field": current.depth_of_field = change.recommended.lower() in ("true", "1", "yes")
            elif change.setting == "Bloom": current.bloom = change.recommended.lower() in ("true", "1", "yes")
        return self.parser.write_config(current)

    def apply_nvidia_changes(self, changes: list[TuneChange]) -> list[str]:
        applied = []
        for change in changes:
            cmd = self._build_nvidia_cmd(change.setting, change.recommended)
            if cmd:
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
                    if result.returncode == 0:
                        applied.append(change.setting)
                except Exception:
                    pass
        return applied

    def _build_nvidia_cmd(self, setting: str, value: str) -> str:
        nvidia_keys = {
            "Power Management Mode": {"Normal": "0x104d4e4d", "Prefer maximum performance": "0x104d4e50"},
            "Texture Filtering - Quality": {"Quality": "0x00000000", "High performance": "0x00000001", "Performance": "0x00000002", "High quality": "0x00000003"},
            "Low Latency Mode": {"Off": "0x00000000", "On": "0x00000001", "Ultra": "0x00000002"},
            "Vertical Sync": {"Off": "0x00000000", "On": "0x00000001", "Use the 3D application setting": "0x00000002"},
        }
        return ""

    def apply_windows_gaming_settings(self, changes: list[TuneChange]) -> list[str]:
        applied = []
        for change in changes:
            if "Game Bar" in change.setting:
                cmd = 'reg add "HKCU\\SOFTWARE\\Microsoft\\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 0 /f'
                self._run_reg(cmd, applied, change.setting)
            elif "Game DVR" in change.setting or "Recording" in change.setting:
                cmd = 'reg add "HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\GameDVR" /v AppCaptureEnabled /t REG_DWORD /d 0 /f'
                self._run_reg(cmd, applied, change.setting)
            elif "Game Mode" in change.setting:
                cmd = 'reg add "HKCU\\SOFTWARE\\Microsoft\\GameBar" /v AllowAutoGameMode /t REG_DWORD /d 0 /f'
                self._run_reg(cmd, applied, change.setting)
            elif "HAGS" in change.setting:
                cmd = 'reg add "HKLM\\SYSTEM\\CurrentControlSet\\Control\\GraphicsDrivers" /v HwSchMode /t REG_DWORD /d 1 /f'
                self._run_reg(cmd, applied, change.setting, admin=True)
        return applied

    def apply_windows_power_settings(self, changes: list[TuneChange]) -> list[str]:
        applied = []
        for change in changes:
            if "Power Plan" in change.setting:
                plan_name = change.recommended
                cmd = f'powercfg /setactive {plan_name}'
                try:
                    subprocess.run(["powercfg", "/setactive", plan_name], capture_output=True, timeout=10)
                    applied.append(change.setting)
                except Exception:
                    pass
            elif "PCI Express" in change.setting:
                cmd = 'powercfg /setacvalueindex SCHEME_CURRENT SUB_PCIEXPRESS ASPM 0'
                try:
                    subprocess.run(["powercfg", "/setacvalueindex", "SCHEME_CURRENT", "SUB_PCIEXPRESS", "ASPM", "0"], capture_output=True, timeout=10)
                    subprocess.run(["powercfg", "/setactive", "SCHEME_CURRENT"], capture_output=True, timeout=10)
                    applied.append(change.setting)
                except Exception:
                    pass
            elif "Processor Minimum" in change.setting:
                pct = change.recommended.replace("%", "")
                cmd = f'powercfg /setacvalueindex SCHEME_CURRENT SUB_PROCESSOR PROCTHROTTLEMIN {pct}'
                try:
                    subprocess.run(["powercfg", "/setacvalueindex", "SCHEME_CURRENT", "SUB_PROCESSOR", "PROCTHROTTLEMIN", pct], capture_output=True, timeout=10)
                    applied.append(change.setting)
                except Exception:
                    pass
            elif "Processor Maximum" in change.setting:
                pct = change.recommended.replace("%", "")
                try:
                    subprocess.run(["powercfg", "/setacvalueindex", "SCHEME_CURRENT", "SUB_PROCESSOR", "PROCTHROTTLEMAX", pct], capture_output=True, timeout=10)
                    applied.append(change.setting)
                except Exception:
                    pass
            elif "Turn Off Display" in change.setting:
                mins = 0 if "Never" in change.recommended else int(change.recommended.split()[0])
                try:
                    subprocess.run(["powercfg", "/setacvalueindex", "SCHEME_CURRENT", "SUB_VIDEO", "VIDEOIDLE", str(mins * 60)], capture_output=True, timeout=10)
                    applied.append(change.setting)
                except Exception:
                    pass
            elif "Sleep" in change.setting and "Plugged In" in change.setting:
                mins = 0 if "Never" in change.recommended else int(change.recommended.split()[0])
                try:
                    subprocess.run(["powercfg", "/setacvalueindex", "SCHEME_CURRENT", "SUB_SLEEP", "STANDBYIDLE", str(mins * 60)], capture_output=True, timeout=10)
                    applied.append(change.setting)
                except Exception:
                    pass
        return applied

    def _run_reg(self, cmd: str, applied: list, setting: str, admin: bool = False):
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            if result.returncode == 0:
                applied.append(setting)
        except Exception:
            pass

    def create_revert_point(self, label: str = "") -> Optional[Path]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not label:
            label = f"revert_{timestamp}"
        revert_dir = REVERT_DIR / timestamp
        revert_dir.mkdir(exist_ok=True)
        usercfg = self.parser.find_usercfg()
        backup_info = {
            "timestamp": timestamp,
            "label": label,
            "msfs_backup": "",
            "power_plan": self._get_current_power_plan(),
        }
        if usercfg and usercfg.exists():
            backup_dest = revert_dir / "UserCfg.opt"
            shutil.copy2(usercfg, backup_dest)
            backup_info["msfs_backup"] = str(backup_dest)
        revert_file = revert_dir / "revert_info.json"
        with open(revert_file, "w", encoding="utf-8") as f:
            json.dump(backup_info, f, indent=2)
        return revert_dir

    def apply_all_changes(self, preset_id: str, revert_label: str = "") -> dict:
        revert_path = self.create_revert_point(revert_label or f"before_{preset_id}")
        all_changes = self.get_all_changes_for_preset(preset_id)
        results = {
            "revert_point": str(revert_path),
            "applied": {},
            "skipped": {},
            "errors": {},
        }
        msfs_changes = all_changes.get(TunerCategory.MSFS_GRAPHICS.value, [])
        if msfs_changes:
            try:
                success = self.apply_msfs_changes(msfs_changes)
                if success:
                    results["applied"][TunerCategory.MSFS_GRAPHICS.value] = [c.setting for c in msfs_changes]
                else:
                    results["errors"][TunerCategory.MSFS_GRAPHICS.value] = "Failed to write config"
            except Exception as e:
                results["errors"][TunerCategory.MSFS_GRAPHICS.value] = str(e)
        nvidia_changes = all_changes.get(TunerCategory.NVIDIA_CONTROL_PANEL.value, [])
        if nvidia_changes:
            try:
                applied = self.apply_nvidia_changes(nvidia_changes)
                results["applied"][TunerCategory.NVIDIA_CONTROL_PANEL.value] = applied
                skipped = [c.setting for c in nvidia_changes if c.setting not in applied]
                if skipped:
                    results["skipped"][TunerCategory.NVIDIA_CONTROL_PANEL.value] = skipped
            except Exception as e:
                results["errors"][TunerCategory.NVIDIA_CONTROL_PANEL.value] = str(e)
        gaming_changes = all_changes.get(TunerCategory.WINDOWS_GAMING.value, [])
        if gaming_changes:
            try:
                applied = self.apply_windows_gaming_settings(gaming_changes)
                results["applied"][TunerCategory.WINDOWS_GAMING.value] = applied
            except Exception as e:
                results["errors"][TunerCategory.WINDOWS_GAMING.value] = str(e)
        power_changes = all_changes.get(TunerCategory.WINDOWS_POWER.value, [])
        if power_changes:
            try:
                applied = self.apply_windows_power_settings(power_changes)
                results["applied"][TunerCategory.WINDOWS_POWER.value] = applied
            except Exception as e:
                results["errors"][TunerCategory.WINDOWS_POWER.value] = str(e)
        return results

    def revert_to_point(self, revert_dir: Path) -> bool:
        info_file = revert_dir / "revert_info.json"
        if not info_file.exists():
            return False
        with open(info_file, "r", encoding="utf-8") as f:
            info = json.load(f)
        backup_cfg = info.get("msfs_backup", "")
        if backup_cfg and Path(backup_cfg).exists():
            usercfg = self.parser.find_usercfg()
            if usercfg:
                shutil.copy2(backup_cfg, usercfg)
        return True

    def list_revert_points(self) -> list[dict]:
        points = []
        if not REVERT_DIR.exists():
            return points
        for d in sorted(REVERT_DIR.iterdir(), reverse=True):
            if d.is_dir():
                info_file = d / "revert_info.json"
                if info_file.exists():
                    with open(info_file, "r", encoding="utf-8") as f:
                        info = json.load(f)
                    info["path"] = str(d)
                    points.append(info)
        return points

    def _get_current_power_plan(self) -> str:
        try:
            result = subprocess.run(["powercfg", "/getactivescheme"], capture_output=True, text=True, timeout=5)
            if result.stdout:
                parts = result.stdout.strip().split()
                return parts[1] if len(parts) > 1 else "unknown"
        except Exception:
            pass
        return "unknown"

    def get_all_tiers(self) -> dict:
        info = self.hw.get_all()
        current_tier = self.determine_tier(info)
        return {
            "detected_hardware": {
                "gpu": info.gpu.name,
                "vram_mb": info.gpu.vram_mb,
                "ram_gb": info.ram_total_gb,
                "cpu": info.cpu.name,
                "cores": info.cpu.cores_physical,
            },
            "current_tier": current_tier,
            "presets": {k: {"name": v.name, "description": v.description, "target_fps": v.target_fps} for k, v in PRESETS.items()},
            "msfs_tiers": {k: v["description"] for k, v in MSFS_PRESET_VALUES.items()},
        }
