"""Production entry point — replaces gunicorn to avoid arbiter+eventlet crash.

flask-socketio's socketio.run() uses eventlet.wsgi directly (no gunicorn
arbiter), so there is no master-process signal handler conflict.
"""
import os
import logging
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stderr,
)

from app import app, socketio

port = int(os.environ.get("PORT", 5000))
socketio.run(
    app,
    host="0.0.0.0",
    port=port,
    debug=False,
    use_reloader=False,
    log_output=True,
)
