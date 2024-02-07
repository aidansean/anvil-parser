class OutOfBoundsCoordinates(ValueError):
    """Exception used for when coordinates are out of bounds"""


class ChunkNotFound(Exception):
    """Exception used for when a chunk was not found"""


class EmptySectionAlreadyExists(Exception):
    """
    Exception used for when trying to add an `EmptySection` to an `EmptyChunk`
    and the chunk already has a section with the same Y
    """


class ChunkCompressionException(Exception):
    """Generic exception for issues related to chunk compression"""

class GZipChunkData(ChunkCompressionException):
    """Exception used when trying to get chunk data compressed in gzip"""

class UnknownCompressionSchema(ChunkCompressionException):
    """Raised when a custom exception (id 127) is encountered post 24w05a"""
    
    def __init__(self, compression: int):
        custom_message = "(Id 127 indicates custom compression)" if compression == 127 else ""
        super().__init__(f"Encountered unknown compression schema {compression} {custom_message}")
