import argparse
import json
import logging
import logging.config

from .metric import Metrics
from .options import Options

logger = logging.getLogger(__name__)


DEFAULT_CONFIGURATION_FILE = "config.json"


def load_config_file(config_file) -> dict:

    with open(config_file, "r") as f:
        conf = json.load(f)
    logger.debug(conf)

    metrics = []
    for element in conf["metrics"]:
        metrics.append(Metrics(**element))

    return {"options": Options(**conf.get("options", {})), "metrics": metrics}


def configure_logger(log_level):
    loggers = {
        # root logger
        "": {"level": log_level, "handlers": ["console"],},
    }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "format": "%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
                },
            },
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "console",},
            },
            "loggers": loggers,
        }
    )


def configure() -> dict:
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="json configuration file")
    parser.add_argument(
        "-v", "--verbose", help="increase output verbosity", action="store_true"
    )
    parser.add_argument(
        "-q", "--quiet", help="decrease output verbosity", action="store_true"
    )

    args = parser.parse_args()

    log_level = logging.INFO
    if args.verbose:
        log_level = logging.DEBUG
    if args.quiet:
        log_level = logging.WARNING
    configure_logger(log_level)

    config_file = DEFAULT_CONFIGURATION_FILE
    if args.config:
        config_file = args.config

    logger.debug(args)
    return load_config_file(config_file)
