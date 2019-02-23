from ..datatypes import DataType
from .faction import Faction
from ..misc import LocalizedString
from .zone import Zone


class Region(DataType):
    """A capturable territory.

    A region (aka. facility or base) is a capturable area of the map belonging
    to a faction.

    """

    _collection = 'region'

    def __init__(self, id_):
        self.id_ = id_

        # Set default values
        self._initial_faction_id = None
        self.name = None
        self._zone_id = None

    # Define properties
    @property
    def initial_faction(self):
        return Faction.get(id_=self._initial_faction_id)

    @property
    def zone(self):
        return Zone.get(id_=self._zone_id)

    def populate(self, data=None):
        d = data if data is not None else super()._get_data(self.id_)
        # Set attribute values
        self._initial_faction_id = d.get('initial_faction_id')
        self.name = LocalizedString(d['name'])
        self._zone_id = Zone(d['zone_id'])


class FacilityLink(DataType):
    """Links two facilities on the map to each other.

    Also known as a lattice link, this data type describes whether two
    facilities are connected and whether one can be attacked from the other.

    """

    _collection = 'facility_link'

    def __init__(self, id_):
        self.id_ = id_

        # Set default values
        self.description = None
        self._facility_a_id = None
        self._facility_b_id = None
        self._zone_id = None

    # Define properties
    @property
    def facility_a(self):
        return Region.get(id_=self._facility_a_id)

    @property
    def facility_b(self):
        return Region.get(id_=self._facility_b_id)

    @property
    def zone(self):
        return Zone.get(id_=self._zone_id)

    def populate(self, data=None):
        d = data if data is not None else super()._get_data(self.id_)

        # Set attribute values
        self.description = d['description']
        self._facility_a_id = d['facility_id_a']
        self._facility_b_id = d['facility_id_b']
        self._zone_id = d['zone_id']


class FacilityType(DataType):
    """A type of facility.

    Examples are "Tech Plant", "Bio Lab" or "Small Outpost".

    """

    _collection = 'facility_type'

    def __init__(self, id_):
        self.id_ = id_

        # Set default values
        self.description = None

    def populate(self, data=None):
        d = data if data is not None else super()._get_data(self.id_)

        # Set attribute values
        self.description = d['description']
