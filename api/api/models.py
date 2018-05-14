import bcrypt
import datetime

from cryptography.fernet import Fernet, MultiFernet
from uuid import uuid4
# from datetime import datetime
from bson.objectid import ObjectId
from bson.binary import Binary


def to_datetime(datetime_string: str):
    if datetime_string:
        return datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S.%f')
    return None


def dict_to_json(target: dict):
    output = {}
    for k, v in target.items():
        # If _id is None, skip it
        if k == '_id' and not v:
            continue
        if isinstance(v, list):
            output[k] = [str(i) for i in v]
        elif isinstance(v, dict):
            output[k] = dict_to_json(v)
        elif isinstance(v, PII):
            output[k] = v.decrypt()
        else:
            output[k] = str(v)
    return output


def dict_to_bson(target: dict):
    output = {}
    for k, v in target.items():
        # If _id is None, skip it
        if k == '_id' and not v:
            continue
        if isinstance(v, list):
            output[k] = [str(i) for i in v]
        elif isinstance(v, dict):
            output[k] = dict_to_bson(v)
        elif isinstance(v, (ObjectId, datetime.datetime, bytes)):
            output[k] = v
        elif isinstance(v, PII):
            output[k] = Binary(v.encrypted)
        else:
            output[k] = str(v)
    return output


def string_to_class(obj_type: str):
    return {
        'api_user': User,
        'program': Program,
        'organization': Organization
    }.get(obj_type, None)


class PII(object):
    key_file = '../keys/fernet.key'

    with open(key_file, 'r') as kf:
        keys = kf.readlines()
    keys = [k.strip().encode('utf-8') for k in keys]
    keys = [Fernet(key) for key in keys]
    keys = MultiFernet(keys)

    def __init__(self, encrypted: bytes):
        if not encrypted:
            self.encrypted = PII.encrypt('None')
        else:
            self.encrypted = encrypted

    def __str__(self) -> str:
        return self.encrypted.decode('utf-8')

    def bytes(self) -> bytes:
        return self.encrypted

    def decrypt(self) -> str:
        keys = self.__class__.keys
        return keys.decrypt(self.encrypted).decode('utf-8')

    @classmethod
    def encrypt(cls, plaintext) -> bytes:
        if not isinstance(plaintext, str):
            plaintext = str(plaintext)
        entry_bytes = plaintext.encode('utf-8')
        encrypted = cls.keys.encrypt(entry_bytes)
        return encrypted


class Password(object):
    def __init__(self, hash_bytes):
        self.hash = hash_bytes

    def __repr__(self):
        return str(self.hash.decode('utf-8'))

    def get_hash(self):
        return self.hash

    def check(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.hash)

    @classmethod
    def from_plaintext(cls, plaintext):
        return cls(cls.hash(plaintext))

    @classmethod
    def from_hashstring(cls, hashstring):
        return cls(hashstring.encode('utf-8'))

    @classmethod
    def hash(cls, plaintext):
        salt = bcrypt.gensalt(14, prefix=b'2a')
        pwd_bytes = plaintext.encode('utf-8')
        pwd_hashed = bcrypt.hashpw(
            pwd_bytes,
            salt
        )
        return pwd_hashed

    @classmethod
    def random_string(cls):
        return str(uuid4()).replace('-', '')

    @classmethod
    def random_hash(cls):
        return Password.hash(Password.get_random_string())


class DatabaseModel(object):
    @property
    def search_field(self):
        """
        The name of the field by which to search the database for this object.
        The field should be unique per object. Example: 'email' for
        User objects.
        """
        raise NotImplementedError

    @property
    def collection(self):
        """
        The name of the collection in which this object will be stored.
        """
        raise NotImplementedError

    # @property
    # def fields(self):
    #     """
    #     A list of the names of fields required to be present in order to
    #     add this object as a document to the database. Other fields may also
    #     be present.
    #     """
    #     raise NotImplementedError

    @classmethod
    def one_from_db_search(cls, db, search_term):
        """Find a matching document in the database, return the result"""
        collection = cls.collection
        search_field = cls.search_field
        result = db[collection].find_one({str(search_field): search_term})
        if result:
            if 'password' in result:
                password_obj = Password.from_hashstring(result['password'])
                result['password'] = password_obj
            return cls(**result)
        else:
            return None

    @classmethod
    def from_db_id(cls, db, id: str):
        collection = cls.collection
        id = ObjectId(id)
        result = db[collection].find_one({'_id': id})
        if result:
            if 'password' in result:
                password_obj = Password.from_hashstring(result['password'])
                result['password'] = password_obj
            return cls(**result)
        else:
            return None

    @classmethod
    def from_registration(cls, **kwargs):
        pass

    @classmethod
    def all(cls, db):
        collection = cls.collection
        result = db[collection].find()
        if result:
            result_list = list(result)
            for i in result_list:
                i['_id'] = str(i['_id'])
            return result_list
        else:
            return None

    @classmethod
    def page(cls, db, page_size, page_number):
        collection = cls.collection
        result = db[collection].find()

        skip_amount = page_size * (page_number - 1)
        offset = skip_amount + page_size
        start_index = skip_amount if skip_amount < result.count() else 0
        end_index = offset if offset < result.count() else result.count()

        if result:
            result_list = list(result[start_index:end_index])
            for i in result_list:
                i['_id'] = str(i['_id'])
            return result_list
        else:
            return None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __json__(self, request):
        return self.to_json()

    def to_json(self):
        return dict_to_json(self.__dict__)

    def to_bson(self):
        return dict_to_bson(self.__dict__)

    def set_id(self):
        self._id = ObjectId()

    def in_db(self, db):
        """Search database for a document matching the search field/term
        """
        search_field = type(self).search_field
        search_term = getattr(self, search_field)
        if type(self).one_from_db_search(db, search_term):
            return True
        else:
            return False

    def save(self, db):
        """Save the document record in the database, return the _id"""
        collection = type(self).collection
        document = self.to_bson()

        result = db[collection].insert_one(document)
        if result.acknowledged:
            return result.inserted_id
        else:
            return None

    def update_db(self, db):
        """Update the database with new object values"""
        collection = type(self).collection
        document = dict_to_bson(self.__dict__)
        document.pop('_id')
        db[collection].update_one(
            {'_id': self._id},
            {'$set': document}
        )

    def relate_to(self, target: 'DatabaseModel'):
        target_doc_type = target.__class__.__name__.lower()
        target_collection = target.__class__.collection

        self_doc_type = self.__class__.__name__.lower()
        self_collection = self.__class__.collection

        if hasattr(self, target_doc_type):  # self has a 1:? relationship
            setattr(self, target_doc_type, target._id)
        elif hasattr(self, target_collection):  # self has a n:? relationship
            getattr(self, target_collection).append(target._id)

        if hasattr(target, self_doc_type):  # target has a ?:1 relationship
            setattr(target, self_doc_type, self._id)
        elif hasattr(target, self_collection):  # target has a ?:n relationship
            getattr(target, self_collection).append(self._id)

        return (self, target)

    def get_related(self, db, collection):
        """Retrieve associated objects from the database"""
        if not getattr(self, collection):
            return []
        related = getattr(self, collection)
        if isinstance(related, list):
            ids = [ObjectId(id) for id in related]
        else:
            ids = [related]
        result = db[collection].find({'_id': {'$in': ids}})
        if result:
            result_list = list(result)
            for i in result_list:
                i['_id'] = str(i['_id'])
            return result_list
        else:
            return []


class DatabaseModelWithPii(DatabaseModel):
    @property
    def pii_fields(self):
        """
        A list of the names of fields considered to contain personally
        identifiable information.
        """
        raise NotImplementedError

    def protect_pii(self):
        for field in self.__class__.pii_fields:
            field_value = getattr(self, field)
            if not isinstance(field_value, PII):
                setattr(self, field, PII.encrypt(field_value))

    def save(self, db):
        self.protect_pii()
        return super().save(db)

    def update_db(self, db):
        self.protect_pii()
        return super().update_db(db)


class AuditLog(DatabaseModel):
    collection = 'audit_logs'
    search_field = '_id'

    def __init__(self,
                 _id,
                 target,
                 collection,
                 action,
                 user,
                 timestamp,
                 document
                 ):
        self._id = _id
        self.target = target
        self.collection = collection
        self.action = action
        self.user = user
        self.timestamp = timestamp
        self.document = document

    @classmethod
    def from_registration(cls, target, collection, action, user, document):
        _id = ObjectId()
        timestamp = datetime.datetime.utcnow()
        return cls(_id, target, collection, action, user, timestamp, document)


class Organization(DatabaseModel):
    collection = 'organizations'
    fields = ['_id',
              'name',
              'email',
              'phone',
              'address',
              'created',
              'created_by',
              'modified',
              'modified_by',
              'active',
              'programs',
              'api_users']
    search_field = 'name'

    def __init__(self,
                 _id,
                 name,
                 email,
                 phone,
                 address,
                 created,
                 created_by,
                 modified=None,
                 modified_by=None,
                 active=True,
                 programs=[],
                 api_users=[]):
        self._id = _id
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self.created = created
        self.created_by = created_by
        self.modified = modified
        self.modified_by = modified_by
        self.active = active
        self.programs = programs
        self.api_users = api_users

    @classmethod
    def from_registration(cls, request, name, email, phone, address):
        _id = ObjectId()
        created = datetime.datetime.utcnow()
        created_by = request.jwt_claims['sub']
        return cls(_id, name, email, phone, address, created, created_by)


class Program(DatabaseModel):
    collection = 'programs'
    fields = ['_id',
              'name',
              'service_categories',
              'description',
              'created',
              'created_by',
              'modified',
              'modified_by',
              'active',
              'api_users']
    search_field = 'name'

    def __init__(self,
                 _id,
                 name,
                 service_categories,
                 description,
                 created,
                 created_by,
                 modified=None,
                 modified_by=None,
                 active=True,
                 api_users=[],
                 organization=None):
        self._id = _id
        self.name = name
        self.service_categories = service_categories
        self.description = description
        self.created = created
        self.created_by = created_by
        self.modified = modified
        self.modified_by = modified_by
        self.active = active
        self.api_users = api_users
        self.organization = organization

    @classmethod
    def from_registration(cls, request, name, service_categories, description):
        _id = ObjectId()
        created = datetime.datetime.utcnow()
        created_by = request.jwt_claims['sub']
        return cls(_id, name, service_categories, description, created,
                   created_by)


class User(DatabaseModel):
    collection = 'api_users'
    fields = {'_id': str,
              'email': str,
              'password': str,
              'role': str,
              'organization': str,
              'program': str,
              'created': to_datetime,
              'last_login': to_datetime,
              'email_verified': bool,
              'email_ver_code': str,
              'approved': bool,
              'approved_by': str,
              'approved_at': to_datetime}
    search_field = 'email'

    def __init__(self,
                 _id,
                 email,
                 password,
                 role,
                 organization,
                 program,
                 created,
                 last_login=None,
                 email_verified=False,
                 email_ver_code=None,
                 approved=False,
                 approved_by=None,
                 approved_at=None,
                 active=True,
                 services=[],
                 modified=None,
                 modified_by=None):
        self._id = _id
        self.email = email
        self.password = password
        self.role = role
        self.organization = organization
        self.program = program
        self.created = created
        self.last_login = last_login
        self.email_verified = email_verified
        self.email_ver_code = email_ver_code
        self.approved = approved
        self.approved_by = approved_by
        self.approved_at = approved_at
        self.active = active
        self.services = services
        self.modified = modified
        self.modified_by = modified_by

    @classmethod
    def from_registration(cls, request, email, password, organization):
        _id = ObjectId()
        role = 'new'
        program = None
        created = str(datetime.datetime.utcnow())
        email_ver_code = Password.random_string()
        password = Password.from_plaintext(password)
        organization = ObjectId(organization)
        return cls(_id, email, password, role, organization, program, created,
                   email_ver_code=email_ver_code)


class Client(DatabaseModelWithPii):
    collection = 'clients'
    search_field = 'full_name'
    pii_fields = [
        'gender',
        'race',
        'ethnicity',
        'email',
        'primary_phone',
        'alt_phone',
        'phys_address',
        'mail_address',
        'ssn'
    ]

    # TODO: Implement more robust checking for self.in_db()

    def __init__(self,
                 _id,
                 first_name,
                 last_name,
                 middle_name,
                 full_name,
                 dob,
                 created,
                 created_by,
                 household_status,
                 modified=None,
                 modified_by=None,
                 gender=None,
                 race=None,
                 ethnicity=None,
                 email=None,
                 primary_phone=None,
                 alt_phone=None,
                 phys_address=None,
                 mail_address=None,
                 ssn=None,
                 household=None,
                 services=[]):
        self._id = _id
        self.first_name = first_name
        self.last_name = last_name
        self.middle_name = middle_name
        self.full_name = full_name
        self.dob = PII(dob)
        self.created = created
        self.created_by = created_by
        self.household_status = household_status
        self.modified = modified
        self.modified_by = modified_by
        self.gender = PII(gender)
        self.race = PII(race)
        self.ethnicity = PII(ethnicity)
        self.email = PII(email)
        self.primary_phone = PII(primary_phone)
        self.alt_phone = PII(alt_phone)
        self.phys_address = PII(phys_address)
        self.mail_address = PII(mail_address)
        self.ssn = PII(ssn)
        self.household = household
        self.services = services

    def new_household(self):
        self.household = ObjectId()
        return self.household

    @classmethod
    def from_registration(cls, request, first_name, last_name,
                          middle_name, dob, household=ObjectId()):
        _id = ObjectId()
        first_name = first_name.title()
        last_name = last_name.title()
        middle_name = middle_name.title()
        full_name = last_name + ', ' + first_name + ' ' + middle_name[0]
        created = datetime.datetime.utcnow()
        created_by = request.jwt_claims['sub']
        household_status = 'member'
        dob = PII.encrypt(dob)
        if not isinstance(household, ObjectId):
            household = ObjectId(household)
        return cls(_id, first_name, last_name, middle_name, full_name, dob,
                   created, created_by, household_status, household=household)


class Household(DatabaseModel):
    collection = 'households'
    search_field = 'hh_name'

    def __init__(self,
                 _id,
                 hh_name,
                 hh_id,
                 created,
                 created_by,
                 modified=None,
                 modified_by=None,
                 active=True,
                 services=[],
                 clients=[]):
        self._id = _id
        self.hh_name = hh_name
        self.hh_id = hh_id
        self.created = created
        self.created_by = created_by
        self.modified = modified
        self.modified_by = modified_by
        self.active = active
        self.services = services
        self.clients = clients

    @classmethod
    def from_registration(cls, request, hh: Client):
        _id = hh.household
        hh_name = hh.full_name
        hh_id = hh._id
        created = datetime.datetime.utcnow()
        created_by = request.jwt_claims['sub']
        clients = [hh._id]
        return cls(_id, hh_name, hh_id, created, created_by, clients=clients)
