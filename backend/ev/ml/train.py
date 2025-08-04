import os
import joblib
import pandas as pd

from datetime import datetime

from sports.models import EventResult
from sports.queries import get_events
from common.constants.aliases import MARKET_TO_STATS
from ev.ml.features import build_features_for_market

from sklearn.ensemble import RandomForestClassifier
from django.conf import settings

def get_training_data(market: str, league: str, season: int, cutoff: datetime):
    events = get_events(league, season, before_date=cutoff)

    X, y = [], []
    for event in events:
        result = EventResult.objects.filter(event_key=event.event_key).first()
        if not result:
            continue

        feature_vector = build_features_for_market(
            market, league, season, 
            team_key=event.home_team, 
            opponent_key=event.away_team, 
            before_date=cutoff
        )
        X.append(feature_vector)

        label_name = MARKET_TO_STATS[league][market]['label']
        label = getattr(result, label_name)
        y.append(label)

    return pd.DataFrame(X), y

        
def train_model(market: str, league: str, season: int, cutoff: datetime, model_name: str = None):
    X, y = get_training_data(market, league, season, cutoff)

    model = RandomForestClassifier()
    model.fit(X, y)

    os.makedirs(settings.MODEL_DIR, exist_ok=True)
    model_name = model_name or f'{league}_{season}_{market}.pkl'
    path = os.path.join(settings.MODEL_DIR, model_name)
    joblib.dump(model, path)
    return path
