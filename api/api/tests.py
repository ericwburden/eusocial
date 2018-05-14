import unittest
import sys

from pyramid import testing

sys.path.append('../tools')

from test_db import reload_db

reload_db()


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    # def test_my_view(self):
    #     from .views import AuthViews
    #     request = testing.DummyRequest()
    #     info = AuthViews.register(request)
    #     self.assertEqual(info['project'], 'api')


class FunctionalTests(unittest.TestCase):
    @classmethod
    def register_attr(cls, attr_name, attr):
        setattr(cls, attr_name, attr)

    def setUp(self):
        from api import main
        settings = {
            'mongo_uri': 'mongodb://127.0.0.1:27017/test'
        }
        app = main({}, **settings)
        from webtest import TestApp
        self.testapp = TestApp(app)
        if hasattr(self.__class__, 'jwt'):
            self.testapp.authorization = ('Bearer', self.__class__.jwt)


class Suite1OwnerTests(FunctionalTests):
    def test0_owner_login(self):
        res = self.testapp.post_json(
            '/login',
            dict(
                email='admin@eusoci.al',
                password='boogers'
            )
        )
        self.__class__.register_attr('jwt', res.json.get('access_token'))
        self.__class__.register_attr('owner_id', res.json.get('id'))
        self.assertTrue('access_token' in res.json)

    def test1_org_create(self):
        res = self.testapp.post_json(
            '/org/create',
            dict(
                create={
                    'name': 'eusocial',
                    'email': 'admin@eusoci.al',
                    'phone': '9019019901',
                    'address': 'Beale St, Memphis, TN'
                }
            )
        )
        self.__class__.register_attr('org_id', res.json.get('id'))
        self.assertTrue(res.status_int == 200)

    def test2_org_retrieve_all(self):
        res = self.testapp.post_json(
            '/org/retrieve/all', dict()
        )
        self.assertTrue(res.status_int == 200)

    def test3_org_retrieve_page(self):
        res = self.testapp.post_json(
            '/org/retrieve/page',
            dict(
                page={
                    'size': 1,
                    'number': 1
                }
            )
        )
        self.assertTrue(res.status_int == 200)

    def test4_register_org_admin(self):
        res = self.testapp.post_json(
            '/register',
            dict(
                email='org_admin@eusoci.al',
                password='password',
                organization=self.__class__.org_id
            )
        )
        self.__class__.register_attr('org_admin_id', res.json.get('id'))
        self.__class__.register_attr('org_admin_ver_code',
                                     res.json.get('ver_code'))
        self.assertTrue('access_token' in res.json)

    def test5_verify_org_admin(self):
        res = self.testapp.post_json(
            '/usr/verify',
            dict(
                update={
                    'id': self.__class__.org_admin_id,
                    'label': 'org_admin@eusoci.al',
                    'ver_code': self.__class__.org_admin_ver_code
                }
            )
        )
        self.assertTrue(res.status_int == 200)

    def test6_approve_org_admin(self):
        res = self.testapp.post_json(
            '/usr/approve',
            dict(
                update={
                    'id': self.__class__.org_admin_id,
                    'email': 'org_admin@eusoci.al',
                    'role': 'admin'
                }
            )
        )
        self.assertTrue(res.status_int == 200)

    def test7_org_retrieve_related(self):
        res = self.testapp.post_json(
            '/org/retrieve/related',
            dict(
                root={
                    'id': self.__class__.org_id,
                    'collection': 'api_users'
                }
            )
        )
        self.assertTrue(res.status_int == 200)


class Suite2OrgAdminTests(FunctionalTests):
    def test0_owner_login(self):
        res = self.testapp.post_json(
            '/login',
            dict(
                email='admin@eusoci.al',
                password='boogers'
            )
        )
        self.__class__.register_attr('jwt', res.json.get('access_token'))
        self.__class__.register_attr('owner_id', res.json.get('id'))
        self.assertTrue('access_token' in res.json)

    def test1_org_admin_setup_login(self):
        res = self.testapp.post_json(
            '/org/create',
            dict(
                create={
                    'name': 'orgadmin_test_org',
                    'email': 'admin@eusoci.al',
                    'phone': '9019019901',
                    'address': 'Beale St, Memphis, TN'
                }
            )
        )
        self.__class__.register_attr('org_id', res.json.get('id'))

        res = self.testapp.post_json(
            '/register',
            dict(
                email='org_admin2@eusoci.al',
                password='password',
                organization=self.__class__.org_id
            )
        )
        self.__class__.register_attr('org_admin_id', res.json.get('id'))
        self.__class__.register_attr('org_admin_ver_code',
                                     res.json.get('ver_code'))

        self.testapp.post_json(
            '/usr/verify',
            dict(
                update={
                    'id': self.__class__.org_admin_id,
                    'label': 'org_admin2@eusoci.al',
                    'ver_code': self.__class__.org_admin_ver_code
                }
            )
        )

        self.testapp.post_json(
            '/usr/approve',
            dict(
                update={
                    'id': self.__class__.org_admin_id,
                    'email': 'org_admin2    @eusoci.al',
                    'role': 'admin'
                }
            )
        )

        res = self.testapp.post_json(
            '/login',
            dict(
                email='org_admin2@eusoci.al',
                password='password',
            )
        )
        self.__class__.register_attr('jwt', res.json.get('access_token'))
        self.assertTrue('access_token' in res.json)

    def test2_prog_create(self):
        res = self.testapp.post_json(
            '/prog/create',
            dict(
                create={
                    'name': 'test_program1',
                    'service_categories': ['cat1', 'cat2', 'cat3'],
                    'description': 'This is a test of the program system.',
                },
                auth={
                    'organization': self.__class__.org_id
                }
            )
        )
        self.__class__.register_attr('prog_id', res.json.get('id'))
        self.assertTrue(res.status_int == 200)

    def test3_add_new_prog_to_org(self):
        res = self.testapp.post_json(
            '/org/relate/new',
            dict(
                root={
                    'id': self.__class__.org_id,
                    'label': 'orgadmin_test_org',
                    'rel_type': 'program',
                    'rel_params': {
                        'name': 'test_program2',
                        'service_categories': ['cat1', 'cat2', 'cat3'],
                        'description': 'A shorter description in < 80 char.'
                    }
                },
                auth={
                    'organization': self.__class__.org_id
                }
            )
        )
        self.assertTrue(res.status_int == 200)

    def test4_add_existing_prog_to_org(self):
        res = self.testapp.post_json(
            '/org/relate/existing',
            dict(
                root={
                    'id': self.__class__.org_id,
                    'label': 'test_program1',
                    'rel_type': 'program',
                    'rel_id': self.__class__.prog_id
                },
                auth={
                    'organization': self.__class__.org_id
                }
            )
        )
        self.assertTrue(res.status_int == 200)

    def test5_register_prog_admin(self):
        res = self.testapp.post_json(
            '/register',
            dict(
                email='prog_admin@eusoci.al',
                password='monkey',
                organization=self.__class__.org_id
            )
        )
        self.__class__.register_attr('prog_admin_id', res.json.get('id'))
        self.__class__.register_attr('prog_admin_ver_code',
                                     res.json.get('ver_code'))
        self.assertTrue('access_token' in res.json)

    def test6_approve_prog_admin(self):
        res = self.testapp.post_json(
            '/usr/approve',
            dict(
                update={
                    'id': self.__class__.prog_admin_id,
                    'email': 'prog_admin@eusoci.al',
                    'role': 'padmin'
                },
                auth={
                    'organization': self.__class__.org_id
                }
            )
        )
        self.assertTrue(res.status_int == 200)


class Suite3ProgAdminTests(FunctionalTests):
    def test0_owner_login(self):
        res = self.testapp.post_json(
            '/login',
            dict(
                email='admin@eusoci.al',
                password='boogers'
            )
        )
        self.__class__.register_attr('jwt', res.json.get('access_token'))
        self.__class__.register_attr('owner_id', res.json.get('id'))
        self.assertTrue('access_token' in res.json)

    def test1_prog_admin_setup_login(self):
        # Create test organization
        res = self.testapp.post_json(
            '/org/create',
            dict(
                create={
                    'name': 'progadmin_test_org',
                    'email': 'admin@eusoci.al',
                    'phone': '9019019901',
                    'address': 'Beale St, Memphis, TN'
                }
            )
        )
        self.__class__.register_attr('org_id', res.json.get('id'))

        # Add test program to test organization
        res = self.testapp.post_json(
            '/org/relate/new',
            dict(
                root={
                    'id': self.__class__.org_id,
                    'label': 'progadmin_test_org',
                    'rel_type': 'program',
                    'rel_params': {
                        'name': 'test_program3',
                        'service_categories': ['cat1', 'cat2', 'cat3'],
                        'description': 'For testing program admin'
                    }
                }
            )
        )
        self.__class__.register_attr('prog_id', res.json.get('id'))

        # Register test program admin
        res = self.testapp.post_json(
            '/register',
            dict(
                email='prog_admin2@eusoci.al',
                password='password',
                organization=self.__class__.org_id
            )
        )
        self.__class__.register_attr('prog_admin_id', res.json.get('id'))
        self.__class__.register_attr('prog_admin_ver_code',
                                     res.json.get('ver_code'))

        # Verify test program admin email
        self.testapp.post_json(
            '/usr/verify',
            dict(
                update={
                    'id': self.__class__.prog_admin_id,
                    'label': 'prog_admin2@eusoci.al',
                    'ver_code': self.__class__.prog_admin_ver_code
                }
            )
        )

        # Approve test program admin, assign role of padmin
        self.testapp.post_json(
            '/usr/approve',
            dict(
                update={
                    'id': self.__class__.prog_admin_id,
                    'email': 'prog_admin2@eusoci.al',
                    'role': 'padmin'
                }
            )
        )

        # Related test program admin to test program_match
        self.testapp.post_json(
            '/prog/relate/existing',
            dict(
                root={
                    'id': self.__class__.prog_id,
                    'label': 'test_program3',
                    'rel_type': 'api_user',
                    'rel_id': self.__class__.prog_admin_id
                }
            )
        )

        # Login as test program admin
        res = self.testapp.post_json(
            '/login',
            dict(
                email='prog_admin2@eusoci.al',
                password='password',
            )
        )
        self.__class__.register_attr('jwt', res.json.get('access_token'))
        self.assertTrue('access_token' in res.json)

    def test2_register_prog_user(self):
        res = self.testapp.post_json(
            '/register',
            dict(
                email='prog_user@eusoci.al',
                password='monkey',
                organization=self.__class__.org_id
            )
        )
        self.__class__.register_attr('prog_user_id', res.json.get('id'))
        self.__class__.register_attr('prog_user_ver_code',
                                     res.json.get('ver_code'))
        self.assertTrue('access_token' in res.json)

    def test3_update_prog_user(self):
        res = self.testapp.post_json(
            '/usr/update',
            dict(
                update={
                    'id': self.__class__.prog_user_id,
                    'label': 'prog_admin2@eusoci.al',
                    'params': {
                        'role': 'report'
                    }
                },
                auth={
                    'organization': self.__class__.org_id,
                    'program': self.__class__.prog_id
                }
            )
        )
        self.assertTrue(res.status_int == 200)

    def test4_household1_create(self):
        res = self.testapp.post_json(
            '/household/create',
            dict(
                hh_type='new',
                new={
                    'first_name': 'Juan',
                    'last_name': 'Arfull',
                    'middle_name': 'Domingo',
                    'dob': '1965-05-01'
                },
                auth={
                    'organization': self.__class__.org_id,
                    'program': self.__class__.prog_id
                }
            )
        )
        self.__class__.register_attr('house_id', res.json.get('id'))
        self.assertTrue(res.status_int == 200)

    def test5_client_create(self):
        res = self.testapp.post_json(
            '/client/create',
            dict(
                create={
                    'first_name': 'Carl',
                    'last_name': 'arcus',
                    'middle_name': 'mIlFoRd',
                    'dob': '1988-05-04',
                    'household': self.__class__.house_id
                },
                auth={
                    'organization': self.__class__.org_id,
                    'program': self.__class__.prog_id
                }
            )
        )
        self.__class__.register_attr('client_id', res.json.get('id'))
        self.assertTrue(res.status_int == 200)

    # def test6_household2_create(self):
    #     res = self.testapp.post_json(
    #         '/household/create',
    #         dict(
    #             hh_type='existing',
    #             existing={
    #                 'hh_id': self.__class__.client_id
    #             },
    #             auth={
    #                 'organization': self.__class__.org_id,
    #                 'program': self.__class__.prog_id
    #             }
    #         )
    #     )
    #     self.__class__.register_attr('house2_id', res.json.get('id'))
    #     self.assertTrue(res.status_int == 200)
