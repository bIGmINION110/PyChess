from pythonjsonlogger import jsonlogger
import logging
import logging.handlers
import os

def setup_logger(
    name: str,
    log_file: str = None,
    level: int = logging.INFO,
    console: bool = True,
    rotate: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    """
    Erstellt einen Logger mit JSON-Format.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # JSON Formatter
    json_formatter = jsonlogger.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    if logger.hasHandlers():
        logger.handlers.clear()

    if console:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(json_formatter)
        logger.addHandler(ch)

    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        if rotate:
            fh = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
            )
        else:
            fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(level)
        fh.setFormatter(json_formatter)
        logger.addHandler(fh)

    return logger


# Beispiel für die Nutzung:
#if __name__ == '__main__':
#    log = setup_logger(
#        name=__name__,
#        log_file='logs/app.log',
#        level=logging.DEBUG,
#        console=True,
#        rotate=True
#    )
#

log = setup_logger(
    name=__name__)
log.info("<---   Logging begonnen   --->")
