import gzip
import zlib
from io import BytesIO
from typing import BinaryIO, Tuple, Union

from nbt import nbt

import anvil

from .errors import UnknownCompressionSchema


# TODO: Try to implement this table as a frozendict maybe?
DECOMPRESSION_TABLE = {
    1: gzip.decompress,
    2: zlib.decompress,
    3: lambda data: data  # Type 3 is uncompressed data
}

class Region:
    """
    Read-only region

    Attributes
    ----------
    data: :class:`bytes`
        Region file (``.mca``) as bytes
    """

    __slots__ = ("data",)

    def __init__(self, data: bytes):
        """Makes a Region object from data, which is the region file content"""
        self.data = data

    @staticmethod
    def header_offset(chunk_x: int, chunk_z: int) -> int:
        """
        Returns the byte offset for given chunk in the header

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value
        """
        return 4 * (chunk_x % 32 + chunk_z % 32 * 32)

    def chunk_location(self, chunk_x: int, chunk_z: int) -> Tuple[int, int]:
        """
        Returns the chunk offset in the 4KiB sectors from the start of the file,
        and the length of the chunk in sectors of 4KiB

        Will return ``(0, 0)`` if chunk hasn't been generated yet

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value
        """
        b_off = self.header_offset(chunk_x, chunk_z)
        off = int.from_bytes(self.data[b_off : b_off + 3], byteorder="big")
        sectors = self.data[b_off + 3]
        return off, sectors

    def chunk_data(self, chunk_x: int, chunk_z: int) -> nbt.NBTFile:
        """
        Returns the NBT data for a chunk

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value

        Raises
        ------
        anvil.GZipChunkData
            If the chunk's compression is gzip
        """
        off = self.chunk_location(chunk_x, chunk_z)
        # (0, 0) means it hasn't generated yet, aka it doesn't exist yet
        if off == (0, 0):
            return
        off = off[0] * 4096
        data_start = off + 5
        length = int.from_bytes(self.data[off:data_start - 1], byteorder='big')
        compression = self.data[data_start - 1] # 2 most of the time
        if compression == 127:
            raise UnknownCompressionSchema("Cannot decode files of custom compression type 127")
        
        compressed_data = self.data[data_start : data_start + length - 1]
        
        try:
            # Not immediately executing decompression here to avoid invalid catching
            # (whyever a compression system should raise KeyError)
            decompression_method = DECOMPRESSION_TABLE[compression]
        except KeyError as e:
            raise UnknownCompressionSchema(compression) from e
        
        return nbt.NBTFile(buffer=BytesIO(decompression_method(compressed_data)))

    def get_chunk(self, chunk_x: int, chunk_z: int) -> "anvil.Chunk":
        """
        Returns the chunk at given coordinates,
        same as doing ``Chunk.from_region(region, chunk_x, chunk_z)``

        Parameters
        ----------
        chunk_x
            Chunk's X value
        chunk_z
            Chunk's Z value


        :rtype: :class:`anvil.Chunk`
        """
        return anvil.Chunk.from_region(self, chunk_x, chunk_z)

    @classmethod
    def from_file(cls, file: Union[str, BinaryIO]):
        """
        Creates a new region with the data from reading the given file

        Parameters
        ----------
        file
            Either a file path or a file object
        """
        if isinstance(file, str):
            with open(file, "rb") as f:
                return cls(data=f.read())
        else:
            return cls(data=file.read())
