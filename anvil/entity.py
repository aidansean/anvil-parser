from frozendict import frozendict
from nbt import nbt

from .legacy import LEGACY_ID_MAP


class Entity:
    """
    Represents a minecraft entity.

    Attributes
    ----------
    id: :class:`str`
        ID of the entity, for example: minecraft:villager
    properties: :class:`dict`
        Entity properties as a dict
    """

    __slots__ = ("entity_id", "x", "y", "z", "properties")

    def __init__(self, entity_id: str, x: int, y: int, z: int, properties: dict = None):
        """
        Parameters
        ----------
        entity_id
            ID of the entity
        properties
            Entity properties
        """
        self.entity_id = entity_id
        self.properties = properties or {}
        self.x, self.y, self.z = x, y, z
        print('my properties are', self.properties)

    def name(self) -> str:
        return self.entity_id

    def __repr__(self):
        return f"Entity({self.name()})"

    def __eq__(self, other):
        if not isinstance(other, Entity):
            return False
        return (
            self.entity_id == other.id
            and self.properties == other.properties
        )

    def __hash__(self):
        return hash(self.name()) ^ hash(frozendict(self.properties))


    def save(self):
        new_entity = nbt.TAG_Compound()
        new_entity.tags.append(nbt.TAG_String(name="id", value=self.entity_id))


        position = nbt.TAG_List(name="Pos", type=nbt.TAG_Double)
        position.tags.append(nbt.TAG_Double(self.x))
        position.tags.append(nbt.TAG_Double(self.y))
        position.tags.append(nbt.TAG_Double(self.z))

        new_entity.tags.append(position)

        for key, value in self.properties.items():
            print('entity.py: processing', key, value)
            if isinstance(value, str):
                new_entity.tags.append(nbt.TAG_String(name=key, value=value))
            elif isinstance(value, int):
                new_entity.tags.append(nbt.TAG_Int(name=key, value=value))
            elif isinstance(value, float):
                new_entity.tags.append(nbt.TAG_Float(name=key, value=value))
            elif isinstance(value, bool):
                new_entity.tags.append(nbt.TAG_Byte(name=key, value=value))
            elif isinstance(value, list):
                if isinstance(value[0], str):
                    new_list = nbt.TAG_List(name=key, type=nbt.TAG_String)
                    for i in value:
                        new_list.tags.append(nbt.TAG_String(i))
                elif isinstance(value[0], float):
                    new_list = nbt.TAG_List(name=key, type=nbt.TAG_Float)
                    for i in value:
                        new_list.tags.append(nbt.TAG_Float(i))
                new_entity.tags.append(new_list)
            else:
                raise TypeError(f"Unknown type {type(value)} for {key}={value}")

        print('entity.py: save', new_entity)
        return new_entity