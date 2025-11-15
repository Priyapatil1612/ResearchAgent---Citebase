# Gunicorn configuration file for production

# Number of worker processes
workers = 4

# Use Uvicorn's worker class for ASGI applications
worker_class = "uvicorn.workers.UvicornWorker"

# The socket to bind
bind = "0.0.0.0:10000"

# Timeout for worker processes
timeout = 120

# The number of seconds to wait for requests on a Keep-Alive connection
keepalive = 5

# Number of threads per worker
threads = 4

# Maximum number of requests a worker will process before restarting
max_requests = 5000
max_requests_jitter = 500

# Logging configuration
loglevel = "info"
errorlog = "-"  # Log to stdout
accesslog = "-"  # Log to stdout

# Preload the application before forking worker processes
preload_app = True