with open("templates/index.html", "r") as f:
    data = f.read()

# adding z-index to #studio
#studio {
#    background: #000;
#    padding: 90px 5vw;
#    border-top: 1px solid rgba(255, 255, 255, .06)
#}
import re
new_data = re.sub(r'(#studio\s*{\s*background:\s*#000;\s*padding:\s*90px\s*5vw;\s*border-top:\s*[^\n]+)', 
                  r'\1\n            position: relative;\n            z-index: 10;', data)

with open("templates/index.html", "w") as f:
    f.write(new_data)
