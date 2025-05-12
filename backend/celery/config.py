import os

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

broker_url = REDIS_URL
result_backend = REDIS_URL

task_serializer = 'json'
accept_content = ['json']

timezone = "UTC"
enable_utc = True

task_track_started = True
task_time_limit = 30 * 60
task_soft_time_limit = 25 * 60

worker_max_tasks_per_child = 100
worker_concurrency = 4

imports = (
    'tasks.event_tasks',
    'tasks.odds_tasks',
    'tasks.dispatch_tasks',
    'tasks.cleanup_tasks',
)
