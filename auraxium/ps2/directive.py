from ..census import Query
from ..datatypes import CachableDataType, EnumeratedDataType
from ..misc import LocalizedString
from .image import Image, ImageSet
from .objective import ObjectiveSet
from .reward import Reward, RewardSet


class Directive(CachableDataType):
    """A directive in PlanetSide 2.

    A directive is a requirement that gives progress towards the next directive
    tier.

     """

    def __init__(self, id):
        self.id = id

        # Set default value
        self.description = None
        self._image_id = None
        self._image_set = None
        self.name = None
        self._objective_set_id = None
        self._directive_tier_id = None
        self._directive_tree_id = None
        self.qualify_requirement_id = None

        # Define properties
        @property
        def image(self):
            try:
                return self._image
            except AttributeError:
                self._image = Image.get(id=self._image_id)
                return self._image

        @property
        def image_set(self):
            try:
                return self._image_set
            except AttributeError:
                self._image_set = ImageSet.get(id=self._image_set_id)
                return self._image_set

        @property
        def objective_set(self):
            try:
                return self._objective_set
            except AttributeError:
                self._objective_set = ObjectiveSet.get(
                    id=self._objective_set_id)
                return self._objective_set

        @property
        def directive_tier(self):
            try:
                return self._directive_tier
            except AttributeError:
                self._directive_tier = DirectiveTier.get(
                    id=self._directive_tier_id)
                return self._directive_tier

        @property
        def directive_tree(self):
            try:
                return self._directive_tree
            except AttributeError:
                self._directive_tree = DirectiveTree.get(
                    id=self._directive_tree_id)
                return self._directive_tree

    def _populate(self, data_override=None):
        data = data_override if data_override != None else super().get(self.id)

        # Set attribute values
        self.description = LocalizedString(data['description'])
        self._image_id = data['image_id']
        self._image_set_id = data['image_set_id']
        self.name = LocalizedString(data['name'])
        self.objective_set = data['objective_set_id']
        self.tier = data['directive_tier_id']
        self.tree = data['directive_tree_id']
        self.qualify_requirement_id = data.get('qualify_requirement_id')


class DirectiveTier(EnumeratedDataType):
    """A directive tier.

    Examples include "Carbines: Novice" and "Combat Medic: Master".

    """

    def __init__(self, id):
        self.id = id

        # Set default values
        self.required_for_completion = None
        self.directive_points = None
        self._directive_tree_id = None
        self._image_id = None
        self._image_set_id = None
        self.name = None
        self._reward_set_id = None

        # Define properties
        @property
        def directive_tree(self):
            try:
                return self._directive_tree
            except AttributeError:
                self._directive_tree = DirectiveTree.get(
                    id=self._directive_tree_id)
                return self._directive_tree

        @property
        def image(self):
            try:
                return self._image
            except AttributeError:
                self._image = Image.get(id=self._image_id)
                return self._image

        @property
        def image_set(self):
            try:
                return self._image_set
            except AttributeError:
                self._image_set = ImageSet.get(id=self._image_set_id)
                return self._image_set

        @property
        def reward_set(self):
            try:
                return self._reward_set
            except AttributeError:
                self._reward_set = RewardSet.get(id=self._reward_set_id)
                return self._reward_set

    def _populate(self, data_override=None):
        data = data_override if data_override != None else super().get(self.id)

        # Set attribute values
        self.required_for_completion = data['completion_count']
        self.directive_points = data['directive_points']
        self._directive_tree_id = data['directive_tree_id']
        self._image_id = data['image_id']
        self._image_set_id = data['image_set_id']
        self.name = LocalizedString(data['name'])
        self.reward_set = data.get('reward_set_id')


class DirectiveTree(EnumeratedDataType):
    """A directive tree.

    Directive trees are an entry for a directive category. Examples for
    directive trees from the "Weapons" category would be "Carbines" or
    "Pistols".

    """

    def __init__(self, id):
        self.id = id

        # Set default values
        self._category_id = None
        self.description = None
        self._image_id = None
        self._image_set_id = None
        self.name = None

        # Define properties
        @property
        def category(self):
            try:
                return self._category
            except AttributeError:
                self._category = DirectiveTreeCategory.get(
                    id=self._category_id)
                return self._category

        @property
        def directives(self):
            try:
                return self._directives
            except AttributeError:
                q = Query(type='directive')
                q.add_filter(field='directive_tree_id', value=self.id)
                data = q.get()
                self._directives = Directive.list(
                    [i['directive_id'] for i in data])
                return self._directives

        @property
        def image(self):
            try:
                return self._image
            except AttributeError:
                self._image = Image.get(id=self._image_id)
                return self._image

        @property
        def image_set(self):
            try:
                return self._image_set
            except AttributeError:
                self._image_set = ImageSet.get(id=self._image_set_id)
                return self._image_set

    def _populate(self, data_override=None):
        data = data_override if data_override != None else super().get(self.id)

        # Set attribute values
        self._category_id = data['directive_tree_category_id']
        self.description = LocalizedString(data['description'])
        self._image_id = data['image_id']
        self._image_set_id = data['image_set_id']
        self.name = LocalizedString(data['name'])


class DirectiveTreeCategory(EnumeratedDataType):
    """A category of directive trees.

    Examples for directive tree categories are "Infantry", "Vehicle" or
    "Weapons".

    """

    def __init__(self, id):
        self.id = id

        # Set default values
        self.name = None

        # Define properties
        @property
        def directive_trees(self):
            try:
                return self._directive_trees
            except AttributeError:
                q = Query(type='directive_tree')
                q.add_filter(field='directive_tree_category_id', value=self.id)
                data = q.get()
                self._directive_trees = DirectiveTree.list(
                    [i['directive_tree_id'] for i in data])
                return self._directive_trees

    def _populate(self, data_override=None):
        data = data_override if data_override != None else super().get(self.id)

        # Set attribute values
        self.name = LocalizedString(data.get('name'))
