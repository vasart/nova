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

import webob.exc

from nova.api.openstack import common
from nova.api.openstack.compute.views import periodic_checks \
    as views_periodic_checks
from nova.api.openstack import wsgi
from nova.api.openstack import xmlutil
from nova import exception
from nova.openstack.common.gettextutils import _


SUPPORTED_FILTERS = {
    'name': 'name',
    'desc': 'desc',
    'timeout': 'timeout',
    'spacing': 'spacing',
}


def make_periodic_check(elem, detailed=False):
    elem.set('id')
    elem.set('name')

#     if detailed:
    elem.set('desc')
    elem.set('timeout')
    elem.set('spacing')

    elem.append(common.MetadataTemplate())


periodic_check_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}


class PeriodicCheck():

    def __init__(self, check_id, name, desc, timeout, spacing):
        self.id = check_id
        self.name = name
        self.desc = desc
        self.timeout = timeout
        self.spacing = spacing


class PeriodicCheckTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('periodic_check',
            selector='periodic_check')
        make_periodic_check(root, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=periodic_check_nsmap)


class MinimalPeriodicCheckTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('periodic_checks')
        elem = xmlutil.SubTemplateElement(root, 'periodic_check',
            selector='periodic_check')
        make_periodic_check(elem)
        return xmlutil.MasterTemplate(root, 1, nsmap=periodic_check_nsmap)


class PeriodicChecksTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('periodic_checks')
        elem = xmlutil.SubTemplateElement(root, 'periodic_check',
            selector='periodic_check')
        make_periodic_check(elem, detailed=True)
        return xmlutil.MasterTemplate(root, 1, nsmap=periodic_check_nsmap)


class Controller(wsgi.Controller):
    """Base controller for retrieving/displaying periodic checks."""

    _view_builder_class = views_periodic_checks.ViewBuilder

    mock_data = [
        PeriodicCheck(0, 'OpenAttestation',
                      'Static file integrity check using IMA/TPM',
                      600, 1200),
        PeriodicCheck(1, 'DynMem',
                      'Dynamic memory check', 300, 600),
        PeriodicCheck(2, 'Yet Another Check',
                      'One more mock check', 720, 1440),
    ]

    def __init__(self, **kwargs):
        """Initialize new `PeriodicCheckController`."""
        super(Controller, self).__init__(**kwargs)

    def _get_filters(self, req):
        """Return a dictionary of query param filters from the request.

        :param req: the Request object coming from the wsgi layer
        :retval a dict of key/value filters
        """
        filters = {}
        for param in req.params:
            if param in SUPPORTED_FILTERS or param.startswith('property-'):
                # map filter name or carry through if property-*
                filter_name = SUPPORTED_FILTERS.get(param, param)
                filters[filter_name] = req.params.get(param)

        # ensure server filter is the instance uuid
        filter_name = 'property-instance_uuid'
        try:
            filters[filter_name] = filters[filter_name].rsplit('/', 1)[1]
        except (AttributeError, IndexError, KeyError):
            pass

        filter_name = 'status'
        if filter_name in filters:
            # The API expects us to use lowercase strings for status
            filters[filter_name] = filters[filter_name].lower()

        return filters

    @wsgi.serializers(xml=PeriodicCheckTemplate)
    def show(self, req, id):
        """Return detailed information about a specific periodic check.

        :param req: `wsgi.Request` object
        :param id: Periodic check identifier
        """
        #context = req.environ['nova.context']

        try:
            periodic_check = None
            #periodic_check = self._periodic_check_service.show(context, id)
        except (exception.NotFound):
            explanation = _("Periodic check not found.")
            raise webob.exc.HTTPNotFound(explanation=explanation)

        req.cache_db_items('periodic_checks', [periodic_check], 'id')
        return self._view_builder.show(req, periodic_check)

    def delete(self, req, id):
        """Delete a periodic check, if allowed.

        :param req: `wsgi.Request` object
        :param id: Periodic check identifier (integer)
        """
        #context = req.environ['nova.context']
        try:
            pass
            #self._periodic_check_service.delete(context, id)
        except exception.NotFound:
            explanation = _("Periodic check not found.")
            raise webob.exc.HTTPNotFound(explanation=explanation)
        except exception.Forbidden:
            # This exception is raised on delete of OpenAttestation check
            explanation = \
                _("You are not allowed to delete the periodic check.")
            raise webob.exc.HTTPForbidden(explanation=explanation)
        return webob.exc.HTTPNoContent()

    @wsgi.serializers(xml=MinimalPeriodicCheckTemplate)
    def index(self, req):
        """Return an index listing of periodic checks available to the request.

        :param req: `wsgi.Request` object

        """
        #context = req.environ['nova.context']
        #filters = self._get_filters(req)
        params = req.GET.copy()
        page_params = common.get_pagination_params(req)
        for key, val in page_params.iteritems():
            params[key] = val

        try:
            periodic_checks = Controller.mock_data
            #periodic_checks = self._periodic_check_service.detail(context,
            #    filters=filters, **page_params)
        except exception.Invalid as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())
        return self._view_builder.index(req, periodic_checks)

    @wsgi.serializers(xml=PeriodicChecksTemplate)
    def detail(self, req):
        """Return a detailed index listing of periodic checks.

        :param req: `wsgi.Request` object.

        """
        #context = req.environ['nova.context']
        #filters = self._get_filters(req)
        params = req.GET.copy()
        page_params = common.get_pagination_params(req)
        for key, val in page_params.iteritems():
            params[key] = val
        try:
            periodic_checks = []
            #periodic_checks = self._periodic_check_service.detail(context,
            #    filters=filters, **page_params)
        except exception.Invalid as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())

        req.cache_db_items('periodic_checks', periodic_checks, 'id')
        return self._view_builder.detail(req, periodic_checks)

    @wsgi.serializers(xml=PeriodicCheckTemplate)
    def create(self, req, body):
        """Create periodic check.

        :param req: `wsgi.Request` object
        :param id: Periodic check identifier
        """
        periodic_check_dict = body['periodic_check']
        
        id = periodic_check_dict['id']
        name = periodic_check_dict['name']
        desc = periodic_check_dict['desc']
        spacing = periodic_check_dict['spacing']
        timeout = periodic_check_dict['timeout']

        periodic_check = PeriodicCheck(id, name, desc, timeout, spacing)
        Controller.mock_data.append(periodic_check)
        return self._view_builder.show(req, periodic_check)


def create_resource():
    return wsgi.Resource(Controller())
