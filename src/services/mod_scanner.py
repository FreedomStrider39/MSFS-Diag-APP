import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModInfo:
    name: str = ""
    path: str = ""
    size_mb: float = 0.0
    has_wasm: bool = False
    has_cfg: bool = False
    has_texture: bool = False
    has_model: bool = False
    subfolder_count: int = 0
    issues: list = field(default_factory=list)


@dataclass
class ScanResult:
    community_path: str = ""
    total_mods: int = 0
    total_size_gb: float = 0.0
    mods: list = field(default_factory=list)
    duplicate_names: list = field(default_factory=list)
    broken_wasm: list = field(default_factory=list)
    large_mods: list = field(default_factory=list)
    warnings: list = field(default_factory=list)


class ModScanner:
    WASM_EXTENSIONS = {".wasm", ".dll"}
    CFG_EXTENSIONS = {".cfg", ".json", ".xml"}
    TEXTURE_EXTENSIONS = {".dds", ".png", ".jpg", ".bmp", ".tga"}
    MODEL_EXTENSIONS = {".gltf", ".bin", ".modelLibrary"}

    LARGE_MOD_THRESHOLD_MB = 2000

    def __init__(self):
        self._result: Optional[ScanResult] = None

    def scan(self, community_path: Optional[Path] = None) -> ScanResult:
        if community_path is None:
            community_path = self._find_community_folder()

        result = ScanResult()
        if not community_path or not community_path.exists():
            result.warnings.append("Community folder not found.")
            self._result = result
            return result

        result.community_path = str(community_path)

        mod_names = {}
        for item in sorted(community_path.iterdir()):
            if not item.is_dir():
                continue

            mod = ModInfo(name=item.name, path=str(item))
            self._scan_mod_folder(item, mod)
            result.mods.append(mod)
            result.total_mods += 1
            result.total_size_gb += mod.size_mb / 1024

            if item.name in mod_names:
                mod_names[item.name].append(mod)
            else:
                mod_names[item.name] = [mod]

        for name, mods in mod_names.items():
            if len(mods) > 1:
                result.duplicate_names.append({
                    "name": name,
                    "count": len(mods),
                    "paths": [m.path for m in mods],
                })

        for mod in result.mods:
            if mod.size_mb > self.LARGE_MOD_THRESHOLD_MB:
                result.large_mods.append({
                    "name": mod.name,
                    "size_mb": round(mod.size_mb, 1),
                })

        self._result = result
        return result

    def _scan_mod_folder(self, folder: Path, mod: ModInfo):
        total_size = 0
        for f in folder.rglob("*"):
            if f.is_file():
                total_size += f.stat().st_size
                ext = f.suffix.lower()

                if ext in self.WASM_EXTENSIONS:
                    mod.has_wasm = True
                    if ext == ".wasm":
                        if f.stat().st_size == 0:
                            mod.issues.append(f"Empty WASM file: {f.name}")
                elif ext in self.CFG_EXTENSIONS:
                    mod.has_cfg = True
                elif ext in self.TEXTURE_EXTENSIONS:
                    mod.has_texture = True
                elif ext in self.MODEL_EXTENSIONS:
                    mod.has_model = True

        mod.size_mb = round(total_size / (1024 * 1024), 1)
        mod.subfolder_count = sum(1 for d in folder.rglob("*") if d.is_dir())

        if not mod.has_wasm and not mod.has_cfg and not mod.has_texture:
            mod.issues.append("Mod has no recognized content files (WASM, CFG, textures).")

    def _find_community_folder(self) -> Optional[Path]:
        from .config_parser import ConfigParser
        parser = ConfigParser()
        return parser.find_community_folder()

    def get_summary(self) -> str:
        result = self._result or self.scan()
        lines = [
            f"Community Folder: {result.community_path}",
            f"Total Mods: {result.total_mods}",
            f"Total Size: {result.total_size_gb:.1f} GB",
            "",
        ]

        if result.duplicate_names:
            lines.append(f"DUPLICATE MOD NAMES ({len(result.duplicate_names)}):")
            for dup in result.duplicate_names:
                lines.append(f"  {dup['name']} ({dup['count']} copies)")
            lines.append("")

        issues = [m for m in result.mods if m.issues]
        if issues:
            lines.append(f"MODS WITH ISSUES ({len(issues)}):")
            for mod in issues:
                lines.append(f"  {mod.name}: {'; '.join(mod.issues)}")
            lines.append("")

        if result.large_mods:
            lines.append(f"LARGE MODS ({len(result.large_mods)}):")
            for lm in sorted(result.large_mods, key=lambda x: x["size_mb"], reverse=True):
                lines.append(f"  {lm['name']}: {lm['size_mb']} MB")
            lines.append("")

        if result.warnings:
            lines.append("WARNINGS:")
            for w in result.warnings:
                lines.append(f"  {w}")

        return "\n".join(lines)
