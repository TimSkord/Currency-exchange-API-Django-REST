from typing import Any

from django.core.management.base import BaseCommand
from exchange.utils import upload_csv


class Command(BaseCommand):
    help = 'Uploads data from a CSV file into the Exchange model'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the CSV file')

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        The main method that is called when the management command is executed.

        It reads the file path from the command arguments, calls the function to upload CSV data,
        and handles any exceptions that occur during the upload process.

        Parameters:
        args (Any): Variable length argument list.
        kwargs (Any): Arbitrary keyword arguments, contains 'file_path' for the CSV file.

        Raises:
        Exception: Propagates exceptions from the upload_csv function with a custom error message.
        """
        file_path = kwargs['file_path']
        try:
            upload_csv(file_path)
            self.stdout.write(self.style.SUCCESS('Successfully uploaded CSV file'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {e}'))
