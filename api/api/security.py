from datetime import datetime
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import (
    ALL_PERMISSIONS,
    Allow,
    Deny,
    Authenticated,
    DENY_ALL
)


class RootACL(object):
    __acl__ = [
        (Deny, 'token_state:blacklisted', ALL_PERMISSIONS),
        (Allow, 'role:owner', ALL_PERMISSIONS),
        (Allow, Authenticated, 'logged_in'),
        (Allow, 'organization_admin:True', ('org_admin',
                                            'org_match',
                                            'prog_admin',
                                            'prog_match',
                                            'user_match')),
        (Allow, 'organization_match:True', ('org_match',
                                            'prog_match')),
        (Allow, 'program_admin:True', ('prog_admin',
                                       'prog_match',
                                       'user_match')),
        (Allow, 'program_match:True', 'prog_match'),
        (Allow, 'user_match:True', 'user_match'),
        DENY_ALL
    ]

    def __init__(self, request):
        pass


def add_role_principals(userid, request):
    req_params = request.json_body.get('auth', {})
    jwt_claims = request.jwt_claims

    jwt_role = jwt_claims.get('role', 'none')
    jwt_organization = jwt_claims.get('organization', 'none')
    jwt_program = jwt_claims.get('program', 'none')

    # Check if the requested organization and the user's organization match
    request_organization = req_params.get('organization', 'none')
    organization_match = (request_organization != 'none' and
                          request_organization == jwt_organization)
    organization_admin = jwt_role == 'admin' and organization_match

    # Check if the requested program and the user's program matching
    request_program = req_params.get('program', 'none')
    program_match = (organization_match and
                     request_program != 'none' and
                     request_program == jwt_program)
    program_admin = jwt_role == 'padmin' and program_match

    # Check if the requested user is the authenticated users
    request_user = req_params.get('user', 'none')
    user_match = (request_user != 'none' and
                  request_user == jwt_claims.get('userid', 'none'))

    # If there's a JWT, check to be sure it isn't blacklisted
    token_state = 'ok'
    expiry_time = datetime.fromtimestamp(request.jwt_claims.get('exp'))
    if expiry_time and expiry_time > datetime.now():
        jti = request.jwt_claims.get('jti')
        result = request.db.jwt_blacklist.find_one({'jti': jti})
        if result:
            token_state = 'blacklisted'

    principals_dict = {
        'role': jwt_role,
        'organization_match': str(organization_match),
        'organization_admin': str(organization_admin),
        'program_match': str(program_match),
        'program_admin': str(program_admin),
        'user_match': str(user_match),
        'token_state': token_state
    }

    principals_list = [(k + ':' + v) for k, v in principals_dict.items()]
    return principals_list


def includeme(config):

    with open("../keys/development_private_key.pem", 'rb') as key_file:
        pem_private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None,
            backend=default_backend()
        )

    with open("../keys/development_public_key.pem", 'rb') as key_file:
        pem_public_key = serialization.load_pem_public_key(
            key_file.read(),
            backend=default_backend()
        )

    config.set_root_factory(RootACL)
    config.set_jwt_authentication_policy(
        http_header='Authorization',
        auth_type='Bearer',
        private_key=pem_private_key,
        public_key=pem_public_key,
        algorithm='ES256',
        expiration=3000000,
        callback=add_role_principals
    )
    config.set_authorization_policy(ACLAuthorizationPolicy())
