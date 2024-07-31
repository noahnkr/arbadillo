from scraper import (
    WebDriver, WebElement,
    By, WebDriverWait, EC,
    BeautifulSoup,
    datetime, timedelta
)
from scraper.sportsbook import BookScraper

class BetMGMScraper(BookScraper):
    def __init__(self, driver: WebDriver):
        super().__init__(driver, 'BetMGM')

    def _get_event_info(self, html: str) -> tuple:
        soup = BeautifulSoup(html, 'lxml')
        participants = soup.find_all('div', class_='participant-name')
        if len(participants) < 2:
            raise ValueError("Not enough participant information found")

        participant1 = self._get_team_abbreviation(participants[0].text.strip().upper())
        participant2 = self._get_team_abbreviation(participants[1].text.strip().upper())

        try:
            date = soup.find('span', class_='date').text.strip()
            time = soup.find('span', class_='time').text.strip()
            datetime_ = self._format_event_datetime(date, time)
        except Exception as e:
            print(f'Error formatting event datetime: {e}')
            date = datetime.today().strftime('%Y-%m-%d')
            datetime_ = f'{date}_LIVE'
        
        return participant1, participant2, datetime_


    def _format_event_datetime(self, date: str, time: str) -> str:
        if date.lower() == 'today':
            date = datetime.now().date()
        elif date.lower() == 'tomorrow':
            date = (datetime.now() + timedelta(1)).date()
        else:
            date = datetime.strptime(date, '%m/%d/%y').date()
        
        time = datetime.strptime(time, '%I:%M %p').time()
        formatted_datetime = datetime.combine(date, time)
        return formatted_datetime.strftime('%Y-%m-%d_%H:%M')


    def _scrape_league(self, league: str) -> list:
        league_picks = []
        league_url = self._get_base_url(league)
        self.driver.get(league_url)

        # Wait for main content to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'main'))
        )

        # Wait for each clickable event to load
        events = WebDriverWait(self.driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ms-six-pack-event.grid-event'))
        )

        for event in events:
            try:
                event.click()
                event_picks = self._scrape_event(league)
                league_picks.extend(event_picks)
                self.driver.back()
                # Wait for events to load back in
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ms-six-pack-event.grid-event'))
                )
            except Exception as e:
                print(f'Error scraping event: {e}')

        return league_picks


    def _scrape_event(self, league: str) -> list:
        event_picks = []

        # Wait for game header to load
        WebDriverWait(self.driver, 10).until(
             EC.presence_of_element_located((By.CSS_SELECTOR, 'div.main-score-container'))
        )

        html = self.driver.page_source
        away, home, datetime_ = self._get_event_info(html)
        event_title = f'{away}@{home}_{datetime_}'

        print(f'Scraping event: {event_title}')

        blocks = WebDriverWait(self.driver, 10).until(
             EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'ms-option-panel.option-panel'))
        )

        for block in blocks:
            try:
                block_picks = self._scrape_block(block, league, event_title)
                event_picks.extend(block_picks)
            except Exception as e:
                print(f'Error scraping block" {e}')

        return event_picks


    def _scrape_block(self, block: WebElement, league, event_title) -> list:
        block_picks = []

        # Expand block if it is closed
        try:
            is_closed = block.find_element(By.CSS_SELECTOR, 'div.option-group-header-chevron span').get_attribute('class') == 'theme-down'
            if is_closed:
                expand_button = block.find_element(By.CSS_SELECTOR, 'div.option-group-name.clickable')
                expand_button.click()
        except Exception as e:
            print(f'Error expanding block: {e}')

        # If there is a show more button, click it
        try:
            show_more_button = block.find_elements(By.CSS_SELECTOR, 'div.show-more-less-button')
            if show_more_button:
                show_more_button[0].click()
        except Exception as e:
            print(f'Error clicking show more button: {e}')

        try:
            block_title = block.find_element(By.CSS_SELECTOR, 'span.market-name').text.upper()
            block_type = block.find_element(By.CSS_SELECTOR, 'div.option-group-container').get_attribute('class').split()[1]
        except Exception as e:
            print(f'Error getting block title and type')
            return []

        print(f'Scraping block: {block_title} ({block_type})')

        tabs = []
        scroll_bar = block.find_elements(By.TAG_NAME, 'ms-scroll-adapter')
        if scroll_bar:
            tab_links = block.find_elements(By.CSS_SELECTOR, 'a.link-without-count')
            tabs.extend(tab_links)
        else:
            tabs.append(None)

        for tab in tabs:
            if tab:
                tab.click()

            block_html = block.get_attribute('innerHTML')
            soup = BeautifulSoup(block_html, 'lxml')

            match block_type:
                case 'six-pack-container':
                    game_lines = []
                    rows = soup.find_all('div', class_='option-row')
                    if len(rows) != 2:
                            raise ValueError('Game lines must have 2 rows')

                    for row in rows:
                        try:
                            team_text = row.find('div', class_='six-pack-player-name').text.strip().upper()
                        except Exception as e:
                             print(f'Error getting team name in block {block_title} ({block_type}): {e}')
                             continue

                        team = self._get_team_abbreviation(team_text)
                        options = row.find_all('ms-option', class_='option')

                        for option in options:
                            try:
                                option_pick = option.find('ms-event-pick', class_='option-pick')
                                if option_pick:
                                    name = option_pick.find('div', class_='name')
                                    value = option_pick.find('div', class_='value')

                                    if name and ('+' in name.text or '-' in name.text):
                                        line = float(name.text.replace('+', ''))
                                        odds = int(value.text.replace('+', ''))
                                        game_lines.append(('SPREAD', team, line, odds))
                                    elif name and ('O' in name.text or 'U' in name.text):
                                        ou = 'TOTAL_OVER' if 'O' in name.text else 'TOTAL_UNDER'
                                        line = float(name.text.replace('O', '').replace('U', '').strip())
                                        odds = int(value.text.replace('+', ''))
                                        game_lines.append((ou, team, line, odds))
                                    else:
                                        odds = int(value.text.replace('+', ''))
                                        game_lines.append(('MONEYLINE', team, None, odds))
                            except Exception as e:
                                 print(f'Error with option in block {block_title} ({block_type}): {e}')

                    for game_line in game_lines:
                        pick = self._create_pick(event_title, self.book_name, league,
                                                 game_line[0], game_line[1], game_line[2], game_line[3],
                                                 None, None)
                        block_picks.append(pick)

                case 'over-under-container':
                    if ':' in block_title:
                        title_parts = block_title.split(':')
                        team = self._get_team_abbreviation(title_parts[0].strip())
                        pick_title = title_parts[1].strip().replace(' ', '-')
                    else:
                        team = None
                        pick_title = block_title.strip().replace(' ', '-')

                    lines = soup.find_all('div', class_='attribute-key')
                    options = soup.find_all('ms-option', class_='option')
                    for i, option in enumerate(options):
                        try:
                            line = float(lines[i // 2].text)
                            pick_type = f'{pick_title}_{'OVER' if i % 2 == 0 else 'UNDER'}'

                            option_pick = option.find('ms-event-pick', class_='option-pick')
                            if option_pick:
                                odds = int(option_pick.find('ms-font-resizer').text.replace('+', '').strip())
                                pick = self._create_pick(event_title, self.book_name, league,
                                                        pick_type, team, line, odds,
                                                        None, None)
                                block_picks.append(pick)
                        except Exception as e:
                            print(f'Error with option in block {block_title} ({block_type}): {e}')

                case 'player-props-container':
                        players = soup.find_all('div', class_='player-props-player-name')
                        options = soup.find_all('ms-option', class_='option')
                        pick_type = 'PLAYER-PROP'
                        for i, option in enumerate(options):
                            try:
                                player = players[i // 2].text
                                prop = f'{tab.text.replace(' ', '-').upper()}_{'OVER' if i % 2 == 0 else 'UNDER'}'
                                option_pick = option.find('ms-event-pick', class_='option-pick')
                                if option_pick:
                                    line = float(option_pick.find('div', class_='name').text
                                                            .replace('Over', '')
                                                            .replace('Under', '')
                                                            .strip())
                                    odds = int(option_pick.find('div', class_='value').text.replace('+', ''))
                                    pick = self._create_pick(event_title, self.book_name, league,
                                                                pick_type, None, line, odds,
                                                                player, prop)
                                    block_picks.append(pick)
                            except Exception as e:
                                print(f'Error with option in block {block_title} ({block_type}): {e}')

                case _:
                    print(f'Unsupported block type: {block_type}')

        return block_picks