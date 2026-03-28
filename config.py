import os
import re

def get_secret(key):
    try:
        with open(".streamlit/secrets.toml", "r", encoding="utf-8") as f:
            content = f.read()
            # Support both double quotes and single quotes
            match = re.search(rf'{key}\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except:
        pass
    return os.getenv(key, "")
