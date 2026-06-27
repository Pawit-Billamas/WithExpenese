import sys
import os

# Add the project directory to the sys.path
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path:
    sys.path.append(path)

from app.main import app
```python
# We wrap the FastAPI app to make it WSGI compatible for PythonAnywhere
from fastapi.wsgi import WSGIMiddleware

# Use the WSGI middleware to wrap the FastAPI app
application = WSGIMiddleware(app)
```
