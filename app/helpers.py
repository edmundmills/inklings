from typing import List

from django.db import models

from app.models import Tag, User


def create_tags(tags: List[str], object: models.Model):
    for tag_name in tags:
        tag, created = Tag.objects.get_or_create(name=tag_name.lower(), user=object.user)  # type: ignore
        object.tags.add(tag) # type: ignore

