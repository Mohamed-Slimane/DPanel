from dpanel.functions import get_option


def context(request):
    status = {
        'mysql_status': get_option('mysql_status', default=False),
        'uwsgi_status': get_option('uwsgi_status', default=False),
        'nginx_status': get_option('nginx_status', default=False),
        'ssl_status': get_option('ssl_status', default=False),
        'certbot_status': get_option('certbot_status', default=False),
        }
    return {
        'status': status,
        'config': {
            'paginator': int(get_option('paginator', '20')),
        }
    }
