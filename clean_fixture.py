import json
import os
import shutil
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
INPUT = os.path.join(HERE, "full_backup.json")
OUTPUT = os.path.join(HERE, "full_backup_cleaned.json")
BACKUP = os.path.join(HERE, f"full_backup.json.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}")

if not os.path.exists(INPUT):
    print("Error: full_backup.json not found in:", HERE)
    raise SystemExit(2)

# Backup original
shutil.copy2(INPUT, BACKUP)
print("Backup written to:", BACKUP)

with open(INPUT, "r", encoding="utf-8") as f:
    try:
        data = json.load(f)
    except json.JSONDecodeError as exc:
        print("JSON decode error:", exc)
        raise

if not isinstance(data, list):
    print("Unexpected fixture format: top-level JSON value is not a list.")
    raise SystemExit(3)

cleaned = []
removed = 0
KEEP_MODELS = {"myapp.product", "myapp.orderdetail", "auth.user"}
for i, obj in enumerate(data, start=1):
    if isinstance(obj, dict) and "model" in obj:
        if obj.get("model") in KEEP_MODELS:
            cleaned.append(obj)
        else:
            removed += 1
    else:
        removed += 1

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(cleaned, f, indent=2)

print(f"Total objects in original: {len(data)}")
print(f"Objects kept (have 'model'): {len(cleaned)}")
print(f"Objects removed (missing 'model'): {removed}")
print("Cleaned fixture written to:", OUTPUT)
print("Now run: python manage.py loaddata full_backup_cleaned.json (from your project/manage.py directory)")