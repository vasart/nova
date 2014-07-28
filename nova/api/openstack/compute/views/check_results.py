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

from nova.api.openstack import common
from nova.openstack.common import timeutils


class ViewBuilder(common.ViewBuilder):

    _collection_name = "check_results"

    def basic(self, request, check_result):
        """Return a dictionary with basic result attributes."""
        return {
            "check_result": {
                "id": check_result.id,
                "time": check_result.time,
                "name": check_result.name,
                "node": check_result.node,
                "result": check_result.result,
                "status": check_result.status,
            },
        }

    def show(self, request, check_result):
        """Return a dictionary with result details."""
        check_result_dict = {
            "id": check_result.id,
            "time": check_result.time,
            "name": check_result.name,
            "node": check_result.node,
            "result": check_result.result,
            "status": check_result.status,
        }

        return dict(check_result=check_result_dict)

    def detail(self, request, check_results):
        """Show a list of periodic check results with details."""
        list_func = self.show
        return self._list_view(list_func, request, check_results)

    def index(self, request, check_results):
        """Show a list of periodic check results with basic attributes."""
        list_func = self.basic
        return self._list_view(list_func, request, check_results)

    def _list_view(self, list_func, request, check_results):
        """Provide a view for a list of periodic check results."""
        check_result_list = [list_func(request, check_result)["check_result"]
            for check_result in check_results]

        return dict(check_results=check_result_list)

    @staticmethod
    def _format_date(dt):
        """Return standard format for a given datetime object."""
        if dt is not None:
            return timeutils.isotime(dt)


class ViewBuilderV3(ViewBuilder):
    pass
