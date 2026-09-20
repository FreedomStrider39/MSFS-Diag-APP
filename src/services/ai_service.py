import json
import os
import re
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

from .local_ai import LocalDiagnostics


class AIService:
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL = "llama3-70b-8192"

    SYSTEM_PROMPT = """You are an expert MSFS 2020/2024 flight simulator technical support agent.
Analyze the provided crash log, error codes, faulting modules, and system info.
Provide:
1. Plain-English explanation of what went wrong
2. Most likely root cause  
3. Step-by-step fix instructions
Keep response under 200 words. Be direct and actionable."""

    def __init__(self):
        self.provider = "builtin"
        self.api_key = ""
        self.groq_key = ""
        self.local_engine = LocalDiagnostics()
        self._settings_path = os.path.join(
            os.path.expanduser("~"), ".msfs_diagnostics", "ai_settings.json"
        )
        self._load_settings()

    def _load_settings(self):
        try:
            if os.path.exists(self._settings_path):
                with open(self._settings_path, "r") as f:
                    data = json.load(f)
                    self.groq_key = data.get("groq_key", "")
        except Exception:
            pass

    def save_settings(self):
        os.makedirs(os.path.dirname(self._settings_path), exist_ok=True)
        with open(self._settings_path, "w") as f:
            json.dump({"groq_key": self.groq_key}, f)

    def set_groq_key(self, key: str):
        self.groq_key = key
        self.save_settings()

    def has_groq(self) -> bool:
        return bool(self.groq_key and len(self.groq_key) > 10)

    def diagnose(self, context: str) -> str:
        if self.has_groq() and requests:
            result = self._call_groq(context)
            if result:
                return "[Powered by Groq - Llama 3 70B]\n\n" + result

        return "[Built-in Rule Engine]\n\n" + self._run_local(context)

    def _call_groq(self, context: str) -> Optional[str]:
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": context},
                ],
                "temperature": 0.3,
                "max_tokens": 1024,
            }
            resp = requests.post(self.GROQ_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            return None
        except Exception:
            return None

    def _run_local(self, context: str) -> str:
        crash_details = {
            "faulting_module": "",
            "exception_code": "",
            "app_name": "",
            "fault_offset": "",
            "message": context,
        }

        m = re.search(r"Faulting Module:\s*(.+)", context)
        if m:
            crash_details["faulting_module"] = m.group(1).strip()

        m = re.search(r"Exception Code:\s*(0x[0-9a-fA-F]+)", context)
        if m:
            crash_details["exception_code"] = m.group(1).strip()

        result = self.local_engine.analyze_crash(crash_details, context)
        return result.to_text()
