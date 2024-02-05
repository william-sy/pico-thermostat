import json
SETTING_FILE = "./settings.json"
with open(SETTING_FILE, "r") as f:
    settings = json.load(f)
    f.close()

for key, value in settings.items():
    print(key, value)