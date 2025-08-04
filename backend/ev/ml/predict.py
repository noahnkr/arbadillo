
import joblib
import json
import os
import pandas as pd

from datetime import datetime
from django.conf import settings
from ev.ml.features import build_features_for_market

from sports.queries import get_events

def predict_events(market: str, league: str, season: int, cutoff: datetime, model_name: str, output_path: str = None):
    path = os.path.join(settings.MODEL_DIR, model_name)
    model = joblib.load(path)

    predictions = {}
    events = get_events(league, season, after_date=cutoff)

    for event in events:
        features_home = build_features_for_market(market, league, season, event.home_team, event.away_team, before_date=cutoff)
        features_away = build_features_for_market(market, league, season, event.away_team, event.home_team, before_date=cutoff)

        X = pd.DataFrame([features_home, features_away])
        proba = model.predict_proba(X)
        
        home_prob = proba[0][1]
        away_prob = proba[1][1]

        prediction = event.home_team if home_prob > away_prob else event.away_team
        confidence = max(home_prob, away_prob)

        predictions[event.event_key] = {
            'prediction': prediction,
            'confidence': float(confidence)
        }

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(predictions, f)

    return predictions
