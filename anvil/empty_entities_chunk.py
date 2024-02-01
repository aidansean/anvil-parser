from typing import List

from nbt import nbt

from .entity import Entity
from .empty_section import EmptySection

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
