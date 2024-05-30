import logging
import sys



def setup_logging():
    logging.basicConfig(
        stream=sys.stdout,
        level=logging.INFO, # This will capture all logs with level INFO and above
				datefmt="%Y-%m-%dT%H:%M:%SZ",
        format="%(levelname)s | %(asctime)s | %(message)s",
    )