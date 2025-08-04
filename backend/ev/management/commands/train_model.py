from django.core.management.base import BaseCommand
from ev.ml.train import train_model
from datetime import datetime

class Command(BaseCommand):
    help = 'Train a model for a given market, league, and season.'

    def add_arguments(self, parser):
        parser.add_argument('--market', type=str, required=True, help='Market type (e.g., moneyline, spread)')
        parser.add_argument('--league', type=str, required=True)
        parser.add_argument('--season', type=int, required=True)
        parser.add_argument('--cutoff', type=str, required=True, help='Cutoff datetime in ISO format')
        parser.add_argument('--model-name', type=str, help='Optional model name')

    def handle(self, *args, **options):
        market = options['market']
        league = options['league']
        season = options['season']
        cutoff = datetime.fromisoformat(options['cutoff'])
        model_name = options.get('model_name')

        model_path = train_model(market, league, season, cutoff, model_name)
        self.stdout.write(self.style.SUCCESS(f'Model trained and saved to {model_path}'))