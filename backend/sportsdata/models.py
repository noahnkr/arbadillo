from django.db import models

class Event(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'

    event_key = models.CharField(max_length=255, unique=True)
    league = models.CharField(max_length=50)
    start_time = models.DateTimeField()
    away = models.CharField(max_length=100)
    home = models.CharField(max_length=100)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UPCOMING)
    collected_at = models.DateTimeField(auto_now_add=True)