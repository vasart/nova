# Copyright (c) 2014 VMware, Inc.
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

import contextlib
import mock

from nova.openstack.common import units
from nova import test
from nova.virt.vmwareapi import ds_util
from nova.virt.vmwareapi import error_util
from nova.virt.vmwareapi import fake


class fake_session(object):
    def __init__(self, ret=None):
        self.ret = ret

    def _get_vim(self):
        return fake.FakeVim()

    def _call_method(self, module, method, *args, **kwargs):
        return self.ret

    def _wait_for_task(self, task_ref):
        task_info = self._call_method('module', "get_dynamic_property",
                        task_ref, "Task", "info")
        if task_info.state == 'success':
            return task_info
        else:
            error_info = 'fake error'
            error = task_info.error
            name = error.fault.__class__.__name__
            raise error_util.get_fault_class(name)(error_info)


class DsUtilTestCase(test.NoDBTestCase):
    def setUp(self):
        super(DsUtilTestCase, self).setUp()
        self.session = fake_session()
        self.flags(api_retry_count=1, group='vmware')
        fake.reset()

    def tearDown(self):
        super(DsUtilTestCase, self).tearDown()
        fake.reset()

    def test_build_datastore_path(self):
        path = ds_util.build_datastore_path('ds', 'folder')
        self.assertEqual('[ds] folder', path)
        path = ds_util.build_datastore_path('ds', 'folder/file')
        self.assertEqual('[ds] folder/file', path)

    def test_file_delete(self):
        def fake_call_method(module, method, *args, **kwargs):
            self.assertEqual('DeleteDatastoreFile_Task', method)
            name = kwargs.get('name')
            self.assertEqual('fake-datastore-path', name)
            datacenter = kwargs.get('datacenter')
            self.assertEqual('fake-dc-ref', datacenter)
            return 'fake_delete_task'

        with contextlib.nested(
            mock.patch.object(self.session, '_wait_for_task'),
            mock.patch.object(self.session, '_call_method',
                              fake_call_method)
        ) as (_wait_for_task, _call_method):
            ds_util.file_delete(self.session,
                                'fake-datastore-path', 'fake-dc-ref')
            _wait_for_task.assert_has_calls([
                   mock.call('fake_delete_task')])

    def test_file_move(self):
        def fake_call_method(module, method, *args, **kwargs):
            self.assertEqual('MoveDatastoreFile_Task', method)
            sourceName = kwargs.get('sourceName')
            self.assertEqual('[ds] tmp/src', sourceName)
            destinationName = kwargs.get('destinationName')
            self.assertEqual('[ds] base/dst', destinationName)
            sourceDatacenter = kwargs.get('sourceDatacenter')
            self.assertEqual('fake-dc-ref', sourceDatacenter)
            destinationDatacenter = kwargs.get('destinationDatacenter')
            self.assertEqual('fake-dc-ref', destinationDatacenter)
            return 'fake_move_task'

        with contextlib.nested(
            mock.patch.object(self.session, '_wait_for_task'),
            mock.patch.object(self.session, '_call_method',
                              fake_call_method)
        ) as (_wait_for_task, _call_method):
            ds_util.file_move(self.session,
                              'fake-dc-ref', '[ds] tmp/src', '[ds] base/dst')
            _wait_for_task.assert_has_calls([
                   mock.call('fake_move_task')])

    def test_mkdir(self):
        def fake_call_method(module, method, *args, **kwargs):
            self.assertEqual('MakeDirectory', method)
            name = kwargs.get('name')
            self.assertEqual('fake-path', name)
            datacenter = kwargs.get('datacenter')
            self.assertEqual('fake-dc-ref', datacenter)
            createParentDirectories = kwargs.get('createParentDirectories')
            self.assertTrue(createParentDirectories)

        with mock.patch.object(self.session, '_call_method',
                               fake_call_method):
            ds_util.mkdir(self.session, 'fake-path', 'fake-dc-ref')

    def test_file_exists(self):
        def fake_call_method(module, method, *args, **kwargs):
            if method == 'SearchDatastore_Task':
                ds_browser = args[0]
                self.assertEqual('fake-browser', ds_browser)
                datastorePath = kwargs.get('datastorePath')
                self.assertEqual('fake-path', datastorePath)
                return 'fake_exists_task'
            elif method == 'get_dynamic_property':
                info = fake.DataObject()
                info.name = 'search_task'
                info.state = 'success'
                result = fake.DataObject()
                result.path = 'fake-path'
                matched = fake.DataObject()
                matched.path = 'fake-file'
                result.file = [matched]
                info.result = result
                return info
            # Should never get here
            self.fail()

        with mock.patch.object(self.session, '_call_method',
                               fake_call_method):
            file_exists = ds_util.file_exists(self.session,
                    'fake-browser', 'fake-path', 'fake-file')
            self.assertTrue(file_exists)

    def test_file_exists_fails(self):
        def fake_call_method(module, method, *args, **kwargs):
            if method == 'SearchDatastore_Task':
                return 'fake_exists_task'
            elif method == 'get_dynamic_property':
                info = fake.DataObject()
                info.name = 'search_task'
                info.state = 'error'
                error = fake.DataObject()
                error.localizedMessage = "Error message"
                error.fault = fake.FileNotFound()
                info.error = error
                return info
            # Should never get here
            self.fail()

        with mock.patch.object(self.session, '_call_method',
                               fake_call_method):
            file_exists = ds_util.file_exists(self.session,
                    'fake-browser', 'fake-path', 'fake-file')
            self.assertFalse(file_exists)


class DatastoreTestCase(test.NoDBTestCase):
    def test_ds(self):
        ds = ds_util.Datastore(
                "fake_ref", "ds_name", 2 * units.Gi, 1 * units.Gi)
        self.assertEqual('ds_name', ds.name)
        self.assertEqual('fake_ref', ds.ref)
        self.assertEqual(2 * units.Gi, ds.capacity)
        self.assertEqual(1 * units.Gi, ds.freespace)

    def test_ds_invalid_space(self):
        self.assertRaises(ValueError, ds_util.Datastore,
                "fake_ref", "ds_name", 1 * units.Gi, 2 * units.Gi)
        self.assertRaises(ValueError, ds_util.Datastore,
                "fake_ref", "ds_name", None, 2 * units.Gi)

    def test_ds_no_capacity_no_freespace(self):
        ds = ds_util.Datastore("fake_ref", "ds_name")
        self.assertIsNone(ds.capacity)
        self.assertIsNone(ds.freespace)

    def test_ds_invalid(self):
        self.assertRaises(ValueError, ds_util.Datastore, None, "ds_name")
        self.assertRaises(ValueError, ds_util.Datastore, "fake_ref", None)

    def test_build_path(self):
        ds = ds_util.Datastore("fake_ref", "ds_name")
        ds_path = ds.build_path("some_dir", "foo.vmdk")
        self.assertEqual('[ds_name] some_dir/foo.vmdk', str(ds_path))


class DatastorePathTestCase(test.NoDBTestCase):

    def test_ds_path(self):
        p = ds_util.DatastorePath('dsname', 'a/b/c', 'file.iso')
        self.assertEqual('[dsname] a/b/c/file.iso', str(p))
        self.assertEqual('a/b/c/file.iso', p.rel_path)
        self.assertEqual('a/b/c', p.parent.rel_path)
        self.assertEqual('[dsname] a/b/c', str(p.parent))
        self.assertEqual('dsname', p.datastore)
        self.assertEqual('file.iso', p.basename)
        self.assertEqual('a/b/c', p.dirname)

    def test_ds_path_no_ds_name(self):
        bad_args = [
                ('', ['a/b/c', 'file.iso']),
                (None, ['a/b/c', 'file.iso'])]
        for t in bad_args:
            self.assertRaises(
                ValueError, ds_util.DatastorePath,
                t[0], *t[1])

    def test_ds_path_invalid_path_components(self):
        bad_args = [
            ('dsname', [None]),
            ('dsname', ['', None]),
            ('dsname', ['a', None]),
            ('dsname', ['a', None, 'b']),
            ('dsname', [None, '']),
            ('dsname', [None, 'b'])]

        for t in bad_args:
            self.assertRaises(
                ValueError, ds_util.DatastorePath,
                t[0], *t[1])

    def test_ds_path_no_subdir(self):
        args = [
            ('dsname', ['', 'x.vmdk']),
            ('dsname', ['x.vmdk'])]

        canonical_p = ds_util.DatastorePath('dsname', 'x.vmdk')
        self.assertEqual('[dsname] x.vmdk', str(canonical_p))
        self.assertEqual('', canonical_p.dirname)
        self.assertEqual('x.vmdk', canonical_p.basename)
        self.assertEqual('x.vmdk', canonical_p.rel_path)
        for t in args:
            p = ds_util.DatastorePath(t[0], *t[1])
            self.assertEqual(str(canonical_p), str(p))

    def test_ds_path_ds_only(self):
        args = [
            ('dsname', []),
            ('dsname', ['']),
            ('dsname', ['', ''])]

        canonical_p = ds_util.DatastorePath('dsname')
        self.assertEqual('[dsname]', str(canonical_p))
        self.assertEqual('', canonical_p.rel_path)
        self.assertEqual('', canonical_p.basename)
        self.assertEqual('', canonical_p.dirname)
        for t in args:
            p = ds_util.DatastorePath(t[0], *t[1])
            self.assertEqual(str(canonical_p), str(p))
            self.assertEqual(canonical_p.rel_path, p.rel_path)

    def test_ds_path_equivalence(self):
        args = [
            ('dsname', ['a/b/c/', 'x.vmdk']),
            ('dsname', ['a/', 'b/c/', 'x.vmdk']),
            ('dsname', ['a', 'b', 'c', 'x.vmdk']),
            ('dsname', ['a/b/c', 'x.vmdk'])]

        canonical_p = ds_util.DatastorePath('dsname', 'a/b/c', 'x.vmdk')
        for t in args:
            p = ds_util.DatastorePath(t[0], *t[1])
            self.assertEqual(str(canonical_p), str(p))
            self.assertEqual(canonical_p.datastore, p.datastore)
            self.assertEqual(canonical_p.rel_path, p.rel_path)
            self.assertEqual(str(canonical_p.parent), str(p.parent))

    def test_ds_path_non_equivalence(self):
        args = [
            # leading slash
            ('dsname', ['/a', 'b', 'c', 'x.vmdk']),
            ('dsname', ['/a/b/c/', 'x.vmdk']),
            ('dsname', ['a/b/c', '/x.vmdk']),
            # leading space
            ('dsname', ['a/b/c/', ' x.vmdk']),
            ('dsname', ['a/', ' b/c/', 'x.vmdk']),
            ('dsname', [' a', 'b', 'c', 'x.vmdk']),
            # trailing space
            ('dsname', ['/a/b/c/', 'x.vmdk ']),
            ('dsname', ['a/b/c/ ', 'x.vmdk'])]

        canonical_p = ds_util.DatastorePath('dsname', 'a/b/c', 'x.vmdk')
        for t in args:
            p = ds_util.DatastorePath(t[0], *t[1])
            self.assertNotEqual(str(canonical_p), str(p))

    def test_ds_path_parse(self):
        p = ds_util.DatastorePath.parse('[dsname]')
        self.assertEqual('dsname', p.datastore)
        self.assertEqual('', p.rel_path)

        p = ds_util.DatastorePath.parse('[dsname] folder')
        self.assertEqual('dsname', p.datastore)
        self.assertEqual('folder', p.rel_path)

        p = ds_util.DatastorePath.parse('[dsname] folder/file')
        self.assertEqual('dsname', p.datastore)
        self.assertEqual('folder/file', p.rel_path)

        for p in [None, '']:
            self.assertRaises(ValueError, ds_util.DatastorePath.parse, p)

        for p in ['bad path', '/a/b/c', 'a/b/c']:
            self.assertRaises(IndexError, ds_util.DatastorePath.parse, p)
