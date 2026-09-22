import os
import json
import random
import datetime
import requests
import time
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Project configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '')

HISTORY_FILE = os.path.join(PROJECT_ROOT, 'assets', 'content_history.json')

# 30+ Tech Domains with detailed sub-topics
TECH_DOMAINS = [
    {
        "name": "Humanoid Robotics",
        "subtopics": [
            "Bipedal locomotion algorithms and stability",
            "Artificial muscle fibers and actuators",
            "Facial micro-expression synthesis and empathy",
            "Tactile sensing electronic skin (e-skin)",
            "Dexterous manipulation of fragile objects",
            "Human-robot interaction safety protocols",
            "High-density battery packs for robotics",
            "Swarm coordination in humanoid fleets"
        ]
    },
    {
        "name": "Quantum Computing",
        "subtopics": [
            "Superconducting qubits vs trapped ions",
            "Quantum error correction algorithms",
            "Quantum supremacy milestones",
            "Quantum cryptography and QKD",
            "Shor's algorithm and encryption breaking",
            "Quantum machine learning applications",
            "Room-temperature quantum computing",
            "Quantum annealing for optimization"
        ]
    },
    {
        "name": "Neuralink and BCI",
        "subtopics": [
            "High-bandwidth brain-machine interfaces",
            "Motor cortex decoding algorithms",
            "Non-invasive EEG vs invasive implants",
            "Restoring vision and hearing via BCI",
            "Memory enhancement and cognitive boosting",
            "Ethical concerns of mind reading",
            "Brain-to-brain communication protocols",
            "Neural dust and nanoscale electrodes"
        ]
    },
    {
        "name": "Artificial General Intelligence (AGI)",
        "subtopics": [
            "Defining and measuring AGI milestones",
            "Self-improving AI systems",
            "The alignment problem and AI safety",
            "AGI reasoning and logic architectures",
            "Multi-modal world models",
            "Compute requirements for AGI",
            "Consciousness and sentience in machines",
            "Economic impact of human-level AI"
        ]
    },
    {
        "name": "Fusion Energy",
        "subtopics": [
            "Tokamak vs Stellarator designs",
            "Magnetic confinement breakthroughs",
            "Inertial confinement with lasers",
            "Superconducting magnets (YBCO)",
            "Tritium breeding and fuel cycles",
            "Plasma instability mitigation",
            "Net-positive energy milestones (Q>1)",
            "Commercial fusion reactor timelines"
        ]
    },
    {
        "name": "Space Megastructures",
        "subtopics": [
            "Dyson Swarm construction logistics",
            "O'Neill Cylinders and space habitats",
            "Space elevators and tether materials",
            "Orbital rings for planetary transport",
            "Kardashev Type II civilization tech",
            "Lunar mass drivers",
            "Solar power satellites (SPS)",
            "Stellar engines (Shkadov thrusters)"
        ]
    },
    {
        "name": "Nanotechnology",
        "subtopics": [
            "Medical nanobots for targeted drug delivery",
            "Carbon nanotube applications in materials",
            "DNA origami and programmable matter",
            "Nanosensors for environmental monitoring",
            "Molecular manufacturing and assemblers",
            "Self-healing nanomaterials",
            "Nanoparticle toxicity and safety",
            "Quantum dots in displays and solar"
        ]
    },
    {
        "name": "Biomimetic Engineering",
        "subtopics": [
            "Gecko-inspired dry adhesives",
            "Shark-skin drag reduction surfaces",
            "Lotus effect superhydrophobic materials",
            "Spider silk synthetic production",
            "Kingfisher-inspired bullet train aerodynamics",
            "Mantis shrimp impact-resistant armor",
            "Photosynthesis-inspired energy generation",
            "Neuromorphic vision sensors (event cameras)"
        ]
    },
    {
        "name": "Autonomous Vehicles",
        "subtopics": [
            "Level 5 autonomy edge cases",
            "LiDAR vs Vision-only perception",
            "V2X (Vehicle-to-Everything) communication",
            "Platooning and highway efficiency",
            "Adverse weather sensor fusion",
            "Trolley problem and ethical decision making",
            "Robotaxi fleet management",
            "Autonomous cargo shipping"
        ]
    },
    {
        "name": "Smart Cities",
        "subtopics": [
            "Dynamic traffic flow optimization",
            "Predictive maintenance for infrastructure",
            "Microgrid energy distribution",
            "Waste management autonomous systems",
            "Urban vertical farming integration",
            "Biometric security and privacy",
            "IoT sensor networks for air quality",
            "Responsive street lighting"
        ]
    },
    {
        "name": "6G Networks",
        "subtopics": [
            "Terahertz band communication",
            "Holographic telepresence bandwidth",
            "Microsecond latency applications",
            "AI-native network architecture",
            "Satellite and terrestrial integration",
            "Sensing and communication joint systems",
            "Quantum-safe 6G security",
            "Energy harvesting in 6G IoT devices"
        ]
    },
    {
        "name": "Holographic Displays",
        "subtopics": [
            "Volumetric 3D displays",
            "Light field technology",
            "Acoustic levitation holograms",
            "Holographic optical elements (HOE)",
            "Glasses-free 3D consumer tech",
            "Hologram bandwidth compression",
            "Tactile holograms (haptic feedback)",
            "Medical imaging holography"
        ]
    },
    {
        "name": "Exoskeletons",
        "subtopics": [
            "Soft robotics for rehabilitation",
            "Military load-bearing exosuits",
            "Industrial fatigue-reduction suits",
            "Brain-controlled exoskeletons",
            "Pneumatic vs hydraulic actuators",
            "Energy regeneration during walking",
            "Exoskeleton balance and fall prevention",
            "Pediatric exoskeletons for mobility"
        ]
    },
    {
        "name": "DNA Computing",
        "subtopics": [
            "Massive parallel processing with DNA",
            "DNA data storage density limits",
            "Error rates in DNA synthesis and sequencing",
            "Biological logic gates",
            "In-vivo biocomputing",
            "Solving NP-hard problems with DNA",
            "DNA cryptography",
            "Longevity of DNA storage vs silicon"
        ]
    },
    {
        "name": "Photonic AI Chips",
        "subtopics": [
            "Light-speed neural network inference",
            "Optical multiplexing for bandwidth",
            "Energy efficiency of optical computing",
            "Photonic tensor core architectures",
            "Silicon photonics integration",
            "Analog optical computing limitations",
            "Data center photonics deployment",
            "On-chip lasers for AI"
        ]
    },
    {
        "name": "Swarm Robotics",
        "subtopics": [
            "Emergent behavior algorithms",
            "Ant-colony optimization in robotics",
            "Micro-drone swarms for search and rescue",
            "Agricultural swarm harvesting",
            "Distributed sensing and mapping",
            "Self-assembling robot structures",
            "Swarm resilience and fault tolerance",
            "Underwater drone swarms"
        ]
    },
    {
        "name": "Ocean Energy",
        "subtopics": [
            "Tidal stream generators",
            "Wave energy converters (Pelamis)",
            "Ocean thermal energy conversion (OTEC)",
            "Salinity gradient power",
            "Floating solar and wind hybrids",
            "Corrosion-resistant marine materials",
            "Environmental impact on marine life",
            "Deep sea energy transmission cables"
        ]
    },
    {
        "name": "Carbon Capture",
        "subtopics": [
            "Direct Air Capture (DAC) efficiency",
            "Metal-organic frameworks (MOFs)",
            "Bioenergy with carbon capture (BECCS)",
            "Ocean alkalinity enhancement",
            "Carbon mineralization in basalt",
            "Artificial trees and synthetic biology",
            "Industrial point-source capture",
            "Utilization: turning CO2 into fuel"
        ]
    },
    {
        "name": "Metamaterials",
        "subtopics": [
            "Invisibility cloaks and optical illusions",
            "Negative refractive index materials",
            "Acoustic metamaterials for soundproofing",
            "Seismic metamaterials for earthquake protection",
            "Programmable smart materials",
            "Thermodynamic metamaterials",
            "Metamaterial antennas for 5G/6G",
            "Structural color without pigments"
        ]
    },
    {
        "name": "Synthetic Food",
        "subtopics": [
            "Lab-grown cultured meat scaling",
            "Precision fermentation for dairy",
            "3D printed food textures",
            "Algae-based protein alternatives",
            "Nutritionally optimized synthetic meals",
            "Bioreactor design for cell culture",
            "Fetal bovine serum (FBS) alternatives",
            "Synthetic food safety and regulation"
        ]
    },
    {
        "name": "Digital Twins",
        "subtopics": [
            "Human body digital twins for medicine",
            "Factory automation digital twins",
            "Earth digital twin for climate modeling",
            "Real-time sensor synchronization",
            "Predictive failure analysis",
            "Smart city digital replicas",
            "Aviation engine twins",
            "Metaverse integration with physical twins"
        ]
    },
    {
        "name": "Neuromorphic Computing",
        "subtopics": [
            "Spiking neural networks (SNNs)",
            "Memristor hardware synapses",
            "Event-based processing efficiency",
            "Brain-inspired chip architectures (Loihi)",
            "Ultra-low power AI at the edge",
            "Continuous learning without catastrophic forgetting",
            "Neuromorphic sensory processing",
            "Analog vs digital neuromorphic designs"
        ]
    },
    {
        "name": "Edge AI",
        "subtopics": [
            "TinyML for microcontrollers",
            "Federated learning for privacy",
            "On-device LLM inference",
            "Energy harvesting edge sensors",
            "Real-time video analytics at the edge",
            "Edge AI in wearable medical devices",
            "Model pruning and quantization",
            "Distributed edge swarm intelligence"
        ]
    },
    {
        "name": "LiDAR Mapping",
        "subtopics": [
            "Solid-state LiDAR miniaturization",
            "FMCW (Frequency Modulated Continuous Wave) LiDAR",
            "Drone-based archaeological LiDAR",
            "Forest canopy biomass estimation",
            "Bathymetric (underwater) LiDAR",
            "Photon-counting LiDAR",
            "Autonomous vehicle sensor fusion",
            "Space-borne LiDAR for Earth observation"
        ]
    },
    {
        "name": "Hypersonic Transport",
        "subtopics": [
            "Scramjet engine propulsion",
            "Thermal protection systems (TPS)",
            "Sonic boom mitigation shaping",
            "Hypersonic passenger aircraft",
            "Mach 5+ aerodynamics",
            "Sub-orbital point-to-point travel",
            "Cryogenic fuel management",
            "Materials for extreme heat and stress"
        ]
    },
    {
        "name": "Anti-Aging Technology",
        "subtopics": [
            "Senolytics for clearing senescent cells",
            "Telomerase gene therapy",
            "Epigenetic reprogramming (Yamanaka factors)",
            "NAD+ boosters and metabolic aging",
            "Mitochondrial dysfunction repair",
            "Blood parabiosis and plasma exchange",
            "Cryonics and vitrification",
            "AI-driven longevity drug discovery"
        ]
    },
    {
        "name": "Mars Colonization",
        "subtopics": [
            "In-Situ Resource Utilization (ISRU)",
            "Moxie: Oxygen generation from CO2",
            "Radiation shielding habitats",
            "Martian agriculture and hydroponics",
            "Starship payload logistics",
            "Lava tube settlements",
            "Terraforming timelines and ethics",
            "Martian concrete and 3D printed habitats"
        ]
    },
    {
        "name": "Asteroid Mining",
        "subtopics": [
            "Optical mining with concentrated sunlight",
            "Near-Earth Object (NEO) prospecting",
            "Platinum group metals extraction",
            "Water harvesting for orbital fuel",
            "Zero-gravity processing plants",
            "Space law and asteroid ownership",
            "Robotic swarm mining",
            "Deflection techniques for hazardous asteroids"
        ]
    },
    {
        "name": "Brain Uploading",
        "subtopics": [
            "Connectome mapping at nanoscale",
            "Whole brain emulation software",
            "Destructive vs non-destructive scanning",
            "The hard problem of consciousness transfer",
            "Digital immortality and identity",
            "Substrate-independent minds",
            "Simulated reality environments",
            "Legal rights of uploaded minds"
        ]
    },
    {
        "name": "Zero-Gravity Manufacturing",
        "subtopics": [
            "ZBLAN fiber optic cable production",
            "Perfect protein crystal growth",
            "3D printing large space structures",
            "Ultra-pure semiconductor wafers",
            "Alloy mixing without buoyancy convection",
            "Bioprinting human organs in microgravity",
            "Commercial space station factories",
            "Lunar regolith processing"
        ]
    }
]

class GeminiContentBrain:
    def __init__(self):
        self.history_file = HISTORY_FILE
        self._ensure_directories()
        self.history = self._load_history()

    def _ensure_directories(self):
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)

    def _load_history(self) -> List[Dict]:
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return []
        return []

    def save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=4, ensure_ascii=False)

    def record_content_history(self, plan: Dict):
        """Saves generated plan to history file"""
        record = {
            "date": datetime.datetime.now().isoformat(),
            "topic": plan.get("topic", ""),
            "title": plan.get("title", ""),
            "domain": plan.get("domain", "")
        }
        self.history.append(record)
        self.save_history()

    def is_topic_used(self, topic: str) -> bool:
        """Checks if a topic is too similar to past topics"""
        topic_lower = topic.lower()
        for record in self.history:
            if record.get("topic", "").lower() == topic_lower:
                return True
        return False

    def get_todays_domain(self) -> Dict:
        """Selects today's unique tech domain deterministically but with variety"""
        # Seed with current date so running multiple times today gives same domain context
        # but cross-reference history to ensure no immediate repeats
        today = datetime.datetime.now()
        seed_value = today.year * 1000 + today.timetuple().tm_yday
        random.seed(seed_value)
        
        available_domains = [d for d in TECH_DOMAINS]
        random.shuffle(available_domains)
        
        # Try to find a domain that hasn't been heavily used recently
        recent_domains = [r.get("domain") for r in self.history[-10:]]
        
        for domain in available_domains:
            if domain["name"] not in recent_domains:
                # Pick a random subtopic based on a different seed so it changes even if domain is same
                random.seed(time.time())
                subtopic = random.choice(domain["subtopics"])
                return {"domain": domain["name"], "subtopic": subtopic}
                
        # Fallback if all used recently
        domain = random.choice(TECH_DOMAINS)
        subtopic = random.choice(domain["subtopics"])
        return {"domain": domain["name"], "subtopic": subtopic}

    def build_gemini_prompt(self, domain: Dict, competitor_context: Optional[Dict] = None) -> str:
        """Constructs the prompt for Gemini"""
        prompt = f"""
You are an elite, highly creative YouTube Shorts producer and tech visionary. 
Generate a DIVERSE, UNIQUE, and VIRAL video script and production plan.

Topic Area: {domain['domain']}
Specific Focus: {domain['subtopic']}

"""
        if competitor_context:
            prompt += f"""
COMPETITOR ANALYSIS:
We have analyzed competitor videos in this space:
- Competitor Titles: {competitor_context.get('titles', [])}
- What made them viral: {competitor_context.get('viral_factors', 'Fast pacing, shocking facts')}

Your task is to create something SIMILAR but UNIQUE and BETTER. Do NOT copy them directly.
Take the core appeal and elevate it with mind-blowing new facts.
"""

        prompt += """
REQUIREMENTS:
1. Script: 80-120 words. English. Natural conversational tone. Use a 0-3s pattern-interrupt hook.
2. Ending: Must be a cliffhanger that loops perfectly back to the beginning hook.
3. Visuals: Provide 5 cinematic Google Flow video prompts per scene to generate AI video.
4. Metadata: Viral YouTube title (with emojis), description, tags, hashtags.
5. Uzbek Localization: Provide a summary/analysis of this script in Uzbek.
6. Duration: 30-60 seconds.

Return ONLY a valid JSON object matching this schema perfectly, no markdown formatting outside the JSON, no extra text:
{
  "topic": "Specific unique topic title",
  "domain": "The domain name",
  "title": "Viral YouTube Title 🚀",
  "hook": "The opening 3 seconds text",
  "script": "The full voiceover text...",
  "scenes": [
    {
      "scene_number": 1,
      "duration": 5,
      "voiceover": "Text for this scene",
      "prompt": "Cinematic visual prompt for AI video generation"
    }
  ],
  "scene_prompts": ["prompt 1", "prompt 2", "prompt 3", "prompt 4", "prompt 5"],
  "creative_direction": {
    "voice_name": "Deep tech male",
    "music_profile": "Synthwave suspense",
    "visual_theme": "Cyberpunk neon",
    "subtitle_color": "#FF00FF"
  },
  "tags": ["tag1", "tag2"],
  "hashtags": ["#tech", "#future"],
  "description": "YouTube description...",
  "uzbek_analysis": "O'zbek tilida qisqacha tahlil...",
  "uzbek_voice_summary": "O'zbek tilida ovozli matn qisqartmasi...",
  "duration": 45,
  "video_type": "shorts"
}
"""
        return prompt

    def call_gemini(self, prompt: str) -> Dict:
        """Calls Gemini API with the exact pattern requested"""
        models = ['models/gemini-3.6-flash', 'models/gemini-3.6-flash']
        
        for model in models:
            endpoint = f'https://generativelanguage.googleapis.com/v1beta/{model}:generateContent?key={GEMINI_KEY}'
            try:
                resp = requests.post(endpoint, json={
                    'contents': [{'parts': [{'text': prompt}]}],
                    'generationConfig': {
                        'response_mime_type': 'application/json',
                        'temperature': 0.9
                    }
                }, timeout=45)
                
                if resp.status_code == 200:
                    data = resp.json()
                    try:
                        text_content = data['candidates'][0]['content']['parts'][0]['text']
                        # Sometimes Gemini returns markdown JSON blocks even when mime_type is json
                        text_content = text_content.strip()
                        if text_content.startswith('```json'):
                            text_content = text_content[7:]
                        if text_content.endswith('```'):
                            text_content = text_content[:-3]
                            
                        result = json.loads(text_content.strip())
                        return result
                    except (KeyError, IndexError, json.JSONDecodeError) as e:
                        print(f"Error parsing Gemini response from {model}: {e}")
                        continue
                else:
                    print(f"API Error with {model}: {resp.status_code} - {resp.text}")
                    continue
            except requests.RequestException as e:
                print(f"Request failed for {model}: {e}")
                continue
                
        raise Exception("All Gemini API calls failed.")

    def get_fallback_plan(self, domain: Dict) -> Dict:
        """Quality fallback if API fails completely"""
        return {
            "topic": f"The Future of {domain['subtopic']}",
            "domain": domain['domain'],
            "title": f"Mind-Blowing {domain['domain']} Secrets! 🤯",
            "hook": f"Did you know {domain['subtopic']} will change everything?",
            "script": f"Did you know {domain['subtopic']} will change everything? By 2030, this technology will be everywhere. Scientists are making massive breakthroughs right now. Imagine a world where this is normal. But there is a catch. What happens when it goes wrong? The answer might surprise you...",
            "scenes": [
                {
                    "scene_number": 1,
                    "duration": 10,
                    "voiceover": f"Did you know {domain['subtopic']} will change everything?",
                    "prompt": f"Cinematic shot of {domain['subtopic']}, photorealistic, 8k, highly detailed, dramatic lighting"
                }
            ],
            "scene_prompts": [
                f"Cinematic shot of {domain['subtopic']}, photorealistic, 8k",
                f"Futuristic laboratory working on {domain['domain']}, neon lights",
                f"Close up of {domain['subtopic']} components glowing",
                f"Wide shot of a future city utilizing {domain['domain']}",
                f"Dramatic abstract representation of {domain['subtopic']}"
            ],
            "creative_direction": {
                "voice_name": "Authoritative tech voice",
                "music_profile": "Epic sci-fi tension",
                "visual_theme": "High-tech cinematic",
                "subtitle_color": "#00FFFF"
            },
            "tags": ["technology", "future", domain['domain'].lower()],
            "hashtags": ["#tech", "#innovation", "#future"],
            "description": f"Exploring the incredible world of {domain['subtopic']}! Subscribe for more daily tech content.",
            "uzbek_analysis": f"{domain['domain']} kelajagi haqida qiziqarli faktlar. {domain['subtopic']} texnologiyasi qanday ishlashi tushuntiriladi.",
            "uzbek_voice_summary": f"{domain['subtopic']} hamma narsani o'zgartiradi. 2030 yilga borib bu oddiy holga aylanadi.",
            "duration": 45,
            "video_type": "shorts"
        }

    def generate_unique_daily_content(self, competitor_data: Optional[Dict] = None) -> Dict:
        """Main entry point to generate daily content"""
        # 1. Select domain
        domain = self.get_todays_domain()
        print(f"Selected Domain: {domain['domain']} -> {domain['subtopic']}")
        
        # 2. Build prompt
        prompt = self.build_gemini_prompt(domain, competitor_data)
        
        # 3. Call Gemini
        try:
            content_plan = self.call_gemini(prompt)
            # Ensure domain is recorded
            content_plan["domain"] = domain["domain"]
        except Exception as e:
            print(f"Failed to generate content with Gemini: {e}")
            print("Using fallback plan...")
            content_plan = self.get_fallback_plan(domain)
            
        # 4. Check history for duplicates (basic retry loop could be here, but keeping it simple for now)
        if self.is_topic_used(content_plan.get("topic", "")):
            print("Warning: Topic seems similar to past content. Proceeding anyway but note history check.")
            
        # 5. Record history
        self.record_content_history(content_plan)
        
        return content_plan

# Test execution if run directly
if __name__ == "__main__":
    brain = GeminiContentBrain()
    try:
        plan = brain.generate_unique_daily_content()
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"Execution failed: {e}")
