#!/usr/bin/env python3
"""
Email alerts voor Baakie Space Monitor
Stuurt een mail bij status changes (online → offline, etc.)
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict

# ═══════════════════════════════════════════════════════════════
# CONFIGURATIE — Pas dit aan voor jouw situatie
# ═══════════════════════════════════════════════════════════════

SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SMTP_USER = "a.verboon@inspreadables.com"
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")  # Gebruik environment variable!

# Ontvanger(s) van alerts
ALERT_RECIPIENTS = [
    "a.verboon@inspreadables.com",
    # Voeg meer adressen toe indien nodig
]

# Alleen alerts sturen voor deze status changes
ALERT_ON_CHANGES = ["online→offline", "online→degraded", "degraded→offline"]

# ═══════════════════════════════════════════════════════════════
# FUNCTIES
# ═══════════════════════════════════════════════════════════════

def send_alert(changes: List[Dict]) -> bool:
    """
    Stuur een email alert voor status changes.
    Retourneert True bij succes, False bij fout.
    """
    if not changes:
        print("📧 Geen changes om te rapporteren")
        return True
    
    if not SMTP_PASSWORD:
        print("⚠️ Geen SMTP wachtwoord ingesteld. Mail wordt niet verzonden.")
        print("   Stel in met: $env:SMTP_PASSWORD = 'jouw_wachtwoord'")
        return False
    
    # Filter changes op basis van ALERT_ON_CHANGES
    relevant_changes = []
    for change in changes:
        change_key = f"{change['old_status']}→{change['new_status']}"
        if change_key in ALERT_ON_CHANGES:
            relevant_changes.append(change)
    
    if not relevant_changes:
        print(f"📧 Geen relevante changes voor alerts: {[c['old_status']+'→'+c['new_status'] for c in changes]}")
        return True
    
    # Bouw email op
    subject = f"🚨 Baakie Alert: {len(relevant_changes)} space(s) offline/degraded"
    
    body = f"""
Baakie Space Monitor — Status Alert
{'=' * 50}

Tijdstip: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Aantal changes: {len(relevant_changes)}

{'═' * 50}
DETAILS PER SPACE
{'═' * 50}

"""
    
    for change in relevant_changes:
        body += f"""
Space: {change['space']}
Oude status: {change['old_status']}
Nieuwe status: {change['new_status']}
Tijd: {change['timestamp']}
{'-' * 30}
"""
    
    body += f"""
{'═' * 50}
Dashboard: http://localhost:5000
{'═' * 50}

Dit is een automatische melding van de Baakie Space Monitor.
"""
    
    # Verstuur email
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(ALERT_RECIPIENTS)
        msg["Subject"] = subject
        
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"📧 Alert verstuurd naar {len(ALERT_RECIPIENTS)} ontvanger(s)")
        return True
        
    except Exception as e:
        print(f"❌ Fout bij verzenden email: {e}")
        return False

def send_test_email() -> bool:
    """
    Stuur een test email om de configuratie te controleren.
    """
    print("📧 Test email verzenden...")
    
    if not SMTP_PASSWORD:
        print("⚠️ Geen SMTP wachtwoord ingesteld.")
        print("   Stel in met: $env:SMTP_PASSWORD = 'jouw_wachtwoord'")
        return False
    
    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER
        msg["To"] = ", ".join(ALERT_RECIPIENTS)
        msg["Subject"] = "✅ Baakie Monitor — Test alert"
        
        body = f"""
Baakie Space Monitor — Test

Dit is een testmelding.
Configuratie is correct.

Tijdstip: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Ontvanger: {ALERT_RECIPIENTS}
"""
        msg.attach(MIMEText(body, "plain"))
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        
        print("✅ Test email verzonden!")
        return True
        
    except Exception as e:
        print(f"❌ Fout bij test email: {e}")
        return False

if __name__ == "__main__":
    # Test de email configuratie
    send_test_email()
    