import re

def main():
    with open("rewrite.py", "r", encoding="utf-8") as f:
        rewrite_code = f.read()

    # Extract the new_main_html block from rewrite.py
    match = re.search(r'new_main_html = f?"""(.*?)"""', rewrite_code, re.DOTALL)
    new_main_html = match.group(1)

    parts = new_main_html.split("{glass_panel_html}")
    header_html = parts[0]
    footer_html = parts[1]

    # Read index.html
    with open("templates/index.html", "r", encoding="utf-8") as f:
        index_html = f.read()

    # Replace head
    head_inject = """
    <script src="https://cdn.tailwindcss.com"></script>
    <script>tailwind.config = { corePlugins: { preflight: false } }</script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vanilla-tilt/1.8.0/vanilla-tilt.min.js"></script>
"""
    if "cdn.tailwindcss.com" not in index_html:
        index_html = index_html.replace('<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap', head_inject + '    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap')

    # Extract Studio section
    s_idx = index_html.find('<section id="studio">')
    e_idx = index_html.find('</section>', s_idx) + 10
    studio_html = index_html[s_idx:e_idx]

    # Find where to replace
    nav_start = index_html.find('<nav>')
    nav_end = index_html.find('</nav>') + 6
    nav_html = index_html[nav_start:nav_end]
    nav_html = nav_html.replace('#showcase-wrap', '#features-section').replace('#studio', '#app-section')

    # We want to replace from nav_end to the end of studio_html
    pre_content = index_html[:nav_start]
    post_content = index_html[e_idx:]

    # Assemble
    final_html = pre_content + nav_html + "\n" + header_html + "\n" + studio_html + "\n" + footer_html + post_content

    with open("templates/index.html", "w", encoding="utf-8") as f:
        f.write(final_html)

    # Extract GSAP logic from rewrite.py
    gsap_match = re.search(r'gsap_init_script = """(.*?)"""', rewrite_code, re.DOTALL)
    gsap_script = gsap_match.group(1)
    # Remove script tags
    gsap_script = gsap_script.replace("<script>", "").replace("</script>", "")
    # Remove DOMContentLoaded wrapper because we will put it inside main.js's wrapper
    # wait, the string has "document.addEventListener('DOMContentLoaded', () => {" and "});" at the end.
    gsap_body = gsap_script.split("document.addEventListener('DOMContentLoaded', () => {")[1].rsplit("});", 1)[0]

    # Read main.js
    with open("static/js/main.js", "r", encoding="utf-8") as f:
        main_js = f.read()

    start_gsap = main_js.find("// ── GSAP ──")
    end_gsap = main_js.find("// ── DECEPTION AUDIO ──")

    new_gsap_block = """// ── GSAP ──
document.addEventListener('DOMContentLoaded', () => {
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') return;
    gsap.registerPlugin(ScrollTrigger);

""" + gsap_body + """
});

"""

    final_main_js = main_js[:start_gsap] + new_gsap_block + main_js[end_gsap:]

    with open("static/js/main.js", "w", encoding="utf-8") as f:
        f.write(final_main_js)

if __name__ == "__main__":
    main()
