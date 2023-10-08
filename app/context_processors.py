from .forms import SearchForm
from .models import NodeModel


def sidebar_data(request):
    if not request.user.is_authenticated:
        return dict()
    return dict(
        search_form=SearchForm(),
        all_memos=request.user.memo_set.all(),
        all_tags=request.user.tag_set.all(),
        link_types=request.user.linktype_set.all(),
    )