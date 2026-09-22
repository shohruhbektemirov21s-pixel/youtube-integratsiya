#!/usr/bin/env python3
"""
Flow Engine - Generation Logger & Hermes Prompt Tracer.
Provides structured auditing, tracing and diagnostic telemetry for all AI operations.
Tracks:
- User Prompt -> Hermes Steps -> Gemini Requests -> Flow Prompts -> Video Generation
- Exact request counts, duplicates, retries, credit changes, and timing.
"""

import os
import sys
import json
import time
import uuid
import logging
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
LOGS_DIR = os.path.join(PROJECT_ROOT, "workspace/logs/flow_traces")
SCREENSHOTS_DIR = os.path.join(PROJECT_ROOT, "workspace/logs/screenshots")
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


class PromptTraceRecord:
    """Represents a single end-to-end execution trace for an AI request."""

    def __init__(self, request_id: Optional[str] = None, user_prompt: str = ""):
        self.request_id = request_id or f"REQ_{uuid.uuid4().hex[:8].upper()}"
        self.user_prompt = user_prompt
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.hermes_steps: List[Dict[str, Any]] = []
        self.gemini_requests: List[Dict[str, Any]] = []
        self.flow_prompts: List[Dict[str, Any]] = []
        self.flow_generations: List[Dict[str, Any]] = []
        self.retries: List[Dict[str, Any]] = []
        self.credit_start: Optional[int] = None
        self.credit_end: Optional[int] = None
        self.final_video_path: Optional[str] = None
        self.status = "INITIALIZED"
        self.error: Optional[Dict[str, Any]] = None

    def add_hermes_step(self, step_name: str, payload: Any = None):
        step_entry = {
            "step_index": len(self.hermes_steps) + 1,
            "step_name": step_name,
            "timestamp": datetime.now().isoformat(),
            "payload": payload
        }
        self.hermes_steps.append(step_entry)

    def add_gemini_request(self, prompt: str, model: str, response_summary: str = "", tokens: int = 0):
        gem_entry = {
            "index": len(self.gemini_requests) + 1,
            "model": model,
            "prompt_snippet": prompt[:120],
            "prompt_full": prompt,
            "response_summary": response_summary[:120],
            "timestamp": datetime.now().isoformat()
        }
        self.gemini_requests.append(gem_entry)

    def add_flow_prompt(self, scene_index: int, prompt: str, target_category: str = ""):
        fp_entry = {
            "index": len(self.flow_prompts) + 1,
            "scene_index": scene_index,
            "prompt": prompt,
            "category": target_category,
            "timestamp": datetime.now().isoformat()
        }
        self.flow_prompts.append(fp_entry)

    def add_flow_generation(self, generation_id: str, prompt: str, model: str = "veo-flow", status: str = "STARTED"):
        gen_entry = {
            "index": len(self.flow_generations) + 1,
            "generation_id": generation_id,
            "prompt": prompt,
            "model": model,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        self.flow_generations.append(gen_entry)

    def add_retry(self, stage: str, reason: str, attempt: int, max_attempts: int):
        retry_entry = {
            "stage": stage,
            "reason": reason,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "timestamp": datetime.now().isoformat()
        }
        self.retries.append(retry_entry)

    def set_credits(self, start: Optional[int] = None, end: Optional[int] = None):
        if start is not None:
            self.credit_start = start
        if end is not None:
            self.credit_end = end

    def set_error(self, code: str, message: str, retryable: bool = False, screenshot_path: str = ""):
        self.status = "FAILED"
        self.error = {
            "code": code,
            "message": message,
            "retryable": retryable,
            "timestamp": datetime.now().isoformat(),
            "screenshot_path": screenshot_path
        }

    def complete(self, video_path: str):
        self.end_time = time.time()
        self.final_video_path = video_path
        self.status = "COMPLETED"

    def to_dict(self) -> Dict[str, Any]:
        duration = round((self.end_time or time.time()) - self.start_time, 2)
        credits_used = (self.credit_start - self.credit_end) if (self.credit_start is not None and self.credit_end is not None) else None
        return {
            "request_id": self.request_id,
            "user_prompt": self.user_prompt,
            "status": self.status,
            "duration_seconds": duration,
            "counts": {
                "hermes_steps": len(self.hermes_steps),
                "gemini_requests": len(self.gemini_requests),
                "flow_prompts": len(self.flow_prompts),
                "flow_generations": len(self.flow_generations),
                "retries": len(self.retries)
            },
            "credits": {
                "start": self.credit_start,
                "end": self.credit_end,
                "used": credits_used
            },
            "hermes_steps": self.hermes_steps,
            "gemini_requests": self.gemini_requests,
            "flow_prompts": self.flow_prompts,
            "flow_generations": self.flow_generations,
            "retries": self.retries,
            "final_video_path": self.final_video_path,
            "error": self.error
        }

    def print_structured_summary(self):
        d = self.to_dict()
        print("\n" + "=" * 75)
        print(f"📊 [PROMPT TRACER] REQUEST ID: {self.request_id}")
        print(f"🎯 USER PROMPT: \"{self.user_prompt}\"")
        print(f"⏱ Status: {self.status} (Davomiyligi: {d['duration_seconds']}s)")
        print(f"🔢 AI Requestlar Statistikasi:")
        print(f"   • Hermes qadamlari:   {d['counts']['hermes_steps']} ta")
        print(f"   • Gemini API chaqiruvlari: {d['counts']['gemini_requests']} ta")
        print(f"   • Flow sahnasi promptlari: {d['counts']['flow_prompts']} ta")
        print(f"   • Flow video generatsiyalari: {d['counts']['flow_generations']} ta")
        print(f"   • Qayta urinishlar (Retries): {d['counts']['retries']} ta")
        if d['credits']['used'] is not None:
            print(f"⚡️ Kredit Sarfi: {d['credits']['used']} ta ({d['credits']['start']} -> {d['credits']['end']})")
        if self.final_video_path:
            print(f"🎬 Yakuniy Video: {self.final_video_path}")
        if self.error:
            print(f"❌ Xatolik [{self.error['code']}]: {self.error['message']}")
        print("=" * 75 + "\n")


class GenerationLogger:
    """Manages writing structured traces to disk and taking debug screenshots."""

    def __init__(self):
        self.logger = logging.getLogger("FlowGenerationLogger")

    def save_trace(self, trace: PromptTraceRecord) -> str:
        trace_file = os.path.join(LOGS_DIR, f"trace_{trace.request_id}.json")
        with open(trace_file, "w", encoding="utf-8") as f:
            json.dump(trace.to_dict(), f, indent=2, ensure_ascii=False)
        return trace_file

    def capture_screenshot(self, window_id: Optional[str] = None, label: str = "debug") -> str:
        timestamp = int(time.time() * 1000)
        shot_path = os.path.join(SCREENSHOTS_DIR, f"{label}_{timestamp}.png")
        try:
            cmd = ["import", "-window", window_id or "root", shot_path]
            env = os.environ.copy()
            env["DISPLAY"] = os.getenv("DISPLAY", ":0.0")
            subprocess.run(cmd, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
            if os.path.exists(shot_path):
                return shot_path
        except Exception:
            pass
        return ""
