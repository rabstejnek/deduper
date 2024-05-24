from deduper import dedupe


class TitleDeduper(dedupe.Deduper):
    modules = [
        dedupe.FuzzyDedupe(field="title",threshold=90)
    ]

class IdDeduper(dedupe.Deduper):
    modules = [
        dedupe.UniqueDedupe(fields=["id"])
    ]

class IdAndTitleDeduper(dedupe.Deduper):
    modules = [
        dedupe.UniqueDedupe(fields=["id"]), dedupe.FuzzyDedupe(field="title",threshold=90)
    ]


DEDUPER_MAP = {
    "title_only": TitleDeduper,
    "id_only":IdDeduper,
    "id_and_title":IdAndTitleDeduper,
}

PAGE_SIZE = 10
ANNOTATE_CHOICES = {
    0: "Not reviewed",
    1: "No duplicates found",
}
