from functools import lru_cache
from typing import Optional, Union

import numpy as np
from django.contrib.contenttypes.models import ContentType
from django.db import models
from pgvector.django import CosineDistance
from sentence_transformers import SentenceTransformer
from sentence_transformers.util import cos_sim

from .models import (EmbeddableModel, Memo, NodeModel, Query, Tag,
                     TaggableModel, User)

FILTER_THRESHOLD = 0.7


MODEL = None

def load_model():
    global MODEL
    if MODEL is None:
        MODEL = SentenceTransformer('paraphrase-albert-small-v2')
    return MODEL

@lru_cache(maxsize=1000)
def generate_embedding(text):
    model = load_model()
    embedding = model.encode([text])[0]
    return embedding

def sort_by_distance(embedding, objects: list):
    if not objects:
        return []
    to_sort = np.stack([o.embedding for o in objects], axis=0)
    distances = cos_sim(embedding, to_sort).tolist()[0] # type: ignore
    sorted_objects = sorted(zip(objects, distances), key=lambda t: -t[1])
    return [o for o, d in sorted_objects]

def get_similar_objects(model: type[EmbeddableModel], embedding, user: User, 
                        exclude_kwargs: Optional[dict] = None,
                        limit: Optional[int] = None) -> models.QuerySet:

    queryset = (model.objects.filter(user=user)
                .alias(distance=CosineDistance('embedding', embedding))
                .filter(distance__lt=FILTER_THRESHOLD)
                .order_by('distance'))
    if exclude_kwargs is not None:
        for k, v in exclude_kwargs.items():
            queryset = queryset.exclude(**{k: v})
        
    if limit:
        queryset = queryset[:limit]
        
    return queryset


def get_similar_tags(model: Union[EmbeddableModel, Query], user: User, limit: Optional[int] = None) -> models.QuerySet:
    if isinstance(model, TaggableModel):
        exclude_kwargs = {'pk__in': model.tags.all()}
    elif isinstance(model, Tag):
        exclude_kwargs = {'pk': model.pk}
    else:
        exclude_kwargs = dict()
    return get_similar_objects(Tag, model.embedding, user, exclude_kwargs, limit)


def related_node_exclude_kwargs(model: NodeModel, other_model_class: type[NodeModel]) -> dict:
    """
    Returns a dictionary with keyword arguments to exclude relationships between model and other_model.
    """
    other_model_content_type = ContentType.objects.get_for_model(other_model_class)
        
    exclude_kwargs = {
        'source_links__source_content_type': other_model_content_type,
        'target_links__target_content_type': other_model_content_type,
    }
    if isinstance(model, other_model_class):
        exclude_kwargs['pk'] = model.pk
    return exclude_kwargs    


def get_similar_nodes_to_node(model: NodeModel, node_class: type[NodeModel], user: User, limit: Optional[int]) -> models.QuerySet:
    exclude_kwargs = related_node_exclude_kwargs(model, node_class)
    return get_similar_objects(node_class, model.embedding, user, exclude_kwargs, limit)


def get_similar_to_tag(tag: Tag, model: type[EmbeddableModel], user: User, limit: Optional[int]) -> models.QuerySet:
    if issubclass(model, TaggableModel):
        exclude_kwargs = {'tags': tag}
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