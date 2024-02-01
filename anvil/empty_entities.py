import math
import zlib
from io import BytesIO
from typing import BinaryIO, List, Union

from .empty_entities_chunk import EmptyEntitiesChunk
from .errors import OutOfBoundsCoordinates

from .constants import YMIN, YMAX


def from_inclusive(a, b):
    """Returns a range from a to b, including both endpoints"""
    c = int(b > a) * 2 - 1
    return range(a, b + c, c)


class EmptyEntities:
    """
    Used for making own entities

    Attributes
    ----------
    chunks: List[:class:`anvil.EmptyEntitiesChunk`]
        List of chunks in this region
    x: :class:`int`
    z: :class:`int`
    """

    __slots__ = ("entities_chunks", "x", "z")

    def __init__(self, x: int, z: int):
        # Create a 1d list for the 32x32 chunks
        self.entities_chunks: List[EmptyEntitiesChunk] = [None] * 1024
        self.x = x
        self.z = z

    def inside(self, x: int, y: int, z: int, chunk: bool = False) -> bool:
        """
        Returns if the given coordinates are inside this region

        Parameters
        ----------
        x
            The x coordinate
        y
            The y coordinate
        z
            The z coordinate
        chunk
            Whether coordinates are global or chunk coordinates
        """
        factor = 32 if chunk else 512
        rx = x // factor
        rz = z // factor
        return not (rx != self.x or rz != self.z or y < YMIN or y > YMAX)

    def get_chunk(self, x: int, z: int) -> EmptyEntitiesChunk:
        """
        Returns the chunk at given chunk coordinates

        Parameters
        ----------
        int x, z
            Chunk's coordinates

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If the chunk (x, z) is not inside this region

        :rtype: :class:`anvil.EmptyEntitiesChunk`
        """
        if not self.inside(x, 0, z, chunk=True):
            raise OutOfBoundsCoordinates(f"Chunk ({x}, {z}) is not inside this region")
        return self.entities_chunks[z % 32 * 32 + x % 32]

    def add_chunk(self, chunk: EmptyEntitiesChunk):
        """
        Adds given chunk to this region.
        Will overwrite if a chunk already exists in this location

        Parameters
        ----------
        chunk: :class:`EmptyEntitiesChunk`

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If the chunk (x, z) is not inside this region
        """
        if not self.inside(chunk.x, 0, chunk.z, chunk=True):
            raise OutOfBoundsCoordinates(
                f"Chunk ({chunk.x}, {chunk.z}) is not inside this region"
            )
        self.entities_chunks[chunk.z % 32 * 32 + chunk.x % 32] = chunk

    def add_entity(self, entity_id: str, x: int, y: int, z: int, entity_properties: dict = None):
        """
        Sets entity at given coordinates.
        New chunk is made if it doesn't exist.

        Parameters
        ----------
        entity: :class:`Entity`
            Entity to place
        x
            The x coordinate
        y
            The y coordinate
        z
            The z coordinate

        Raises
        ------
        anvil.OutOfBoundsCoordinates
            If the entity (x, y, z) is not inside this region
        """

        chunk_x = x % 512
        chunk_z = z % 512
        if not self.inside(chunk_x, y, chunk_z):
            raise OutOfBoundsCoordinates(
                f"Entity ({x}, {y}, {z}) is not inside this region"
            )
        cx = chunk_x // 16
        cz = chunk_z // 16
        chunk = self.get_chunk(cx, cz)
        if chunk is None:
            chunk = EmptyEntitiesChunk(cx, cz)
            self.add_chunk(chunk)
        chunk.add_entity(entity_id, x, y, z, entity_properties)

    def save(self, file: Union[str, BinaryIO] = None) -> bytes:
        """
        Returns the region as bytes with
        the anvil file format structure,
        aka the final ``.mca`` file.

        Parameters
        ----------
        file
            Either a path or a file object, if given region
            will be saved there.
        """
        # Store all the chunks data as zlib compressed nbt data
        chunks_data = []
        for chunk in self.entities_chunks:
            if chunk is None:
                chunks_data.append(None)
                continue
            chunk_data = BytesIO()
            nbt_data = chunk.save()
            nbt_data.write_file(buffer=chunk_data)
            chunk_data.seek(0)
            chunk_data = zlib.compress(chunk_data.read())
            chunks_data.append(chunk_data)

        # This is what is added after the location and timestamp header
        chunks_bytes = bytes()
        offsets = []
        for chunk in chunks_data:
            if chunk is None:
                offsets.append(None)
                continue
            # 4 bytes are for length, b'\x02' is the compression type which is 2 since its using zlib
            to_add = (len(chunk) + 1).to_bytes(4, "big") + b"\x02" + chunk

            # offset in 4KiB sectors
            sector_offset = len(chunks_bytes) // 4096
            sector_count = math.ceil(len(to_add) / 4096)
            offsets.append((sector_offset, sector_count))

            # Padding to be a multiple of 4KiB long
            to_add += bytes(4096 - (len(to_add) % 4096))
            chunks_bytes += to_add

        locations_header = bytes()
        for offset in offsets:
            # None means the chunk is not an actual chunk in the region
            # and will be 4 null bytes, which represents non-generated chunks to minecraft
            if offset is None:
                locations_header += bytes(4)
            else:
                # offset is (sector offset, sector count)
                locations_header += (offset[0] + 2).to_bytes(3, "big") + offset[
                    1
                ].to_bytes(1, "big")

        # Set them all as 0
        timestamps_header = bytes(4096)

        final = locations_header + timestamps_header + chunks_bytes

        # Pad file to be a multiple of 4KiB in size
        # as Minecraft only accepts region files that are like that
        final += bytes(4096 - (len(final) % 4096))
        assert len(final) % 4096 == 0  # just in case

        # Save to a file if it was given
        if file:
            if isinstance(file, str):
                with open(file, "wb") as f:
                    f.write(final)
            else:
                file.write(final)
        return final
