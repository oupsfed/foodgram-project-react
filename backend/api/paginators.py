from rest_framework.pagination import PageNumberPagination


class RecipePagination(PageNumberPagination):
    """Погинатор со страницами и лимитом объектов на странице"""
    page_size_query_param = 'limit'
