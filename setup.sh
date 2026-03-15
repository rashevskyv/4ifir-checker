#!/bin/bash

# Exit on error
set -e

echo "==================================================="
echo "  4IFIR-checker Installation Script (Linux)"
echo "==================================================="
echo ""

# 1. Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed."
    echo "Please install Python 3 (e.g., sudo apt install python3 python3-venv)"
    exit 1
fi

# 2. Create virtual environment
echo "[1/4] Creating virtual environment (venv)..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to create virtual environment."
        exit 1
    fi
fi

# 3. Install dependencies
echo "[2/4] Installing dependencies from requirements.txt..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies."
    exit 1
fi

# 4. Verify setup
echo "[3/4] Verifying installation..."
python3 verify_setup.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Verification failed. Please check the logs above."
    exit 1
fi

# 5. Start the application (checker.py)
echo "[4/4] Starting the application (checker.py)..."
echo ""
# We use || true so the script doesn't exit if checker.py returns non-zero, 
# because we want to show the final status message.
python3 checker.py || RUN_STATUS=$?

RUN_STATUS=${RUN_STATUS:-0}

# 6. Show final status
echo ""
echo "==================================================="
if [ $RUN_STATUS -eq 0 ]; then
    echo "[OK] Installation and initial run successful!"
    echo "Everything is working correctly."
else
    echo "[WARNING] Application finished with exit code $RUN_STATUS."
    echo "This might be due to missing environment variables or network issues."
    echo "Please check the output above."
fi
echo "==================================================="
echo ""

# Create a quick launch script
cat <<EOF > run.sh
#!/bin/bash
source venv/bin/activate
python3 checker.py "\$@"
EOF

chmod +x run.sh

echo "Created 'run.sh' for future launches."
echo ""
