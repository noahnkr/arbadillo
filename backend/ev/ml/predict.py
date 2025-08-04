import joblib
import os
import pandas as pd

from datetime import datetime
from django.conf import settings
from ev.ml.features import build_features_for_market

from sports.queries import get_events

def predict_events(market: str, league: str, season: int, cutoff: datetime, model_name: str):
    path = os.path.join(settings.MODEL_DIR, model_name)
    model = joblib.load(path)

    predictions = {}

    events = get_events(league, season, after_date=cutoff)
    for event in events:
        features = build_features_for_market(market, league, season, event.home_team, event.away_team)
        X = pd.DataFrame([features], columns=model.feature_names_in_)

        proba = model.predict_proba(X)[0]
        prediction = model.classes_[proba.argmax()]
        confidence = proba.max()

        predictions[event.event_key] = {
            'prediction': prediction,
            'confidence': confidence
        }

    return predictions
