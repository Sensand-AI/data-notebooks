import logging

# Initialize the logger for this module
logger = logging.getLogger(__name__)

def validateIsTiff(file_path):
		"""
		Validate if the file is a tiff file
		This is because blockbase wants a specific `.tiff` file in many cases
		:param file_path: Path to the file
		:return: True if the file is a tiff file, False otherwise
		"""
		if not file_path.lower().endswith('.tiff'):
			logger.error(f"File rejected, not a .tiff extension: {file_path}")
			return False

		try:
				with open(file_path, 'rb') as f:
						tiff = f.read(4)
						is_tiff = tiff == b'II*\x00' or tiff == b'MM\x00*'
						if not is_tiff:
								logger.error(f"File rejected, invalid TIFF header: {file_path}")
						return is_tiff
		except Exception as e:
				logger.error(f"Error while validating if the file is a tiff file: {e}")
				return False