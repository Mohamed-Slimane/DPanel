from dpanel.functions import get_option


def context(request):
    return {
        'config': {
            'paginator': int(get_option('paginator', '20')),
        }
    }
