# Invalid input exception.
class InputError(Exception):
	pass

# Exceptions that happen during webscraping
class ScraperError(Exception):
	pass

class EventLengthMismatchError(ScraperError):
	pass

class LeagueNotFoundError(ScraperError):
	pass

class EventNotFoundError(ScraperError):
	pass

class BlockError(ScraperError):
	pass

class BlockNotFoundError(BlockError):
	pass

class UnsupportedBlockType(BlockError):
	pass

class UnsupportedBlockMarket(BlockError):
	pass