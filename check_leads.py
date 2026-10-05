import os
from datetime import date

import requests

SHEET_ID = "1-ZLZsp5yF4oan04zxoWvgguz_IumUFK1bRauHJLmEog"
BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]

SHEETS = ["DE/FR/NL", "Europe"]

# Column indices (0-based)
COL_DATE = 0
COL_NAME = 1
COL_COUNTRY = 2
COL_TYPE = 3
COL_ACQUIRED = 5
COL_STATUS = 10

BASE_URL = "https://sheets.googleapis.com/v4/spreadsheets"


def fetch_sheet(sheet_name: str) -> list[list[str]]:
    url = f"{BASE_URL}/{SHEET_ID}/values/{sheet_name!r}!A:K"
    r = requests.get(url, params={"key": GOOGLE_API_KEY}, timeout=30)
    r.raise_for_status()
    return r.json().get("values", [])


def get_today_leads(rows: list[list[str]]) -> list[list[str]]:
    today = date.today().strftime("%d/%m")
    leads = []
    for row in rows[1:]:  # skip header
        if row and row[COL_DATE].strip() == today:
            leads.append(row)
    return leads


def format_lead(row: list[str]) -> str:
    def col(i: int) -> str:
        return row[i].strip() if len(row) > i else ""

    parts = [p for p in [col(COL_NAME), col(COL_COUNTRY), col(COL_TYPE), col(COL_ACQUIRED)] if p]
    line = " | ".join(parts)
    status = col(COL_STATUS)
    if status:
        line += f"\n  _{status}_"
    return line


def send_telegram(text: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    r = requests.post(
        url,
        json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"},
        timeout=30,
    )
    r.raise_for_status()


def main() -> None:
    today_str = date.today().strftime("%d/%m/%Y")
    results: dict[str, list[list[str]]] = {}
    total = 0

    for sheet in SHEETS:
        rows = fetch_sheet(sheet)
        leads = get_today_leads(rows)
        results[sheet] = leads
        total += len(leads)

    lines = [f"*Daily Lead Report — {today_str}*\n"]

    for sheet, leads in results.items():
        count = len(leads)
        noun = "lead" if count == 1 else "leads"
        lines.append(f"*{sheet}* ({count} new {noun})")
        if leads:
            for lead in leads:
                lines.append(f"• {format_lead(lead)}")
        else:
            lines.append("  No new leads today.")
        lines.append("")

    noun = "lead" if total == 1 else "leads"
    lines.append(f"*Total: {total} new {noun} today*")

    send_telegram("\n".join(lines))
    print(f"Done. {total} leads found today.")


if __name__ == "__main__":
    main()
