
from django.core.management.base import BaseCommand

from knowledge_base.services import ingest_knowledge_articles


class Command(BaseCommand):
    help = "Ingest Django knowledge articles into ChromaDB"

    def handle(self, *args, **options):
        count = ingest_knowledge_articles()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully ingested {count} knowledge articles into ChromaDB."
            )
        )
