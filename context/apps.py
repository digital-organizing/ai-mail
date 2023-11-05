import logging
import os
import sys

from django.apps import AppConfig
from django.conf import settings
from pymilvus import MilvusException, connections

logger = logging.getLogger(__name__)


class ContextConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "context"

    def ready(self) -> None:
        """Connect to milvus."""
        if sys.argv[0].endswith("mypy") or os.environ.get("SKIP_MILVUS", False):
            return
        try:
            connections.connect(host=settings.MILVUS_HOST)
        except MilvusException as e:
            logger.warning("Couldn't connect to Milvus: {}".format(e))

        return super().ready()
