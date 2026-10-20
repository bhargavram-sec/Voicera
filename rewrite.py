import re

index_path = "/Users/bhargavram/Voicera/templates/index.html"

with open(index_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add GSAP & ScrollTrigger to head
head_end_idx = content.find("</head>")
gsap_scripts = """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>
    <style>
        .perspective-1000 { perspective: 1000px; }
        .perspective-2000 { perspective: 2000px; }
        .rotate-x-12 { transform: rotateX(12deg); }
        .translate-z-negative { transform: translateZ(-500px); }
        
        /* Smooth scrolling */
        html {
            scroll-behavior: smooth;
        }
    </style>
"""
if "gsap.min.js" not in content:
    content = content[:head_end_idx] + gsap_scripts + content[head_end_idx:]

# 2. Extract the glass-panel tool HTML
glass_panel_start = content.find('<div class="glass-panel rounded-3xl overflow-hidden')
glass_panel_end = content.find('</main>')
glass_panel_html = content[glass_panel_start:glass_panel_end].strip()

# 3. Build the new <main> block
new_main_html = f"""
    <main class="w-full relative overflow-x-hidden">
        
        <!-- Hero Section -->
        <section id="hero-section" class="w-full h-screen flex flex-col items-center justify-center relative origin-center">
            <header class="text-center z-10 w-full px-4 animate-float">
                <h1 id="main-title" class="text-6xl md:text-8xl font-bold mb-6 tracking-tight">
                    <span class="bg-clip-text text-transparent bg-gradient-to-r from-blue-400 via-indigo-400 to-purple-400">Voicera</span>
                </h1>
                <p id="main-subtitle" class="text-xl text-slate-400 max-w-2xl mx-auto font-light">
                    Professional Video Dubbing & Synchronization Platform
                </p>
            </header>

            <!-- Scroll Indicator -->
            <div id="scroll-indicator" class="absolute bottom-12 left-1/2 transform -translate-x-1/2 flex flex-col items-center opacity-80 cursor-pointer" onclick="document.getElementById('features-section').scrollIntoView({{behavior: 'smooth'}})">
                <span class="text-slate-400 text-xs mb-3 font-medium tracking-[0.2em] uppercase">Scroll to Explore</span>
                <div class="w-6 h-10 border-2 border-slate-600 rounded-full flex justify-center p-1">
                    <div class="w-1.5 h-2.5 bg-indigo-500 rounded-full animate-bounce mt-1"></div>
                </div>
            </div>
        </section>

        <!-- Features Section -->
        <section id="features-section" class="w-full min-h-screen py-24 flex items-center justify-center relative z-10">
            <div class="container mx-auto px-4 perspective-1000">
                <h2 class="text-4xl md:text-5xl font-bold text-center mb-16 text-white section-title opacity-0">How it works</h2>
                
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    <!-- Feature Cards -->
                    <div class="feature-card glass-panel p-8 rounded-2xl opacity-0 transform translate-y-20 rotate-x-12">
                         <div class="w-12 h-12 bg-indigo-500/20 text-indigo-400 rounded-xl flex items-center justify-center mb-6 shadow-[0_0_15px_rgba(99,102,241,0.2)]">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" /></svg>
                         </div>
                         <h3 class="text-xl font-bold text-white mb-3">Audio Extraction</h3>
                         <p class="text-slate-400 text-sm leading-relaxed">We separate the vocal tracks from background noise and music with clean precision.</p>
                    </div>
                    <!-- Card 2 -->
                    <div class="feature-card glass-panel p-8 rounded-2xl opacity-0 transform translate-y-20 rotate-x-12">
                         <div class="w-12 h-12 bg-purple-500/20 text-purple-400 rounded-xl flex items-center justify-center mb-6 shadow-[0_0_15px_rgba(168,85,247,0.2)]">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 19v-8.93a2 2 0 01.89-1.664l7-4.666a2 2 0 012.22 0l7 4.666A2 2 0 0121 10.07V19M3 19a2 2 0 002 2h14a2 2 0 002-2M3 19l6.75-4.5M21 19l-6.75-4.5M3 10l6.75 4.5M21 10l-6.75 4.5M10 12l2.25-1.5M16 12l-2.25-1.5"></path></svg>
                         </div>
                         <h3 class="text-xl font-bold text-white mb-3">Speech-to-Text</h3>
                         <p class="text-slate-400 text-sm leading-relaxed">Powered by AI to perfectly transcribe the spoken audio with exact timestamps.</p>
                    </div>
                    <!-- Card 3 -->
                    <div class="feature-card glass-panel p-8 rounded-2xl opacity-0 transform translate-y-20 rotate-x-12">
                         <div class="w-12 h-12 bg-pink-500/20 text-pink-400 rounded-xl flex items-center justify-center mb-6 shadow-[0_0_15px_rgba(236,72,153,0.2)]">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"></path></svg>
                         </div>
                         <h3 class="text-xl font-bold text-white mb-3">Translation</h3>
                         <p class="text-slate-400 text-sm leading-relaxed">Context-aware natural language translation into your desired target language.</p>
                    </div>
                    <!-- Card 4 -->
                    <div class="feature-card glass-panel p-8 rounded-2xl opacity-0 transform translate-y-20 rotate-x-12">
                         <div class="w-12 h-12 bg-blue-500/20 text-blue-400 rounded-xl flex items-center justify-center mb-6 shadow-[0_0_15px_rgba(59,130,246,0.2)]">
                            <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>
                         </div>
                         <h3 class="text-xl font-bold text-white mb-3">Voice Sync</h3>
                         <p class="text-slate-400 text-sm leading-relaxed">Generating realistic voices with lip-sync timing adjusted to match the video.</p>
                    </div>
                </div>
            </div>
        </section>

        <!-- App / Tool Section -->
        <section id="app-section" class="w-full min-h-screen py-20 flex items-center justify-center relative perspective-2000 z-20">
             <div class="container mx-auto px-4 flex justify-center pb-20">
                  <div id="main-app-container" class="w-full max-w-5xl opacity-0 transform scale-90 translate-z-negative rotate-x-12">
                      {glass_panel_html}
                  </div>
             </div>
        </section>
    </main>
"""

# Replace the old main block with the new one
main_start = content.find('<main class="container')
if main_start != -1:
    content = content[:main_start] + new_main_html + "\n"
else:
    print("Error: Could not find <main> block")
    exit(1)

# 4. Add GSAP initialization scripts at the end
gsap_init_script = """
    <script>
        // GSAP 3D Scroll Animations
        document.addEventListener('DOMContentLoaded', () => {
            gsap.registerPlugin(ScrollTrigger);

            // Hero section scroll effect: Zoom out and fade
            gsap.to("#hero-section", {
                scrollTrigger: {
                    trigger: "#hero-section",
                    start: "top top",
                    end: "bottom top",
                    scrub: 1
                },
                opacity: 0,
                scale: 0.8,
                y: 150,
                rotationX: 10,
                transformOrigin: "center center"
            });

            // Features section title
            gsap.to(".section-title", {
                scrollTrigger: {
                    trigger: "#features-section",
                    start: "top 80%",
                },
                opacity: 1,
                y: 0,
                duration: 1,
                ease: "power2.out"
            });

            // Feature cards 3D stagger
            gsap.utils.toArray(".feature-card").forEach((card, i) => {
                gsap.to(card, {
                    scrollTrigger: {
                        trigger: "#features-section",
                        start: "top 75%",
                    },
                    opacity: 1,
                    y: 0,
                    rotationX: 0,
                    duration: 1,
                    delay: i * 0.15,
                    ease: "back.out(1.5)"
                });
            });

            // Main App Container 3D scroll effect
            gsap.to("#main-app-container", {
                scrollTrigger: {
                    trigger: "#app-section",
                    start: "top 85%",
                    end: "center center",
                    scrub: 1
                },
                opacity: 1,
                scale: 1,
                z: 0,
                rotationX: 0,
                y: 0,
                ease: "power2.out",
                clearProps: "transform" // allows VanillaTilt to work properly once animation finishes
            });
            
            // Re-bind VanillaTilt for main container to ensure it works after scroll
            VanillaTilt.init(document.querySelector("#main-app-container .glass-panel"), {
                max: 3,
                speed: 400,
                glare: true,
                "max-glare": 0.15,
                gyroscope: true
            });
        });
    </script>
"""

body_end_idx = content.find("</body>")
if gsap_init_script not in content:
    content = content[:body_end_idx] + gsap_init_script + content[body_end_idx:]

with open(index_path, "w", encoding="utf-8") as f:
    f.write(content)

print("index.html rewritten successfully!")
