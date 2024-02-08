# from datetime import datetime, timezone

import pytest

from deduper import dedupe


def compare_set_lists(first_set_list, second_set_list):
    # we don't care about the order of the lists,
    # only that they contain the same elements
    assert len(first_set_list) == len(second_set_list)
    assert all(el in second_set_list for el in first_set_list)


@pytest.mark.django_db()
class TestDedupeModule:
    def test_condense_obj_set_list(self):
        tests = [
            ([{1, 2}, {2, 3}, {3, 4}], [{1, 2, 3, 4}]),
            ([{1, 2}, {3, 4}, {2, 3}], [{1, 2, 3, 4}]),
            ([{1, 2}, {3, 4}], [{1, 2}, {3, 4}]),
        ]
        for test in tests:
            results = dedupe.DedupeModule().condense_obj_set_list(test[0])
            compare_set_lists(results, test[1])

    def test_resolve_obj_set_lists(self):
        # test when join is True
        tests = [
            ([{1, 2}, {3, 4}], [{2, 3}, {5, 6}], [{1, 2, 3, 4}, {5, 6}]),
            ([{1, 2}], [{2, 3}], [{1, 2, 3}]),
        ]
        for test in tests:
            results = dedupe.DedupeModule().join_obj_set_lists(test[0], test[1])
            compare_set_lists(results, test[2])

        # test when join is False
        tests = [
            ([{1, 2}, {3, 4}], [{2, 3}, {5, 6}], [{1, 2}, {3, 4}, {5, 6}]),
            ([{1, 2}], [{2, 3}], [{1, 2, 3}]),
        ]
        for test in tests:
            results = dedupe.DedupeModule().separate_obj_set_lists(test[0], test[1])
            compare_set_lists(results, test[2])


"""
@pytest.mark.django_db()
class TestUniqueTogetherDedupe:
    def test_execute(self, unreviewed_annotation_recipe):
        # each annotation tuple is hero id, pubmed id, wos id, and doi
        reference_tuples = [
            (1, None, "", "doi1"),  # duplicate 1a
            (None, 1, "", "doi1"),  # duplicate 1b
            (2, None, "", ""),  # duplicate 2a
            (2, None, "", ""),  # duplicate 2b
            (1, None, "", ""),
            (1, None, "", "doi2"),
            (2, None, "wos1", ""),
            (2, None, "wos2", ""),
            (3, None, "", ""),
        ]

        reference_args = [iter(_) for _ in zip(*reference_tuples, strict=True)]
        references = reference_recipe.make(
            _quantity=len(reference_tuples),
            hero_id=iter(reference_args[0]),
            pubmed_id=iter(reference_args[1]),
            wos_id=iter(reference_args[2]),
            doi=iter(reference_args[3]),
        )
        annotations = unreviewed_annotation_recipe.make(
            _quantity=len(reference_tuples),
            reference=iter(references),
        )
        results = dedupe.UniqueTogetherDedupe(
            fields=[
                "reference__hero_id",
                "reference__pubmed_id",
                "reference__wos_id",
                "reference__doi",
            ]
        ).execute([set(annotations)])

        expected = [{annotations[0], annotations[1]}, {annotations[2], annotations[3]}]
        compare_set_lists(results, expected)


@pytest.mark.django_db()
class TestFuzzyDedupe:
    def test_execute(self, unreviewed_annotation_recipe):
        reference_titles = [
            "this is a duplicate title",  # duplicate 1a
            "THIS IS A DUPLICATE TITLE!",  # duplicate 1b
            "this is duplicate title",  # duplicate 1c
            "this is unique",
            "another duplicate",  # duplicate 2a
            "and another duplicate",  # duplicate 2b
        ]

        references = reference_recipe.make(
            _quantity=len(reference_titles),
            title=iter(reference_titles),
        )
        annotations = unreviewed_annotation_recipe.make(
            _quantity=len(reference_titles),
            reference=iter(references),
        )
        results = dedupe.FuzzyDedupe(field="reference__title", threshold=90).execute(
            [set(annotations)]
        )

        expected = [
            {annotations[0], annotations[1], annotations[2]},
            {annotations[4], annotations[5]},
        ]
        compare_set_lists(results, expected)


@pytest.mark.django_db()
class TestAnnotationDedupe:
    def test_separate_duplicates(
        self, unreviewed_annotation_recipe, reviewed_annotation_recipe
    ):
        # test to make sure annotations are being scored correctly
        reference_tuples = [
            (1, 1, "wos1", "doi1"),
            (1, 1, "", ""),
            (1, 1, "wos1", "doi1"),
        ]
        reference_args = [iter(_) for _ in zip(*reference_tuples, strict=True)]
        unreviewed_references = reference_recipe.make(
            _quantity=len(reference_tuples),
            hero_id=iter(reference_args[0]),
            pubmed_id=iter(reference_args[1]),
            wos_id=iter(reference_args[2]),
            doi=iter(reference_args[3]),
        )
        unreviewed_annotations = unreviewed_annotation_recipe.make(
            _quantity=len(reference_tuples),
            reference=iter(unreviewed_references),
        )

        reference_args = [iter(_) for _ in zip(*reference_tuples, strict=True)]
        reviewed_references = reference_recipe.make(
            _quantity=len(reference_tuples),
            hero_id=iter(reference_args[0]),
            pubmed_id=iter(reference_args[1]),
            wos_id=iter(reference_args[2]),
            doi=iter(reference_args[3]),
        )
        reviewed_annotations = reviewed_annotation_recipe.make(
            _quantity=len(reference_tuples),
            reference=iter(reviewed_references),
        )
        # manually set last_updated
        annotation_last_updated = [
            datetime(2000, 1, 1, tzinfo=timezone.utc),
            datetime(2000, 1, 1, tzinfo=timezone.utc),
            datetime(2001, 1, 1, tzinfo=timezone.utc),
        ]
        for index, annotation in enumerate(unreviewed_annotations):
            annotation.last_updated = annotation_last_updated[index]
        for index, annotation in enumerate(reviewed_annotations):
            annotation.last_updated = annotation_last_updated[index]

        # reviewed annotations take priority over unreviewed
        annotations = [unreviewed_annotations[0], reviewed_annotations[0]]
        primary, secondaries = dedupe.AnnotationDedupe.separate_duplicates(annotations)
        assert primary == reviewed_annotations[0]
        assert len(secondaries) == 1
        # newer reviewed annotations take priority over older reviewed
        annotations = [reviewed_annotations[0], reviewed_annotations[2]]
        primary, secondaries = dedupe.AnnotationDedupe.separate_duplicates(annotations)
        assert primary == reviewed_annotations[2]
        assert len(secondaries) == 1
        # reviewed annotations that were updated at the same time
        # but have more ids take priority over other reviewed
        annotations = [reviewed_annotations[0], reviewed_annotations[1]]
        primary, secondaries = dedupe.AnnotationDedupe.separate_duplicates(annotations)
        assert primary == reviewed_annotations[0]
        assert len(secondaries) == 1
        # unreviewed annotations with more ids take priority over other unreviewed
        annotations = [unreviewed_annotations[0], unreviewed_annotations[1]]
        primary, secondaries = dedupe.AnnotationDedupe.separate_duplicates(annotations)
        assert primary == unreviewed_annotations[0]
        assert len(secondaries) == 1
        # unreviewed annotations with same number of ids
        # but newer take priority over older unreviewed
        annotations = [unreviewed_annotations[0], unreviewed_annotations[2]]
        primary, secondaries = dedupe.AnnotationDedupe.separate_duplicates(annotations)
        assert primary == unreviewed_annotations[2]
        assert len(secondaries) == 1
        # all together...
        annotations = [*unreviewed_annotations, *reviewed_annotations]
        primary, secondaries = dedupe.AnnotationDedupe.separate_duplicates(annotations)
        assert primary == reviewed_annotations[2]
        assert len(secondaries) == len(annotations) - 1

    def test_deduplicate(self, llr_topic, unreviewed_annotation_recipe):
        # test all cases at once
        reference_tuples = [
            ("this is a title", 1, None, "", "doi1"),  # duplicate 1a
            ("THIS is a title", None, 1, "", "doi1"),  # duplicate 1b
            ("this is title!", None, None, "", "doi1"),  # duplicate 1c
            ("this is a title", 2, None, "", ""),  # duplicate 2a
            ("this  is  a  title", 2, None, "", ""),  # duplicate 2b
            ("this is a title", 1, None, "", ""),
            ("this is a title", 1, None, "", "doi2"),
            ("this is an alternate title", 2, None, "", ""),
            ("this is a title", 2, None, "wos1", ""),
            ("this is a title", 2, None, "wos2", ""),
            ("this is a title", 3, None, "", ""),
        ]
        reference_args = [iter(_) for _ in zip(*reference_tuples, strict=True)]
        references = reference_recipe.make(
            _quantity=len(reference_tuples),
            title=iter(reference_args[0]),
            hero_id=iter(reference_args[1]),
            pubmed_id=iter(reference_args[2]),
            wos_id=iter(reference_args[3]),
            doi=iter(reference_args[4]),
        )
        annotations = unreviewed_annotation_recipe.make(
            _quantity=len(reference_tuples),
            reference=iter(references),
        )
        search_results = search_results_recipe.make()
        annotations[0].searches.add(search_results, search_results_recipe.make())
        annotations[1].searches.add(search_results, search_results_recipe.make())
        annotations[2].searches.add(search_results, search_results_recipe.make())

        assert len(qs := Annotation.objects.filter(topic=llr_topic)) == len(annotations)
        dedupe.AnnotationDedupe.deduplicate(qs)
        assert (
            len(qs := Annotation.objects.filter(topic=llr_topic))
            == len(annotations) - 3
        )

        assert len(qs1 := qs.filter(pk__in=[_.pk for _ in annotations[0:3]])) == 1
        ann = qs1[0]
        assert len(ann.searches.all()) == 4
        ref = ann.reference
        assert ref.hero_id == 1
        assert ref.pubmed_id == 1
        assert ref.wos_id == ""
        assert ref.doi == "doi1"

        assert len(qs2 := qs.filter(pk__in=[_.pk for _ in annotations[3:5]])) == 1
        ann = qs2[0]
        assert len(ann.searches.all()) == 0
        ref = ann.reference
        assert ref.hero_id == 2
        assert ref.pubmed_id is None
        assert ref.wos_id == ""
        assert ref.doi == ""

        """
