from rest_framework.pagination import PageNumberPagination


class StandardPagination(PageNumberPagination):
    """Reusable page-number pagination for list endpoints.

    Query params:
      page       — 1-based page index
      page_size  — optional page size (capped by max_page_size)
    """

    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
