from ..datatypes import DataType


class ResistInfo(DataType):
    """A resist info entry.

    Resist info contains information about how resistant an entity is to certain
    types of damage.

    """

    _collection = 'resist_info'

    def __init__(self, id_):
        self.id_ = id_

        # Set default values
        self.description = None
        self.headshot_multiplier = None
        self.percent = None
        self._resist_type_id = None

    # Define properties
    @property
    def resist_type(self):
        return ResistType.get(id_=self._resist_type_id)

    def populate(self, data=None):
        d = data if data is not None else super()._get_data(self.id_)

        # Set attribute values
        self.description = d.get('description')
        self.headshot_multiplier = d.get('multiplier_when_headshot')
        self.percent = d['resist_percent']
        self._resist_type_id = d.get('resist_type_id')


class ResistType(DataType):
    """A resist type.

    A type of damage for which resistance information might exist.
    Examples include "Heavy Machine Gun" or "Explosive".

    """

    _collection = 'resist_type'

    def __init__(self, id_):
        self.id_ = id_

        # Set default values
        self.description = None

    def populate(self, data=None):
        d = data if data is not None else super()._get_data(self.id_)

        # Set attribute values
        self.description = d['description']
