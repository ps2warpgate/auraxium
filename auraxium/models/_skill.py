"""Data classes for :mod:`auraxium.ps2.skill`."""

from typing import Optional

from .base import ImageData
from ..types import LocaleData

from .base import RESTPayload

__all__ = [
    'SkillData',
    'SkillCategoryData',
    'SkillLineData',
    'SkillSetData'
]

# pylint: disable=too-few-public-methods


class SkillData(RESTPayload, ImageData):
    """Data class for :class:`auraxium.ps2.skill.Skill`.

    This class mirrors the payload data returned by the API, you may
    use its attributes as keys in filters or queries.
    """

    skill_id: int
    skill_line_id: int
    skill_line_index: int
    skill_points: int
    grant_item_id: Optional[int] = None
    name: LocaleData
    description: Optional[LocaleData] = None


class SkillCategoryData(RESTPayload, ImageData):
    """Data class for :class:`auraxium.ps2.skill.SkillCategory`.

    This class mirrors the payload data returned by the API, you may
    use its attributes as keys in filters or queries.
    """

    skill_category_id: int
    skill_set_id: int
    skill_set_index: int
    skill_points: int
    name: LocaleData
    description: Optional[LocaleData] = None


class SkillLineData(RESTPayload, ImageData):
    """Data class for :class:`auraxium.ps2.skill.SkillLine`.

    This class mirrors the payload data returned by the API, you may
    use its attributes as keys in filters or queries.
    """

    skill_line_id: int
    skill_points: int
    skill_category_id: Optional[int] = None
    skill_category_index: Optional[int] = None
    name: LocaleData
    description: Optional[LocaleData] = None


class SkillSetData(RESTPayload, ImageData):
    """Data class for :class:`auraxium.ps2.skill.SkillSet`.

    This class mirrors the payload data returned by the API, you may
    use its attributes as keys in filters or queries.
    """

    skill_set_id: int
    skill_points: Optional[int] = None
    required_item_id: Optional[int] = None
    name: LocaleData
    description: Optional[LocaleData] = None