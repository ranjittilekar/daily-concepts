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

def generate_concept(theme, api_key):
    """Have Claude generate a fresh, novel concept for the given theme."""
    covered = get_covered_concepts()
    covered_list = ", ".join(sorted(covered)) if covered else "None yet"
    
    client = anthropic.Anthropic(api_key=api_key)
    
    prompt = f"""You are a creative design thinker. Generate ONE fresh, interesting concept to rethink for the theme: "{theme}"

CONSTRAINTS:
- Pick something specific and concrete (not too abstract)
- It should be something people use/experience in everyday life
- Should be something that hasn't been questioned much
- AVOID these already-covered concepts: {covered_list}

RESPOND WITH ONLY THE CONCEPT NAME, nothing else. Just the name, no explanation.
Examples of good responses: "The coffee cup", "Email signatures", "Handshakes", "Status messages"

Generate a new concept now:"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=100,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    concept = message.content[0].text.strip()
    return concept

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

**PART 4: Self-Evaluation**
Now be brutally honest: Is this redesign actually GOOD? Is it logical, impactful, and interesting? Or does it feel forced, generic, or not that novel?
Answer with ONE word only: GOOD or WEAK

Format your response as:
---PROBLEMS---
[list here]

---REDESIGN---
[description here]

---TAGLINE---
[one-liner]

---QUALITY---
[GOOD or WEAK]
"""
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1200,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    return message.content[0].text

def markdown_to_html(text):
    """Convert markdown formatting to HTML."""
    import re
    # Convert **bold** to <strong>bold</strong>
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    # Convert *italic* to <em>italic</em>
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    return text

def parse_analysis(text):
    """Parse Claude's response into structured format."""
    sections = {
        "problems": "",
        "redesign": "",
        "tagline": "",
        "quality_assessment": ""
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
        elif "---QUALITY---" in line:
            current_section = "quality_assessment"
        elif current_section and line.strip():
            sections[current_section] += line + "\n"
    
    # Convert markdown to HTML for non-tagline sections
    sections["problems"] = markdown_to_html(sections["problems"].strip())
    sections["redesign"] = markdown_to_html(sections["redesign"].strip())
    sections["quality_assessment"] = sections["quality_assessment"].strip()
    
    return sections

# ============================================================================
# EMAIL GENERATION & SENDING
# ============================================================================

# ============================================================================
# EMAIL GENERATION & SENDING
# ============================================================================

def get_history_html():
    """Generate HTML for history summary with stats."""
    history = load_history()
    concepts = history.get("concepts", [])
    
    if not concepts:
        return f"""
        <p style="color: #666; font-style: italic;">No concepts yet. You're on the ground floor! 🚀</p>
        """
    
    total = len(concepts)
    themes_covered = {}
    for c in concepts:
        theme = c.get("theme", "Unknown")
        themes_covered[theme] = themes_covered.get(theme, 0) + 1
    
    recent = concepts[-3:]
    
    theme_html = "".join([
        f'<li style="margin: 8px 0; color: #555;"><strong>{theme}:</strong> {count} concepts</li>'
        for theme, count in sorted(themes_covered.items())
    ])
    
    recent_html = "".join([
        f'<li style="margin: 8px 0; color: #555;">{c["concept"]} <span style="color: #999; font-size: 0.9em;">({datetime.fromisoformat(c["date"]).strftime("%b %d")})</span></li>'
        for c in recent
    ])
    
    return f"""
    <div style="background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%); padding: 20px; border-radius: 12px; margin-top: 20px;">
        <h3 style="margin: 0 0 15px 0; color: #2c3e50; font-size: 16px;">📊 Your Exploration Journey</h3>
        <p style="margin: 0 0 12px 0; color: #2c3e50; font-weight: bold; font-size: 18px;">{total} concepts explored</p>
        <ul style="list-style: none; padding: 0; margin: 12px 0 0 0;">
            {theme_html}
        </ul>
        <p style="margin: 15px 0 8px 0; color: #2c3e50; font-weight: 600; font-size: 13px;">Recent:</p>
        <ul style="list-style: none; padding: 0; margin: 0;">
            {recent_html}
        </ul>
    </div>
    """

def format_email_body(concept, theme, analysis):
    """Format the email body as vibrant, playful HTML."""
    parsed = parse_analysis(analysis)
    history_html = get_history_html()
    
    date_str = datetime.now().strftime('%A, %B %d, %Y')
    
    body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; color: #333; line-height: 1.6; }}
            a {{ color: #6366f1; text-decoration: none; }}
        </style>
    </head>
    <body style="font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; color: #333; margin: 0; padding: 0; background-color: #fafbfc;">
        
        <!-- Container -->
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            
            <!-- Header -->
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="margin: 0 0 10px 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; font-size: 32px; font-weight: 700;">
                    Daily Rethink 🧠
                </h1>
                <p style="margin: 0; color: #999; font-size: 13px; letter-spacing: 1px;">A Fresh Concept Every Day</p>
            </div>
            
            <!-- Date & Theme -->
            <div style="text-align: center; margin-bottom: 30px; padding: 15px; background: #f0f4ff; border-radius: 10px;">
                <p style="margin: 0; color: #667eea; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">{date_str}</p>
                <p style="margin: 8px 0 0 0; color: #764ba2; font-size: 14px; font-weight: 500;">Theme: <strong>{theme}</strong></p>
            </div>
            
            <!-- Concept Card -->
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 15px; margin-bottom: 25px; color: white; text-align: center;">
                <p style="margin: 0 0 10px 0; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; opacity: 0.9;">Today's Concept</p>
                <h2 style="margin: 0; font-size: 28px; font-weight: 700; line-height: 1.2;">{concept}</h2>
            </div>
            
            <!-- Problems Section -->
            <div style="margin-bottom: 25px;">
                <div style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 2px; border-radius: 12px; margin-bottom: 15px;">
                    <div style="background: white; padding: 20px; border-radius: 10px;">
                        <h3 style="margin: 0 0 15px 0; color: #f5576c; font-size: 18px; font-weight: 700;">🤔 What's Actually Weird About It?</h3>
                        <div style="color: #555; font-size: 15px; line-height: 1.7;">
                            {parsed['problems'].replace(chr(10), '<br>')}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Redesign Section -->
            <div style="margin-bottom: 25px;">
                <div style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); padding: 2px; border-radius: 12px; margin-bottom: 15px;">
                    <div style="background: white; padding: 20px; border-radius: 10px;">
                        <h3 style="margin: 0 0 15px 0; color: #00f2fe; font-size: 18px; font-weight: 700;">✨ Here's a Better Way</h3>
                        <div style="color: #555; font-size: 15px; line-height: 1.7;">
                            {parsed['redesign'].replace(chr(10), '<br>')}
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Tagline Section -->
            <div style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 25px;">
                <p style="margin: 0; color: #fff; font-size: 16px; font-weight: 600; font-style: italic;">
                    "{parsed['tagline']}"
                </p>
            </div>
            
            <!-- History Section -->
            {history_html}
            
            <!-- Footer -->
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                <p style="margin: 0 0 10px 0; color: #999; font-size: 13px;">See you tomorrow for a fresh concept</p>
                <p style="margin: 0; color: #bbb; font-size: 12px;">Your Daily Design Muse 🧠✨</p>
            </div>
            
        </div>
        
    </body>
    </html>
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
        msg.attach(MIMEText(body, "html"))
        
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
    
    # Pick theme and generate a novel concept with quality check
    theme = get_todays_theme()
    print(f"[INFO] Theme: {theme}")
    
    max_attempts = 3
    attempt = 0
    analysis = None
    concept = None
    
    while attempt < max_attempts:
        attempt += 1
        print(f"[INFO] Attempt {attempt}/{max_attempts}")
        print("[INFO] Generating a novel concept...")
        concept = generate_concept(theme, API_KEY)
        print(f"[INFO] Generated concept: {concept}")
        
        # Generate analysis
        print("[INFO] Analyzing concept...")
        analysis = generate_concept_analysis(concept, theme)
        
        # Check quality assessment
        parsed = parse_analysis(analysis)
        quality = parsed.get("quality_assessment", "").strip().upper()
        
        if "GOOD" in quality:
            print(f"[INFO] Quality assessment: GOOD ✓")
            break
        else:
            print(f"[INFO] Quality assessment: WEAK - Trying another concept...")
            if attempt < max_attempts:
                continue
            else:
                print(f"[INFO] Max attempts reached. Sending this concept anyway.")
                break
    
    if not analysis:
        print("[ERROR] Failed to generate analysis")
        return False
    
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