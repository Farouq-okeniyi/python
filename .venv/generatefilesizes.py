import os

def generate_text_file(filename, size_kb):
    size_bytes = size_kb * 1024
    line = "This is a sample line of text to fill the file.\n"
    with open(filename, "w") as f:
        while f.tell() < size_bytes:
            f.write(line)

# Sizes in KB
sizes = {
    "100KB.txt": 100,
    "500KB.txt": 500,
    "1MB.txt": 1024,
    "2MB.txt": 2 * 1024,
    "3MB.txt": 3 * 1024,
    "4MB.txt": 4 * 1024,
    "5MB.txt": 5 * 1024,
}

for filename, size_kb in sizes.items():
    generate_text_file(filename, size_kb)
    print(f"{filename} generated with size {os.path.getsize(filename)} bytes")
