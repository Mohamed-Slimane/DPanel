from dpanel.functions import get_option


def context(request):
    status = {
        'postgres_status': get_option('postgres_status', default=False),
        'mysql_status': get_option('mysql_status', default=False),
        'uwsgi_status': get_option('uwsgi_status', default=False),
        'nginx_status': get_option('nginx_status', default=False),

        'postgres_version': get_option('postgres_version', default=False),
        'mysql_version': get_option('mysql_version', default=False),
        'uwsgi_version': get_option('uwsgi_version', default=False),
        'nginx_version': get_option('nginx_version', default=False),

        'postgres_path': get_option('postgres_path', default=False),
        'mysql_path': get_option('mysql_path', default=False),
        'uwsgi_path': get_option('uwsgi_path', default=False),
        'nginx_path': get_option('nginx_path', default=False),
        }
    return {
        'status': status
    }
