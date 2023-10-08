from typing import List, Union

from django.db import models
from pgvector.django import CosineDistance
from sentence_transformers import SentenceTransformer

from .models import Inkling, Link, LinkType, Memo, Query, Tag, User

FILTER_THRESHOLD = 0.7


def generate_embedding(text):
    model = SentenceTransformer('paraphrase-albert-small-v2')
    embedding = model.encode([text])[0]
    return embedding


# def get_similar_to_tag(tag: Tag, user: User) -> dict:
#     embedding = tag.embedding
#     context = dict()
#     context['similar_inklings'] = Inkling.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance').exclude(tags=tag)[:5]
#     context['similar_tags'] = Tag.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance').exclude(pk=tag.pk)[:10]
#     context['similar_memos'] = Memo.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance').exclude(tags=tag)[:3]
#     return context


# def get_similar_to_query(query: Query, user: User) -> dict:
#     embedding = query.embedding
#     context = dict()
#     context['similar_inklings'] = Inkling.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')[:5]
#     context['similar_tags'] = Tag.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')[:10]
#     context['similar_memos'] = Memo.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')[:3]
#     return context


# def get_similar_to_memo(memo: Memo, user: User) -> dict:
#     embedding = memo.embedding
#     context = dict()

#     context['similar_inklings'] = (Inkling.objects.filter(user=user)
#                                   .alias(distance=CosineDistance('embedding', embedding))
#                                   .filter(distance__lt=FILTER_THRESHOLD)
#                                   .order_by('distance')[:5])

#     context['similar_tags'] = (Tag.objects.filter(user=user)
#                               .alias(distance=CosineDistance('embedding', embedding))
#                               .filter(distance__lt=FILTER_THRESHOLD)
#                               .exclude(memo=memo)
#                               .order_by('distance')[:10])

#     context['similar_memos'] = (Memo.objects.filter(user=user)
#                                .alias(distance=CosineDistance('embedding', embedding))
#                                .filter(distance__lt=FILTER_THRESHOLD)
#                                .exclude(pk=memo.pk) 
#                                .order_by('distance')[:3])

#     return context



# def get_similar_to_inkling(inkling: Inkling, user: User) -> dict:
#     embedding = inkling.embedding
#     context = dict()

#     context['similar_inklings'] = (Inkling.objects.filter(user=user)
#                                   .alias(distance=CosineDistance('embedding', embedding))
#                                   .filter(distance__lt=FILTER_THRESHOLD)
#                                   .exclude(pk=inkling.pk)
#                                   .order_by('distance')[:5])

#     context['similar_tags'] = (Tag.objects.filter(user=user)
#                               .alias(distance=CosineDistance('embedding', embedding))
#                               .filter(distance__lt=FILTER_THRESHOLD)
#                               .exclude(inkling=inkling)
#                               .order_by('distance')[:10])

#     context['similar_memos'] = (Memo.objects.filter(user=user)
#                                .alias(distance=CosineDistance('embedding', embedding))
#                                .filter(distance__lt=FILTER_THRESHOLD)
#                                .exclude(pk=inkling.memo.pk if inkling.memo else None)
#                                .order_by('distance')[:3])

#     return context


# def get_similar(object: Union[Tag, Memo, Inkling, Query], user: User) -> dict:
#     similar_fns = {Tag: get_similar_to_tag, Memo: get_similar_to_memo, Inkling: get_similar_to_inkling, Query: get_similar_to_query}
#     return similar_fns[type(object)](object, user)




