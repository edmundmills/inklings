from .forms import InklingForm, SearchForm, URLReferenceForm
from .models import NodeModel


def sidebar_data(request):
    if not request.user.is_authenticated:
        return dict()
    return dict(
        search_form=SearchForm(),
        new_inkling_form=InklingForm(),
        new_reference_form=URLReferenceForm(),
        all_memos=request.user.memo_set.all(),
        all_tags=request.user.tag_set.all(),
        all_references=request.user.reference_set.all(),
        link_types=request.user.linktype_set.all(),
    )