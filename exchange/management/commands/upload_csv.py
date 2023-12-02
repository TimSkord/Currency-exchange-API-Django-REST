from django.core.management.base import BaseCommand
from exchange.utils import upload_csv


class Command(BaseCommand):
    help = 'Uploads data from a CSV file into the Exchange model'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        try:
            upload_csv(file_path)
            self.stdout.write(self.style.SUCCESS('Successfully uploaded CSV file'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
