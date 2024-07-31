class ScraperError(Exception):
	pass

class LeagueNotFoundError(ScraperError):
	pass

class EventNotFoundError(ScraperError):
	pass

class BlockNotFoundError(ScraperError):
	pass