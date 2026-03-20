# Daily Concept Rethink Generator

A system that emails you a new everyday concept to rethink every morning. Picks from digital products, physical things, social systems, behavioral patterns, and more. Identifies problems, proposes playful redesigns.

Your daily dose of speculative design thinking.

---

## Quick Start (5 minutes)

### 1. Install Dependencies
```bash
pip install anthropic pyyaml
```

### 2. Get Your API Keys

**Anthropic API Key:**
- Go to [console.anthropic.com](https://console.anthropic.com)
- Sign in, click profile icon (top right)
- Click "API Keys" > "Create Key"
- Copy the key

**Gmail App Password:**
- Enable 2FA on your Google account (if not already done)
- Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
- Select "Mail" and "Windows Computer" (or any device)
- Google generates a 16-character password
- Copy it (you'll only see it once)

### 3. Set Environment Variables
```bash
cd ~/claude-concepts

# Copy the template
cp .env.example .env

# Edit .env with your values
nano .env
# OR
vim .env
```

Fill in:
```
export ANTHROPIC_API_KEY="sk-ant-xxxxx..."
export GMAIL_USER="your-email@gmail.com"
export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"  # 16 chars, spaces OK
export RECIPIENT_EMAIL="your-email@gmail.com"  # Optional, defaults to GMAIL_USER
```

### 4. Test It
```bash
source .env
/generate
```

You should receive an email with today's concept rethink.

---

## Using Claude Code

This project is structured for Claude Code with slash commands. After setup:

```
/generate       Manually trigger concept generation (test mode)
/history        View all concepts explored so far
/recent         Show last 5 concepts with full detail
/schedule       Instructions for automating with cron
/test-email     Diagnose Gmail configuration
```

### How to Run in Claude Code

1. Save the project to a location Claude Code can access
2. Set env vars in your terminal session
3. Use the slash commands above

Or manually run:
```bash
python3 ~/claude-concepts/concept_generator.py
```

---

## Setting Up Daily Automation (Cron)

Once testing is done:

### 1. Create Log Directory
```bash
mkdir -p ~/claude-concepts/logs
```

### 2. Add to Crontab
```bash
crontab -e
```

Paste this line (runs at 7 AM daily):
```
0 7 * * * source ~/.bash_profile && cd ~/claude-concepts && source .env && python3 concept_generator.py >> ~/claude-concepts/logs/cron.log 2>&1
```

Change the hour (first `0` = minute, first `7` = hour in 24-hour format):
- `0 7 * * *` = 7 AM
- `0 9 * * *` = 9 AM
- `0 20 * * *` = 8 PM

### 3. Verify It's Running
```bash
tail -f ~/claude-concepts/logs/cron.log
```

You should see success messages each day.

---

## Customization

### Change Themes or Concepts

Edit `concept_generator.py`:

```python
THEMES = {
    0: "Digital/Consumer Apps",  # Monday
    1: "Physical Products",       # Tuesday
    2: "Social/Institutional Systems",  # Wednesday
    # ... etc
}

CONCEPT_POOLS = {
    "Digital/Consumer Apps": [
        "Email inbox organization",
        "Search result ranking",
        # Add or remove concepts here
    ],
    # ... more themes
}
```

### Change Email Time

Edit the crontab line. Examples:
- `0 6 * * *` = 6 AM
- `30 8 * * *` = 8:30 AM
- `0 22 * * *` = 10 PM

### Change Email Recipient

Set `RECIPIENT_EMAIL` to a different email address, or add multiple cron jobs with different email addresses.

---

## How It Works

1. **Picks a concept** based on today's theme (rotates daily: Digital, Physical, Systems, Patterns, Wildcard, Cultural, Time & Rituals)
2. **Avoids repeats** by tracking concepts in `concepts_history.yaml`
3. **Calls Claude API** with a detailed prompt asking for:
   - Problems with the current approach
   - A playful but achievable redesign
   - A cheeky tagline
4. **Sends an email** with formatted analysis and your exploration history
5. **Logs to history file** so it never covers the same concept twice

---

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
Make sure you ran: `source .env`

### Email not sending
Run: `/test-email`

This will:
- Check your Gmail credentials
- Attempt SMTP connection
- Send a test email
- Give you specific error messages

Common issues:
- Using regular Gmail password instead of app password
- 2FA not enabled on Google account
- Gmail blocking the connection (check your email for alerts)

### Cron job not running
Check:
1. `crontab -l` to see your job
2. `tail ~/claude-concepts/logs/cron.log` for errors
3. Make sure `.env` is sourced in the cron command

### API rate limits
The Anthropic API is generous. If you hit limits, concepts are cached in history so it won't re-analyze.

---

## Project Structure

```
~/claude-concepts/
├── concept_generator.py       # Main script
├── concepts_history.yaml      # Tracking file (auto-created)
├── .env                       # Your secrets (don't commit)
├── .env.example              # Template
├── gstack.yaml               # Claude Code commands
├── handlers/
│   ├── generate.sh           # /generate
│   ├── history.sh            # /history
│   ├── recent.sh             # /recent
│   ├── schedule.sh           # /schedule
│   └── test-email.sh         # /test-email
├── logs/
│   └── cron.log             # Cron execution log
└── README.md                 # This file
```

---

## Notes & Tips

- **History is sacred**: Every concept is tracked to prevent repeats. Check `concepts_history.yaml` to see your journey.
- **Themes rotate**: Monday through Friday follow the schedule. Weekends too. Friday = Wildcard = surprise me.
- **Tone**: Emails are playful and design-doc-ish. Adjust the format in `format_email_body()` if you want.
- **Scale**: The concept pools have 12 ideas each. After ~60 concepts per theme, the pool resets. So you'll never fully run out.
- **API cost**: Each concept costs ~1-2 cents in API calls (very cheap).

---

## Feedback & Iteration

Want to skip a concept? Edit `concepts_history.yaml` and remove it, or add notes.

Want to add concepts? Expand `CONCEPT_POOLS` with new ideas.

Want different themes? Rename or reorder `THEMES` and `CONCEPT_POOLS`.

---

## Questions?

If something breaks:
1. Run `/test-email` to diagnose
2. Check cron logs: `tail ~/claude-concepts/logs/cron.log`
3. Look for error messages in the terminal output
4. Verify all env vars are set: `echo $ANTHROPIC_API_KEY`

---

Happy rethinking! 🧠✨