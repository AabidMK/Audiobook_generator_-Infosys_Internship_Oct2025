import os

path = r"C:\Users\hp\Desktop\SM\infy internship\text_enrichment\input\input.txt"

print("File path:", path)
print("Exists?", os.path.exists(path))

if os.path.exists(path):
    with open(path, "r", encoding="utf-8") as f:
        print("✅ File content preview:")
        print(f.read()[:300])
else:
    print("❌ File not found!")
