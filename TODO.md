# Arbadillo TODOs

## Infrastructure

-   [x] Fix Celery task logging
-   [x] Seperate Celery queues for scraping and database operations
-   [x] Converet Redis HSET -> SET and add TTL
-   [x] Fix run_periodic_scrape chaining

## Scraping

-   [x] Incorporate player odds into API client parsing
-   [x] Normalize missed player prop market names
-   [x] Convert yes/no props -> over/under 0.5
-   [x] Add status indicator to odds if they got locked
-   [x] Implement ESPNBet scraping from TheScore's API
-   [ ] Figure out how to fetch data from BetMGM while in headless mode
-   [x] Set collected_at value to scraping time, not database insertion time
-   [x] Data classes for Event, Player, Team, and Odds
-   [ ] Better handling for alternate totals and spreads

## Database

-   [x] Batch insert event and odds

## API

## Testing

-   [x] Test FanDuel prop scraping
-   [x] Test DraftKings prop scraping
-   [x] Test ESPNBet prop scraping
-   [ ] Add execution times for Celery tasks

## Frontend
