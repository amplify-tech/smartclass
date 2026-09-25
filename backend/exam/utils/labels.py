"""Label resolve/create helpers for the question bank."""

from django.db.models import Q

from exam.models import Label


def resolve_labels(names):
    """Return Label rows for names (case-insensitive), creating missing ones."""
    cleaned = []
    seen = set()
    for raw in names:
        name = str(raw or '').strip()[:64]
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(name)

    if not cleaned:
        return []

    query = Q()
    for name in cleaned:
        query |= Q(name__iexact=name)
    existing = {
        label.name.lower(): label
        for label in Label.objects.filter(query)
    }

    labels = []
    for name in cleaned:
        label = existing.get(name.lower())
        if label is None:
            label = Label.objects.create(name=name)
            existing[name.lower()] = label
        labels.append(label)
    return labels
