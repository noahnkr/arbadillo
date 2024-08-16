from django.db import models

class Event(models.Model):
	id = models.CharField(primary_key=True)
	league = models.CharField()
	away_team = models.CharField(max_length=100)
	home_team = models.CharField(max_length=100)
	start_time = models.DateTimeField()
	active = models.BooleanField(default=True)

class Sportsbook(models.Model):
	event = models.ForeignKey(Event, related_name='sportsbooks', on_delete=models.CASCADE)
	title = models.CharField(max_length=100)
	last_updated = models.DateTimeField(auto_now_add=True)

class Pick(models.Model):
	sportsbook = models.ForeignKey(Sportsbook, related_name='picks', on_delete=models.CASCADE)
	market = models.CharField(null=False)
	team = models.CharField(max_length=100, null=True, blank=True)
	line = models.FloatField(null=True, blank=True)
	odds = models.IntegerField(null=False)
	player = models.CharField(max_length=100, null=True, blank=True)
	outcome = models.CharField(max_length=100, null=True, blank=True)