import json
import os
import re
from dataclasses import dataclass, field
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

from .local_ai import LocalDiagnostics
from .web_search import WebSearch


@dataclass
class TuningRecommendation:
    setting: str
    current_value: str
    recommended_value: str
    reason: str
    impact: str = ""
    confidence: str = "high"

    def to_text(self) -> str:
        return f"{self.setting}: {self.current_value} -> {self.recommended_value}\n  Why: {self.reason}"


@dataclass
class TuningReport:
    source: str = ""
    summary: str = ""
    recommendations: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    overall_tier: str = ""
    target_fps: int = 0

    def to_text(self) -> str:
        parts = [f"=== AI Tuning Analysis ({self.source}) ===", ""]
        if self.summary:
            parts.append(self.summary)
            parts.append("")
        if self.overall_tier:
            parts.append(f"Detected tier: {self.overall_tier.upper()}")
        if self.target_fps:
            parts.append(f"Target FPS: {self.target_fps}")
        parts.append(f"\nRecommendations ({len(self.recommendations)}):")
        for i, rec in enumerate(self.recommendations, 1):
            parts.append(f"\n  {i}. {rec.setting}")
            parts.append(f"     Current:    {rec.current_value}")
            parts.append(f"     Recommended: {rec.recommended_value}")
            parts.append(f"     Reason:     {rec.reason}")
            if rec.impact:
                parts.append(f"     Impact:     {rec.impact}")
        if self.warnings:
            parts.append("\nWarnings:")
            for w in self.warnings:
                parts.append(f"  ! {w}")
        return "\n".join(parts)


class AIService:
    GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL = "llama3-70b-8192"

    GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    GEMINI_MODEL = "gemini-2.5-flash"

    SYSTEM_PROMPT = (
        "You are an expert MSFS 2020/2024 flight simulator technical support agent.\n"
        "Analyze the provided crash log, error codes, faulting modules, and system info.\n"
        "Provide:\n"
        "1. Plain-English explanation of what went wrong\n"
        "2. Most likely root cause\n"
        "3. Step-by-step fix instructions\n"
        "Keep response under 200 words. Be direct and actionable."
    )

    TUNING_PROMPT = (
        "You are an expert MSFS 2020/2024 graphics optimization engineer.\n"
        "Analyze the user's hardware, current settings, and crash history.\n"
        "Provide personalized tuning recommendations to maximize FPS while maintaining visual quality.\n\n"
        "For each setting to change, provide:\n"
        "- Setting name\n- Current value\n- Recommended value\n- Why this change helps\n- Expected impact (high/medium/low)\n\n"
        "Also provide:\n"
        "- Overall hardware tier assessment (low/medium/high/ultra)\n"
        "- Target FPS estimate for the recommended settings\n"
        "- Any warnings about problematic settings or crash-prone configs\n\n"
        "Be specific with numbers. Prioritize crash-causing settings first, then FPS gains.\n"
        "Keep response concise and actionable."
    )

    def __init__(self):
        self.provider = "builtin"
        self.api_key = ""
        self.groq_key = ""
        self.gemini_key = ""
        self.local_engine = LocalDiagnostics()
        self.web_search = WebSearch()
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
                    self.gemini_key = data.get("gemini_key", "")
        except Exception:
            pass

    def save_settings(self):
        os.makedirs(os.path.dirname(self._settings_path), exist_ok=True)
        with open(self._settings_path, "w") as f:
            json.dump({"groq_key": self.groq_key, "gemini_key": self.gemini_key}, f)

    def set_groq_key(self, key: str):
        self.groq_key = key
        self.save_settings()

    def set_gemini_key(self, key: str):
        self.gemini_key = key
        self.save_settings()

    def has_groq(self) -> bool:
        return bool(self.groq_key and len(self.groq_key) > 10)

    def has_gemini(self) -> bool:
        return bool(self.gemini_key and len(self.gemini_key) > 10)

    def _get_active_provider(self) -> str:
        if self.has_groq():
            return "Groq"
        elif self.has_gemini():
            return "Gemini"
        return "Local"

    def diagnose(self, context: str) -> str:
        local_result = self._run_local(context)

        has_local_match = (
            "=== Error Analysis ===" in local_result
            or "Severity:" in local_result
            or "Most likely cause:" in local_result
        ) and "No specific match" not in local_result

        if has_local_match:
            return "[Built-in Rule Engine]\n\n" + local_result

        web_context = self._search_web_for_error(context)

        if self.has_groq() and requests:
            enhanced_context = context
            if web_context:
                enhanced_context += f"\n\n=== WEB SEARCH RESULTS ===\n{web_context}"
            result = self._call_groq(enhanced_context)
            if result:
                source = "Groq AI + Web Search" if web_context else "Groq AI"
                return f"[Powered by {source} - Llama 3 70B]\n\n" + result

        if self.has_gemini() and requests:
            enhanced_context = context
            if web_context:
                enhanced_context += f"\n\n=== WEB SEARCH RESULTS ===\n{web_context}"
            result = self._call_gemini(enhanced_context)
            if result:
                source = "Gemini AI + Web Search" if web_context else "Gemini AI"
                return f"[Powered by {source} - 2.5 Flash]\n\n" + result

        if web_context:
            return f"[Built-in Rules + Web Search]\n\n{local_result}\n\n=== ONLINE SOLUTIONS ===\n{web_context}"

        return "[Built-in Rule Engine]\n\n" + local_result

    def recommend_tuning(self, system_info, current_settings, crash_events=None, mods=None) -> TuningReport:
        context = self._build_tuning_context(system_info, current_settings, crash_events, mods)

        web_context = ""
        if crash_events:
            for crash in crash_events[:2]:
                if crash.faulting_module or crash.exception_code:
                    web_context += self._search_web_for_error(
                        f"Faulting Module: {crash.faulting_module}\nException Code: {crash.exception_code}\n{crash.message}"
                    ) + "\n"

        if self.has_groq() and requests:
            enhanced = context
            if web_context:
                enhanced += f"\n\n=== WEB SEARCH RESULTS FOR CRASHES ===\n{web_context}"
            result = self._call_groq_tuning(enhanced)
            if result:
                if web_context:
                    result.source = "Groq AI + Web Search (Llama 3 70B)"
                return result

        if self.has_gemini() and requests:
            enhanced = context
            if web_context:
                enhanced += f"\n\n=== WEB SEARCH RESULTS FOR CRASHES ===\n{web_context}"
            result = self._call_gemini_tuning(enhanced)
            if result:
                if web_context:
                    result.source = "Gemini AI + Web Search (2.5 Flash)"
                return result

        return self._local_tuning_analysis(system_info, current_settings, crash_events)

    def _search_web_for_error(self, context: str) -> str:
        module = ""
        code = ""
        error_desc = ""

        m = re.search(r"Faulting Module:\s*(.+)", context)
        if m:
            module = m.group(1).strip()

        m = re.search(r"Exception Code:\s*(0x[0-9a-fA-F]+)", context)
        if m:
            code = m.group(1).strip()

        m = re.search(r"(?:error|crash|fault)[:\s]*(.+?)(?:\n|$)", context, re.IGNORECASE)
        if m:
            error_desc = m.group(1).strip()[:100]

        if not error_desc:
            error_desc = context[:200]

        results = self.web_search.search_msfs_error(error_desc, module, code)
        return results.to_context()

    def _build_tuning_context(self, system_info, current_settings, crash_events=None, mods=None) -> str:
        lines = [
            "=== SYSTEM HARDWARE ===",
            f"GPU: {system_info.gpu.name} ({system_info.gpu.vram_mb} MB VRAM)",
            f"Driver: {system_info.gpu.driver_version}",
            f"CPU: {system_info.cpu.name} ({system_info.cpu.cores_physical} cores, {system_info.cpu.max_ghz} GHz)",
            f"RAM: {system_info.ram_total_gb} GB total, {system_info.ram_available_gb} GB available",
            f"Display: {system_info.monitor.width}x{system_info.monitor.height} @ {system_info.monitor.refresh_hz}Hz",
            f"OS: {system_info.os_name} {system_info.os_version}",
            "",
            "=== CURRENT MSFS SETTINGS ===",
            f"Render Scale: {current_settings.render_scale}%",
            f"Terrain LOD: {current_settings.terrain_lod}",
            f"Object LOD: {current_settings.object_lod}",
            f"Volumetric Clouds: {current_settings.volumetric_clouds}",
            f"Texture Resolution: {current_settings.texture_res}",
            f"Anisotropic Filtering: {current_settings.anisotropic}x",
            f"Shadow Resolution: {current_settings.shadows}",
            f"Reflection: {current_settings.reflection}",
            f"Grass: {current_settings.grass}",
            f"Ambient Occlusion: {'On' if current_settings.ambient_occlusion else 'Off'}",
            f"Motion Blur: {'On' if current_settings.motion_blur else 'Off'}",
            f"Depth of Field: {'On' if current_settings.depth_of_field else 'Off'}",
            f"Bloom: {'On' if current_settings.bloom else 'Off'}",
            f"VSync: {current_settings.vsync}",
            f"Frame Rate Limit: {current_settings.frame_rate_limit if current_settings.frame_rate_limit else 'Unlimited'}",
        ]

        if crash_events:
            lines.extend(["", f"=== RECENT CRASHES ({len(crash_events)}) ==="])
            for crash in crash_events[:5]:
                lines.append(f"- [{crash.source}] {crash.faulting_module or 'N/A'} | {crash.exception_code or 'N/A'} | {crash.message[:100]}")

        if mods:
            lines.extend(["", f"=== INSTALLED MODS ({len(mods)}) ==="])
            for mod in mods[:15]:
                lines.append(f"- {mod}")

        return "\n".join(lines)

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

    def _call_groq_tuning(self, context: str) -> Optional[TuningReport]:
        try:
            headers = {
                "Authorization": f"Bearer {self.groq_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": self.GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": self.TUNING_PROMPT},
                    {"role": "user", "content": context},
                ],
                "temperature": 0.2,
                "max_tokens": 2048,
            }
            resp = requests.post(self.GROQ_URL, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return self._parse_groq_tuning_response(content)
            return None
        except Exception:
            return None

    def _parse_groq_tuning_response(self, content: str) -> TuningReport:
        report = TuningReport(source="Groq AI (Llama 3 70B)")
        report.summary = content

        tier_match = re.search(r"tier[:\s]+(low|medium|high|ultra)", content, re.IGNORECASE)
        if tier_match:
            report.overall_tier = tier_match.group(1).lower()

        fps_match = re.search(r"(\d+)\s*fps", content, re.IGNORECASE)
        if fps_match:
            report.target_fps = int(fps_match.group(1))

        setting_pattern = re.compile(
            r"(?:setting|parameter)[:\s]*(.+?)[:\s]*(?:from|current)[:\s]*(.+?)[,;]\s*(?:to|recommend|set)[:\s]*(.+?)[,;.\n]",
            re.IGNORECASE
        )
        for match in setting_pattern.finditer(content):
            rec = TuningRecommendation(
                setting=match.group(1).strip(),
                current_value=match.group(2).strip(),
                recommended_value=match.group(3).strip(),
                reason="AI recommended",
                impact="medium"
            )
            report.recommendations.append(rec)

        if not report.recommendations:
            report.recommendations.append(TuningRecommendation(
                setting="Full Analysis",
                current_value="(see summary)",
                recommended_value="(see summary)",
                reason=content,
                impact="high"
            ))

        return report

    def _call_gemini(self, context: str) -> Optional[str]:
        try:
            url = self.GEMINI_URL.format(model=self.GEMINI_MODEL)
            headers = {
                "x-goog-api-key": self.gemini_key,
                "Content-Type": "application/json",
            }
            payload = {
                "contents": [{"parts": [{"text": f"{self.SYSTEM_PROMPT}\n\n{context}"}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1024,
                },
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            return None
        except Exception:
            return None

    def _call_gemini_tuning(self, context: str) -> Optional[TuningReport]:
        try:
            url = self.GEMINI_URL.format(model=self.GEMINI_MODEL)
            headers = {
                "x-goog-api-key": self.gemini_key,
                "Content-Type": "application/json",
            }
            payload = {
                "contents": [{"parts": [{"text": f"{self.TUNING_PROMPT}\n\n{context}"}]}],
                "generationConfig": {
                    "temperature": 0.2,
                    "maxOutputTokens": 2048,
                },
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        content = parts[0].get("text", "")
                        return self._parse_gemini_tuning_response(content)
            return None
        except Exception:
            return None

    def _parse_gemini_tuning_response(self, content: str) -> TuningReport:
        report = TuningReport(source="Gemini AI (2.5 Flash)")
        report.summary = content

        tier_match = re.search(r"tier[:\s]+(low|medium|high|ultra)", content, re.IGNORECASE)
        if tier_match:
            report.overall_tier = tier_match.group(1).lower()

        fps_match = re.search(r"(\d+)\s*fps", content, re.IGNORECASE)
        if fps_match:
            report.target_fps = int(fps_match.group(1))

        setting_pattern = re.compile(
            r"(?:setting|parameter)[:\s]*(.+?)[:\s]*(?:from|current)[:\s]*(.+?)[,;]\s*(?:to|recommend|set)[:\s]*(.+?)[,;.\n]",
            re.IGNORECASE
        )
        for match in setting_pattern.finditer(content):
            rec = TuningRecommendation(
                setting=match.group(1).strip(),
                current_value=match.group(2).strip(),
                recommended_value=match.group(3).strip(),
                reason="AI recommended",
                impact="medium"
            )
            report.recommendations.append(rec)

        if not report.recommendations:
            report.recommendations.append(TuningRecommendation(
                setting="Full Analysis",
                current_value="(see summary)",
                recommended_value="(see summary)",
                reason=content,
                impact="high"
            ))

        return report

    def _local_tuning_analysis(self, system_info, current_settings, crash_events=None) -> TuningReport:
        report = TuningReport(source="Built-in Rule Engine")
        recs = []
        warnings = []

        vram = system_info.gpu.vram_mb
        ram = system_info.ram_total_gb
        cores = system_info.cpu.cores_physical
        gpu_name = system_info.gpu.name.lower()

        if vram >= 12000:
            tier = "ultra"
        elif vram >= 8000:
            tier = "high"
        elif vram >= 4000:
            tier = "medium"
        else:
            tier = "low"

        if any(k in gpu_name for k in ["4090", "4080", "3090", "7900 xtx", "5090", "5080"]):
            tier = "ultra"
        elif any(k in gpu_name for k in ["4070", "3080", "6900", "7900"]):
            if tier not in ("low",): tier = "high"
        elif any(k in gpu_name for k in ["4060", "3070", "6800", "7800"]):
            if tier == "ultra": tier = "high"

        if ram < 16:
            tier = "low"
            warnings.append("Less than 16GB RAM detected - some settings will be limited")

        report.overall_tier = tier
        report.target_fps = {"low": 60, "medium": 55, "high": 45, "ultra": 35}.get(tier, 45)

        if vram < 4000 and current_settings.texture_res >= 4096:
            recs.append(TuningRecommendation(
                setting="Texture Resolution",
                current_value=str(current_settings.texture_res),
                recommended_value="1024",
                reason=f"GPU has only {vram}MB VRAM - 4096 textures will cause stutters and crashes",
                impact="high"))
        elif vram < 8000 and current_settings.texture_res >= 4096:
            recs.append(TuningRecommendation(
                setting="Texture Resolution",
                current_value=str(current_settings.texture_res),
                recommended_value="2048",
                reason=f"GPU has {vram}MB VRAM - 2048 textures are safer and barely noticeable difference",
                impact="high"))
        elif vram >= 8000 and current_settings.texture_res < 2048:
            recs.append(TuningRecommendation(
                setting="Texture Resolution",
                current_value=str(current_settings.texture_res),
                recommended_value="2048",
                reason=f"GPU has {vram}MB VRAM - can handle higher textures",
                impact="low", confidence="medium"))

        if current_settings.shadows > 2048 and vram < 8000:
            recs.append(TuningRecommendation(
                setting="Shadow Resolution",
                current_value=str(current_settings.shadows),
                recommended_value="1024",
                reason="High shadows eat VRAM - 1024 is sufficient for most scenarios",
                impact="medium"))

        if current_settings.terrain_lod > 180 and vram < 8000:
            recs.append(TuningRecommendation(
                setting="Terrain LOD",
                current_value=str(current_settings.terrain_lod),
                recommended_value="140",
                reason="High terrain LOD is GPU-heavy - reducing slightly gives big FPS boost",
                impact="medium", confidence="medium"))

        if current_settings.volumetric_clouds > 160:
            recs.append(TuningRecommendation(
                setting="Volumetric Clouds",
                current_value=str(current_settings.volumetric_clouds),
                recommended_value="120",
                reason="Clouds are one of the biggest FPS killers - reducing saves 10-15 FPS",
                impact="high"))

        if current_settings.ambient_occlusion and vram < 6000:
            recs.append(TuningRecommendation(
                setting="Ambient Occlusion",
                current_value="On",
                recommended_value="Off",
                reason=f"AO is expensive on low-VRAM GPUs ({vram}MB) - disabling saves 3-5 FPS",
                impact="medium"))

        if current_settings.motion_blur:
            recs.append(TuningRecommendation(
                setting="Motion Blur",
                current_value="On",
                recommended_value="Off",
                reason="Motion blur adds processing overhead and most pilots prefer it off",
                impact="low"))

        if current_settings.reflection > 2048 and vram < 8000:
            recs.append(TuningRecommendation(
                setting="Reflection",
                current_value=str(current_settings.reflection),
                recommended_value="1024",
                reason="High reflections are expensive - 1024 is barely noticeable",
                impact="medium", confidence="medium"))

        if current_settings.render_scale > 100:
            recs.append(TuningRecommendation(
                setting="Render Scale",
                current_value=f"{current_settings.render_scale}%",
                recommended_value="100%",
                reason="Rendering above native resolution is extremely GPU-intensive with minimal visual gain",
                impact="high"))
        elif current_settings.render_scale < 80:
            recs.append(TuningRecommendation(
                setting="Render Scale",
                current_value=f"{current_settings.render_scale}%",
                recommended_value="100%",
                reason="Render scale below 80% makes the image noticeably blurry",
                impact="medium", confidence="medium"))

        if cores < 6:
            warnings.append("CPU has fewer than 6 cores - reduce traffic and AI settings for stability")

        if current_settings.object_lod > 180 and vram < 6000:
            recs.append(TuningRecommendation(
                setting="Object LOD",
                current_value=str(current_settings.object_lod),
                recommended_value="120",
                reason="High object LOD is CPU/GPU heavy on limited hardware",
                impact="medium", confidence="medium"))

        if current_settings.anisotropic > 8 and vram < 6000:
            recs.append(TuningRecommendation(
                setting="Anisotropic Filtering",
                current_value=f"{current_settings.anisotropic}x",
                recommended_value="8x",
                reason="16x anisotropic filtering costs performance with minimal visual gain below 8x",
                impact="low", confidence="medium"))

        if crash_events:
            fault_modules = [c.faulting_module for c in crash_events if c.faulting_module]
            if any("d3d" in m.lower() or "dxgi" in m.lower() for m in fault_modules):
                warnings.append("DXGI/D3D crashes detected - reduce graphics settings to prevent future crashes")
                if current_settings.shadows > 1024:
                    recs.append(TuningRecommendation(
                        setting="Shadow Resolution",
                        current_value=str(current_settings.shadows),
                        recommended_value="1024",
                        reason="DXGI crashes often caused by excessive VRAM usage from high shadows",
                        impact="high"))
            if any("weather" in m.lower() or "cloud" in m.lower() for m in fault_modules):
                warnings.append("Weather/cloud-related crashes detected")
                recs.append(TuningRecommendation(
                    setting="Volumetric Clouds",
                    current_value=str(current_settings.volumetric_clouds),
                    recommended_value="100",
                    reason="Cloud-related crashes detected - reducing clouds improves stability",
                    impact="high"))
            if any("memory" in m.lower() or "oom" in m.lower() for m in fault_modules):
                warnings.append("Out-of-memory crashes detected")
                if current_settings.texture_res > 2048:
                    recs.append(TuningRecommendation(
                        setting="Texture Resolution",
                        current_value=str(current_settings.texture_res),
                        recommended_value="2048",
                        reason="OOM crashes - reducing texture memory usage is critical",
                        impact="high"))

        if not recs:
            report.summary = (
                f"Hardware analysis: {system_info.gpu.name} with {vram}MB VRAM, "
                f"{ram}GB RAM, {cores}-core CPU.\n"
                f"Detected tier: {tier.upper()}.\n"
                f"Current settings appear well-optimized for your hardware. "
                f"No changes recommended."
            )
        else:
            high_impact = [r for r in recs if r.impact == "high"]
            med_impact = [r for r in recs if r.impact == "medium"]
            report.summary = (
                f"Hardware analysis: {system_info.gpu.name} with {vram}MB VRAM, "
                f"{ram}GB RAM, {cores}-core CPU.\n"
                f"Detected tier: {tier.upper()} | Target: ~{report.target_fps} FPS\n"
                f"Found {len(recs)} recommendations "
                f"({len(high_impact)} high impact, {len(med_impact)} medium impact)."
            )

        report.recommendations = recs
        report.warnings = warnings
        return report

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
