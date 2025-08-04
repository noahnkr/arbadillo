import pprint
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from ev.ml.predict import predict_events
from datetime import datetime

class Command(BaseCommand):
    help = 'Run predictions for a given market and season using a trained model.'

    def add_arguments(self, parser):
        parser.add_argument('--market', type=str, required=True)
        parser.add_argument('--league', type=str, required=True)
        parser.add_argument('--season', type=int, required=True)
        parser.add_argument('--after', type=str, help='Filter events after this date (YYYY-MM-DD)')
        parser.add_argument('--model-name', type=str, required=True)
        parser.add_argument('--output-path', type=str)

    def handle(self, *args, **options):
        market = options['market']
        league = options['league']
        season = options['season']
        after = options.get('after')
        after_date = datetime.fromisoformat(after) if after else None
        model_name = options['model_name']

        output_path = options['output_path']

        output = os.path.join(settings.BASE_DIR, output_path)

        predictions = predict_events(market, league, season, cutoff=after_date, model_name=model_name, output_path=output)
        self.stdout.write(self.style.SUCCESS(f'{len(predictions)} predictions made.'))
        pprint.pprint(predictions)