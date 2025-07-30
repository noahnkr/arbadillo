from django.db import models

class Selection(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'

    sportsbook = models.CharField(max_length=50)
    league = models.CharField(max_length=20)
    event = models.CharField(max_length=100)
    event_key = models.CharField(max_length=100)
    market_key = models.CharField(max_length=100)
    market = models.CharField(max_length=50)
    outcome = models.CharField(max_length=100)
    value = models.FloatField()
    line = models.FloatField(null=True, blank=True)
    team = models.CharField(max_length=100, null=True, blank=True)
    player = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    collected_at = models.DateTimeField()
 
    class Meta:
        unique_together = ('sportsbook', 'league', 'event_key', 'market_key', 'outcome')