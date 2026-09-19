"""
Production Gunicorn Configuration for YouTube Integratsiya Backend.
"""
import multiprocessing
import os

bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
threads = int(os.getenv("GUNICORN_THREADS", 2))
worker_class = "gthread"
timeout = int(os.getenv("GUNICORN_TIMEOUT", 60))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", 5))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Process naming
proc_name = "youtube_integratsiya_backend"
