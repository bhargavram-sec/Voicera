
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
# Maps internal code to display name, locale code, voices, and sarvam code
LANGUAGES = {
    "hi": {
        "name": "Hindi",
        "code": "hi-IN",
        "voices": {
            "male": "hi-IN-MadhurNeural",
            "female": "hi-IN-SwaraNeural"
        },
        "sarvam_code": "hi-IN",
        "mms_code": "hin"
    },
    "ta": {
        "name": "Tamil",
        "code": "ta-IN",
        "voices": {
            "male": "ta-IN-ValluvarNeural",
            "female": "ta-IN-PallaviNeural"
        },
        "sarvam_code": "ta-IN",
        "mms_code": "tam"
    },
    "te": {
        "name": "Telugu",
        "code": "te-IN",
        "voices": {
            "male": "te-IN-MohanNeural",
            "female": "te-IN-ShrutiNeural"
        },
        "sarvam_code": "te-IN",
        "mms_code": "tel"
    },
    "kn": {
        "name": "Kannada",
        "code": "kn-IN",
        "voices": {
            "male": "kn-IN-GaganNeural",
            "female": "kn-IN-SapnaNeural"
        },
        "sarvam_code": "kn-IN",
        "mms_code": "kan"
    },
    "ml": {
        "name": "Malayalam",
        "code": "ml-IN",
        "voices": {
            "male": "ml-IN-MidhunNeural",
            "female": "ml-IN-SobhanaNeural"
        },
        "sarvam_code": "ml-IN",
        "mms_code": "mal"
    },
    "en": {
        "name": "English",
        "code": "en-IN",  # Using Indian English for consistency in tone
        "voices": {
            "male": "en-IN-PrabhatNeural",
            "female": "en-IN-NeerjaNeural"
        },
        "sarvam_code": "en-IN",
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

    # Common UI/UX & Digital (Keep in English for natural feel)
    "Video", "Audio", "Click", "Link", "Browser", "Tab", "Menu", "Settings", 
    "Profile", "Login", "Sign up", "Download", "Upload", "Button", "Screen",
    "Laptop", "Mobile", "Desktop", "App", "Website", "Page", "Internet",
    "Message", "Call", "Chat", "Post", "Story", "Reel", "Photo", "Selfie", "Status",
    "Group", "Network", "Wi-Fi", "Data", "Sim", "Recharge", "Battery", "Charger",
    "Bluetooth", "Notification", "Update", "Account", "Password", "OTP",

    # Education & School/College Life
    "School", "College", "University", "Class", "Section", "Subject", "Lesson",
    "Teacher", "Sir", "Madam", "Student", "Principal", "Staff", "Homework", "Project",
    "Assignment", "Exam", "Test", "Quiz", "Marks", "Grade", "Rank", "Pass", "Fail",
    "Degree", "Certificate", "Fees", "Scholarship", "Campus", "Library", "Hostel",

    # Objects, Stationery & Daily Essentials
    "Phone", "Computer", "Pen", "Pencil", "Eraser", "Sharpener", "Book", "Notebook",
    "Paper", "Bag", "Bottle", "Box", "File", "Folder", "Camera", "Mic", "Speaker",
    "Headphones", "Earphones", "Key", "Lock", "Wallet", "Purse", "Pocket",

    # Work, Career & Professional Life
    "Office", "Company", "Job", "Work", "Duty", "Shift", "Meeting", "Interview",
    "Resume", "Salary", "Bonus", "Leave", "Holiday", "Boss", "Manager", "Colleague",
    "Client", "Customer", "Report", "Task", "Target", "Deadline", "Promotion",

    # Places, Buildings & Rooms
    "Hospital", "Clinic", "Bank", "Hotel", "Restaurant", "Mall", "Shop", "Store",
    "Market", "Flat", "Apartment", "Room", "Hall", "Kitchen", "Bedroom", "Bathroom",
    "Balcony", "Garden", "Gate", "Door", "Window",

    # Household Appliances & Furniture
    "Fan", "Light", "Switch", "Plug", "Wire", "Remote", "TV", "Fridge",
    "Washing machine", "Iron", "AC", "Cooler", "Heater", "Tap", "Mirror",
    "Table", "Chair", "Sofa", "Bed", "Pillow", "Blanket", "Towel", "Soap", "Shampoo",

    # Travel, Vehicles & Commute
    "Bus", "Train", "Metro", "Car", "Bike", "Scooter", "Cycle", "Auto", "Cab", "Taxi",
    "Flight", "Plane", "Airport", "Station", "Stop", "Stand", "Platform", "Ticket",
    "Seat", "Road", "Highway", "Bridge", "Traffic", "Signal", "Helmet", "License",
    "Petrol", "Diesel", "Fastag", "Mechanic", "Garage", "Puncture", "Route", "Map", "GPS",

    # Medical & Healthcare
    "Doctor", "Nurse", "Medicine", "Tablet", "Capsule", "Syrup", "Injection",
    "Bandage", "X-ray", "Scan", "Blood test", "Fever", "Cold", "Cough", "Headache",
    "Pain", "BP", "Sugar", "Operation", "Emergency", "Ambulance", "Gym", "Diet",

    # Food, Dining & Groceries
    "Breakfast", "Lunch", "Dinner", "Snack", "Snacks", "Coffee", "Tea", "Milk",
    "Bread", "Butter", "Jam", "Juice", "Shake", "Ice cream", "Cake", "Chocolate",
    "Biscuit", "Order", "Parcel", "Delivery", "Menu", "Plate", "Glass", "Spoon", "Fork",

    # Financial & Shopping Transactions
    "Money", "Cash", "Coin", "Card", "Bill", "Balance", "Account", "Transfer",
    "UPI", "Scanner", "QR code", "Credit", "Debit", "Loan", "EMI", "Interest",
    "Discount", "Offer", "Sale", "Brand", "Shopping", "Receipt", "Signature",

    # Time, Days & Routine
    "Time", "Date", "Month", "Year", "Minute", "Second", "Hour",
    "Morning", "Afternoon", "Evening", "Night", "Daily", "Weekly", "Weekend",
    "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
    "Birthday", "Anniversary", "Party", "Function",

    # Casual Conversational Words & Emotions
    "Problem", "Issue", "Solution", "Idea", "Plan", "Tension", "Stress", "Mood",
    "Boring", "Busy", "Free", "Late", "Early", "Ready", "Sure", "Clear", "Doubt",
    "Simple", "Easy", "Hard", "Important", "Urgent", "Mistake", "Sorry", "Thank you",
    "Welcome", "Please", "Bye", "Hi", "Hello", "OK", "Okay", "Done", "Super", "Nice"
]

# Processing settings
MAX_VIDEO_LENGTH = 600  # 10 minutes in seconds
TEMPO_MIN = 0.85
TEMPO_MAX = 1.15
MAX_EXPANSION_RATIO = 1.30
