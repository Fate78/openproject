from odoo import models
import requests
import json


class PostWorkPackages(models.TransientModel):
    _name = 'post.work_packages'
    _description = 'Create Work_Packages'
    headers = {
        'content-type': 'application/json'
    }

    @staticmethod
    def get_main_url(project_id):
        base_path = "http://localhost:3000"
        endpoint_url = "/api/v3/projects/%s/work_packages" % project_id
        main_url = "%s%s" % (base_path, endpoint_url)
        return main_url

    @staticmethod
    def get_payload(project_id, id):
        payload = {
            "subject": "package%s" % id,
            "description": {
                "format": "markdown",
                "raw": None,
                "html": ""
            },
            "scheduleManually": False,
            "startDate": None,
            "dueDate": None,
            "estimatedTime": None,
            "percentageDone": 0,
            "remainingTime": None,
            "_links": {
                "category": {
                    "href": None
                },
                "type": {
                    "href": "/api/v3/types/1",
                    "title": "Task"
                },
                "priority": {
                    "href": "/api/v3/priorities/8",
                    "title": "Normal"
                },
                "project": {
                    "href": "/api/v3/projects/%s" % project_id,
                },
                "status": {
                    "href": "/api/v3/statuses/1",
                    "title": "New"
                },
                "responsible": {
                    "href": None
                },
                "assignee": {
                    "href": None
                },
                "version": {
                    "href": None
                },
                "parent": {
                    "href": None,
                    "title": None
                }
            }
        }
        return payload

    def get_api_key(self):
        api_key = self.env['ir.config_parameter'].sudo(
        ).get_param('openproject.api_key') or False
        return api_key

    def post_response(self, url, payload):
        api_key = self.get_api_key()

        resp = requests.post(
            url,
            auth=('apikey', api_key),
            data=json.dumps(payload),
            headers=self.headers
        )
        return json.loads(resp.text)

    def cron_create_work_packages(self):
        try:
            for p in range(1843, 1862):
                main_url = self.get_main_url(p)
                print(p)
                print("main_url: ", main_url)
                for id in range(1, 5):
                    response = self.post_response(main_url, self.get_payload(p, id))
                    print(response)
            # Range: first and last id of projects
        except Exception as e:
            print("Exception has occurred: ", e)
            print("Exception type: ", type(e))
