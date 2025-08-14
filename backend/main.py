import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.server:app",
        host="localhost",
        port=8000,
        loop="uvloop" if os.name == "posix" else "asyncio",
    )

 