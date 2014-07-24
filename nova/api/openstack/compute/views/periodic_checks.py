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

    _collection_name = "periodic_checks"

    def basic(self, request, periodic_check):
        """Return a dictionary with basic periodic checks attributes."""
        return {
            "periodic_check": {
                "id": periodic_check.id,
                "name": periodic_check.name,
                "desc": periodic_check.desc,
                "timeout": periodic_check.timeout,
                "spacing": periodic_check.spacing,
            },
        }

    def show(self, request, periodic_check):
        """Return a dictionary with periodic check details."""
        periodic_check_dict = {
            "id": periodic_check.id,
            "name": periodic_check.name,
            "desc": periodic_check.desc,
            "timeout": periodic_check.timeout,
            "spacing": periodic_check.spacing,
#             "created": self._format_date(periodic_check.get("created")),
        }

        return dict(periodic_check=periodic_check_dict)

    def detail(self, request, periodic_checks):
        """Show a list of periodic checks with details."""
        list_func = self.show
        return self._list_view(list_func, request, periodic_checks)

    def index(self, request, periodic_checks):
        """Show a list of periodic checks with basic attributes."""
        list_func = self.basic
        return self._list_view(list_func, request, periodic_checks)

    def _list_view(self, list_func, request, periodic_checks):
        """Provide a view for a list of periodic checks."""
        periodic_check_list = [list_func(request, periodic_check)["periodic_check"]
            for periodic_check in periodic_checks]

        return dict(periodic_checks=periodic_check_list)

    @staticmethod
    def _format_date(dt):
        """Return standard format for a given datetime object."""
        if dt is not None:
            return timeutils.isotime(dt)


class ViewBuilderV3(ViewBuilder):
    pass
