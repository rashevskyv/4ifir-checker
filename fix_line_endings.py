import os

# Read the file
with open('setup.sh', 'rb') as f:
    content = f.read()

# Replace CRLF with LF
new_content = content.replace(b'\r\n', b'\n')

# Write back
with open('setup.sh', 'wb') as f:
    f.write(new_content)

print("Converted setup.sh to LF line endings.")
