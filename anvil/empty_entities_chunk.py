from typing import List

from nbt import nbt

from .block import Block
from .entity import Entity
from .empty_section import EmptySection
from .errors import EmptySectionAlreadyExists, OutOfBoundsCoordinates

from .constants import YMIN, YMAX, NSECTIONS


class EmptyEntitiesChunk:
    """
    Used for making own chunks

    Attributes
    ----------
    x: :class:`int`
        Chunk's X position
    z: :class:`int`
        Chunk's Z position
    sections: List[:class:`anvil.EmptySection`]
        List of all the sections in this chunk
    version: :class:`int`
        Chunk's DataVersion
    """

    __slots__ = ("x", "z", "sections", "version", "entities")

    def __init__(self, x: int, z: int):
        self.x = x
        self.z = z
        self.sections: List[EmptySection] = [None] * NSECTIONS
        self.version = 1976
        self.entities: List[Entity] = []

    def add_section(self, section: EmptySection, replace: bool = True):
        """
        Adds a section to the chunk

        Parameters
        ----------
        section
            Section to add
        replace
            Whether to replace section if one at same Y already exists

        Raises
        ------
        anvil.EmptySectionAlreadyExists
            If ``replace`` is ``False`` and section with same Y already exists in this chunk
        """
        if self.sections[section.y] and not replace:
            raise EmptySectionAlreadyExists(
                f"EmptySection (Y={section.y}) already exists in this chunk"
            )
        self.sections[section.y] = section

    def get_block(self, x: int, y: int, z: int) -> Block:
        """
        Gets the block at given coordinates

        Parameters
        ----------
        x
            In range of 0 to 15
        y
            In range of 0 to 255
        z
            In range of 0 to 15

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range

        Returns
        -------
        block : :class:`anvil.Block` or None
            Returns ``None`` if the section is empty, meaning the block
            is most likely an air block.
        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f"X ({x!r}) must be in range of 0 to 15")
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f"Z ({z!r}) must be in range of 0 to 15")
        if y < YMIN or y > YMAX:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of {YMIN} to {YMAX}')

        section = self.sections[y // 16]

        if section is None:
            return

        return section.get_block(x, y % 16, z)

    def set_block(self, block: Block, x: int, y: int, z: int):
        """
        Sets block at given coordinates

        Parameters
        ----------
        block
            The block to set
        x
            In range of 0 to 15
        y
            In range of 0 to 255
        z
            In range of 0 to 15

        Raises
        ------
        anvil.OutOfBoundCoordidnates
            If X, Y or Z are not in the proper range

        """
        if x < 0 or x > 15:
            raise OutOfBoundsCoordinates(f"X ({x!r}) must be in range of 0 to 15")
        if z < 0 or z > 15:
            raise OutOfBoundsCoordinates(f"Z ({z!r}) must be in range of 0 to 15")
        if y < YMIN or y > YMAX:
            raise OutOfBoundsCoordinates(f'Y ({y!r}) must be in range of {YMIN} to {YMAX}')
        section = self.sections[y // 16]
        if section is None:
            section = EmptySection(y // 16)
            self.add_section(section)
        section.set_block(block, x, y % 16, z)

    def add_entity(self, entity_id: str, x: int, y: int, z: int, entity_properties: dict = None):
        print('chunk.py: set_entity', entity_id, x, y, z)
        """
        Sets entity at given coordinates

        Parameters
        ----------
        entity
            The entity to set
        x
        y
        z

        """

        entity: Entity = Entity(entity_id, x, y, z, entity_properties)
        self.entities.append(entity)


    def save(self) -> nbt.NBTFile:
        print('chunk.save')
        """
        Saves the chunk data to a :class:`NBTFile`

        Notes
        -----
        Does not contain most data a regular chunk would have,
        but minecraft stills accept it.
        """
        root = nbt.NBTFile()


        position = nbt.TAG_Int_Array(name="Position")
        position.value = [self.x, self.z]
        root.tags.extend([
                nbt.TAG_Int(name="DataVersion", value=self.version),
                position
        ])
        entities = nbt.TAG_List(name="Entities", type=nbt.TAG_Compound)

        for entity in self.entities:
            entities.tags.append(entity.save())

        root.tags.append(entities)
        return root
