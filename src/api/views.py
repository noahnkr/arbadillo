from django.http import JsonResponse
from .models import Event

async def event_list(request):
	events = Event.objects.all()
	data = [
		{
			'event_id': event.id,
			'away_team': event.away_team,
			'home_team': event.home_team,
			'start_time': event.start_time,
			'active': event.active,
			'sportsbooks': [
				{
					'title': sportsbook.title,
					'last_update': sportsbook.last_update,
					'picks': [
						{
							'market': pick.market,
							'team': pick.team,
							'line': pick.line,
							'odds': pick.odds,
							'player': pick.player,
							'outcome': pick.outcome,
						}
						for pick in sportsbook.picks.all()
					],
				}
				for sportsbook in event.sportsbooks.all()
			],
		}
		for event in events
	]
	return JsonResponse(data, safe=False)