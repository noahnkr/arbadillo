# Invalid input exception.
class InputError(Exception):
	pass

# Exceptions that happen during webscraping
class ScraperError(Exception):
	pass

class LeagueNotFoundError(ScraperError):
	pass

class EventNotFoundError(ScraperError):
	pass

class BlockNotFoundError(ScraperError):
	pass