from django.db import models

from sportsdata.models import Event

class Odds(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='odds')
    event_key = models.CharField(max_length=100)
    market_key = models.CharField(max_length=100)
    sportsbook = models.CharField(max_length=50)
    market = models.CharField(max_length=50)
    outcome = models.CharField(max_length=100)
    line = models.FloatField(null=True, blank=True)
    value = models.FloatField()
    team = models.CharField(max_length=100, null=True, blank=True)
    player = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    collected_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        unique_together = ('event_key', 'market_key', 'sportsbook', 'outcome')