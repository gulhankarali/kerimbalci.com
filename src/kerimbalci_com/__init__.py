from kerimbalci_com.config import get_settings, setup_logging


def main() -> None:
    settings = get_settings()
    logger = setup_logging(settings)
    logger.info("%s basladi (ortam: %s, debug: %s)", settings.app_name, settings.environment, settings.debug)
    logger.debug("Debug modu acik - ayrintili loglar gorunur.")
