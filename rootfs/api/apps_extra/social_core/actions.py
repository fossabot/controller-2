from urllib.parse import quote

from social_core.utils import sanitize_redirect, user_is_authenticated, \
                   user_is_active, partial_pipeline_data, setting_url


def do_auth(backend, redirect_name='next'):
    # Save any defined next value into session
    data = backend.strategy.request_data(merge=False)

    # Save extra data into session.
    for field_name in backend.setting('FIELDS_STORED_IN_SESSION', []):
        if field_name in data:
            backend.strategy.session_set(field_name, data[field_name])
        else:
            backend.strategy.session_set(field_name, None)
    # uri = None
    if redirect_name in data:
        # Check and sanitize a user-defined GET/POST next field value
        redirect_uri = data[redirect_name]
        if backend.setting('SANITIZE_REDIRECTS', True):
            allowed_hosts = backend.setting('ALLOWED_REDIRECT_HOSTS', []) + \
                            [backend.strategy.request_host()]
            redirect_uri = sanitize_redirect(allowed_hosts, redirect_uri)
        backend.strategy.session_set(
            redirect_name,
            redirect_uri or backend.setting('LOGIN_REDIRECT_URL')
        )
    response = backend.start()
    url = response.url.split('?')[1]

    def form2json(form_data):
        from urllib.parse import parse_qs, urlparse
        query = urlparse('?' + form_data).query
        params = parse_qs(query)
        return {key: params[key][0] for key in params}
    from django.core.cache import cache
    cache.set("oidc_key_" + data.get('key', ''), form2json(url).get('state'), 60 * 10)
    return response


def do_complete(backend, login, user=None, redirect_name='next',
                *args, **kwargs):
    data = backend.strategy.request_data()

    is_authenticated = user_is_authenticated(user)
    user = user if is_authenticated else None

    partial = partial_pipeline_data(backend, user, *args, **kwargs)
    if partial:
        user = backend.continue_pipeline(partial)
        # clean partial data after usage
        backend.strategy.clean_partial_pipeline(partial.token)
    else:
        user = backend.complete(user=user, *args, **kwargs)

    # pop redirect value before the session is trashed on login(), but after
    # the pipeline so that the pipeline can change the redirect if needed
    redirect_value = backend.strategy.session_get(redirect_name, '') or \
        data.get(redirect_name, '')

    # check if the output value is something else than a user and just
    # return it to the client
    user_model = backend.strategy.storage.user.user_model()
    if user and not isinstance(user, user_model):
        return user

    if is_authenticated:
        if not user:
            url = setting_url(backend, redirect_value, 'LOGIN_REDIRECT_URL')
        else:
            url = setting_url(backend, redirect_value,
                              'NEW_ASSOCIATION_REDIRECT_URL',
                              'LOGIN_REDIRECT_URL')
    elif user:
        if user_is_active(user):
            # catch is_new/social_user in case login() resets the instance
            is_new = getattr(user, 'is_new', False)
            social_user = user.social_user
            login(backend, user, social_user)
            # store last login backend name in session
            backend.strategy.session_set('social_auth_last_login_backend',
                                         social_user.provider)

            if is_new:
                url = setting_url(backend,
                                  'NEW_USER_REDIRECT_URL',
                                  redirect_value,
                                  'LOGIN_REDIRECT_URL')
            else:
                url = setting_url(backend, redirect_value,
                                  'LOGIN_REDIRECT_URL')
        else:
            if backend.setting('INACTIVE_USER_LOGIN', False):
                social_user = user.social_user
                login(backend, user, social_user)
            url = setting_url(backend, 'INACTIVE_USER_URL', 'LOGIN_ERROR_URL',
                              'LOGIN_URL')
    else:
        url = setting_url(backend, 'LOGIN_ERROR_URL', 'LOGIN_URL')

    if redirect_value and redirect_value != url:
        redirect_value = quote(redirect_value)
        url += ('&' if '?' in url else '?') + \
            '{0}={1}'.format(redirect_name, redirect_value)

    if backend.setting('SANITIZE_REDIRECTS', True):
        allowed_hosts = backend.setting('ALLOWED_REDIRECT_HOSTS', []) + \
                        [backend.strategy.request_host()]
        url = sanitize_redirect(allowed_hosts, url) or \
            backend.setting('LOGIN_REDIRECT_URL')
    response = backend.strategy.redirect(url)
    social_auth = user.social_auth.filter(provider='drycc').\
        order_by('-modified').last()
    from django.core.cache import cache
    cache.set("oidc_state_" + data.get('state'),
              {'token': social_auth.extra_data.get('id_token', 'fail'),
               'username': user.username},
              60 * 10)
    return response
