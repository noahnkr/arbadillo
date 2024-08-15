class ScraperError(Exception):
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
