#!/usr/bin/env python3
"""
Step-by-Step Test 1: Validation of Flow Master Pipeline.
Validates:
1. Flow browser opening (Profile 17).
2. Session & security checkpoint verification.
3. Credit balance reading & pre-flight check.
4. Prompt dispatching to Flow workspace.
5. Generation monitoring.
6. Asset downloading and storage verification.
7. Credit balance post-verification.
8. Structured Prompt Trace recording.
"""

import os
import sys
import json
import time

PROJECT_ROOT = "/home/kali/Рабочий стол/Youtube akkaunt integratsiyasi"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.flow_engine.pipeline import FlowAutomationPipeline

def run_step_by_step_test():
    print("=" * 80)
    print("🔬 [STEP-BY-STEP TEST 1] GOOGLE FLOW AVTOMATIK MASTER PIPELINE SINOVI")
    print("=" * 80)

    test_prompt = "Futuristic quantum neural interface holographic HUD display"
    test_topic = "Quantum Neural Computing"

    pipeline = FlowAutomationPipeline(profile_dir="Profile 17", auto_publish=False)

    print("\n▶️ Test ishga tushirilmoqda...")
    res = pipeline.execute_prompt(user_prompt=test_prompt, topic=test_topic)

    print("\n" + "=" * 80)
    print("📋 [TEST NATIJASI]")
    print(json.dumps(res, indent=2, ensure_ascii=False))
    print("=" * 80)

    if res.get("success"):
        print("\n🎉 1-BOSQICH SINOVI 100% MUVAFFAQIYATLI YAKUNLANDI!")
        print(f"🎬 Video yo'li: {res.get('video_path')}")
        print(f"🔒 SHA256: {res.get('sha256')}")
        print(f"💳 Kreditlar: {res.get('credits')}")
        print(f"📁 Trace fayli: {res.get('trace_file')}")
    else:
        print(f"\n❌ Sinovda xatolik: {res.get('error')}")

if __name__ == "__main__":
    run_step_by_step_test()
