import subprocess
import re
import json
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CrashEvent:
    timestamp: str = ""
    source: str = ""
    event_id: int = 0
    level: str = ""
    message: str = ""
    faulting_module: str = ""
    exception_code: str = ""


@dataclass
class DriverInfo:
    name: str = ""
    version: str = ""
    date: str = ""


class CrashReader:
    EVENT_LOG_APP = "Application"
    EVENT_LOG_SYS = "System"
    MSFS_SOURCES = [
        "Microsoft Flight Simulator",
        "FlightSimulator",
        "MSFS",
        "SimConnect",
        "FlightSimulator.exe",
    ]

    def __init__(self):
        self._cached_events: list[CrashEvent] = []

    def get_recent_crashes(self, max_events: int = 20) -> list[CrashEvent]:
        events = []
        for log_name in [self.EVENT_LOG_APP, self.EVENT_LOG_SYS]:
            try:
                ps_cmd = (
                    f'Get-EventLog -LogName "{log_name}" -EntryType Error '
                    f"-Newest {max_events} | "
                    f"Select-Object TimeGenerated, Source, EventID, Message | "
                    f"ConvertTo-Json"
                )
                result = subprocess.run(
                    ["powershell", "-Command", ps_cmd],
                    capture_output=True, text=True, timeout=15
                )
                if result.returncode != 0:
                    continue

                output = result.stdout.strip()
                if not output:
                    continue

                data = json.loads(output)
                if isinstance(data, dict):
                    data = [data]

                for item in data:
                    event = CrashEvent(
                        timestamp=item.get("TimeGenerated", ""),
                        source=item.get("Source", ""),
                        event_id=int(item.get("EventID", 0)),
                        level="Error",
                        message=item.get("Message", "")[:2000],
                    )
                    if self._is_msfs_related(event):
                        events.append(event)
            except Exception:
                continue

        events.sort(key=lambda e: e.timestamp, reverse=True)
        self._cached_events = events
        return events

    def get_crash_details(self, event: CrashEvent) -> dict:
        details = {
            "timestamp": event.timestamp,
            "source": event.source,
            "event_id": event.event_id,
            "message": event.message,
            "faulting_module": "",
            "exception_code": "",
            "app_name": "",
            "fault_offset": "",
        }

        text = event.message
        patterns = {
            "faulting_module": r"Faulting module name:\s*(.+?)[,\r\n]",
            "exception_code": r"Exception code:\s*(0x[0-9a-fA-F]+)",
            "app_name": r"Application Name:\s*(.+?)[,\r\n]",
            "fault_offset": r"Fault offset:\s*(0x[0-9a-fA-F]+)",
        }
        for key, pattern in patterns.items():
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                details[key] = m.group(1).strip()

        return details

    def get_active_drivers(self) -> list[DriverInfo]:
        drivers = []
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-CimInstance Win32_PnPSignedDriver | "
                 "Where-Object { $_.DriverVersion -ne $null } | "
                 "Select-Object DeviceName, DriverVersion, DriverDate | "
                 "Sort-Object DeviceName | ConvertTo-Json"],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    name = item.get("DeviceName", "")
                    if any(kw in name.lower() for kw in ["display", "gpu", "nvidia", "amd", "radeon", "geforce"]):
                        drivers.append(DriverInfo(
                            name=name,
                            version=item.get("DriverVersion", ""),
                            date=item.get("DriverDate", ""),
                        ))
        except Exception:
            pass
        return drivers

    def build_diagnostic_context(self) -> str:
        parts = ["=== MSFS Crash Diagnostic Report ===\n"]

        parts.append("--- Recent Crash Events ---")
        crashes = self.get_recent_crashes(10)
        if not crashes:
            parts.append("No recent crashes found in Event Log.\n")
        for i, crash in enumerate(crashes[:5], 1):
            details = self.get_crash_details(crash)
            parts.append(f"\nCrash #{i}:")
            parts.append(f"  Time: {crash.timestamp}")
            parts.append(f"  Source: {crash.source}")
            parts.append(f"  Event ID: {crash.event_id}")
            if details["faulting_module"]:
                parts.append(f"  Faulting Module: {details['faulting_module']}")
            if details["exception_code"]:
                parts.append(f"  Exception Code: {details['exception_code']}")
            parts.append(f"  Message (first 500 chars): {crash.message[:500]}")

        parts.append("\n--- GPU Driver Info ---")
        drivers = self.get_active_drivers()
        if not drivers:
            parts.append("Could not retrieve driver info.\n")
        for d in drivers:
            parts.append(f"  {d.name}: v{d.version} ({d.date})")

        return "\n".join(parts)

    def _is_msfs_related(self, event: CrashEvent) -> bool:
        source_lower = event.source.lower()
        message_lower = event.message.lower()
        for source in self.MSFS_SOURCES:
            if source.lower() in source_lower or source.lower() in message_lower:
                return True
        msfs_keywords = [
            "flightsimulator", "simconnect", "msfs",
            "flight simulator", "asobo", "community folder",
        ]
        for kw in msfs_keywords:
            if kw in message_lower:
                return True
        return False
