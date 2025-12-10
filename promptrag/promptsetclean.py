import re
with open("promptset.csv", "r") as f:
    data = f.read()

data = re.sub(r"sk-[A-Za-z0-9]{24,}", "<REDACTED>", data)  # OpenAI keys
data = re.sub(r"AIza[0-9A-Za-z-_]{35}", "<REDACTED>", data)  # Google API keys

with open("promptset_safe.csv", "w") as f:
    f.write(data)
