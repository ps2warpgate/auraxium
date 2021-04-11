"""Outfit and outfit member class definitions."""

import logging
from typing import ClassVar, Final, List, Optional, TYPE_CHECKING, Type, Union

from ..base import Cached, Named, NamedT
from .._cache import TLRUCache
from ..census import Query
from ..errors import NotFoundError
from ..models import OutfitData, OutfitMemberData, OutfitRankData
from .._proxy import InstanceProxy, SequenceProxy
from .._rest import RequestClient, extract_payload, extract_single
from .._support import deprecated

if TYPE_CHECKING:  # pragma: no cover
    # This is only imported during static type checking to resolve the
    # 'Character' forward reference. This avoids a circular import at runtime.
    from ._character import Character

__all__ = [
    'Outfit',
    'OutfitMember'
]

log = logging.getLogger('auraxium.ps2')


class OutfitMember(Cached, cache_size=100, cache_ttu=300.0):
    """A member of an outfit.

    This class can be treated as an extension of the
    :class:`auraxium.ps2.Character` class.

    Attributes:
        outfit_id: The ID of the outfit this member is a part of.
        id: The ID of the associated character.
        member_since: The date the character joined the outfit at as
            a UTC timestamp.
        member_since_date: Human-readable version of
            :attr:`member_since`.
        rank: The name of the member's in-game outfit rank.
        rank_ordinal: The ordinal position of the member's rank within
            the outfit. The lower the value, the higher the rank.

    """

    collection = 'outfit_member'
    data: OutfitMemberData
    id_field = 'character_id'
    _model = OutfitMemberData

    # Type hints for data class fallback attributes
    outfit_id: int
    id: int
    member_since: int
    member_since_date: str
    rank: str
    rank_ordinal: int

    def character(self) -> InstanceProxy['Character']:
        """Return the character associated with this member.

        This returns an :class:`auraxium.InstanceProxy`.
        """
        # NOTE: This is required due to OutfitMember effectively being an
        # extension of Character.
        # pylint: disable=import-outside-toplevel
        from ._character import Character
        query = Query(Character.collection, service_id=self._client.service_id)
        query.add_term(field=Character.id_field, value=self.data.character_id)
        return InstanceProxy(Character, query, client=self._client)

    def outfit(self) -> InstanceProxy['Outfit']:
        """Return the character associated with this member.

        This returns an :class:`auraxium.InstanceProxy`.
        """
        query = Query(Outfit.collection, service_id=self._client.service_id)
        query.add_term(field=Outfit.id_field, value=self.data.outfit_id)
        return InstanceProxy(Outfit, query, client=self._client)


class Outfit(Named, cache_size=20, cache_ttu=300.0):
    """A player-run outfit.

    Attributes:
        id: The unique ID of the outfit.
        name_lower: Lowercase version of :attr`name`. Useful for
            optimising case-insensitive searches.
        alias: The alias (or tag) of the outfit.
        alias_lower: Lowercase version of :attr:`alias`. Useful for
            optimising case-insensitive searches.
        name: Name of the outfit. Not localised.
        time_created: The creation date of the outfit as a UTC
            timestamp.
        time_created_date: Human-readable version of
            :attr:`time_created`.
        leader_character_id: The character/member ID of the outfit
            leader.
        member_count: The number of members in the outfit.

    """

    _cache: ClassVar[TLRUCache[Union[int, str], 'Outfit']]
    collection = 'outfit'
    data: OutfitData
    id_field = 'outfit_id'
    _model = OutfitData

    # Type hints for data class fallback attributes
    id: int
    alias: str
    time_created: int
    time_created_date: str
    leader_character_id: int
    member_count: int
    name: str

    @property
    def tag(self) -> str:
        """Alias of :attr:`Outfit.alias`."""
        return self.alias

    @classmethod
    @deprecated('0.3', replacement='Client.get()')
    async def get_by_name(cls: Type[NamedT], name: str, *, locale: str = 'en',
                          client: RequestClient) -> Optional[NamedT]:
        """Retrieve an outfit by its unique name.

        This query is always case-insensitive.

        """
        log.debug('%s "%s"[%s] requested', cls.__name__, name, locale)
        if (instance := cls._cache.get(f'_{name.lower()}')) is not None:
            log.debug('%r restored from cache', instance)
            return instance
        log.debug('%s "%s"[%s] not cached, generating API query...',
                  cls.__name__, name, locale)
        query = Query(cls.collection, service_id=client.service_id,
                      name_lower=name.lower()).limit(1)
        data = await client.request(query)
        try:
            payload = extract_single(data, cls.collection)
        except NotFoundError:
            return None
        return cls(payload, client=client)

    @classmethod
    @deprecated('0.3', replacement='Client.get()')
    async def get_by_tag(cls, tag: str, client: RequestClient) -> Optional['Outfit']:
        """Return an outfit by its unique tag.

        This query is always case-insensitive.

        """
        log.debug('%s with tag "%s" requested, generating API query...',
                  cls.__name__, tag)
        query = Query(cls.collection, service_id=client.service_id,
                      alias_lower=tag.lower()).limit(1)
        data = await client.request(query)
        try:
            payload = extract_single(data, cls.collection)
        except NotFoundError:
            return None
        return cls(payload, client=client)

    def leader(self) -> InstanceProxy[OutfitMember]:
        """Return the current leader of the outfit.

        This returns an :class:`auraxium.InstanceProxy`.
        """
        query = Query(
            OutfitMember.collection, service_id=self._client.service_id)
        query.add_term(
            field=OutfitMember.id_field, value=self.data.leader_character_id)
        return InstanceProxy(OutfitMember, query, client=self._client)

    def members(self) -> SequenceProxy[OutfitMember]:
        """Return the members of the outfit.

        This returns a :class:`auraxium.SequenceProxy`.
        """
        query = Query(
            OutfitMember.collection, service_id=self._client.service_id)
        query.add_term(field=self.id_field, value=self.id)
        query.limit(5000)
        return SequenceProxy(OutfitMember, query, client=self._client)

    async def ranks(self) -> List[OutfitRankData]:
        """Return the list of ranks for the outfit."""
        collection: Final[str] = 'outfit_rank'
        query = Query(collection, service_id=self._client.service_id)
        query.add_term(field=self.id_field, value=self.id)
        query.limit(20)
        data = await self._client.request(query)
        payload = extract_payload(data, collection)
        return [OutfitRankData(**c) for c in payload]
