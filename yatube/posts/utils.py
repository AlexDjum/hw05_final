from django.core.paginator import Paginator


def paginator(posts, request, post_count):
    paginator = Paginator(posts, post_count)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj
