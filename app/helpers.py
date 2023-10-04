from typing import List

from django.db import models
from sentence_transformers import SentenceTransformer

from app.models import Tag, User


def create_tags(tags: List[str], object: models.Model):
    for tag_name in tags:
        tag, created = Tag.objects.get_or_create(name=tag_name.lower(), user=object.user)  # type: ignore
        object.tags.add(tag) # type: ignore


def get_user_tags(user: User):
    return [t.name for t in Tag.objects.filter(user=user).order_by('name')]


def generate_embedding(text):
    model = SentenceTransformer('paraphrase-albert-small-v2')
    embedding = model.encode([text])[0]
    return embedding
