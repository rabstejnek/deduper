"""Deduping classes."""
from typing import Any

from rapidfuzz.process import extract
from rapidfuzz.utils import default_process

RenameMe = Any


class DedupeModule:
    """Base module used for deduping."""

    def condense_obj_set_list(self, obj_set_list: list[set[RenameMe]]) -> list[set[RenameMe]]:
        """Condenses a list of sets by joining them where they intersect.

        Args:
            obj_set_list (list[set[RenameMe]]): List of object sets.

        Returns:
            list[set[RenameMe]]: Condensed list of object sets.
        """
        _obj_set_list = obj_set_list.copy()
        remove_list = [False] * len(_obj_set_list)
        for index, obj_set in enumerate(_obj_set_list):
            remaining_obj_set_list = _obj_set_list[index + 1 :]
            for index_diff, other_obj_set in enumerate(remaining_obj_set_list, 1):
                if obj_set & other_obj_set:
                    # join intersecting object sets
                    _obj_set_list[index + index_diff] = obj_set | other_obj_set
                    # if this object set was condensed into another,
                    # then it is safe to remove
                    remove_list[index] = True
                    break
        # filter out removed object sets
        return [
            obj_set
            for obj_set, remove in zip(_obj_set_list, remove_list, strict=True)
            if not remove
        ]

    def join_obj_set_lists(
        self,
        first_obj_set_list: list[set[RenameMe]],
        second_obj_set_list: list[set[RenameMe]],
    ) -> list[set[RenameMe]]:
        """Join object sets between two lists where they intersect.

        If there is any commonality among two or more object sets
        they will be joined, even if the commonality is a degree removed.

        For example, if [{1,2},{3,4}] and [{2,3}] is passed in, the result
        would be [{1,2,3,4}]. Even though {1,2} and {3,4} share no direct
        commonality that would join them, they do share {2,3} from the second
        list, which is why they are joined.

        Args:
            first_obj_set_list (list[set[RenameMe]]): First object set list.
            second_obj_set_list (list[set[RenameMe]]): Second object set list.

        Returns:
            list[set[RenameMe]]: Joined object set list.
        """
        return self.condense_obj_set_list(first_obj_set_list + second_obj_set_list)

    def separate_obj_set_lists(
        self,
        first_obj_set_list: list[set[RenameMe]],
        second_obj_set_list: list[set[RenameMe]],
    ) -> list[set[RenameMe]]:
        """Separate object sets based on how they intersect between two lists.

        If an object set from one list is intersected by two or more object sets
        from the other list, then the non-intersecting elements from that
        first object set can not be included with any of the intersecting elements,
        since theres no way to resolve it (we will refer to this as a "conflict").
        For example, if [{1,2,3,4}] and [{1},{4}] are passed in, the result would be
        [{1},{2,3},{4}]. The reasoning is that {1,2,3,4} is intersected twice,
        by {1} and {4}, and since there is no way to determine if {2,3} should be kept
        with {1} or {4} it is separated.

        If an object set from one list is only intersected by one or fewer object sets
        from the other list, then no separating has to be performed on that object set.
        For example, if [{1,2},{4,5}] and [{2,3}] are passed in, the result would be
        [{1,2,3},{4,5}]. The reasoning is that {1,2} intersects with {2,3} but there are
        no other intersections on either of these object sets, so without a "conflict"
        it is safe to include the non-intersecting elements (ie {1} and {3}) with this
        intersection. And again, there is no intersection with {4,5} from the other list
        so it is free to be included without any separation.


        Args:
            first_obj_set_list (list[set[RenameMe]]): First object set list.
            second_obj_set_list (list[set[RenameMe]]): Second object set list.

        Returns:
            list[set[RenameMe]]: Separated object set list.
        """
        _obj_set_list = []

        # all elements in the first object set list
        all_first_obj_set = {obj for obj_set in first_obj_set_list for obj in obj_set}
        # all elements in the second object set list
        all_second_obj_set = {obj for obj_set in second_obj_set_list for obj in obj_set}
        # all elements that intersect between the first and second object set list
        intersected_obj_set = all_first_obj_set & all_second_obj_set

        first_obj_set_included = [False] * len(first_obj_set_list)
        second_obj_set_included = [False] * len(second_obj_set_list)

        for i, first_obj_set in enumerate(first_obj_set_list):
            for j, second_obj_set in enumerate(second_obj_set_list):
                if intersection := first_obj_set & second_obj_set:
                    # determine what should be included with the intersection
                    split_obj_set = intersection

                    # if the first object set has no other intersection
                    # with any other second object set...
                    if not ((first_obj_set - intersection) & intersected_obj_set):
                        # then the first object set does not need to be separated
                        split_obj_set |= first_obj_set
                        first_obj_set_included[i] = True
                    # if the second object set has no other intersection
                    # with any other first object set...
                    if not ((second_obj_set - intersection) & intersected_obj_set):
                        # then the second object set does not need to be separated
                        split_obj_set |= second_obj_set
                        second_obj_set_included[j] = True

                    _obj_set_list.append(split_obj_set)

        # go through all of the first object sets that were not joined
        # during intersection resolution
        for included, first_obj_set in zip(first_obj_set_included, first_obj_set_list, strict=True):
            # either there was no intersection on this object set,
            # or there were two or more.
            # either way, removing all intersected elements from
            # this object set creates the appropriate set to append.
            non_intersected_obj_set = first_obj_set - intersected_obj_set
            if not included and non_intersected_obj_set:
                _obj_set_list.append(non_intersected_obj_set)
        # go through all of the second object sets that were not joined
        # during intersection resolution
        for included, second_obj_set in zip(
            second_obj_set_included, second_obj_set_list, strict=True
        ):
            # either there was no intersection on this object set,
            # or there were two or more.
            # either way, removing all intersected elements from
            # this object set creates the appropriate set to append.
            non_intersected_obj_set = second_obj_set - intersected_obj_set
            if not included and non_intersected_obj_set:
                _obj_set_list.append(non_intersected_obj_set)

        return _obj_set_list

    def execute(self, obj_set_list: list[set[RenameMe]]) -> list[set[RenameMe]]:
        """Perform deduping on the object set list by splitting up candidate sets.

        Args:
            obj_set_list (list[set[RenameMe]]): Object set list.

        Raises:
            NotImplementedError: This method must implemented on subclasses.

        Returns:
            list[set[RenameMe]]: Deduped object set list.
        """
        raise NotImplementedError

    def really_execute(self, obj_list_list:list[list[RenameMe]])->list[list[RenameMe]]:
        self.obj_list_list = obj_list_list
        index_list_list = [{(i1,i2) for i2 in range(len(obj_list))} for i1, obj_list in enumerate(obj_list_list)]
        index_list_list = self.execute(index_list_list)
        return [[obj_list_list[index[0]][index[1]] for index in index_list] for index_list in index_list_list]

class UniqueDedupe(DedupeModule):
    """Dedupe by matching objects by their fields."""

    def __init__(self, fields: list[str], case_sensitive: bool = True):
        """Create dedupe module.

        Args:
            fields (list[str]): Fields to check on objects.
            case_sensitive (bool): Whether field values should be
                matched in a case sensitive manner.
        """
        self.fields = fields
        self.case_sensitive = case_sensitive

    def get_value(self, obj: RenameMe, field: str) -> Any:
        """Get field value from object.

        The field can follow relations by use of __,
        ie "foo__bar".

        Empty strings are returned as None.

        Args:
            obj (RenameMe): Object to retrieve field from.
            field (str): Field path.

        Returns:
            Any: Field value of object.
        """
        # TODO update comment, make this a method on DedupeModule so it can be overridden
        # easily on each module
        return self.obj_list_list[obj[0]][obj[1]].get(field)

    def get_field_obj_set_list(self, obj_set: set[RenameMe], field: str) -> list[set[RenameMe]]:
        """Get objects grouped by field values.

        Args:
            obj_set (set[RenameMe]): Object set.
            field (str): Field path.

        Returns:
            list[set[RenameMe]]: Object set list.
        """
        mapping = {}
        # map all of the field values to their respective objects
        for obj in obj_set:
            value = self.get_value(obj, field)
            value = value.lower() if isinstance(value, str) and not self.case_sensitive else value
            if value is not None:
                if value not in mapping:
                    mapping[value] = {obj}
                else:
                    mapping[value].add(obj)
        return list(mapping.values())

    def execute(self, obj_set_list: list[set[RenameMe]]) -> list[set[RenameMe]]:
        """Perform deduping on the object set list by splitting up candidate sets.

        Args:
            obj_set_list (list[set[RenameMe]]): Object set list.

        Returns:
            list[set[RenameMe]]: Deduped object set list.
        """
        _obj_set_list = []
        for obj_set in obj_set_list:
            joined_obj_set_list = []
            for field in self.fields:
                field_obj_set_list = self.get_field_obj_set_list(obj_set, field)
                joined_obj_set_list = self.join_obj_set_lists(
                    joined_obj_set_list, field_obj_set_list
                )
            _obj_set_list.extend(joined_obj_set_list)
        return [obj_set for obj_set in _obj_set_list if len(obj_set) > 1]



class UniqueTogetherDedupe(UniqueDedupe):
    """Dedupe by matching objects on their field sets."""

    def execute(self, obj_set_list: list[set[RenameMe]]) -> list[set[RenameMe]]:
        """Perform deduping on the object set list by splitting up candidate sets.

        The UniqueDedupe module is executed first to get a baseline list to filter.

        Args:
            obj_set_list (list[set[RenameMe]]): Object set list.

        Returns:
            list[set[RenameMe]]: Deduped object set list.
        """
        obj_set_list = super().execute(obj_set_list)
        _obj_set_list = []
        for obj_set in obj_set_list:
            separated_obj_set_list = [obj_set]
            for field in self.fields:
                field_obj_set_list = self.get_field_obj_set_list(obj_set, field)
                separated_obj_set_list = self.separate_obj_set_lists(
                    separated_obj_set_list, field_obj_set_list
                )
            _obj_set_list.extend(separated_obj_set_list)
        return [obj_set for obj_set in _obj_set_list if len(obj_set) > 1]


class FuzzyDedupe(DedupeModule):
    """Dedupe by fuzzy text matching on object field values."""

    def __init__(self, field: str, threshold: float):
        """Create dedupe module.

        Args:
            field (str): Object field. Values from this field should be string or None.
            threshold (float): Score cutoff for successful match. Between 0-100.
        """
        self.field = field
        self.threshold = threshold

    def get_str_field(self, obj: RenameMe, field: str) -> str:
        """Get str field value for an object.

        If the value is None, return an empty string.

        Args:
            obj (RenameMe): Object.
            field (str): Field path.

        Returns:
            str: Field value.
        """
        # TODO update comment, refactor so that this uses a DedupeModule function
        return self.obj_list_list[obj[0]][obj[1]].get(field) or ""

    def execute(self, obj_set_list: list[set[RenameMe]]) -> list[set[RenameMe]]:
        """Perform deduping on the object set list by splitting up candidate sets.

        Args:
            obj_set_list (list[set[RenameMe]]): Object set list.

        Returns:
            list[set[RenameMe]]: Deduped object set list.
        """
        _obj_set_list = []
        for obj_set in obj_set_list:
            obj_list = list(obj_set)
            new_obj_set_list = []
            for index, obj in enumerate(obj_list):
                # compare the object with remainder of list.
                # we do this since previous objects in the list
                # have already been compared.
                compare_list = obj_list[index + 1 :]
                results = extract(
                    query=self.get_str_field(obj, self.field),
                    choices=[self.get_str_field(_obj, self.field) for _obj in compare_list],
                    processor=default_process,
                    score_cutoff=self.threshold,
                )
                # make a set with object and other duplicates
                # that score high enough.
                new_obj_set = {obj}
                for _, _, _index in results:
                    new_obj_set.add(obj_list[index + _index + 1])
                new_obj_set_list.append(new_obj_set)

            _obj_set_list.extend(self.condense_obj_set_list(new_obj_set_list))
        return [obj_set for obj_set in _obj_set_list if len(obj_set) > 1]


class Deduper:
    """Deduper."""

    modules: list[DedupeModule]

    @classmethod
    def get_duplicates(cls, qs: list[RenameMe]) -> list[set[RenameMe]]:
        """Get duplicates from a queryset.

        This is done by piping the results from the first dedupe module
        into the next and so on until all of the modules have been run.
        So each module refines the results from the previous one further.

        Args:
            qs (list[RenameMe]): queryset.

        Returns:
            list[set[RenameMe]]: Duplicates.
        """
        obj_set_list = [qs]
        for module in cls.modules:
            obj_set_list = module.really_execute(obj_set_list)
        return obj_set_list

    @classmethod
    def score_obj(cls, obj: RenameMe) -> Any:
        """Score an object.

        This is used to determine the primary object in a set of duplicates.

        Override this method to provide custom scoring.

        Args:
            obj (RenameMe): Object.

        Returns:
            Any: Object score.
        """
        # TODO maybe catch if this is not overridden and just fetch first instead
        # technically it does this, but it runs this method on every obj when its unnecessary
        return 1

    @classmethod
    def separate_duplicates(cls, obj_list: list[RenameMe]) -> tuple[RenameMe, list[RenameMe]]:
        """Determine a primary object among a list of duplicates.

        Args:
            obj_list (list[RenameMe]): Duplicates.

        Returns:
            tuple[RenameMe, list[RenameMe]]: The first element is the primary,
                the second element is a list of secondaries.
        """
        # TODO remove copy, use slicing instead
        _obj_list = obj_list.copy()
        scores = [cls.score_obj(obj) for obj in _obj_list]
        return _obj_list.pop(scores.index(max(scores))), _obj_list

    @classmethod
    def deduplicate(cls, qs: list[RenameMe]) -> list[tuple[RenameMe, list[RenameMe]]]:
        """Deduplicate a queryset.

        Args:
            qs (list[RenameMe]): queryset.
        """
        duplicates = cls.get_duplicates(qs)
        separated_duplicates = []
        for obj_set in duplicates:
            primary_secondary_tuple = cls.separate_duplicates(list(obj_set))
            separated_duplicates.append(primary_secondary_tuple)
        return separated_duplicates
