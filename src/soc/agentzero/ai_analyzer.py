import os
import json
from pathlib import Path
from openai import OpenAI

MODEL = "gpt-5.2"  # you can change to mini later if needed

def analyze_incident(incident_key: str):
    root = Path(__file__).resolve().parents[3]
    inbox_path = root / "data" / "ai" / "inbox" / f"{incident_key}.json"
    outbox_path = root / "data" / "ai" / "outbox" / f"{incident_key}.report.json"

    if not inbox_path.exists():
        raise FileNotFoundError(f"Incident file not found: {inbox_path}")

    incident_data = json.loads(inbox_path.read_text(encoding="utf-8"))

    system_prompt = """
You are a professional SOC (Security Operations Center) analyst.
Analyze the provided incident JSON.
Return ONLY a valid JSON object with these fields:
executive_summary,
technical_summary,
timeline (array of {time, event}),
triage_checklist (array of strings),
containment_recommendations (array of strings),
remediation_recommendations (array of strings),
assumptions (array of strings),
confidence (one of: low, medium, high)

Do not include markdown.
Do not include explanations outside JSON.
If something is unknown, state assumptions clearly.
"""

    client = OpenAI()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(incident_data)}
        ],
        temperature=0.2
    )

    content = response.choices[0].message.content

    # Validate JSON
    report_json = json.loads(content)

    outbox_path.write_text(json.dumps(report_json, indent=2), encoding="utf-8")

    print(f"✅ AI report saved to {outbox_path}")

if __name__ == "__main__":
    analyze_incident("INC-2026-000001")