# Arbadillo TODOs

## Infrastructure

-   [x] Fix Celery task logging
-   [x] Seperate Celery queues for scraping and database operations
-   [x] Converet Redis HSET -> SET and add TTL
-   [x] Fix run_periodic_scrape chaining

## Scraping

-   [x] Incorporate player odds into API client parsing
-   [x] Normalize missed player prop market names
-   [ ] Convert yes/no props -> over/under 0.5
-   [ ] Add status indicator to odds if they got locked

## Database

-   [x] Batch insert event and odds

## API

## Testing

## Frontend
