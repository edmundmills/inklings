from functools import lru_cache
from typing import Optional, Union

import numpy as np
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from pgvector.django import CosineDistance
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from .models import (EmbeddableModel, Link, Memo, NodeModel, Query, Tag,
                     TaggableModel, User)

FILTER_THRESHOLD = 0.7


MODEL = None

def load_model():
    global MODEL
    if MODEL is None:
        MODEL = SentenceTransformer('paraphrase-albert-small-v2')
    return MODEL


def chunk_text(text: str, max_length: int = 512, overlap: int = 50) -> list[str]:
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


def get_similar_objects(model: type[EmbeddableModel], embedding, user: User, 
                        exclude_kwargs: Optional[Union[list[tuple], Q]] = None,
                        limit: Optional[int] = None) -> models.QuerySet:

    queryset = (model.objects.filter(user=user)
                .alias(distance=CosineDistance('embedding', embedding))
                .filter(distance__lt=FILTER_THRESHOLD)
                .order_by('distance'))
    if isinstance(exclude_kwargs, Q):
        queryset = queryset.exclude(exclude_kwargs)
    elif exclude_kwargs is not None:
        for k, v in exclude_kwargs:
            queryset = queryset.exclude(**{k: v})
        
    if limit:
        queryset = queryset[:limit]
        
    return queryset


def get_similar_tags(model: Union[EmbeddableModel, Query], user: User, limit: Optional[int] = None) -> models.QuerySet:
    if isinstance(model, TaggableModel):
        exclude_kwargs = [('pk__in', model.tags.all())]
    elif isinstance(model, Tag):
        exclude_kwargs = [('pk', model.pk)]
    else:
        exclude_kwargs = None
    return get_similar_objects(Tag, model.embedding, user, exclude_kwargs, limit)


def related_node_exclude_kwargs(model: NodeModel, other_model_class: type[NodeModel]) -> Q:
    other_model_content_type = ContentType.objects.get_for_model(other_model_class)
    model_content_type = ContentType.objects.get_for_model(model)

    exclude_conditions = Q()

    exclude_conditions |= Q(source_links__source_content_type=other_model_content_type)
    exclude_conditions |= Q(target_links__target_content_type=other_model_content_type)

    if other_model_class == Link:
        exclude_conditions |= Q(source_content_type=model_content_type, source_object_id=model.pk)
        exclude_conditions |= Q(target_content_type=model_content_type, target_object_id=model.pk)


    if isinstance(model, Link):
        if isinstance(model.source_content_object, other_model_class):
            exclude_conditions |= Q(pk=model.source_object_id)
        if isinstance(model.target_content_object, other_model_class):
            exclude_conditions |= Q(pk=model.target_object_id)
    
    if isinstance(model, other_model_class):
        exclude_conditions |= Q(pk=model.pk)
    
    return exclude_conditions    


def get_similar_nodes_to_node(model: NodeModel, node_class: type[NodeModel], user: User, limit: Optional[int]) -> models.QuerySet:
    exclude_kwargs = related_node_exclude_kwargs(model, node_class)
    return get_similar_objects(node_class, model.embedding, user, exclude_kwargs, limit)


def get_similar_to_tag(tag: Tag, model: type[EmbeddableModel], user: User, limit: Optional[int]) -> models.QuerySet:
    if issubclass(model, TaggableModel):
        exclude_kwargs = [('tags', tag)]
    else:
        exclude_kwargs = None
    return get_similar_objects(model, tag.embedding, user, exclude_kwargs, limit)


def get_similar_nodes(model: Union[EmbeddableModel, Query], node_class: type[NodeModel], user: User, limit: Optional[int]):
    if isinstance(model, Tag):
        return get_similar_to_tag(model, node_class, user, limit)
    elif isinstance(model, NodeModel):
        return get_similar_nodes_to_node(model, node_class, user, limit)
    elif isinstance(model, Query):
        return get_similar_objects(node_class, model.embedding, user, limit=limit)
    else:
        raise NotImplementedError()