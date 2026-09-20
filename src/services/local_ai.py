import re
from dataclasses import dataclass

from src.services.error_library import (
    get_all_errors,
    search_errors,
    get_error_by_id,
    get_all_categories,
    ErrorEntry,
)


@dataclass
class DiagnosticResult:
    title: str = ""
    explanation: str = ""
    cause: str = ""
    fixes: list = None
    severity: str = "info"
    category: str = "general"
    related_errors: list = None
    references: list = None

    def __post_init__(self):
        if self.fixes is None:
            self.fixes = []
        if self.related_errors is None:
            self.related_errors = []
        if self.references is None:
            self.references = []

    def to_text(self) -> str:
        parts = [
            f"=== {self.title} ===",
            f"Severity: {self.severity.upper()}",
            f"Category: {self.category}",
            "",
            "What happened:",
            self.explanation,
            "",
            "Most likely cause:",
            self.cause,
            "",
            "Recommended fixes:",
        ]
        for i, fix in enumerate(self.fixes, 1):
            parts.append(f"  {i}. {fix}")
        if self.references:
            parts.append("")
            parts.append("References:")
            for ref in self.references:
                parts.append(f"  {ref}")
        return "\n".join(parts)


class LocalDiagnostics:

    def _error_entry_to_result(self, entry: ErrorEntry, extra_context: str = "") -> DiagnosticResult:
        explanation = entry.description
        if extra_context:
            explanation += f"\n\n{extra_context}"

        causes_text = "\n".join(f"  - {c}" for c in entry.causes) if entry.causes else "Unknown"

        return DiagnosticResult(
            title=entry.name,
            explanation=explanation,
            cause=causes_text,
            fixes=list(entry.fixes),
            severity=entry.severity,
            category=entry.category,
            references=list(entry.references),
        )

    def analyze_crash(self, crash_details: dict, raw_message: str = "") -> DiagnosticResult:
        faulting_module = crash_details.get("faulting_module", "")
        exception_code = crash_details.get("exception_code", "")
        full_text = f"{faulting_module} {exception_code} {raw_message}".lower()

        matched_entries: list[ErrorEntry] = []

        for entry in get_all_errors():
            score = 0
            for term in entry.search_terms:
                if term.lower() in full_text:
                    score += 2
            for dll in entry.related_dlls:
                if dll.lower() in full_text:
                    score += 3
            for code in entry.related_codes:
                if code.lower() in full_text:
                    score += 5
            if faulting_module:
                if faulting_module.lower() in entry.name.lower() or faulting_module.lower() in entry.description.lower():
                    score += 4
            if score > 0:
                matched_entries.append((score, entry))

        matched_entries.sort(key=lambda x: x[0], reverse=True)

        if matched_entries:
            best_score, best_entry = matched_entries[0]
            context_parts = []
            if faulting_module:
                context_parts.append(f"Faulting module: {faulting_module}")
            if exception_code:
                context_parts.append(f"Exception code: {exception_code}")
            context = "\n".join(context_parts)

            result = self._error_entry_to_result(best_entry, context)

            if len(matched_entries) > 1:
                result.related_errors = [
                    f"{e.name} (ID: {e.id})" for _, e in matched_entries[1:4]
                ]

            return result

        all_errors = get_all_errors()
        for entry in all_errors:
            if exception_code and exception_code in entry.related_codes:
                return self._error_entry_to_result(entry, f"Exception code: {exception_code}")

        return DiagnosticResult(
            title="General Crash Detected",
            explanation="A crash event was found but the specific cause could not be determined from the available information.",
            cause="Unknown - requires manual investigation. Check the crash details below for more clues.",
            fixes=[
                "Check the faulting module name in the crash details",
                "Remove all Community folder add-ons and test stability",
                "Clean-install GPU drivers using DDU in Safe Mode",
                "Run sfc /scannow and DISM restorehealth as admin",
                "Verify MSFS files or Repair the app",
                "Search the MSFS forums for the specific faulting module name",
                "As a last resort, reinstall MSFS completely",
            ],
            severity="medium",
            category="General",
        )

    def analyze_error_code(self, error_code: str) -> DiagnosticResult:
        results = search_errors(error_code)
        if results:
            return self._error_entry_to_result(results[0], f"Error code: {error_code}")

        code_explanations = {
            "0xc0000005": "Access Violation - MSFS tried to access invalid memory. Often caused by add-ons, driver issues, or corrupted files.",
            "0xc000000d": "Invalid Parameter - A function received bad data. Usually indicates corrupted installation or add-on bug.",
            "0xc0000135": "DLL Not Found - A required system library is missing. Install VC++ Redistributables and run sfc /scannow.",
            "0xc000007b": "Bad Image Format - 32/64 bit DLL mismatch. Reinstall VC++ Redistributables (both x86 and x64).",
            "0x80070005": "Access Denied - Permission issue. Run MSFS as Administrator and check folder permissions.",
            "0x80004005": "Unspecified Error - Generic failure. Check Event Viewer for more details.",
            "0xc0000409": "Stack Buffer Overrun - Memory corruption. Install English language pack, set locale to English (US).",
            "0x80000003": "Breakpoint Reached - Debug assertion triggered. For Intel 14th gen: update BIOS microcode.",
            "0xc000012f": "Bad Image - Corrupted DLL. Run sfc /scannow and DISM, then verify MSFS files.",
            "0x887a0006": "DXGI_DEVICE_HUNG - GPU hung. Disable MSI Afterburner/RTSS, lower settings, clean-install drivers.",
            "0x887a0005": "DXGI_DEVICE_REMOVED - GPU physically removed or severe driver crash. Check GPU hardware and power.",
            "0x887a0004": "DXGI_UNSUPPORTED - GPU doesn't support required Shader Model. MSFS 2024 needs SM 6.7 (GTX 1080+).",
        }

        explanation = code_explanations.get(
            error_code.lower(),
            f"Windows error code {error_code} encountered. Check Event Viewer for detailed information.",
        )

        return DiagnosticResult(
            title=f"Windows Error: {error_code}",
            explanation=explanation,
            cause="This error code indicates a specific failure mode. See explanation for likely causes.",
            fixes=[
                "Run sfc /scannow as administrator",
                "Clean-install GPU drivers using DDU",
                "Check Windows Event Viewer for additional context",
                "Search MSFS forums for this specific error code",
                "Verify MSFS installation files",
            ],
            severity="high",
            category="System",
        )

    def analyze_mod_issues(self, scan_result) -> list[DiagnosticResult]:
        results = []

        for dup in scan_result.duplicate_names:
            entry = get_error_by_id("MOD_001")
            if entry:
                result = self._error_entry_to_result(entry)
                result.title = f"Duplicate Add-on: {dup['name']}"
                result.explanation = (
                    f"Found {dup['count']} copies of '{dup['name']}' in your Community folder.\n\n"
                    f"{entry.description}"
                )
                results.append(result)
            else:
                results.append(DiagnosticResult(
                    title=f"Duplicate Add-on: {dup['name']}",
                    explanation=f"Found {dup['count']} copies of '{dup['name']}' in your Community folder.",
                    cause="Multiple installations of the same add-on can cause conflicts.",
                    fixes=[
                        f"Remove all but one copy of '{dup['name']}'",
                        "Keep the most recent version",
                        "Check if they are actually different add-ons with the same name",
                    ],
                    severity="low",
                    category="Add-ons",
                ))

        mod_issue_map = {
            "layout.json missing": "MOD_001",
            "empty wasm": "WASM_001",
            "no content": "MOD_001",
        }

        for mod in scan_result.mods:
            if mod.issues:
                for issue in mod.issues:
                    issue_lower = issue.lower()
                    matched_id = None
                    if "empty" in issue_lower and "wasm" in issue_lower:
                        matched_id = "WASM_001"
                    elif "layout.json" in issue_lower:
                        matched_id = "MOD_001"
                    elif "no recognized" in issue_lower:
                        matched_id = "MOD_001"

                    if matched_id:
                        entry = get_error_by_id(matched_id)
                        if entry:
                            result = self._error_entry_to_result(entry)
                            result.title = f"{entry.name} - {mod.name}"
                            result.explanation = f"Add-on '{mod.name}': {issue}\n\n{entry.description}"
                            results.append(result)
                        else:
                            results.append(DiagnosticResult(
                                title=f"Add-on Issue - {mod.name}",
                                explanation=issue,
                                cause="Incomplete or corrupted add-on installation.",
                                fixes=[
                                    "Re-download the add-on from the original source",
                                    "Verify the add-on is compatible with your MSFS version",
                                    "Check the add-on developer's website for updates",
                                ],
                                severity="medium",
                                category="Add-ons",
                            ))

        return results

    def get_system_tips(self, hardware_info) -> list[str]:
        tips = []
        info = hardware_info.get_all()

        if info.ram_total_gb < 16:
            tips.append("Your system has less than 16GB RAM. MSFS recommends 32GB for best experience. Close unnecessary background apps.")
        elif info.ram_total_gb < 32:
            tips.append("You have 16-32GB RAM. For ultra settings, 32GB is recommended.")

        if info.gpu.vram_mb > 0 and info.gpu.vram_mb < 4000:
            tips.append("Your GPU has less than 4GB VRAM. Use lower texture resolution (1024) and render scale (80-90%).")
        elif info.gpu.vram_mb >= 4000 and info.gpu.vram_mb < 8000:
            tips.append("Your GPU has 4-8GB VRAM. Medium-high settings should work well.")

        gpu_name = info.gpu.name.lower()
        if "laptop" in gpu_name:
            tips.append("You're on a laptop GPU. Ensure your laptop is plugged in and set to high performance mode for MSFS.")
        if "intel" in gpu_name and "iris" in gpu_name:
            tips.append("Intel integrated graphics are not recommended for MSFS. A dedicated GPU is strongly recommended.")

        if info.cpu.cores_physical < 4:
            tips.append("MSFS benefits from 6+ CPU cores. Consider upgrading your CPU for better performance.")

        return tips

    def get_error_library_stats(self) -> dict:
        all_errors = get_all_errors()
        categories = {}
        severities = {}
        for e in all_errors:
            categories[e.category] = categories.get(e.category, 0) + 1
            severities[e.severity] = severities.get(e.severity, 0) + 1
        return {
            "total_errors": len(all_errors),
            "categories": categories,
            "severities": severities,
            "all_categories": get_all_categories(),
        }
