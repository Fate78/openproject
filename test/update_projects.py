from odoo import models
import requests
import json


class UpdateProjects(models.TransientModel):
    _name = 'update.projects'
    _description = 'Update Projects'
    base_path = "http://localhost:3000"
    endpoint_url = "/api/v3/projects/"
    headers = {
        'content-type': 'application/json'
    }

    @staticmethod
    def get_payload(id):
        payload = {
            "lockVersion": 1,
            "identifier": "updatedproject%s" % id,
            "name": "updatedproject%s" % id,
            "active": True,
            "public": False,
            "description": {
                "format": "markdown",
                "raw": None,
                "html": ""
            },
            "statusExplanation": {
                "format": "markdown",
                "raw": None,
                "html": ""
            },
            "_links": {
                "parent": {
                    "href": None
                },
                "status": {
                    "href": None
                }
            }
        }
        return payload

    def get_api_key(self):
        api_key = self.env['ir.config_parameter'].sudo(
        ).get_param('openproject.api_key') or False
        return api_key

    def patch_response(self, url, payload):
        api_key = self.get_api_key()

        resp = requests.patch(
            url,
            auth=('apikey', api_key),
            data=json.dumps(payload),
            headers=self.headers
        )
        return json.loads(resp.text)

    def cron_update_projects(self):
        try:
            for id in range(1821, 1858):
                main_url = "%s%s/%s" % (self.base_path, self.endpoint_url, id)
                response = self.patch_response(main_url, self.get_payload(id))
        except Exception as e:
            print("Exception has occurred: ", e)
            print("Exception type: ", type(e))
