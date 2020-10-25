"""Base classes for the Auraxium object model.

These classes define shared functionality required by all object
representations of API data, and defines the basic class hierarchy used
throughout the PlanetSide 2 object model.
"""

import abc
import copy
import dataclasses
import logging
import warnings
from typing import (Any, ClassVar, Dict, List, Optional, Type, TYPE_CHECKING,
                    TypeVar, Union)

import pydantic

from .cache import TLRUCache
from .census import Query
from .errors import PayloadError, NotFoundError
from .request import extract_payload, extract_single
from .types import CensusData

if TYPE_CHECKING:
    # This is only imported during static type checking to resolve the 'Client'
    # forward reference. This avoids a circular import at runtime.
    from .client import Client

__all__ = [
    'Ps2Data',
    'Ps2Object',
    'Cached',
    'Named'
]

CachedT = TypeVar('CachedT', bound='Cached')
NamedT = TypeVar('NamedT', bound='Named')
Ps2DataT = TypeVar('Ps2DataT', bound='Ps2Data')
Ps2ObjectT = TypeVar('Ps2ObjectT', bound='Ps2Object')
log = logging.getLogger('auraxium.ps2')


class Ps2Data(pydantic.BaseModel, metaclass=abc.ABCMeta):
    """Base class for PlanetSide 2 data classes.

    This defines the interface used to populate the data classes, and
    also performs type checking for data class attributes.

    Upon instantiation, a :class:`TypeError` will be raised for any
    attributes that do not match the annotation. This does process
    compound type declarations like :class:`typing.Union` or
    :class:`typing.Optional`.
    """
    # TODO: Update docstring

    class Config:
        """Pydantic model configuration.

        This inner class is used to namespace the pydantic
        configuration options.
        """
        allow_mutation = False


class FallbackMixin:
    """A mixin class used to provide hard-coded fallback instances.

    Some collections are out of date and do not contain all required
    data. This mixin provides a hook to insert this missing data into
    data types while not causing issues if the API ends up being
    updated to include these missing types.
    """

    _fallback: ClassVar[Dict[int, CensusData]]


class Ps2Object(metaclass=abc.ABCMeta):
    """Common base class for all PS2 object representations.

    This requires that subclasses implement the
    :attr:`Ps2Object.collection` and :attr:`Ps2Object.id_field` names,
    which are used to tie the class to its corresponding API
    counterpart.

    Likewise, subclasses must implement the abstract
    :meth:`Ps2Object._build_dataclass`, which is called to convert the
    API response into an instance of the respective subclass of
    :class:`Ps2Data`.
    """

    collection: ClassVar[str] = 'bogus'
    id_field: ClassVar[str] = 'bogus_id'

    def __init__(self, data: CensusData, client: 'Client') -> None:
        """Initialise the object.

        This sets the object's :attr:`~Ps2Object.id` attribute and
        populates the instance using the provided payload.

        Arguments:
            data: The census response dictionary to populate the
                object with.
            client (optional): The client object to use for requests
                performed via this object. Defaults to ``None``.

        """
        id_ = int(data[self.id_field])
        log.debug('Instantiating <%s:%d> using payload: %s',
                  self.__class__.__name__, id_, data)
        self.id = id_  # pylint: disable=invalid-name
        self._client = client
        # Work with a copy of the data to allow pop-ing used keys
        data = copy.copy(data)
        try:
            self.data = self._build_dataclass(data)
        except KeyError as err:
            raise PayloadError(
                f'Unable to populate {self.__class__.__name__} due to a '
                f'missing key: {err.args[0]}', data) from err
        except ValueError as err:
            raise PayloadError(
                f'Unable to instantiate {self.__class__.__name__} instance '
                f'from given payload: {err.args[0]}', data) from err
        if data and (keys := filter(lambda k: '_join_' not in k, data.keys())):
            # Any leftover data (excluding joins) will raise a warning as it
            # points to a mismatch between the object model and the API
            msg = 'keys' if len(list(keys)) > 1 else 'key'
            warnings.warn(
                f'Unexpected {msg} in payload: {list(keys)}\n'
                'Please report this error as it hints at a mismatch between '
                'the auraxium object model and the API.')

    def __eq__(self, value: Any) -> bool:
        if not isinstance(value, self.__class__):
            return False
        return self.id == value.id

    def __hash__(self) -> int:
        return hash((self.__class__, self.id))

    def __repr__(self) -> str:
        """Return the unique string representation of this object.

        This will take the form of ``<Class:id>``, e.g.
        ``<Weapon:108>``.

        Returns:
            A string representing the object.

        """
        return f'<{self.__class__.__name__}:{self.id}>'

    @staticmethod
    @abc.abstractmethod
    def _build_dataclass(data: CensusData) -> Ps2Data:
        """Factory method for the appropriate data class.

        This connects the class initialiser to the appropriate
        :class:`Ps2Data` subclass.

        Arguments:
            data: The API response dictionary to process.

        Returns:
            An instance of the appropriate data class.

        """
        ...

    @classmethod
    async def count(cls: Type[Ps2ObjectT], client: 'Client',
                    **kwargs: Any) -> int:
        """Return the number of items matching the given terms.

        Arguments:
            client: The client through which to perform the request.
            **kwargs: Any number of query filters to apply.

        Returns:
            The number of entries entries.

        """
        service_id = 's:example' if client is None else client.service_id
        query = Query(cls.collection, service_id=service_id, **kwargs)
        result = await client.request(query, verb='count')
        try:
            return int(result['count'])
        except KeyError as err:
            raise PayloadError(
                'Missing key "count" in API response', result) from err
        except ValueError as err:
            raise PayloadError(
                f'Invalid count: {result["count"]}', result) from err

    @classmethod
    async def find(cls: Type[Ps2ObjectT], results: int = 10, *,
                   offset: int = 0, promote_exact: bool = False,
                   check_case: bool = True, client: 'Client',
                   **kwargs: Any) -> List[Ps2ObjectT]:
        """Return a list of entries matching the given terms.

        This returns up to as many entries as indicated by the results
        argument. Note that it may be fewer if not enough matches are
        found.

        Arguments:
            results (optional): The maximum number of results. Defaults
                to ``10``.
            offset (optional): The number of entries to skip. Useful
                for paginated views. Defaults to ``0``.
            promote_exact (optional): If enabled, exact matches to
                non-exact searches will always come first in the return
                list. Defaults to ``False``.
            check_case (optional): Whether to check case when comparing
                strings. Note that case-insensitive searches are much
                more expensive. Defaults to ``True``.
            client: The client through which to perform the request.
            **kwargs: Any number of filters to apply.

        Returns:
            A list of matching entries.

        """
        service_id = 's:example' if client is None else client.service_id
        query = Query(cls.collection, service_id=service_id, **kwargs)
        query.limit(results)
        if offset > 0:
            query.offset(offset)
        query.exact_match_first(promote_exact).case(check_case)
        matches = await client.request(query)
        return [cls(i, client=client) for i in extract_payload(
            matches, cls.collection)]

    @classmethod
    async def get(cls: Type[Ps2ObjectT], client: 'Client',
                  check_case: bool = True, **kwargs: Any
                  ) -> Optional[Ps2ObjectT]:
        """Return the first entry matching the given terms.

        Like :meth:`Ps2Object.get()`, but will only return one item.

        Arguments:
            client: The client through which to perform the request.
            check_case (optional): Whether to check case when comparing
                strings. Note that case-insensitive searches are much
                more expensive. Defaults to ``True``.

        Returns:
            A matching entry, or None if not found.

        """
        results = await cls.find(client=client, results=1,
                                 check_case=check_case, **kwargs)
        if results:
            return results[0]
        return None

    @classmethod
    async def get_by_id(cls: Type[Ps2ObjectT], id_: int, *, client: 'Client'
                        ) -> Optional[Ps2ObjectT]:
        """Retrieve an object by its unique Census ID.

        Arguments:
            id_: The unique ID of the object.
            client: The client through which to perform the request.

        Returns:
            The entry with the matching ID, or None if not found.

        """
        filters: CensusData = {cls.id_field: id_}
        results = await cls.find(client=client, results=1, **filters)

        # Check for FallbackMixin compatibility
        if hasattr(cls, '_fallback'):
            # pylint: disable=no-member
            fallbacks: Dict[int, CensusData] = cls._fallback  # type: ignore
            log.debug('Fallback attribute found for type "%s", checking ID...',
                      cls.__name__)
            if (data := fallbacks.get(id_)) is not None:
                log.debug('Instantiating "%s" with ID %d through local copy',
                          cls.__name__, id_)

                if results:
                    # Log the fact that the local copy is not required
                    log.info('Type "%s" provides a local fallback for ID %d '
                             'despite this type being available on-line',
                             cls.__name__, id_)
                    return results[0]

                # Return a locally instantiated copy
                return cls(data, client=client)

            log.debug('No matching fallback instance found for ID %d', id_)

        elif results:
            # If no fallback value was provided, return the first item found
            # as normal
            return results[0]

        return None

    def query(self) -> Query:
        """Return a query from the current object.

        This is a utility method targeted at advanced users and
        developers. It is generally not required for most use cases.
        """
        return Query(collection=self.collection,
                     service_id=self._client.service_id)


class Cached(Ps2Object, metaclass=abc.ABCMeta):
    """Base class for cacheable data types.

    This generates a cache for each subclass that allows the storage
    and retrieval of objects by ID. This cache may be customised using
    keyword arguments as part of the class definition.

    This customisation is done via two parameters: the cache size and
    the TTU.

    The cache size defines the maximum number of items the cache may
    bold before it will discard the least recently used item for every
    new item added.

    The TTU (time-to-use) will independently discard items that are
    older than the given number of seconds to ensure data does not go
    too far out of date.

    """

    _cache: ClassVar[TLRUCache[int, Any]]

    def __init__(self, data: CensusData, client: 'Client') -> None:
        """Initialise the cached object.

        After initialising this object via the parent class's
        initialiser, this adds the current class to the cache.

        Arguments:
            data: The API response to instantiate the object from.
            client: The client used to retrieve the object.

        """
        super().__init__(data=data, client=client)
        self._cache.add(self.id, self)

    @classmethod
    def __init_subclass__(cls: Type[CachedT], cache_size: int,
                          cache_ttu: float = 0.0) -> None:
        """Initialise a cacheable subclass.

        This sets up the TLRU cache for the given subclass using the
        keyword arguments provided in the class definitions.

        Arguments:
            cache_size: The maximum number of items in the cache. Once
                the cache reaches this number of items, it will delete
                the  least recently used item for every new item added.
            cache_ttu (optional): The time-to-use for cache items. If
                an item is older than  TTU allows, it will be
                re-fetched regardless of how often it is accessed.
                Defaults to ``0.0``.

        """
        super().__init_subclass__()
        log.debug('Setting up cache for %s (size: %d, ttu: %.1f sec.)',
                  cls.__name__, cache_size, cache_ttu)
        cls._cache = TLRUCache(size=cache_size, ttu=cache_ttu,
                               name=f'{cls.__name__}_Cache')

    @classmethod
    def alter_cache(cls, size: int, ttu: Optional[float] = None) -> None:
        """Modify the class cache to use a new size and TTU.

        This will update and clear the cache for the current class.
        This allows customisation of the class depending on your
        use-case.

        Arguments:
            size: The new cache size.
            ttu (optional): The new item TTU. Defaults to ``None``.

        Raises:
            ValueError: Raised if the size is less than 1.

        """
        if size < 1:
            raise ValueError(f'{size} is not a valid cache size')
        cls._cache.clear()
        cls._cache.size = size
        if ttu is not None:
            cls._cache.ttu = ttu

    @classmethod
    def _check_cache(cls: Type[CachedT], id_: int) -> Optional[CachedT]:
        """Attempt to restore an item from the cache.

        If the item cannot be found, ``None`` will be returned instead.

        Arguments:
            id_: The unique identifier the item is cached by.

        Returns:
            An existing instance if found, or ``None`` if the object
            has not been retrieved before or expired.

        """
        return cls._cache.get(id_)

    @classmethod
    async def get_by_id(cls: Type[CachedT], id_: int, *,  # type: ignore
                        client: 'Client') -> Optional[CachedT]:
        """Retrieve an object by by ID.

        This query uses caches and might return an existing instance if
        the object has been recently retrieved.

        Arguments:
            id_: The unique id of the object.
            client: The client through which to perform the request.

        Returns:
            The object matching the given ID or ``None`` if no match
            was found.

        """
        log.debug('<%s:%d> requested', cls.__name__, id_)
        if (instance := cls._cache.get(id_)) is not None:
            log.debug('%r restored from cache', instance)
            return instance  # type: ignore
        log.debug('<%s:%d> not cached, generating API query...',
                  cls.__name__, id_)
        return await super().get_by_id(id_, client=client)  # type: ignore


class Named(Cached, cache_size=0, cache_ttu=0.0, metaclass=abc.ABCMeta):
    """Mix-in class for named objects.

    This extends the functionality provided by :class:`Cached` to also
    cache objects retrieved via :meth:`Named.get_by_name()`. The cache
    will also store the locale used for the request.

    """

    _cache: ClassVar[TLRUCache[Union[int, str], Any]]  # type: ignore

    def __init__(self, *args: Any, locale: Optional[str] = None,
                 **kwargs: Any) -> None:
        """Initialise the named object.

        This sets the object's id attribute and adds it to the cache.

        Arguments:
            locale: The locale under which to cache this object.
            *args: Any extra positional arguments are forwarded to the
                :class:`Cached` class's initialiser.
            **kwargs: Any keyword arguments are forwarded to the
                :class:`Cached` class's initialiser.

        """
        super().__init__(*args, **kwargs)
        if locale is not None:
            key = f'{locale}_{self.name(locale=locale).lower()}'
            self._cache.add(key, self)

    def __repr__(self) -> str:
        """Return the unique string representation of the faction.

        This will take the form of ``<class:id:name>``, e.g.
        ``<Item:2:NC4 Mag-Shot>``.

        Returns:
            A string representing the object.

        """
        return (f'<{self.__class__.__name__}:{self.id}:'
                f'\'{self.name(locale="en")}\'>')

    def __str__(self) -> str:
        """Return the string representation of this object.

        This calls the :meth:``Named.name()`` method for the English
        locale.

        Returns:
            A string representation of the object.

        """
        return self.name(locale='en')

    @classmethod
    async def get_by_name(cls: Type[NamedT], name: str, *, locale: str = 'en',
                          client: 'Client') -> Optional[NamedT]:
        """Retrieve an object by its unique name.

        If the same query has been performed recently, it may be
        restored from cache instead.

        This query is always case-insensitive.

        Arguments:
            name: The name to search for.
            locale (optional): The locale of the search key. Defaults
                to ``'en'``.
            client: The client through which to perform the request.

        Returns:
            The entry with the matching name, or ``None`` if not found.

        """
        key = f'{locale}_{name.lower()}'
        log.debug('%s "%s"[%s] requested', cls.__name__, name, locale)
        if (instance := cls._cache.get(key)) is not None:
            log.debug('%r restored from cache', instance)
            return instance  # type: ignore
        log.debug('%s "%s"[%s] not cached, generating API query...',
                  cls.__name__, name, locale)
        query = Query(cls.collection, service_id=client.service_id)
        query.case(False).add_term(field=f'name.{locale}', value=name)
        payload = await client.request(query)
        try:
            payload = extract_single(payload, cls.collection)
        except NotFoundError:
            return None
        return cls(payload, locale=locale, client=client)

    def name(self, locale: str = 'en') -> str:
        """Return the localised name of the object.

        Some subclasses may not have a localised name field. In these
        cases, the ``locale`` argument will be ignored.

        Arguments:
            locale (optional): The locale identifier to return.
                Defaults to ``'en'``.

        Raises:
            ValueError: Raised if the given locale is unknown.

        Returns:
            The localised name of the object.

        """
        data = self.data
        assert hasattr(data, 'name')
        try:
            return str(getattr(data.name, locale))  # type: ignore
        except AttributeError as err:
            raise ValueError(f'Invalid locale: {locale}') from err


class ImageMixin(Ps2Object, metaclass=abc.ABCMeta):
    """A mixin class for types supporting image access."""

    def image(self) -> str:
        """Return the default image for this type."""
        image_id: int = self.data.image_id  # type: ignore
        return self._image_url(image_id)

    @staticmethod
    def _image_url(image_id: int) -> str:
        """Return the URL for a given image ID."""
        url = 'https://census.daybreakgames.com/files/ps2/images/static/'
        return url + f'{image_id}.png'


@dataclasses.dataclass(frozen=True)
class ImageData:
    """Mixin dataclass for types supporting image access."""

    image_id: Optional[int]
    image_set_id: Optional[int]
    image_path: Optional[str]
