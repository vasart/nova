{
    "servers": [
    {
            "status": "ACTIVE",
            "created": "%(isotime)s",
            "os-server-usage:launched_at": "%(strtime)s",
            "user_id": "fake",
            "addresses": {
                "private": [
                    {
                        "addr": "%(ip)s",
                        "mac_addr": "aa:bb:cc:dd:ee:ff",
                        "type": "fixed",
                        "version": 4
                    }
                ]
            },
            "key_name": null,
            "links": [
                {
                    "href": "%(host)s/v3/servers/%(uuid)s",
                    "rel": "self"
                },
                {
                    "href": "%(host)s/servers/%(id)s",
                    "rel": "bookmark"
                }
            ],
            "updated": "%(isotime)s",
            "name": "new-server-test",
            "image": {
                "id": "%(uuid)s",
                "links": [
                    {
                        "href": "%(glance_host)s/images/%(uuid)s",
                        "rel": "bookmark"
                    }
                ]
            },
            "id": "%(uuid)s",
            "os-server-usage:terminated_at": null,
            "tenant_id": "openstack",
            "progress": 0,
            "flavor": {
                "id": "1",
                "links": [
                    {
                        "href": "%(host)s/flavors/1",
                        "rel": "bookmark"
                    }
                ]
            },
            "host_id": "%(hostid)s",
            "metadata": {
                "My Server Name": "Apache1"
            }
    }]
}
