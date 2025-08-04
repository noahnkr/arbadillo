import os
import json
from django.core.management.base import BaseCommand
from django.conf import settings
from sports.queries import get_events, get_event_results
from ev.ml.predict import predict_events
from datetime import datetime

class Command(BaseCommand):
    help = 'Evaluate predictions for a given market and season'

    def add_arguments(self, parser):
        parser.add_argument('--league', type=str, required=True)
        parser.add_argument('--season', type=int, required=True)
        parser.add_argument('--predictions-path', type=str, required=True)

    def handle(self, *args, **options):
        league = options['league']
        season = options['season']
        predictions_path = options['predictions_path']

        path = os.path.join(settings.BASE_DIR, predictions_path)

        with open(path, 'r') as f:
            predictions = json.load(f)

        event_keys = get_events(league, season).values_list('event_key', flat=True)
        results = get_event_results(event_keys)

        correct = 0
        total = 0
        unmatched = []

        for event_key, prediction in predictions.items():
            result = results.filter(event_key=event_key).first()
            if not result:
                unmatched.append(event_key)
                continue
    
            predicted_team = prediction['prediction']
            actual_team = result.winner

            is_correct = predicted_team == actual_team
            correct += is_correct
            total += 1

            if is_correct:
                self.stdout.write(self.style.SUCCESS(
                    f'[CORRECT] {event_key}: predicted={predicted_team}, actual={predicted_team}, '
                    f'confidence={prediction["confidence"]:.2f}'
                ))
            else:
                self.stdout.write(self.style.ERROR(
                    f'[INCORRECT] {event_key}: predicted={predicted_team}, actual={predicted_team}, '
                    f'confidence={prediction["confidence"]:.2f}'
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f'\nEvaluation complete: {correct}/{total} correct '
            f'({100.0 * correct / total:.2f}% accuracy)'
        ))

        if unmatched:
            self.stdout.write(self.style.WARNING(
                f'\n{len(unmatched)} predictions had no matching result:'
            ))
            for event in unmatched:
                self.stdout.write(f' - {event}')