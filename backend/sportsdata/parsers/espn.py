def parse_team(team_json, league):
    aliases = [
        team_json['slug'], team_json['abbreviation'], team_json['displayName'],
        team_json['shortDisplayName'], team_json['name'], team_json['nickname'],
        f'{team_json["abbreviation"]} {team_json["name"]}'
    ]
    return {
        'espn_id': team_json['id'],
        'league': league,
        'team_key': team_json['slug'],
        'name': team_json['displayName'],
        'aliases': aliases
    }


def parse_event(event_json, league):
    return {
        'espn_id': event_json['id'],
        'league': league,
        'away_team_id': event_json['competitions'][0]['competitors'][0]['id'],
        'home_team_id': event_json['competitions'][0]['competitors'][1]['id'],
        'start_time': event_json['date'],
        'status': event_json['status']['type']['state']
    }


def parse_player(player_json, league):
    return {
        'espn_id': player_json['id'],
        'league': league,
        'name': player_json['displayName'],
        'player_key': player_json['slug'],
        'position': player_json['position']['name']
    }
    

