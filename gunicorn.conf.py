# gunicorn.conf.py — kept as fallback reference; production now uses run.py
bind = "0.0.0.0:10000"
worker_class = "eventlet"
workers = 1
timeout = 180