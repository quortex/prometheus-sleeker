import argparse
import logging
import logging.config
import json


from .metric import Metrics, MetricConfig

logger = logging.getLogger(__name__)


DEFAULT_CONFIGURATION_FILE = "config.json"


def load_config_file(config_file):

    with open(config_file, "r") as f:
        conf = json.load(f)
    logger.debug(conf)

    result = []
    for element in conf["metrics"]:
        result.append(Metrics(MetricConfig.load(element)))

    return result


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


def configure():
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
