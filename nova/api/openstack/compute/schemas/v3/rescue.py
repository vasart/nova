# Copyright 2014 NEC Corporation.
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

from nova.api.validation import parameter_types

rescue = {
    'type': 'object',
    'properties': {
        'rescue': {
            'type': ['object', 'null'],
            'properties': {
                'admin_password': parameter_types.admin_password,
                'image_ref': parameter_types.image_ref,
            },
            'additionalProperties': False,
        },
    },
    'required': ['rescue'],
    'additionalProperties': False,
}
