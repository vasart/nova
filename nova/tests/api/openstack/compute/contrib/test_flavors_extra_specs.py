# Copyright 2011 University of Southern California
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock
import webob

from nova.api.openstack.compute.contrib import flavorextraspecs
import nova.db
from nova import exception
from nova import test
from nova.tests.api.openstack import fakes
from nova.tests.objects import test_flavor


def return_create_flavor_extra_specs(context, flavor_id, extra_specs):
    return stub_flavor_extra_specs()


def return_flavor_extra_specs(context, flavor_id):
    return stub_flavor_extra_specs()


def return_flavor_extra_specs_item(context, flavor_id, key):
    return {key: stub_flavor_extra_specs()[key]}


def return_empty_flavor_extra_specs(context, flavor_id):
    return {}


def delete_flavor_extra_specs(context, flavor_id, key):
    pass


def stub_flavor_extra_specs():
    specs = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3",
            "key4": "value4",
            "key5": "value5"}
    return specs


class FlavorsExtraSpecsTest(test.TestCase):

    def setUp(self):
        super(FlavorsExtraSpecsTest, self).setUp()
        fakes.stub_out_key_pair_funcs(self.stubs)
        self.controller = flavorextraspecs.FlavorExtraSpecsController()

    def test_index(self):
        flavor = dict(test_flavor.fake_flavor,
                      extra_specs={'key1': 'value1'})

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs')
        with mock.patch('nova.db.flavor_get_by_flavor_id') as mock_get:
            mock_get.return_value = flavor
            res_dict = self.controller.index(req, 1)

        self.assertEqual('value1', res_dict['extra_specs']['key1'])

    def test_index_no_data(self):
        self.stubs.Set(nova.db, 'flavor_extra_specs_get',
                       return_empty_flavor_extra_specs)

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs')
        res_dict = self.controller.index(req, 1)

        self.assertEqual(0, len(res_dict['extra_specs']))

    def test_show(self):
        flavor = dict(test_flavor.fake_flavor,
                      extra_specs={'key5': 'value5'})
        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs' +
                                      '/key5')
        with mock.patch('nova.db.flavor_get_by_flavor_id') as mock_get:
            mock_get.return_value = flavor
            res_dict = self.controller.show(req, 1, 'key5')

        self.assertEqual('value5', res_dict['key5'])

    def test_show_spec_not_found(self):
        self.stubs.Set(nova.db, 'flavor_extra_specs_get',
                       return_empty_flavor_extra_specs)

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs' +
                                      '/key6')
        self.assertRaises(webob.exc.HTTPNotFound, self.controller.show,
                          req, 1, 'key6')

    def test_not_found_because_flavor(self):
        req = fakes.HTTPRequestV3.blank('/flavors/1/extra-specs/key5',
                                        use_admin_context=True)
        with mock.patch('nova.db.flavor_get_by_flavor_id') as mock_get:
            mock_get.side_effect = exception.FlavorNotFound(flavor_id='1')
            self.assertRaises(webob.exc.HTTPNotFound, self.controller.show,
                              req, 1, 'key5')
            self.assertRaises(webob.exc.HTTPNotFound, self.controller.update,
                              req, 1, 'key5', {'key5': 'value5'})
            self.assertRaises(webob.exc.HTTPNotFound, self.controller.delete,
                              req, 1, 'key5')

        req = fakes.HTTPRequestV3.blank('/flavors/1/extra-specs',
                                        use_admin_context=True)
        with mock.patch('nova.db.flavor_get_by_flavor_id') as mock_get:
            mock_get.side_effect = exception.FlavorNotFound(flavor_id='1')
            self.assertRaises(webob.exc.HTTPNotFound, self.controller.create,
                              req, 1, {'extra_specs': {'key5': 'value5'}})

    def test_delete(self):
        flavor = dict(test_flavor.fake_flavor,
                      extra_specs={'key5': 'value5'})
        self.stubs.Set(nova.db, 'flavor_extra_specs_delete',
                       delete_flavor_extra_specs)

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs' +
                                      '/key5', use_admin_context=True)
        with mock.patch('nova.db.flavor_get_by_flavor_id') as mock_get:
            mock_get.return_value = flavor
            self.controller.delete(req, 1, 'key5')

    def test_delete_no_admin(self):
        self.stubs.Set(nova.db, 'flavor_extra_specs_delete',
                       delete_flavor_extra_specs)

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs' +
                                      '/key5')
        self.assertRaises(exception.Forbidden, self.controller.delete,
                          req, 1, 'key 5')

    def test_delete_spec_not_found(self):
        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs' +
                                      '/key6', use_admin_context=True)
        self.assertRaises(webob.exc.HTTPNotFound, self.controller.delete,
                          req, 1, 'key6')

    def test_create(self):
        self.stubs.Set(nova.db,
                       'flavor_extra_specs_update_or_create',
                       return_create_flavor_extra_specs)
        body = {"extra_specs": {"key1": "value1"}}

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs',
                                       use_admin_context=True)
        res_dict = self.controller.create(req, 1, body)

        self.assertEqual('value1', res_dict['extra_specs']['key1'])

    def test_create_no_admin(self):
        self.stubs.Set(nova.db,
                       'flavor_extra_specs_update_or_create',
                       return_create_flavor_extra_specs)
        body = {"extra_specs": {"key1": "value1"}}

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs')
        self.assertRaises(exception.Forbidden, self.controller.create,
                          req, 1, body)

    def _test_create_bad_request(self, body):
        self.stubs.Set(nova.db,
                       'flavor_extra_specs_update_or_create',
                       return_create_flavor_extra_specs)

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs',
                                      use_admin_context=True)
        self.assertRaises(webob.exc.HTTPBadRequest, self.controller.create,
                          req, 1, body)

    def test_create_empty_body(self):
        self._test_create_bad_request('')

    def test_create_non_dict_extra_specs(self):
        self._test_create_bad_request({"extra_specs": "non_dict"})

    def test_create_non_string_value(self):
        self._test_create_bad_request({"extra_specs": {"key1": None}})

    def test_create_zero_length_key(self):
        self._test_create_bad_request({"extra_specs": {"": "value1"}})

    def test_create_long_key(self):
        key = "a" * 256
        self._test_create_bad_request({"extra_specs": {key: "value1"}})

    def test_create_long_value(self):
        value = "a" * 256
        self._test_create_bad_request({"extra_specs": {"key1": value}})

    @mock.patch('nova.db.flavor_extra_specs_update_or_create')
    def test_create_invalid_specs_key(self, mock_flavor_extra_specs):
        invalid_keys = ("key1/", "<key>", "$$akey$", "!akey", "")
        mock_flavor_extra_specs.side_effects = return_create_flavor_extra_specs

        for key in invalid_keys:
            body = {"extra_specs": {key: "value1"}}
            req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs',
                                       use_admin_context=True)
            self.assertRaises(webob.exc.HTTPBadRequest, self.controller.create,
                              req, 1, body)

    @mock.patch('nova.db.flavor_extra_specs_update_or_create')
    def test_create_valid_specs_key(self, mock_flavor_extra_specs):
        valid_keys = ("key1", "month.price", "I_am-a Key", "finance:g2")
        mock_flavor_extra_specs.side_effects = return_create_flavor_extra_specs

        for key in valid_keys:
            body = {"extra_specs": {key: "value1"}}
            req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs',
                                       use_admin_context=True)
            res_dict = self.controller.create(req, 1, body)
            self.assertEqual('value1', res_dict['extra_specs'][key])

    def test_update_item(self):
        self.stubs.Set(nova.db,
                       'flavor_extra_specs_update_or_create',
                       return_create_flavor_extra_specs)
        body = {"key1": "value1"}

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs' +
                                      '/key1', use_admin_context=True)
        res_dict = self.controller.update(req, 1, 'key1', body)

        self.assertEqual('value1', res_dict['key1'])

    def test_update_item_no_admin(self):
        self.stubs.Set(nova.db,
                       'flavor_extra_specs_update_or_create',
                       return_create_flavor_extra_specs)
        body = {"key1": "value1"}

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs' +
                                      '/key1')
        self.assertRaises(exception.Forbidden, self.controller.update,
                          req, 1, 'key1', body)

    def _test_update_item_bad_request(self, body):
        self.stubs.Set(nova.db,
                       'flavor_extra_specs_update_or_create',
                       return_create_flavor_extra_specs)

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs' +
                                      '/key1', use_admin_context=True)
        self.assertRaises(webob.exc.HTTPBadRequest, self.controller.update,
                          req, 1, 'key1', body)

    def test_update_item_empty_body(self):
        self._test_update_item_bad_request('')

    def test_update_item_too_many_keys(self):
        body = {"key1": "value1", "key2": "value2"}
        self._test_update_item_bad_request(body)

    def test_update_item_non_dict_extra_specs(self):
        self._test_update_item_bad_request("non_dict")

    def test_update_item_non_string_value(self):
        self._test_update_item_bad_request({"key1": None})

    def test_update_item_zero_length_key(self):
        self._test_update_item_bad_request({"": "value1"})

    def test_update_item_long_key(self):
        key = "a" * 256
        self._test_update_item_bad_request({key: "value1"})

    def test_update_item_long_value(self):
        value = "a" * 256
        self._test_update_item_bad_request({"key1": value})

    def test_update_item_body_uri_mismatch(self):
        self.stubs.Set(nova.db,
                       'flavor_extra_specs_update_or_create',
                       return_create_flavor_extra_specs)
        body = {"key1": "value1"}

        req = fakes.HTTPRequest.blank('/v2/fake/flavors/1/os-extra_specs/bad',
                                     use_admin_context=True)
        self.assertRaises(webob.exc.HTTPBadRequest, self.controller.update,
                          req, 1, 'bad', body)


class FlavorsExtraSpecsXMLSerializerTest(test.TestCase):
    def test_serializer(self):
        serializer = flavorextraspecs.ExtraSpecsTemplate()
        expected = ("<?xml version='1.0' encoding='UTF-8'?>\n"
                    '<extra_specs><key1>value1</key1></extra_specs>')
        text = serializer.serialize(dict(extra_specs={"key1": "value1"}))
        self.assertEqual(text, expected)

    def test_show_update_serializer(self):
        serializer = flavorextraspecs.ExtraSpecTemplate()
        expected = ("<?xml version='1.0' encoding='UTF-8'?>\n"
                    '<extra_spec key="key1">value1</extra_spec>')
        text = serializer.serialize(dict({"key1": "value1"}))
        self.assertEqual(text, expected)

    def test_serializer_with_colon_tagname(self):
        # Our test object to serialize
        obj = {'extra_specs': {'foo:bar': '999'}}
        serializer = flavorextraspecs.ExtraSpecsTemplate()
        expected_xml = (("<?xml version='1.0' encoding='UTF-8'?>\n"
                    '<extra_specs><foo:bar xmlns:foo="foo">999</foo:bar>'
                    '</extra_specs>'))
        result = serializer.serialize(obj)
        self.assertEqual(expected_xml, result)
