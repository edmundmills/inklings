from functools import lru_cache
from typing import Optional, Union

import numpy as np
from django.db import models
from django.db.models import Q
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from .models import EmbeddableModel, NodeModel, Query, Tag, TaggableModel, User

MODEL = None

def load_model():
    global MODEL
    if MODEL is None:
        MODEL = SentenceTransformer('all-MiniLM-L12-v2')
    return MODEL


def chunk_text(text: str, max_length: int = 200, overlap: int = 25) -> list[str]:
    """
    Splits the text into smaller chunks of at most max_length tokens with an overlap.
    """
    words = text.split()
    chunks = []
    position = 0

    while position < len(words):
        end_pos = position + max_length
        chunk = words[position:end_pos]
        chunks.append(' '.join(chunk))
        position = end_pos - overlap

    return chunks


@lru_cache(maxsize=1000)
def generate_embedding(text: str, title: Optional[str] = None) -> np.array: # type: ignore
    model = load_model()
    chunks = chunk_text(text)
    if title:
        chunks += [title]
    embeddings = model.encode(chunks)
    mean_embedding = np.mean(embeddings, axis=0)
    return mean_embedding


def sort_by_distance(embedding, objects: list):
    if not objects:
        return []
    to_sort = np.stack([o.embedding for o in objects], axis=0)
    distances = cos_sim(embedding, to_sort).tolist()[0] # type: ignore
    sorted_objects = sorted(zip(objects, distances), key=lambda t: -t[1])
    return [o for o, d in sorted_objects]


def get_similar_tags(model: Union[EmbeddableModel, Query], user: User, limit: Optional[int] = None) -> models.QuerySet:
    if isinstance(model, TaggableModel):
        exclude_filter = Q(pk__in=model.tags.all())
    elif isinstance(model, Tag):
        exclude_filter = Q(pk=model.pk)
    else:
        exclude_filter = None
    return Tag.get_similar_objects(model.embedding, user, exclude_filter, limit)


def get_similar_nodes(model: Union[EmbeddableModel, Query], node_class: type[NodeModel], user: User, limit: Optional[int], privacy_level: str = 'own'):
    if isinstance(model, Tag):
        exclude_filter = Q(tags=model) if issubclass(node_class, TaggableModel) else None
    elif isinstance(model, NodeModel):
        exclude_filter = model.related_nodes_filter(node_class)
    elif isinstance(model, Query):
        exclude_filter = None
    else:
        raise NotImplementedError()
    return node_class.get_similar_objects(model.embedding, user, exclude_filter, limit, privacy_level=privacy_level)

