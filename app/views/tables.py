from django_filters.views import FilterView
from django_tables2 import SingleTableMixin

from app.filters import (InklingFilter, LinkTypeFilter, MemoFilter,
                         ReferenceFilter)
from app.models import Inkling, LinkType, Memo, Reference
from app.tables import InklingTable, LinkTypeTable, MemoTable, ReferenceTable


class BaseNodeListView(SingleTableMixin, FilterView):
    template_name = "layouts/base_list_view.html"
    
    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

class ReferenceListView(BaseNodeListView):
    model = Reference
    table_class = ReferenceTable
    filterset_class = ReferenceFilter

class InklingListView(BaseNodeListView):
    model = Inkling
    table_class = InklingTable
    filterset_class = InklingFilter

class MemoListView(BaseNodeListView):
    model = Memo
    table_class = MemoTable
    filterset_class = MemoFilter

class LinkTypeListView(SingleTableMixin, FilterView):
    model = LinkType
    table_class = LinkTypeTable
    filterset_class = LinkTypeFilter
    template_name = "layouts/base_list_view.html"

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)
