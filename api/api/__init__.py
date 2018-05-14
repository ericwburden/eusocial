from pyramid.config import Configurator


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_jinja2')
    config.include('.db')

    # Enable JWT
    config.include('pyramid_jwt')
    config.include('.security')

    # AuthViews routes
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('register', '/register')

    # OrganizationViews routes
    config.add_route('org_create', '/org/create')
    config.add_route('org_update', '/org/update')
    config.add_route('org_retrieve', '/org/retrieve')
    config.add_route('org_retrieve_all', '/org/retrieve/all')
    config.add_route('org_retrieve_page', '/org/retrieve/page')
    config.add_route('org_retrieve_related', '/org/retrieve/related')
    config.add_route('org_relate_new', '/org/relate/new')
    config.add_route('org_relate_existing', '/org/relate/existing')

    # ProgramViews routes
    config.add_route('prog_create', '/prog/create')
    config.add_route('prog_update', '/prog/update')
    config.add_route('prog_retrieve', '/prog/retrieve')
    config.add_route('prog_retrieve_all', '/prog/retrieve/all')
    config.add_route('prog_retrieve_page', '/prog/retrieve/page')
    config.add_route('prog_retrieve_related', '/prog/retrieve/related')
    config.add_route('prog_add_relationship', '/prog/relate/new')
    config.add_route('prog_add_existing', '/prog/relate/existing')

    # UserViews routes
    config.add_route('usr_approve', '/usr/approve')
    config.add_route('usr_verify', '/usr/verify')
    config.add_route('usr_update', '/usr/update')

    #ClientViews routes
    config.add_route('client_create', '/client/create')

    config.scan('.views')
    return config.make_wsgi_app()
