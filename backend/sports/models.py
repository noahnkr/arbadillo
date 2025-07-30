from django.db import models

class Event(models.Model):
    class Status(models.TextChoices):
        UPCOMING = 'upcoming', 'Upcoming'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'

    espn_id = models.CharField(max_length=20, unique=True)
    league = models.CharField(max_length=20)
    event_key = models.CharField(max_length=100, unique=True)
    away_team = models.CharField(max_length=100)
    home_team = models.CharField(max_length=100)
    start_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.UPCOMING)
    collected_at = models.DateTimeField(auto_now_add=True)


class EventResult(models.Model):
    league = models.CharField(max_length=50)
    event_key = models.CharField(max_length=100, unique=True)
    home_score = models.IntegerField()
    away_score = models.IntegerField()
    margin_of_victory = models.IntegerField()
    winner = models.CharField(max_length=100)
    collected_at = models.DateTimeField(auto_now_add=True)


class Team(models.Model):
    espn_id = models.CharField(max_length=20, unique=True)
    league = models.CharField(max_length=20)
    team_key = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)


class Player(models.Model):
    espn_id = models.CharField(max_length=20, unique=True)
    league = models.CharField(max_length=20)
    player_key = models.CharField(max_length=100, unique=True)
    team_key = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, null=True, blank=True)


class TeamStat(models.Model):
    league = models.CharField(max_length=50)
    event_key = models.CharField(max_length=100)
    team_key = models.CharField(max_length=100)
    stat_name = models.CharField(max_length=100)
    value = models.FloatField()

    class Meta:
        unique_together = ('league', 'event_key', 'team_key', 'stat_name')


class PlayerStat(models.Model):
    league = models.CharField(max_length=50)
    event_key = models.CharField(max_length=100)
    player_key = models.CharField(max_length=100)
    stat_name = models.CharField(max_length=100)
    value = models.FloatField()

    class Meta:
        unique_together = ('league', 'event_key', 'player_key', 'stat_name')