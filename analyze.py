#!/usr/bin/env python3
"""
Self-Improvement Engine voor Baakie Space Monitor
Analyseert trends en genereert verbetervoorstellen.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════
# CONFIGURATIE
# ═══════════════════════════════════════════════════════════════

DATA_DIR = "data"
HISTORY_FILE = f"{DATA_DIR}/history.json"
REPORT_FILE = f"{DATA_DIR}/self_improvement_report.md"

# Aantal dagen om te analyseren
ANALYSIS_DAYS = 7

# Drempelwaarden voor alerts
RESPONSE_TIME_THRESHOLD = 500  # ms
STATUS_CHANGE_THRESHOLD = 3    # aantal changes per dag

# ═══════════════════════════════════════════════════════════════
# FUNCTIES
# ═══════════════════════════════════════════════════════════════

def load_history() -> Dict:
    """Laad historische data."""
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"history": []}

def calculate_response_time_trend(history: List[Dict], space_name: str) -> Dict:
    """
    Bereken de trend in response tijd voor een specifieke space.
    Retourneert: {trend: "up"/"down"/"stable", avg: float, change: float}
    """
    response_times = []
    for entry in history:
        spaces = entry.get("spaces", {})
        if space_name in spaces:
            rt = spaces[space_name].get("response_time")
            if rt is not None:
                response_times.append(rt)
    
    if len(response_times) < 3:
        return {"trend": "insufficient_data", "avg": None, "change": None}
    
    # Neem laatste 10 metingen
    recent = response_times[-10:]
    avg = sum(recent) / len(recent)
    
    # Vergelijk eerste helft met tweede helft
    half = len(recent) // 2
    first_half = recent[:half]
    second_half = recent[half:]
    avg_first = sum(first_half) / len(first_half) if first_half else avg
    avg_second = sum(second_half) / len(second_half) if second_half else avg
    
    change = avg_second - avg_first
    if change > 20:
        trend = "up"  # word trager
    elif change < -20:
        trend = "down"  # word sneller
    else:
        trend = "stable"
    
    return {"trend": trend, "avg": avg, "change": change}

def calculate_status_changes(history: List[Dict], space_name: str) -> int:
    """Bereken het aantal status changes voor een space."""
    changes = 0
    last_status = None
    
    for entry in history:
        spaces = entry.get("spaces", {})
        if space_name in spaces:
            status = spaces[space_name].get("status")
            if last_status is not None and status != last_status:
                changes += 1
            last_status = status
    
    return changes

def detect_patterns(history: List[Dict]) -> List[str]:
    """
    Detecteer patronen in de data.
    Retourneert een lijst van bevindingen.
    """
    patterns = []
    
    # Check of er een ruimte is die vaak offline is
    space_status_counts = defaultdict(lambda: {"online": 0, "degraded": 0, "offline": 0})
    for entry in history:
        spaces = entry.get("spaces", {})
        for name, data in spaces.items():
            status = data.get("status", "unknown")
            if status in space_status_counts[name]:
                space_status_counts[name][status] += 1
    
    for name, counts in space_status_counts.items():
        total = sum(counts.values())
        if total > 0:
            offline_pct = (counts["offline"] / total) * 100
            if offline_pct > 5:
                patterns.append(f"⚠️ {name} is {offline_pct:.1f}% offline in de afgelopen periode")
    
    return patterns

def generate_recommendations(history: List[Dict], space_name: str, trend_data: Dict) -> List[str]:
    """Genereer verbetervoorstellen op basis van data."""
    recommendations = []
    
    # Check response time trend
    if trend_data["trend"] == "up" and trend_data["avg"] and trend_data["avg"] > RESPONSE_TIME_THRESHOLD:
        recommendations.append(
            f"📈 Response time van {space_name} neemt toe (gemiddeld {trend_data['avg']:.1f}ms). "
            f"Overweeg om de space te optimaliseren."
        )
    
    # Check status changes
    changes = calculate_status_changes(history, space_name)
    if changes > STATUS_CHANGE_THRESHOLD:
        recommendations.append(
            f"🔄 {space_name} heeft {changes} status changes in de afgelopen periode. "
            f"Dit kan duiden op instabiliteit."
        )
    
    return recommendations

def generate_report(history: List[Dict], space_names: List[str]) -> str:
    """Genereer een self-improvement rapport in Markdown."""
    lines = []
    lines.append(f"# 📊 Self-Improvement Report")
    lines.append(f"**Datum:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**Analyse periode:** Laatste {ANALYSIS_DAYS} dagen")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    all_recommendations = []
    all_patterns = []
    
    for space in space_names:
        lines.append(f"## 🔍 {space.upper()}")
        
        # Bereken trends
        trend = calculate_response_time_trend(history, space)
        changes = calculate_status_changes(history, space)
        
        # Status icoon
        if trend["trend"] == "up":
            trend_icon = "🟡"
            trend_text = "wordt trager"
        elif trend["trend"] == "down":
            trend_icon = "🟢"
            trend_text = "wordt sneller"
        else:
            trend_icon = "⚪"
            trend_text = "stabiel"
        
        lines.append(f"- **Response tijd:** {trend_icon} {trend_text} (gem. {trend['avg']:.1f}ms)")
        lines.append(f"- **Status changes:** {changes} in de afgelopen periode")
        lines.append("")
        
        # Genereer recommendations
        recs = generate_recommendations(history, space, trend)
        if recs:
            lines.append("**💡 Advies:**")
            for rec in recs:
                lines.append(f"- {rec}")
                all_recommendations.append(rec)
        else:
            lines.append("✅ Geen advies nodig — deze space draait goed.")
        
        lines.append("")
    
    # Patronen
    patterns = detect_patterns(history)
    if patterns:
        lines.append("## 📈 Gedetecteerde patronen")
        for pattern in patterns:
            lines.append(f"- {pattern}")
        all_patterns.extend(patterns)
    else:
        lines.append("## 📈 Gedetecteerde patronen")
        lines.append("✅ Geen opvallende patronen gevonden.")
    
    # Samenvatting
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 📋 Samenvatting")
    lines.append("")
    if all_recommendations:
        lines.append(f"**Aantal adviezen:** {len(all_recommendations)}")
    if all_patterns:
        lines.append(f"**Aantal patronen:** {len(all_patterns)}")
    
    lines.append("")
    lines.append("*Dit rapport wordt automatisch gegenereerd door de Self-Improvement Engine.*")
    
    return "\n".join(lines)

def save_report(content: str) -> None:
    """Sla het rapport op als Markdown bestand."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"📄 Rapport opgeslagen: {REPORT_FILE}")

def main():
    print("\n🧠 SELF-IMPROVEMENT ENGINE")
    print("═" * 50)
    
    # Laad historische data
    data = load_history()
    history = data.get("history", [])
    
    if len(history) < 3:
        print("⚠️ Niet genoeg data voor analyse. Minimaal 3 metingen nodig.")
        print(f"   Huidig aantal metingen: {len(history)}")
        return
    
    print(f"📊 Aantal metingen: {len(history)}")
    print(f"📅 Eerste meting: {history[0]['timestamp']}")
    print(f"📅 Laatste meting: {history[-1]['timestamp']}")
    print("")
    
    # Bepaal welke spaces er zijn
    space_names = set()
    for entry in history:
        space_names.update(entry.get("spaces", {}).keys())
    
    print(f"🛰️  Gevonden spaces: {', '.join(sorted(space_names))}")
    print("")
    
    # Genereer rapport
    report = generate_report(history, sorted(space_names))
    save_report(report)
    
    print("")
    print("✅ Self-Improvement analyse voltooid!")

if __name__ == "__main__":
    main()