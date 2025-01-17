"""Celery worker configuration."""

import socket

# Broker settings
broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/1'

# Basic settings
broker_connection_retry = True
broker_connection_max_retries = None

# Task settings
task_serializer = 'json'
accept_content = ['json']
result_serializer = 'json'
timezone = 'UTC'
enable_utc = True

# Task execution settings
task_track_started = True
task_time_limit = 300  # 5 minutes
task_soft_time_limit = 240  # 4 minutes
task_acks_late = True
worker_prefetch_multiplier = 1
task_always_eager = False
task_eager_propagates = True
task_default_retry_delay = 5  # 5 seconds between retries
task_max_retries = 3  # Maximum of 3 retries

# Enhanced broker settings
broker_connection_retry = True
broker_connection_retry_on_startup = True
broker_connection_max_retries = None  # Retry indefinitely
broker_connection_timeout = 30  # 30 second connection timeout
broker_heartbeat = 10  # Heartbeat every 10 seconds
broker_pool_limit = 10  # Limit connection pool to prevent resource exhaustion
broker_transport_options = {
    'visibility_timeout': 43200,  # 12 hours
    'socket_timeout': 30,  # 30 seconds
    'socket_connect_timeout': 30,  # 30 seconds
    'socket_keepalive': True,
    'socket_keepalive_options': {
        socket.SOL_SOCKET: socket.SO_KEEPALIVE
    }
}

# Enhanced result backend settings
result_backend_transport_options = {
    'retry_policy': {
        'timeout': 30.0,  # 30 second timeout
        'max_retries': None,  # Retry indefinitely
        'interval_start': 0,  # Start retrying immediately
        'interval_step': 1,  # Increase retry interval by 1 second
        'interval_max': 30,  # Maximum 30 seconds between retries
    }
}

# Worker settings
worker_lost_wait = 30.0  # Wait 30 seconds for lost workers
worker_max_tasks_per_child = 1000  # Restart worker after 1000 tasks
worker_max_memory_per_child = 350000  # 350MB memory limit
worker_disable_rate_limits = True  # Disable rate limits
worker_send_task_events = True  # Enable task events

# Logging settings
worker_redirect_stdouts = False  # Don't redirect stdout/stderr
worker_redirect_stdouts_level = 'INFO'  # Log level for stdout/stderr

# Pool settings
worker_pool = 'solo'  # Use solo pool for better compatibility
worker_concurrency = 1  # Single worker for predictable behavior

# State settings
worker_state_db = None  # Don't persist worker state
