#!/usr/bin/env python3
"""
Baakie Space Monitor v3.0
Robuuste monitoring van alle 5 Baakie spaces in Perplexity.
Met fallback voor corrupte data, error handling, logging en self-improvement.
"""

import json
import os
import time
import requests
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Union

# ═══════════════════════════════════════════════════════════════
# CONFIGURATIE
# ═══════════════════════════════════════════════════════════════

# De 5 Baakie spaces die we monitoren
SPACES: Dict[str, str] = {
    "baakiedoc": "https://www.perplexity.ai/spaces/baakiedoc-prod",
    "baakiekwal": "https://www.perplexity.ai/spaces/baakiekwal-prod",
    "baakieprint": "https://www.perplexity.ai/spaces/baakieprint-prod",
    "baakiehtml": "https://www.perplexity.ai/spaces/baakiehtml-prod",
    "orchestrator": "https://www.perplexity.ai/spaces/baakie-orchestrator-prod",
}

# Bestandspaden
DATA_DIR = "data"
SPACES_FILE = f"{DATA_DIR}/spaces.json"
LOGS_FILE = f"{DATA_DIR}/logs.json"
HISTORY_FILE = f"{DATA_DIR}/history.json"
REPORT_FILE = f"{DATA_DIR}/self_improvement_report.md"

# Timeout in seconden
TIMEOUT = 10

# ═══════════════════════════════════════════════════════════════
# PERPLEXITY SESSIE TOKEN (optioneel, voor betere toegang)
# ═══════════════════════════════════════════════════════════════

PERPLEXITY_TOKEN = os.environ.get("PERPLEXITY_TOKEN", "")

def get_session() -> requests.Session:
    """Maak een sessie met Perplexity token als die beschikbaar is."""
    session = requests.Session()
    if PERPLEXITY_TOKEN:
        session.cookies.set("__Secure-next-auth.session-token", PERPLEXITY_TOKEN)
    return session

# ═══════════════════════════════════════════════════════════════
# FUNCTIES
# ═══════════════════════════════════════════════════════════════

def ensure_data_dir() -> None:
    """Zorg dat de data directory bestaat."""
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"📁 Data directory aangemaakt: {DATA_DIR}")


def check_space(url: str, name: str) -> Dict:
    """
    Check of een space online is.
    Retourneert status, response tijd en eventuele fouten.
    """
    try:
        start = time.time()
        
        # Browser-achtige headers om bot-blocking te omzeilen
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "nl-NL,nl;q=0.9,en;q=0.8",
        }
        
        # Gebruik sessie met token (als die er is)
        session = get_session()
        response = session.get(url, timeout=TIMEOUT, allow_redirects=True, headers=headers)
        elapsed = round((time.time() - start) * 1000, 1)  # ms

        # Debug: toon status code
        print(f"   {name}: status_code={response.status_code}")

        # 200-399 = online (redirects zoals 301, 302 zijn ook OK)
        if 200 <= response.status_code < 400:
            status = "online"
        elif 400 <= response.status_code < 500:
            status = "degraded"
        else:
            status = "offline"

        return {
            "name": name,
            "url": url,
            "status": status,
            "response_time": elapsed,
            "status_code": response.status_code,
            "last_checked": datetime.now().isoformat(),
            "error": None,
        }
    except requests.exceptions.Timeout:
        return {
            "name": name,
            "url": url,
            "status": "offline",
            "response_time": None,
            "status_code": None,
            "last_checked": datetime.now().isoformat(),
            "error": "Timeout after 10s",
        }
    except requests.exceptions.ConnectionError:
        return {
            "name": name,
            "url": url,
            "status": "offline",
            "response_time": None,
            "status_code": None,
            "last_checked": datetime.now().isoformat(),
            "error": "Connection refused",
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "status": "offline",
            "response_time": None,
            "status_code": None,
            "last_checked": datetime.now().isoformat(),
            "error": str(e),
        }


def load_json_safe(filepath: str) -> Union[Dict, List]:
    """
    Laad JSON bestand veilig.
    Retourneert dict of list, of lege dict bij fout.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"   ⚠️ Corrupt JSON in {filepath}, starten met lege data")
        return {}
    except Exception as e:
        print(f"   ⚠️ Fout bij laden {filepath}: {e}")
        return {}


def save_json_safe(filepath: str, data: Union[Dict, List]) -> bool:
    """
    Sla data veilig op als JSON.
    Retourneert True bij succes, False bij fout.
    """
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"   ❌ Fout bij opslaan {filepath}: {e}")
        return False


def normalize_to_dict(data: Union[Dict, List]) -> Dict:
    """
    Zet data om naar een dict als het een list is.
    """
    if isinstance(data, dict):
        return data
    
    if isinstance(data, list):
        # Als de list leeg is, retourneer lege dict
        if not data:
            return {}
        
        # Probeer items te converteren op basis van 'name' veld
        result = {}
        for i, item in enumerate(data):
            if isinstance(item, dict):
                # Gebruik 'name' als key als het bestaat
                name = item.get("name", f"space_{i}")
                result[name] = item
            else:
                result[f"space_{i}"] = item
        return result
    
    return {}


def detect_changes(current: Dict, previous: Union[Dict, List]) -> List[Dict]:
    """
    Vergelijk huidige status met vorige status.
    Kan zowel dict als list verwerken.
    """
    # Normaliseer previous naar dict
    prev_dict = normalize_to_dict(previous)
    
    changes = []
    for name, data in current.items():
        prev = prev_dict.get(name, {})
        old_status = prev.get("status", "unknown")
        new_status = data.get("status", "unknown")
        
        if old_status != new_status:
            changes.append({
                "space": name,
                "old_status": old_status,
                "new_status": new_status,
                "timestamp": datetime.now().isoformat(),
            })
    return changes


def log_changes(changes: List[Dict]) -> None:
    """Log status changes naar logs.json."""
    logs = load_json_safe(LOGS_FILE)
    
    # Zorg dat logs een dict is met een 'logs' lijst
    if not isinstance(logs, dict):
        logs = {"logs": []}
    if "logs" not in logs:
        logs["logs"] = []
    
    for change in changes:
        log_entry = {
            "timestamp": change["timestamp"],
            "space": change["space"],
            "old_status": change["old_status"],
            "new_status": change["new_status"],
            "message": f"Space {change['space']} went from {change['old_status']} to {change['new_status']}"
        }
        logs["logs"].append(log_entry)
    
    # Houd maximaal 500 logs
    if len(logs["logs"]) > 500:
        logs["logs"] = logs["logs"][-500:]
    
    save_json_safe(LOGS_FILE, logs)


def save_history(current: Dict) -> None:
    """Voeg huidige status toe aan historie voor trend analyse."""
    history = load_json_safe(HISTORY_FILE)
    
    # Zorg dat history een dict is met een 'history' lijst
    if not isinstance(history, dict):
        history = {"history": []}
    if "history" not in history:
        history["history"] = []
    
    # Voeg huidige snapshot toe
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "spaces": current
    }
    history["history"].append(snapshot)
    
    # Houd maximaal 1000 snapshots (bij 60s interval = ~16 uur)
    if len(history["history"]) > 1000:
        history["history"] = history["history"][-1000:]
    
    save_json_safe(HISTORY_FILE, history)


def print_status(data: Dict) -> None:
    """Print status op een mooie manier."""
    print("\n" + "═" * 50)
    print("📊 BAAKIE SPACE STATUS")
    print("═" * 50)
    print(f"🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("═" * 50)
    
    for name, info in data.items():
        status = info.get("status", "unknown")
        response_time = info.get("response_time")
        error = info.get("error")
        status_code = info.get("status_code")
        
        # Status icon
        if status == "online":
            icon = "🟢"
        elif status == "degraded":
            icon = "🟡"
        else:
            icon = "🔴"
        
        print(f"\n{icon} {name.upper()}")
        print(f"   Status: {status}")
        if status_code:
            print(f"   Status Code: {status_code}")
        if response_time:
            print(f"   Response: {response_time}ms")
        if error:
            print(f"   Error: {error}")
    
    # Samenvatting
    print("\n" + "═" * 50)
    summary = {"online": 0, "degraded": 0, "offline": 0}
    for info in data.values():
        status = info.get("status", "unknown")
        if status in summary:
            summary[status] += 1
    
    print(f"🟢 Online: {summary['online']}")
    print(f"🟡 Degraded: {summary['degraded']}")
    print(f"🔴 Offline: {summary['offline']}")
    print("═" * 50 + "\n")


def run_self_improvement_analysis() -> None:
    """Draai de self-improvement analyse als er data is."""
    try:
        # Check of er voldoende data is
        history = load_json_safe(HISTORY_FILE)
        if not history or len(history.get("history", [])) < 3:
            print("   ⏳ Not enough data for self-improvement analysis (min 3 snapshots)")
            return
        
        print("\n🧠 Running self-improvement analysis...")
        result = subprocess.run(
            ["C:\\Python314\\python.exe", "analyze.py"],
            capture_output=True,
            text=True,
            cwd=os.getcwd()
        )
        if result.returncode == 0:
            print("✅ Self-improvement analysis complete!")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"⚠️ Self-improvement analysis failed: {result.stderr}")
    except Exception as e:
        print(f"⚠️ Could not run self-improvement analysis: {e}")


# ═══════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════

def main():
    print("\n🔍 BAAKIE SPACE MONITOR v3.0")
    print("═" * 50)
    print(f"Monitored spaces: {len(SPACES)}")
    if PERPLEXITY_TOKEN:
        print("🔑 Sessie token: ✅ gevonden")
    else:
        print("🔑 Sessie token: ❌ niet gevonden (gebruikt fallback)")
    print("═" * 50)
    
    # Zorg dat data directory bestaat
    ensure_data_dir()
    
    # Check alle spaces
    results = {}
    for name, url in SPACES.items():
        print(f"   Checking {name}...")
        results[name] = check_space(url, name)
    
    # Laad vorige status (kan dict of list zijn)
    previous = load_json_safe(SPACES_FILE)
    
    # Detecteer veranderingen
    changes = detect_changes(results, previous)
    if changes:
        print(f"\n🔄 Status changes detected: {len(changes)}")
        for change in changes:
            print(f"   {change['space']}: {change['old_status']} → {change['new_status']}")
        log_changes(changes)
        
        # Draai self-improvement analyse bij status changes
        run_self_improvement_analysis()
    else:
        print("\n✅ No status changes detected")
    
    # Sla huidige status op
    save_json_safe(SPACES_FILE, results)
    
    # Sla historie op voor trends
    save_history(results)
    
    # Print status
    print_status(results)
    
    print("✅ Monitoring complete!")


if __name__ == "__main__":
    main()