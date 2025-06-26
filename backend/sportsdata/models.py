from django.db import models

class Team(models.Model):
    espn_id = models.CharField(max_length=20, unique=True)
    team_key = models.CharField(max_length=100, unique=True)
    league = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    aliases = models.JSONField(default=list)

    def __str__(self):
        return f'{self.league.upper()} - {self.name}'


class Player(models.Model):
    espn_id = models.CharField(max_length=20, unique=True)
    player_key = models.CharField(max_length=100)
    league = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    position = models.CharField(max_length=10, null=True, blank=True)
    collected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Event(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'

    espn_id = models.CharField(max_length=20, unique=True)
    event_key = models.CharField(max_length=100, unique=True)
    league = models.CharField(max_length=20)
    away_team = models.ForeignKey(Team, related_name='away_events', on_delete=models.CASCADE)
    home_team = models.ForeignKey(Team, related_name='home_events', on_delete=models.CASCADE)

    start_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UPCOMING)

    collected_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.league.upper()} - {self.away_team} @ {self.home_team} ({self.start_time})'