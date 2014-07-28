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
from nova.api.openstack.compute.views import check_results \
    as views_check_results
from nova.api.openstack import wsgi
from nova.api.openstack import xmlutil
from nova import db
from nova import exception
from nova.openstack.common import gettextutils


_ = gettextutils._


SUPPORTED_FILTERS = {
    'name': 'name',
    'desc': 'desc',
    'timeout': 'timeout',
    'spacing': 'spacing',
}


def make_check_result(elem):
    elem.set('id')
    elem.set('time')
    elem.set('name')
    elem.set('node')
    elem.set('result')
    elem.set('status')

    elem.append(common.MetadataTemplate())


check_result_nsmap = {None: xmlutil.XMLNS_V11, 'atom': xmlutil.XMLNS_ATOM}


class CheckResultsTemplate(xmlutil.TemplateBuilder):
    def construct(self):
        root = xmlutil.TemplateElement('check_results')
        elem = xmlutil.SubTemplateElement(root, 'check_result',
            selector='check_result')
        make_check_result(elem)
        return xmlutil.MasterTemplate(root, 1, nsmap=check_result_nsmap)


class Controller(wsgi.Controller):

    """Base controller for retrieving/displaying results."""

    _view_builder_class = views_check_results.ViewBuilder

    def __init__(self, **kwargs):
        """Initialize new `ResultsController`."""
        super(Controller, self).__init__(**kwargs)

    def delete(self, req, id):
        """Delete a periodic check result, if allowed.

        :param req: `wsgi.Request` object
        :param id: Periodic check result identifier (integer)
        """
        context = req.environ['nova.context']
        try:
            self.periodic_checks.remove_result(context, id);
        except exception.NotFound:
            explanation = _("Periodic check result not found.")
            raise webob.exc.HTTPNotFound(explanation=explanation)
        except exception.Forbidden:
            # This exception is raised on delete of OpenAttestation check
            explanation = \
                _("You are not allowed to delete the periodic check result.")
            raise webob.exc.HTTPForbidden(explanation=explanation)
        return webob.exc.HTTPNoContent()

    @wsgi.serializers(xml=CheckResultsTemplate)
    def index(self, req):
        """Return an index listing of results available to the request.

        :param req: `wsgi.Request` object

        """
        context = req.environ['nova.context']
        #filters = self._get_filters(req)
        params = req.GET.copy()
        page_params = common.get_pagination_params(req)
        for key, val in page_params.iteritems():
            params[key] = val
        try:
            results = db.periodic_check_results_get(context, num_of_results=100)
        except exception.Invalid as e:
            raise webob.exc.HTTPBadRequest(explanation=e.format_message())

        return self._view_builder.index(req, results)


def create_resource():
    return wsgi.Resource(Controller())
