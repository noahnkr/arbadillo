from django.db import models

class Event(models.Model):
    event_key = models.CharField(max_length=255, unique=True)
    league = models.CharField(max_length=50)
    start_time = models.DateTimeField()
    away = models.CharField(max_length=100)
    home = models.CharField(max_length=100)
    status = models.CharField(max_length=20)
    collected_at = models.DateTimeField(auto_now_add=True)


class Odds(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='odds')
    event_key = models.CharField(max_length=100)
    market_key = models.CharField(max_length=100)
    sportsbook = models.CharField(max_length=50)
    market = models.CharField(max_length=50)
    outcome = models.CharField(max_length=100)
    line = models.FloatField(null=True, blank=True)
    value = models.FloatField()
    player = models.CharField(max_length=100, null=True, blank=True)
    prop = models.CharField(max_length=100, null=True, blank=True)
    collected_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('event_key', 'market_key', 'sportsbook', 'outcome')