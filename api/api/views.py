import json

from datetime import datetime
from pyramid.response import Response
from bson.json_util import dumps
from pyramid.view import (
    view_config,
    view_defaults,
)
from .models import (
    RequestHandler,
    User,
    AuditLog,
    Password,
    Organization,
    Program,
    Household,
    Client,
    string_to_class
)


@view_defaults(renderer='json', request_method='POST')
class AuthViews:
    """Defines the user authorization endpoints"""

    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    @view_config(route_name='register')
    def register(self):
        request = self.request
        org_id = request.json_body.get('organization')
        new_user = User.from_registration(request, **request.json_body)
        user_org = Organization.from_db_id(request.db, org_id)
        if new_user.in_db(request.db):
            msg = 'Cannot create user %s, already registered' % new_user.email
            response_json = json.dumps({'msg': msg})
            response_code = 409
        elif not user_org:
            msg = 'Organization id %s doesn\'t exist.' % org_id
            response_json = json.dumps({'msg': msg})
            response_code = 404
        else:
            msg = 'Registered user %s with %s' % (new_user.email,
                                                  user_org.name)
            new_id = new_user.save(request.db)
            user_org.api_users.append(new_id)
            user_org.update_db(request.db)
            response_json = json.dumps({
                'msg': msg,
                'access_token': request.create_jwt_token(
                    new_user.email,
                    organization=str(new_user.organization),
                    program=str(new_user.program),
                    role=new_user.role,
                    userid=str(new_user._id),
                    jti=Password.random_string()
                ),
                'id': str(new_id),
                'ver_code': new_user.email_ver_code
            })
            response_code = 200
        response = Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )
        return response

    @view_config(route_name='login')
    def login(self):
        request = self.request
        email = request.json_body['email']
        password = request.json_body['password']
        auth_user = User.one_from_db_search(request.db, email)
        if not auth_user:
            msg = 'User %s, not registered' % email
            response_json = json.dumps({'msg': msg})
            response_code = 400
        else:
            if auth_user.password.check(password):
                msg = 'Authenticated user %s' % email
                response_json = json.dumps({
                    'msg': msg,
                    'access_token': request.create_jwt_token(
                        email,
                        organization=str(auth_user.organization),
                        program=str(auth_user.program),
                        role=auth_user.role,
                        userid=str(auth_user._id),
                        jti=Password.random_string()
                    ),
                    'id': str(auth_user._id)
                })
                response_code = 200
                auth_user.last_login = datetime.utcnow()
                auth_user.update_db(request.db)
                AuditLog.from_registration(auth_user._id,
                                           User.collection,
                                           'login',
                                           auth_user.email,
                                           {}).save(request.db)
            else:
                msg = 'User %s, not authenticated' % email
                response_json = json.dumps({'msg': msg})
                response_code = 401
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )

    @view_config(route_name='logout', permission='logged_in')
    def logout(self):
        """
        Add the users JWT to the blacklist, will need to
        implement blacklisting
        """
        request = self.request
        user = request.jwt_claims['sub']
        jti = request.jwt_claims['jti']
        request.db.jwt_blacklist.insert_one({
            'jti': jti,
            'created': datetime.utcnow()
        })
        msg = 'User %s logged out.' % user
        response_json = json.dumps({'msg': msg})
        response_code = 200
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )


@view_defaults(renderer='json', request_method='POST')
class DefaultViews:
    """
    Defines the default set of CRUD endpoints, called by subclasses for
    specific model objects
    """

    def __init__(self, request):
        self.request = request
        self.logged_in = request.authenticated_userid

    def create(self, model):
        """
        Create a new document in the database from required properties

        Request Format:
        {
            'create': {
                "prop1": "prop1 value",
                "prop2": "prop2 value",
                .
                .
                .
                "propN": "propN value"
            }
        }
        """
        request = self.request
        create_params = request.json_body.get('create')
        model_name = model.__name__
        user = request.jwt_claims.get('sub', 'guest')
        new_obj = model.from_registration(request, **create_params)
        new_obj_name = getattr(new_obj, new_obj.__class__.search_field)
        if new_obj.in_db(request.db):
            msg = '%s %s, already registered' % (model_name, new_obj_name)
            response_json = json.dumps({'msg': msg})
            response_code = 409
        else:
            msg = 'Created %s %s' % (model_name.lower(), new_obj_name)
            response_code = 200
            result = new_obj.save(request.db)
            AuditLog.from_registration(result,
                                       model.collection,
                                       'create',
                                       user,
                                       new_obj.__dict__).save(request.db)
            response_json = json.dumps({'msg': msg, 'id': str(result)})
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )

    def retrieve(self, model):
        """
        Retrieve a document from the database

        Request Format: (json)
        {
            "retrieve": {
                "id": "object id",
                "label": "object label" (Used for response messages)
            }
        }
        """
        request = self.request
        model_name = model.__name__
        request_params = request.json_body
        id = request_params['retrieve']['id']
        label = request_params['retrieve']['label']
        model_obj = model.from_db_id(request.db, id)
        if not model_obj:
            msg = '%s %s doesn\'t exist' % (model_name, label)
            response_json = json.dumps({'msg': msg})
            response_code = 404
        else:
            msg = 'Fetched %s %s' % (model_name.lower(), label)
            response_json = json.dumps({
                'msg': msg,
                'org': model_obj.to_json()
            })
            response_code = 200
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )

    def retrieve_all(self, model):
        """
        Retrieve all documents from the database like the supplied model

        No json needed
        """
        request = self.request
        results = model.all(request.db)
        if not results:
            msg = 'No % recorded' % model.collection
            response_json = json.dumps({'msg': msg})
            response_code = 404
        else:
            msg = 'Fetched all %s' % model.collection
            count = len(results)
            response_json = json.dumps({
                'msg': msg,
                'count': count,
                'results': dumps(results)
            })
            response_code = 200
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )

    def retrieve_page(self, model):
        """
        Retrieve a set of documents from the database like the supplied model,
        in increments defined by the 'page size' (number of documents in the
        set) and 'page number' (the order of the set if the total set of
        documents is divided into subsets containing 'page size' number of
        documents). If the combination of 'page size' and 'page number' would
        cause the database to seek an index outside the total number of
        documents, returns all matching documents, or the last 'page size'
        documents if the number of matching documents is greater than 'page
        size'.

        Request Format:
        {
            "page": {
                "size": n (page_size),
                "number": n (page_number)
            }
        }
        """
        request = self.request
        request_params = request.json_body
        page_size = request_params['page']['size']
        page_number = request_params['page']['number']
        results = model.page(request.db, page_size, page_number)
        if not results:
            msg = 'No %s recorded' % model.collection
            response_json = json.dumps({'msg': msg})
            response_code = 404
        else:
            count = len(results)
            msg = 'Fetched %d %s' % (count, model.collection)
            response_json = json.dumps({
                'msg': msg,
                'count': count,
                'page_number': page_number,
                'results': dumps(results)
            })
            response_code = 200
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )

    def retrieve_related(self, model):
        """
        Retrieve all documents with a relationship to the indicated object from
        an indicated collection.

        Request Format:
        {
            "root": {   (the indicated object)
                "id": 'indicated object id',
                "collection": 'name of the collection of related objects'
            }
        }
        """
        request = self.request
        request_params = request.json_body
        id = request_params['root']['id']
        collection = request_params['root']['collection']
        model_obj = model.from_db_id(request.db, id)
        model_name = model.__name__
        if not model_obj:
            msg = '%s with id %s doesn\'t exist' % (model_name, id)
            response_json = json.dumps({'msg': msg})
            response_code = 404
        else:
            model_obj_rels = model_obj.get_related(request.db, collection)
            count = len(model_obj_rels)
            msg = 'Fetched %d %s related to %s %s' % (count,
                                                      collection,
                                                      model_name,
                                                      id)
            response_json = json.dumps({
                'msg': msg,
                'count': count,
                'results': dumps(model_obj_rels)
            })
            response_code = 200
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )

    def update(self, model):
        """
        Update the fields of a document, indicated by the object's id

        Request Format:
        {
            "update": {
                "id": "id of the document to update",
                "label": "label of the document to update (for messages)",
                "params" : { (updated field values)
                    "prop1": "prop1 value",
                    "prop2": "prop2 value",
                    .
                    .
                    .
                    "propN": "propN value"
                }
            }
        }
        """
        request = self.request
        request_params = request.json_body
        user = request.jwt_claims.get('sub', 'guest')
        update_id = request_params['update']['id']
        update_label = request_params['update']['label']
        update_params = request_params['update']['params']
        model_name = model.__name__
        model_obj = model.from_db_id(request.db, update_id)
        if not model_obj:
            msg = '%s %s doesn\'t exist' % (model_name, update_label)
            response_json = json.dumps({'msg': msg})
            response_code = 404
        else:
            msg = 'Updated %s %s' % (model_name, update_label)
            response_json = json.dumps({'msg': msg})
            response_code = 200

            updates = {}
            for k, v in update_params.items():
                if hasattr(model_obj, k):
                    setattr(model_obj, k, v)
                    updates[k] = v

            model_obj.modified_by = user
            model_obj.modified = datetime.utcnow()
            model_obj.update_db(request.db)
            AuditLog.from_registration(model_obj._id,
                                       model.collection,
                                       'update',
                                       user,
                                       updates).save(request.db)
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )

    def add_relationship_new(self, model):
        """
        Create a new document and add it to the database with a relationship to
        the indicated document. The new document type is passed as a lowercase
        string of its model's name (ex: Organization -> organization).

        Request Format:
        {
            "root": {
                "id": "indicated document id",
                "label": "indicated document label (for messages)",
                "rel_type": "the type of the new related object",
                "rel_params": { (parameters of the new document)
                    "prop1": "prop1 value",
                    "prop2": "prop2 value",
                    .
                    .
                    .
                    "propN": "propN value"
                }
            }
        }
        """
        request = self.request
        request_params = request.json_body
        id = request_params['root']['id']
        label = request_params['root']['label']
        user = request.jwt_claims.get('sub', 'guest')
        model_name = model.__name__
        model_obj = model.from_db_id(request.db, id)  # db
        if not model_obj:
            msg = '%s %s doesn\'t exist' % (model_name, label)
            response_json = json.dumps({'msg': msg})
            response_code = 404
        else:
            rel_type = request_params['root']['rel_type']
            new_obj_class = string_to_class(rel_type)
            new_obj_class_name = new_obj_class.__name__
            new_obj_collection = new_obj_class.collection
            search_field = new_obj_class.search_field
            rels = model_obj.get_related(request.db, new_obj_collection)  # db
            rel_search_fields = [i.get(search_field) for i in rels]
            rel_params = request_params['root']['rel_params']
            if rel_params[search_field] in rel_search_fields:
                msg = '%s, already related' % rel_params[search_field]
                response_json = json.dumps({'msg': msg})
                response_code = 409
            elif not type(getattr(model_obj, new_obj_collection)) == list:
                msg = '%s cannot be added to Organization' % new_obj_class_name
                response_json = json.dumps({'msg': msg})
                response_code = 400
            else:
                msg = 'Added %s to %s' % (rel_params[search_field], model_name)
                new_obj = new_obj_class.from_registration(request,
                                                          **rel_params)
                new_obj.set_id()
                model_obj.relate_to(new_obj)

                model_obj.update_db(request.db)  # db
                updates = {
                    model_name.lower(): id,
                    rel_type: new_obj._id
                }
                AuditLog.from_registration(model_obj._id,
                                           model.collection,
                                           'relate',
                                           user,
                                           updates).save(request.db)

                new_obj.save(request.db)  # db
                AuditLog.from_registration(new_obj._id,
                                           new_obj.collection,
                                           'create',
                                           user,
                                           new_obj.__dict__).save(request.db)
                response_json = json.dumps({
                    'msg': msg,
                    'id': str(new_obj._id)
                })
                response_code = 200
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )

    def add_relationship_existing(self, model):
        """
        Add a relationship with an existing document to the indicated document.

        Request Format:
        {
            "root": {
                "id": "indicated document id",
                "label": "indicated document label (for messages)",
                "rel_type": "the type of the related object",
                "rel_id": "the id of the related object",
            }
        }
        """
        request = self.request
        request_params = request.json_body
        id = request_params['root']['id']
        label = request_params['root']['label']
        user = request.jwt_claims.get('sub', 'guest')
        model_name = model.__name__
        model_obj = model.from_db_id(request.db, id)
        if not model_obj:
            msg = '%s %s doesn\'t exist' % (model_name, label)
            response_json = json.dumps({'msg': msg})
            response_code = 404
        else:
            obj_class = string_to_class(request_params['root']['rel_type'])
            obj_class_name = obj_class.__name__
            obj_collection = obj_class.collection
            obj_id = request_params['root']['rel_id']
            rel_obj = obj_class.from_db_id(request.db, obj_id)
            rel_label = getattr(rel_obj, rel_obj.search_field)
            if not rel_obj:
                msg = 'No %s with id %s' % (obj_class_name, obj_id)
                response_json = json.dumps({'msg': msg})
                response_code = 404
            elif obj_id in getattr(model_obj, obj_collection):
                msg = '%s already related to %s' % (rel_label, label)
                response_json = json.dumps({'msg': msg})
                response_code = 409
            else:
                msg = 'Added %s to %s' % (rel_label, label)
                response_json = json.dumps({'msg': msg})
                response_code = 200

                model_obj.relate_to(rel_obj)
                model_obj.update_db(request.db)  # db
                updates = {
                    model_name.lower(): id,
                    obj_class_name.lower(): rel_obj._id
                }
                AuditLog.from_registration(model_obj._id,
                                           model.collection,
                                           'relate',
                                           user,
                                           updates).save(request.db)

                rel_obj.update_db(request.db)  # db
                AuditLog.from_registration(rel_obj._id,
                                           rel_obj.collection,
                                           'relate',
                                           user,
                                           updates).save(request.db)
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )


class OrganizationViews(DefaultViews):
    model = Organization

    @view_config(route_name='org_create', permission='owner')
    def create(self):
        model = self.__class__.model
        return super(OrganizationViews, self).create(model)

    @view_config(route_name='org_retrieve', permission='org_match')
    def retrieve(self):
        model = self.__class__.model
        return super(OrganizationViews, self).retrieve(model)

    @view_config(route_name='org_retrieve_all', permission='owner')
    def retrieve_all(self):
        model = self.__class__.model
        return super(OrganizationViews, self).retrieve_all(model)

    @view_config(route_name='org_retrieve_page', permission='owner')
    def retrieve_page(self):
        model = self.__class__.model
        return super(OrganizationViews, self).retrieve_page(model)

    @view_config(route_name='org_retrieve_related', permission='org_admin')
    def retrieve_related(self):
        model = self.__class__.model
        return super(OrganizationViews, self).retrieve_related(model)

    @view_config(route_name='org_update', permission='org_admin')
    def update(self):
        model = self.__class__.model
        return super(OrganizationViews, self).update(model)

    @view_config(route_name='org_relate_new', permission='org_admin')
    def add_relationship_new(self):
        model = self.__class__.model
        return super(OrganizationViews, self).add_relationship_new(model)

    @view_config(route_name='org_relate_existing', permission='org_admin')
    def add_relationship_existing(self):
        model = self.__class__.model
        return super(OrganizationViews, self).add_relationship_existing(model)


class ProgramViews(DefaultViews):
    model = Program

    @view_config(route_name='prog_create', permission='org_admin')
    def create(self):
        model = self.__class__.model
        return super(ProgramViews, self).create(model)

    @view_config(route_name='prog_retrieve', permission='prog_match')
    def retrieve(self):
        model = self.__class__.model
        return super(ProgramViews, self).retrieve(model)

    @view_config(route_name='prog_retrieve_all', permission='owner')
    def retrieve_all(self):
        model = self.__class__.model
        return super(ProgramViews, self).retrieve_all(model)

    @view_config(route_name='prog_retrieve_page', permission='owner')
    def retrieve_page(self):
        model = self.__class__.model
        return super(ProgramViews, self).retrieve_page(model)

    @view_config(route_name='prog_retrieve_related', permission='prog_admin')
    def retrieve_related(self):
        model = self.__class__.model
        return super(ProgramViews, self).retrieve_related(model)

    @view_config(route_name='prog_update', permission='prog_admin')
    def update(self):
        model = self.__class__.model
        return super(ProgramViews, self).update(model)

    @view_config(route_name='prog_add_relationship', permission='prog_admin')
    def add_relationship_new(self):
        model = self.__class__.model
        return super(ProgramViews, self).add_relationship_new(model)

    @view_config(route_name='prog_add_existing', permission='prog_admin')
    def add_relationship_existing(self):
        model = self.__class__.model
        return super(ProgramViews, self).add_relationship_existing(model)


class UserViews(DefaultViews):
    model = User

    # @view_config(route_name='usr_retrieve', permission='prog_match')
    # def retrieve(self):
    #     model = self.__class__.model
    #     return super(ProgramViews, self).retrieve(model)

    # @view_config(route_name='usr_retrieve_all', permission='owner')
    # def retrieve_all(self):
    #     model = self.__class__.model
    #     return super(ProgramViews, self).retrieve_all(model)

    # @view_config(route_name='usr_retrieve_page', permission='owner')
    # def retrieve_page(self):
    #     model = self.__class__.model
    #     return super(ProgramViews, self).retrieve_page(model)

    # @view_config(route_name='usr_retrieve_related', permission='prog_admin')
    # def retrieve_related(self):
    #     model = self.__class__.model
    #     return super(ProgramViews, self).retrieve_related(model)

    @view_config(route_name='usr_approve', permission='org_admin')
    def approve(self):
        """
        Approve a user for access, indicated by the User's id

        Request Format:
        {
            "update": {
                "id": "id of the user to approve",
                "email": "label of the user to approve (for messages)",
                "role": "the user's approved role"
            }
        }
        """
        request = self.request
        request_params = request.json_body
        approve_id = request_params['update']['id']
        approve_label = request_params['update']['email']
        approve_role = request_params['update']['role']
        user = request.jwt_claims.get('sub')
        model = self.__class__.model
        model_name = model.__name__
        model_obj = model.from_db_id(request.db, approve_id)
        if not model_obj:
            msg = '%s %s doesn\'t exist' % (model_name, approve_label)
            response_json = json.dumps({'msg': msg})
            response_code = 404
        else:
            msg = 'Approved %s %s' % (model_name, approve_label)
            response_json = json.dumps({'msg': msg})
            response_code = 200

            model_obj.approved_by = user
            model_obj.approved_at = datetime.utcnow()
            model_obj.approved = True
            model_obj.role = approve_role
            model_obj.update_db(request.db)
            AuditLog.from_registration(model_obj._id,
                                       model.collection,
                                       'approved',
                                       user,
                                       {'role': approve_role}).save(request.db)
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )

    @view_config(route_name='usr_verify')
    def verify(self):
        """
        Update the fields of a document, indicated by the object's id

        Request Format:
        {
            "update": {
                "id": "id of the document to update",
                "label": "label of the document to update (for messages)",
                "ver_code": "email verification code"
            }
        }
        """
        request = self.request
        request_params = request.json_body
        verify_id = request_params['update']['id']
        verify_label = request_params['update']['label']
        verify_code = request_params['update']['ver_code']
        model = self.__class__.model
        model_name = model.__name__
        model_obj = model.from_db_id(request.db, verify_id)
        if not model_obj:
            msg = '%s %s doesn\'t exist' % (model_name, verify_label)
            response_json = json.dumps({'msg': msg})
            response_code = 404
        elif model_obj.email_ver_code != verify_code:
            msg = 'Wrong verification code for %s' % verify_label
            response_json = json.dumps({'msg': msg})
            response_code = 406
        else:
            msg = 'Verified %s %s' % (model_name, verify_label)
            response_json = json.dumps({'msg': msg})
            response_code = 200

            model_obj.email_verified = True
            model_obj.modified_by = model_obj.email
            model_obj.modified = datetime.utcnow()
            model_obj.update_db(request.db)
            AuditLog.from_registration(model_obj._id,
                                       model.collection,
                                       'verified',
                                       model_obj.email,
                                       {}).save(request.db)
        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )

    @view_config(route_name='usr_update', permission='user_match')
    def update(self):
        model = self.__class__.model
        return DefaultViews.update(self, model)

    # @view_config(route_name='usr_add_relationship', permission='prog_admin')
    # def add_relationship_new(self):
    #     model = self.__class__.model
    #     return super(ProgramViews, self).add_relationship_new(model)

    # @view_config(route_name='usr_add_existing', permission='prog_admin')
    # def add_relationship_existing(self):
    #     model = self.__class__.model
    #     return super(ProgramViews, self).add_relationship_existing(model)


class HouseholdViews(DefaultViews):
    model = Household

    @view_config(route_name='household_create', permission='prog_admin')
    def create(self):
        """
        Creating a new household requires that either a new Client be created
        as well as the Head of Household, or that an existing client be
        attached as the Head of Household.

        Request Format:
        {
            "hh_type": "new | existing",
            "new": { (if hh_type='new')
                "first_name": "hh first name",
                "last_name": "hh last name",
                "middle_name": "hh middle name",
                "dob" = "hh date of birth"
            },
            "existing": { (if hh_type='existing')
                "hh_id": "hh document id"
            }
        }
        """
        request = self.request
        user = request.jwt_claims.get('sub', 'guest')
        hh_type = request.json_body.get('hh_type')
        hh = None
        msg = None
        if hh_type == 'new':
            new_params = request.json_body.get('new')
            hh = Client.from_registration(request, **new_params)
            hh.household_status = 'head'
            if hh.in_db(request.db):
                msg = 'Client %s, already exists' % hh.full_name
                response_json = json.dumps({'msg': msg})
                response_code = 409
            else:
                result = hh.save(request.db)
                AuditLog.from_registration(
                    result,
                    'clients',
                    'create',
                    user,
                    hh.__dict__
                ).save(request.db)
        elif hh_type == 'existing':
            hh_id = request.json_body.get('existing').get('hh_id')
            hh = Client.from_db_id(request.db, hh_id)
            if hh.household_status == 'head':
                msg = 'Client %s is already head of Household %s' % (
                    hh.full_name,
                    hh.household
                )
                response_json = json.dumps({'msg': msg})
                response_code = 409
            else:
                hh.new_household()
                hh.household_status = 'head'
                AuditLog.from_registration(
                    hh._id,
                    'clients',
                    'relate',
                    user,
                    {
                        'Client': hh._id,
                        'Household': hh.household
                    }
                ).save(request.db)
        else:
            msg = 'Request must include "hh_type" as "new" or "existing"'
            response_json = json.dumps({'msg': msg})
            response_code = 400

        if hh and not msg:
            new_household = Household.from_registration(request, hh)
            result = new_household.save(request.db)
            AuditLog.from_registration(
                result,
                'households',
                'create',
                user,
                new_household.__dict__
            ).save(request.db)
            msg = 'New Household created, HH: %s' % hh.full_name
            response_json = json.dumps({
                'msg': msg,
                'id': str(new_household._id)
            })
            response_code = 200

        return Response(
            text=response_json,
            status_int=response_code,
            content_type='application/json'
        )


class ClientViews(DefaultViews):
    model = Client

    @view_config(route_name='client_create', permission='prog_admin')
    def create(self):
        model = self.__class__.model
        return super(ClientViews, self).create(model)

    @view_config(route_name='client_retrieve', permission='prog_match')
    def retrieve(self):
        model = self.__class__.model
        return super(ClientViews, self).retrieve(model)


class AuditLogViews(DefaultViews):
    @view_config(route_name='test')
    def test(self):
        handler = RequestHandler(AuditLog)
        return handler.retrieve(self.request)
        return AuditLog.search_db(self.request)
