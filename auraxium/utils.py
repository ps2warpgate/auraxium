"""Shared utility methods used throughout Auraxium."""

from typing import Any, Callable, Dict, NamedTuple, Optional, TypeVar

from .types import CensusData

AnyT = TypeVar('AnyT')


class LocaleData(NamedTuple):
    de: str
    en: str
    es: str
    fr: str
    it: str

    @classmethod
    def from_census(cls, data: CensusData) -> 'LocaleData':
        return cls(
            data['de'],
            data['en'],
            data['es'],
            data['fr'],
            data['it'])


# NOTE: The functions below are a dummy implementation for testing and will be
# revisited soon.


def nested_dict_get(dict_: Dict[str, Any], key: str) -> Any:
    """Nested dict key access."""
    nested_keys = key.split('.')
    while nested_keys:
        dict_ = dict_[nested_keys.pop(0)]
    return dict_


def nested_dict_pop(dict_: Dict[str, Any], key: str) -> Any:
    """Nested dict access and removal."""

    def nested_pop(sub_: Dict[str, Any], inner: str, *args: str) -> Any:
        if not args:
            return sub_.pop(inner)
        value = nested_pop(sub_[inner], *args)
        if not sub_[inner]:
            del sub_[inner]
        return value

    outer, *inner = key.split('.')
    if not inner:
        return dict_.pop(outer)
    value = nested_pop(dict_[outer], *inner)
    if not dict_[outer]:
        del dict_[outer]
    return value


def optional(data: CensusData, key: str,
             cast: Callable[[Any], AnyT]) -> Optional[AnyT]:
    raw: Optional[AnyT]
    if (raw := data.get(key)) is not None:
        if raw == 'NULL':
            raw = None
        else:
            raw = cast(raw)
    return raw
