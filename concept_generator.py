#!/usr/bin/env python3
"""
Daily Concept Redesign Generator
Picks an everyday concept/product/system, identifies problems, proposes redesigns.
Sends playful design-doc email. Tracks history to avoid repeats.
"""

import os
import json
import yaml
import random
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic

# ============================================================================
# CONFIGURATION
# ============================================================================

CONCEPTS_HISTORY_FILE = os.path.expanduser("~/claude-concepts/concepts_history.yaml")
API_KEY = os.getenv("ANTHROPIC_API_KEY")
GMAIL_USER = os.getenv("GMAIL_USER")  # your email
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")  # app password from Google
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", GMAIL_USER)  # defaults to your email

# Weekly theme rotation
THEMES = {
    0: "Digital/Consumer Apps",  # Monday
    1: "Physical Products",       # Tuesday
    2: "Social/Institutional Systems",  # Wednesday
    3: "Behavioral Patterns",     # Thursday
    4: "Wildcard",                # Friday
    5: "Cultural Concepts",       # Saturday
    6: "Time & Rituals",          # Sunday
}

# Concept pools for each theme
CONCEPT_POOLS = {
    "Digital/Consumer Apps": [
        "Email inbox organization",
        "Search result ranking",
        "Social media feeds",
        "Chat notifications",
        "Password management",
        "Calendar blocking",
        "Note-taking apps",
        "Code collaboration tools",
        "Video conferencing UI",
        "Shopping cart experience",
        "Read-it-later apps",
        "Task management dashboards",
    ],
    "Physical Products": [
        "The keyboard layout (QWERTY)",
        "Door handles and hinges",
        "Staircase design",
        "Light switches",
        "The coffee cup",
        "Pen and paper",
        "The shopping cart",
        "Doorbell mechanics",
        "Toilet paper orientation",
        "The zipper",
        "Bookmark ribbons",
        "Mailbox design",
    ],
    "Social/Institutional Systems": [
        "The resume format",
        "Meeting agendas",
        "Grade letter systems",
        "The job interview",
        "Email etiquette",
        "Commit messages",
        "Pull request reviews",
        "Office hours",
        "The handshake",
        "Waiting in lines",
        "The calendar invite",
        "Feedback forms",
    ],
    "Behavioral Patterns": [
        "How we multitask",
        "Decision fatigue in apps",
        "Context switching costs",
        "The inbox zero myth",
        "Meeting culture",
        "Procrastination triggers",
        "Learning by rote",
        "Documentation reading",
        "Onboarding flows",
        "Exit surveys",
        "The standing ovation",
        "Seating arrangements",
    ],
    "Wildcard": [
        "Naming conventions in code",
        "Error messages",
        "FAQs as a concept",
        "The README file",
        "Credit card layouts",
        "Airport security lines",
        "Library card systems",
        "The resume (again, because it's so weird)",
        "How we measure time",
        "Tipping culture",
        "The license plate format",
        "Bug reporting templates",
    ],
    "Cultural Concepts": [
        "Holiday traditions",
        "Small talk conventions",
        "Gift-giving rituals",
        "The concept of privacy",
        "Personal space bubbles",
        "Eye contact norms",
        "Punctuality expectations",
        "The concept of 'busy'",
        "Status symbols",
        "Apology scripts",
    ],
    "Time & Rituals": [
        "The 9-to-5 workday",
        "Weekly planning",
        "The standup meeting",
        "Break time culture",
        "Commute routines",
        "Sleep schedules",
        "Meal times",
        "The weekend concept",
        "Annual reviews",
        "The sprint cycle",
    ],
}

# ============================================================================
# HISTORY MANAGEMENT
# ============================================================================

def load_history():
    """Load concepts history from YAML file."""
    if not os.path.exists(CONCEPTS_HISTORY_FILE):
        return {"concepts": []}
    with open(CONCEPTS_HISTORY_FILE, "r") as f:
        return yaml.safe_load(f) or {"concepts": []}

def save_history(history):
    """Save concepts history to YAML file."""
    os.makedirs(os.path.dirname(CONCEPTS_HISTORY_FILE), exist_ok=True)
    with open(CONCEPTS_HISTORY_FILE, "w") as f:
        yaml.dump(history, f, default_flow_style=False, sort_keys=False)

def get_covered_concepts():
    """Return set of concept names already covered."""
    history = load_history()
    return {c["concept"] for c in history.get("concepts", [])}

def pick_concept(theme):
    """Pick a concept from the theme pool that hasn't been covered."""
    covered = get_covered_concepts()
    pool = CONCEPT_POOLS.get(theme, CONCEPT_POOLS["Wildcard"])
    available = [c for c in pool if c not in covered]
    
    if not available:
        # Reset pool if all exhausted
        print(f"[INFO] All concepts in '{theme}' exhausted. Resetting pool.")
        available = pool
    
    return random.choice(available)

def add_to_history(concept, theme, analysis, redesign):
    """Add new concept analysis to history."""
    history = load_history()
    entry = {
        "id": len(history["concepts"]) + 1,
        "date": datetime.now().isoformat(),
        "theme": theme,
        "concept": concept,
        "analysis": analysis,
        "redesign": redesign,
    }
    history["concepts"].append(entry)
    save_history(history)
    return entry

# ============================================================================
# CLAUDE API CALLS
# ============================================================================

def generate_concept_analysis(concept, theme):
    """Call Claude to analyze the concept and propose redesign."""
    client = anthropic.Anthropic(api_key=API_KEY)
    
    prompt = f"""You are a playful but insightful design thinker. Your task:

CONCEPT TO RETHINK: {concept}
THEME CATEGORY: {theme}

**PART 1: Identify Problems**
Think about how we currently use/experience {concept}. What assumptions are baked in? What frictions exist? What weird quirks did we just accept as "that's how it's done"? List 3-4 core problems.

**PART 2: Propose a Redesign**
Imagine we're redesigning {concept} from scratch. You can think outside the box, but it should be achievable (not pure sci-fi). How would it work differently? What problems does it solve? What new possibilities does it open?

**PART 3: Tongue-in-Cheek Tagline**
End with a cheeky 1-liner that captures the vibe of your redesign.

Format your response as:
---PROBLEMS---
[list here]

---REDESIGN---
[description here]

---TAGLINE---
[one-liner]
"""
    
    message = client.messages.create(
        model="claude-opus-4-20250805",
        max_tokens=1200,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text

def parse_analysis(text):
    """Parse Claude's response into structured format."""
    sections = {
        "problems": "",
        "redesign": "",
        "tagline": ""
    }
    
    current_section = None
    lines = text.split("\n")
    
    for line in lines:
        if "---PROBLEMS---" in line:
            current_section = "problems"
        elif "---REDESIGN---" in line:
            current_section = "redesign"
        elif "---TAGLINE---" in line:
            current_section = "tagline"
        elif current_section and line.strip():
            sections[current_section] += line + "\n"
    
    return {k: v.strip() for k, v in sections.items()}

# ============================================================================
# EMAIL GENERATION & SENDING
# ============================================================================

def get_history_summary():
    """Get a summary of past concepts."""
    history = load_history()
    concepts = history.get("concepts", [])
    
    if not concepts:
        return "No concepts analyzed yet. You're on the ground floor!"
    
    total = len(concepts)
    themes_covered = {}
    for c in concepts:
        theme = c.get("theme", "Unknown")
        themes_covered[theme] = themes_covered.get(theme, 0) + 1
    
    summary = f"Total concepts explored: {total}\n"
    for theme, count in sorted(themes_covered.items()):
        summary += f"  • {theme}: {count}\n"
    
    recent = concepts[-3:]
    summary += "\nRecent concepts:\n"
    for c in recent:
        date_str = datetime.fromisoformat(c["date"]).strftime("%Y-%m-%d")
        summary += f"  • {c['concept']} ({date_str})\n"
    
    return summary

def format_email_body(concept, theme, analysis):
    """Format the email body with design-doc + playful tone."""
    parsed = parse_analysis(analysis)
    history_summary = get_history_summary()
    
    body = f"""
╔════════════════════════════════════════════════════════════════╗
║          TODAY'S CONCEPT RETHINK                               ║
╚════════════════════════════════════════════════════════════════╝

Date: {datetime.now().strftime('%A, %B %d, %Y')}
Theme: {theme}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CONCEPT: {concept}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

WHAT'S ACTUALLY WEIRD ABOUT IT:

{parsed['problems']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HERE'S A BETTER WAY:

{parsed['redesign']}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

THE VIBE:
"{parsed['tagline']}"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

YOUR EXPLORATION SO FAR:

{history_summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

See you tomorrow for a fresh concept.

- Your Daily Design Muse 🧠✨
"""
    
    return body

def send_email(subject, body):
    """Send email via Gmail SMTP."""
    if not all([GMAIL_USER, GMAIL_APP_PASSWORD, RECIPIENT_EMAIL]):
        print("[ERROR] Missing Gmail credentials. Set GMAIL_USER and GMAIL_APP_PASSWORD env vars.")
        return False
    
    try:
        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = RECIPIENT_EMAIL
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"[SUCCESS] Email sent to {RECIPIENT_EMAIL}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return False

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def get_todays_theme():
    """Get theme based on day of week."""
    day_of_week = datetime.now().weekday()
    return THEMES.get(day_of_week, "Wildcard")

def run_daily_generation():
    """Main function to generate and send today's concept."""
    print("[START] Daily concept generation")
    
    # Validate API key
    if not API_KEY:
        print("[ERROR] ANTHROPIC_API_KEY not set. Exiting.")
        return False
    
    # Pick theme and concept
    theme = get_todays_theme()
    concept = pick_concept(theme)
    print(f"[INFO] Theme: {theme} | Concept: {concept}")
    
    # Generate analysis
    print("[INFO] Calling Claude API...")
    analysis = generate_concept_analysis(concept, theme)
    
    # Save to history
    entry = add_to_history(concept, theme, analysis, "")
    print(f"[INFO] Saved to history (ID: {entry['id']})")
    
    # Format and send email
    email_subject = f"Daily Rethink: {concept} ({theme})"
    email_body = format_email_body(concept, theme, analysis)
    
    if GMAIL_USER:
        send_email(email_subject, email_body)
    else:
        print("[INFO] No GMAIL_USER set. Printing email instead:")
        print(email_subject)
        print(email_body)
    
    print("[END] Daily generation complete\n")
    return True

if __name__ == "__main__":
    run_daily_generation()