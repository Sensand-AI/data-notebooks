import shutil
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def delete_directory(directory_path):
    """
    Deletes the specified directory along with all its contents.

    Parameters:
    - directory_path (str): The path to the directory to be deleted.

    Returns:
    - None
    """
    try:
        shutil.rmtree(directory_path)
    except FileNotFoundError:
        logger.error(
            "Directory: does not exist", extra=dict(data={"directory": directory_path})
        )
    except PermissionError:
        logger.error(
            "Directory: permission denied",
            extra=dict(data={"directory": directory_path}),
        )
    except Exception as e:  # This catches other potential exceptions and logs them.
        logger.error(
            "Directory: failed to delete",
            extra=dict(data={"directory": directory_path, "error": str(e)}),
        )
