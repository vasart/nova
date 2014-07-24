# Copyright (c) 2014 Nebula, Inc.
# All Rights Reserved
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


from sqlalchemy import Column, MetaData, Table
from sqlalchemy import Boolean, Integer, DateTime, String

from nova.db.sqlalchemy import types

from nova.openstack.common import timeutils

def upgrade(migrate_engine):
    """Function adds network mtu, dhcp_server, and share_dhcp fields."""
        
    meta = MetaData(bind=migrate_engine)
    pc = Table(
        'periodic_checks', meta,
        Column('created_at', DateTime, default=timeutils.utcnow),
        Column('updated_at', DateTime, onupdate=timeutils.utcnow),
        Column('deleted_at', DateTime),
        Column('deleted', Integer, default=0), 
        Column('check_id', String(length=50), primary_key=True, nullable=False),
        Column('server', String(length=50)),
        Column('status', String(50), nullable=False, default='turn_off'),
        Column('time_out', Integer, nullable=False),
        Column('port', Integer),
    )
    pcr = Table(
        'periodic_check_results', meta, 
        Column('created_at', DateTime, default=timeutils.utcnow),
        Column('updated_at', DateTime, onupdate=timeutils.utcnow),
        Column('deleted_at', DateTime),
        Column('deleted', Integer, default=0), 
        Column('id', Integer, primary_key=True, nullable=False),
        Column('check_id', String(length=50)),
        Column('host', String(50), nullable=False),
        Column('result', String(5), nullable=False,default=False),
        Column('status', String(50), nullable=False),
    )

    pc.create()
    pcr.create()


def downgrade(migrate_engine):
    """Function removes network mtu, dhcp_server, and share_dhcp fields."""
    meta = MetaData(bind=migrate_engine)
    pc  = Table('periodic_checks', meta, autoload=True)
    pcr = Table('periodic_checks_results', meta, autoload=True)
    pcr.drop()
    pc.drop()
