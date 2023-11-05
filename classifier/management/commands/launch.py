from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from classifier.server import main


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("host", nargs=1)
        return super().add_arguments(parser)

    def handle(self, *args, **options):
        main(
            sbert_model=settings.SBERT_MODEL,
            host=options["host"][0],
            port=settings.API_PORT,
            path=settings.API_PATH,
        )
