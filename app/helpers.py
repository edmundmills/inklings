from typing import List, Union

from django.db import models
from pgvector.django import CosineDistance
from sentence_transformers import SentenceTransformer

from .models import Inkling, Link, LinkType, Memo, Query, Tag, User

FILTER_THRESHOLD = 0.7


def get_similar_to_tag(tag: Tag, user: User) -> dict:
    embedding = tag.embedding
    context = dict()
    context['similar_inklings'] = Inkling.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance').exclude(tags=tag)[:5]
    context['similar_tags'] = Tag.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance').exclude(pk=tag.pk)[:10]
    context['similar_memos'] = Memo.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance').exclude(tags=tag)[:3]
    return context


def get_similar_to_query(query: Query, user: User) -> dict:
    embedding = query.embedding
    context = dict()
    context['similar_inklings'] = Inkling.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')[:5]
    context['similar_tags'] = Tag.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')[:10]
    context['similar_memos'] = Memo.objects.filter(user=user).alias(distance=CosineDistance('embedding', embedding)).filter(distance__lt=FILTER_THRESHOLD).order_by('distance')[:3]
    return context


def get_similar_to_memo(memo: Memo, user: User) -> dict:
    embedding = memo.embedding
    context = dict()

    context['similar_inklings'] = (Inkling.objects.filter(user=user)
                                  .alias(distance=CosineDistance('embedding', embedding))
                                  .filter(distance__lt=FILTER_THRESHOLD)
                                  .order_by('distance')[:5])

    context['similar_tags'] = (Tag.objects.filter(user=user)
                              .alias(distance=CosineDistance('embedding', embedding))
                              .filter(distance__lt=FILTER_THRESHOLD)
                              .exclude(memo=memo)
                              .order_by('distance')[:10])

    context['similar_memos'] = (Memo.objects.filter(user=user)
                               .alias(distance=CosineDistance('embedding', embedding))
                               .filter(distance__lt=FILTER_THRESHOLD)
                               .exclude(pk=memo.pk) 
                               .order_by('distance')[:3])

    return context


def get_link_groups(inkling) -> dict[LinkType, list[Link]]:
        # Query for links where the current inkling is the source
    current_to_selected_links = Link.objects.filter(source_inkling=inkling)
    current_to_selected_links = current_to_selected_links.select_related('link_type').order_by('link_type__name')

    # Query for links where the current inkling is the target
    selected_to_current_links = Link.objects.filter(target_inkling=inkling)
    selected_to_current_links = selected_to_current_links.select_related('link_type').order_by('link_type__name')

    # Create a dictionary to group links by LinkType
    link_groups = {}
    
    for link in current_to_selected_links:
        link_type = link.link_type.name
        if link_type not in link_groups:
            link_groups[link_type] = []
        link_groups[link_type].append(link.target_inkling)  # type: ignore
    
    for link in selected_to_current_links:
        link_type = link.link_type.reverse_name
        if link_type not in link_groups:
            link_groups[link_type] = []
        link_groups[link_type].append(link.source_inkling)  # type: ignore
    return link_groups

def get_similar_to_inkling(inkling: Inkling, user: User) -> dict:
    embedding = inkling.embedding
    context = dict()

    context['similar_inklings'] = (Inkling.objects.filter(user=user)
                                  .alias(distance=CosineDistance('embedding', embedding))
                                  .filter(distance__lt=FILTER_THRESHOLD)
                                  .exclude(pk=inkling.pk)
                                  .order_by('distance')[:5])

    context['similar_tags'] = (Tag.objects.filter(user=user)
                              .alias(distance=CosineDistance('embedding', embedding))
                              .filter(distance__lt=FILTER_THRESHOLD)
                              .exclude(inkling=inkling)
                              .order_by('distance')[:10])

    context['similar_memos'] = (Memo.objects.filter(user=user)
                               .alias(distance=CosineDistance('embedding', embedding))
                               .filter(distance__lt=FILTER_THRESHOLD)
                               .exclude(pk=inkling.memo.pk if inkling.memo else None)
                               .order_by('distance')[:3])

    return context


def get_similar(object: Union[Tag, Memo, Inkling, Query], user: User) -> dict:
    similar_fns = {Tag: get_similar_to_tag, Memo: get_similar_to_memo, Inkling: get_similar_to_inkling, Query: get_similar_to_query}
    return similar_fns[type(object)](object, user)


def get_all(user: User) -> dict:
    context = dict()
    context['all_memos'] = Memo.objects.filter(user=user).order_by('-created_at')
    context['all_tags'] =  Tag.objects.filter(user=user).order_by('name')
    return context


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
