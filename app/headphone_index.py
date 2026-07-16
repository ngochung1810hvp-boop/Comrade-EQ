"""Headphone index built from the measurements/ tree (BUILD_PLAN.md GD1.1).

Layout: measurements/<source>/data/<form>/<name>.csv, with an optional rig
directory level (measurements/<source>/data/<form>/<rig>/<name>.csv) used by
e.g. Rtings and HypetheSonics.
"""

import os
from dataclasses import dataclass

FORMS = ("earbud", "in-ear", "over-ear")


@dataclass(frozen=True)
class HeadphoneEntry:
    name: str
    source: str
    form: str
    rig: str | None
    path: str

    @property
    def meta(self) -> str:
        parts = [self.source, self.form]
        if self.rig:
            parts.append(self.rig)
        return " · ".join(parts)


def build_index(measurements_dir: str) -> list[HeadphoneEntry]:
    entries: list[HeadphoneEntry] = []
    for source in sorted(os.listdir(measurements_dir)):
        data_dir = os.path.join(measurements_dir, source, "data")
        if not os.path.isdir(data_dir):
            continue
        for form in FORMS:
            form_dir = os.path.join(data_dir, form)
            if not os.path.isdir(form_dir):
                continue
            for entry in sorted(os.listdir(form_dir)):
                entry_path = os.path.join(form_dir, entry)
                if entry.endswith(".csv"):
                    entries.append(HeadphoneEntry(
                        name=entry[:-4], source=source, form=form, rig=None,
                        path=entry_path,
                    ))
                elif os.path.isdir(entry_path):  # rig level
                    for fname in sorted(os.listdir(entry_path)):
                        if fname.endswith(".csv"):
                            entries.append(HeadphoneEntry(
                                name=fname[:-4], source=source, form=form,
                                rig=entry, path=os.path.join(entry_path, fname),
                            ))
    entries.sort(key=lambda e: (e.name.lower(), e.source.lower()))
    return entries


def search(entries: list[HeadphoneEntry], query: str, limit: int = 100) -> list[HeadphoneEntry]:
    """Case-insensitive search: every whitespace-separated token must appear
    in the entry's name or meta line."""
    tokens = query.lower().split()
    if not tokens:
        return entries[:limit]
    results = []
    for e in entries:
        haystack = f"{e.name} {e.meta}".lower()
        if all(t in haystack for t in tokens):
            results.append(e)
            if len(results) >= limit:
                break
    return results
