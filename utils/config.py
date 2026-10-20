
"""
Configuration settings for Voicera.
Includes language definitions, voice mappings, and technical terms.
"""

import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "outputs")
TEMP_FOLDER = os.path.join(BASE_DIR, "temp")

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Language configurations
# Maps internal code to display name, locale code, voices, and whisper code
LANGUAGES = {
    "hi": {
        "name": "Hindi",
        "code": "hi-IN",
        "voices": {
            "male": "hi-IN-MadhurNeural",
            "female": "hi-IN-SwaraNeural"
        },
        "whisper_code": "hi",
        "mms_code": "hin"
    },
    "ta": {
        "name": "Tamil",
        "code": "ta-IN",
        "voices": {
            "male": "ta-IN-ValluvarNeural",
            "female": "ta-IN-PallaviNeural"
        },
        "whisper_code": "ta",
        "mms_code": "tam"
    },
    "te": {
        "name": "Telugu",
        "code": "te-IN",
        "voices": {
            "male": "te-IN-MohanNeural",
            "female": "te-IN-ShrutiNeural"
        },
        "whisper_code": "te",
        "mms_code": "tel"
    },
    "kn": {
        "name": "Kannada",
        "code": "kn-IN",
        "voices": {
            "male": "kn-IN-GaganNeural",
            "female": "kn-IN-SapnaNeural"
        },
        "whisper_code": "kn",
        "mms_code": "kan"
    },
    "ml": {
        "name": "Malayalam",
        "code": "ml-IN",
        "voices": {
            "male": "ml-IN-MidhunNeural",
            "female": "ml-IN-SobhanaNeural"
        },
        "whisper_code": "ml",
        "mms_code": "mal"
    },
    "en": {
        "name": "English",
        "code": "en-IN",  # Using Indian English for consistency in tone
        "voices": {
            "male": "en-IN-PrabhatNeural",
            "female": "en-IN-NeerjaNeural"
        },
        "whisper_code": "en",
        "mms_code": "eng"
    }
}

# Technical terms to preserve during translation
TECHNICAL_TERMS = [
    # Programming basics
    "API", "JSON", "XML", "HTML", "CSS", "Function", "Array", "Class",
    "Object", "Variable", "Loop", "If", "Else", "Return", "Import", "Export",
    "String", "Integer", "Boolean", "Float", "Void", "Null", "Public", "Private",
    
    # Python specific
    "List", "Dict", "Tuple", "Set", "Lambda", "Decorator", "Generator", "Pip",
    "Virtualenv", "Self", "Init", "Dunder",
    
    # JavaScript
    "Async", "Await", "Promise", "Callback", "DOM", "Const", "Let", "Var",
    "Arrow function", "React", "Vue", "Angular", "Node", "Npm", "Yarn",
    
    # Data/ML
    "Database", "Query", "Neural network", "Algorithm", "Dataset", "Model",
    "Training", "Inference", "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn",
    
    # Tools/Platforms
    "GitHub", "Docker", "AWS", "Azure", "Linux", "Git", "Kubernetes", "Redis",
    "Mongo", "Postgres", "SQL", "REST", "GraphQL", "HTTP", "HTTPS", "Localhost",

    # Common UI/UX (Keep these in English for natural feel)
    "Video", "Audio", "Click", "Link", "Browser", "Tab", "Menu", "Settings", 
    "Profile", "Login", "Sign up", "Download", "Upload", "Button", "Screen",
    "Laptop", "Mobile", "Desktop", "App", "Website", "Page", "Internet"
]

# Processing settings
MAX_VIDEO_LENGTH = 600  # 10 minutes in seconds
TEMPO_MIN = 0.85
TEMPO_MAX = 1.15
MAX_EXPANSION_RATIO = 1.30
