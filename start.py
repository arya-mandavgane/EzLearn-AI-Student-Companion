import os
import sys

# Ensure backend directory is in sys.path and is current working directory
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
if os.path.isdir(backend_dir):
    sys.path.insert(0, backend_dir)
    os.chdir(backend_dir)
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting EzLearn backend server on 0.0.0.0:{port}...", flush=True)
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
