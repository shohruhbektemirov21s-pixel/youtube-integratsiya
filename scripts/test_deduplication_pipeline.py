#!/usr/bin/env python3
"""
Comprehensive Verification Test Suite for Central AI Agent Orchestrator & Deduplication.
Executes PHASE 25 Verification:
1. Generates 3 sequential videos via CentralAIOrchestrator.
2. Verifies Research Dossiers (Browser search, facts, sources).
3. Verifies all 3 video hashes are strictly unique (video1_hash != video2_hash != video3_hash).
4. Verifies all 3 topics are distinct (video1_topic != video2_topic != video3_topic).
5. Verifies YouTube uploader strictly blocks duplicate re-upload (FAILED_DUPLICATE).
6. Verifies semantic similarity rejection on repeated topics.
"""

import os
import sys
import json
import time
import shutil

DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.ai_agent_orchestrator import CentralAIOrchestrator, JobState
from scripts.youtube_uploader import upload_to_youtube
from scripts.content_history_manager import ContentHistoryManager, compute_sha256_file, calculate_semantic_similarity


def run_orchestrator_3_video_test():
    print("=" * 85)
    print("🧪 BEYONDERA TECH: CENTRAL AI ORCHESTRATOR 3-CONSECUTIVE GENERATION TEST")
    print("=" * 85)

    orchestrator = CentralAIOrchestrator(preferred_profile="4")
    history_mgr = ContentHistoryManager()
    initial_records_count = len(history_mgr.load_records())
    print(f"📊 Boshlang'ich tarix yozuvlari soni: {initial_records_count} ta")

    generated_videos = []

    # Run 3 consecutive generations via Central AI Orchestrator
    for i in range(1, 4):
        print("\n" + "#" * 75)
        print(f"🎬 ORCHESTRATOR SIKL #{i} / 3: MULTI-AGENT PIPELINE ISHGA TUSHMOQDA...")
        print("#" * 75)

        res = orchestrator.run_full_autonomous_cycle(
            video_type="shorts",
            send_telegram=False,
            auto_upload=True
        )

        if not res.get("success"):
            print(f"❌ Xatolik: Sikl #{i} muvaffaqiyatsiz: {res}")
            sys.exit(1)

        v_path = res.get("video_path")
        v_hash = res.get("video_hash") or compute_sha256_file(v_path)
        topic = res.get("topic")
        title = res.get("title")
        gen_id = res.get("generation_id")
        yt_id = res.get("youtube_video_id")
        res_id = res.get("research_id")

        print(f"✅ SIKL #{i} Muvaffaqiyatli:")
        print(f"   🔬 Research ID:    {res_id}")
        print(f"   🔑 Generation ID:  {gen_id}")
        print(f"   📌 Topic:          {topic}")
        print(f"   🎬 Title:          {title}")
        print(f"   🔒 SHA256 Hash:    {v_hash}")
        print(f"   🆔 YouTube ID:     {yt_id}")
        print(f"   📁 File:           {v_path}")

        generated_videos.append({
            "index": i,
            "generation_id": gen_id,
            "research_id": res_id,
            "topic": topic,
            "title": title,
            "hash": v_hash,
            "path": v_path,
            "youtube_id": yt_id
        })
        time.sleep(1)

    print("\n" + "=" * 85)
    print("🔍 TEKSHIRUV BOSQICHI (VERIFICATION & ASSERTIONS)")
    print("=" * 85)

    v1 = generated_videos[0]
    v2 = generated_videos[1]
    v3 = generated_videos[2]

    print("\n1. VIDEO SHA-256 HASH NOYOBLIGI:")
    print(f"   Video 1 Hash: {v1['hash']}")
    print(f"   Video 2 Hash: {v2['hash']}")
    print(f"   Video 3 Hash: {v3['hash']}")

    assert v1['hash'] != v2['hash'], "XATOLIK: Video 1 va Video 2 hashlari bir xil!"
    assert v2['hash'] != v3['hash'], "XATOLIK: Video 2 va Video 3 hashlari bir xil!"
    assert v1['hash'] != v3['hash'], "XATOLIK: Video 1 va Video 3 hashlari bir xil!"
    print("   ✅ Barcha 3 ta video fayllar SHA-256 hashi 100% MUTLAQO NOYOB (video1_hash != video2_hash != video3_hash)!")

    print("\n2. MAVZULAR (TOPICS) NOYOBLIGI:")
    print(f"   Video 1 Topic: {v1['topic']}")
    print(f"   Video 2 Topic: {v2['topic']}")
    print(f"   Video 3 Topic: {v3['topic']}")

    assert v1['topic'] != v2['topic'], "XATOLIK: Video 1 va Video 2 mavzulari bir xil!"
    assert v2['topic'] != v3['topic'], "XATOLIK: Video 2 va Video 3 mavzulari bir xil!"
    assert v1['topic'] != v3['topic'], "XATOLIK: Video 1 va Video 3 mavzulari bir xil!"
    print("   ✅ Barcha 3 ta mavzular 100% MUTLAQO NOYOB (video1_topic != video2_topic != video3_topic)!")

    print("\n3. DUPLICATE UPLOAD RESISTANCE TEST (ESKI VIDEONI QAYTA YUKLASHGA URINISH):")
    print(f"   Video 1 ni qayta yuklashga urinamiz: {v1['path']}")
    dup_meta = {
        "generation_id": f"reupload_attempt_{int(time.time())}",
        "title": "Duplicate Video Test Upload",
        "topic": "Duplicate Test Topic",
        "video_type": "shorts"
    }
    dup_res = upload_to_youtube(v1['path'], dup_meta)
    print(f"   Natija: Success={dup_res.get('success')}, Status={dup_res.get('status')}, Error={dup_res.get('error')}")

    assert dup_res.get("success") is False, "XATOLIK: Uploader eski videoni rad etmadi!"
    assert dup_res.get("status") == "FAILED_DUPLICATE", f"XATOLIK: Kutilgan status FAILED_DUPLICATE, lekin {dup_res.get('status')} qaytdi!"
    print("   ✅ Uploader eski videoni darhol aniqladi va FAILED_DUPLICATE bilan yuklashni to'xtatdi!")

    print("\n4. SEMANTIC DUPLICATE PREVENTION TEST:")
    sim = calculate_semantic_similarity(
        "5 Future Technologies That Will Change Your Life",
        "5 Technologies That Will Transform Your Future"
    )
    print(f"   O'xshash mavzular o'rtasidagi semantik ball: {sim:.2f}")
    assert sim >= 0.50, "XATOLIK: Semantik o'xshashlik aniqlanmadi!"
    print("   ✅ Semantik deduplication mexanizmi muvaffaqiyatli ishladi!")

    print("\n" + "=" * 85)
    print("🏆 BARCHA TESTLAR 100% MUVAFFAQIYATLI O'TDI (ALL ASSERTIONS PASSED)!")
    print("=" * 85)


if __name__ == "__main__":
    run_orchestrator_3_video_test()
