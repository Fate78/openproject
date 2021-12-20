from requests.models import HTTPBasicAuth
from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import json
import hashlib
from base64 import b64encode
from pprint import pprint
from dateutil import parser
from datetime import datetime
from datetime import timedelta
import isodate
import json
import logging

_logger = logging.getLogger(__name__)

class NonStopException(UserError):
    """Will bypass the record"""

class SyncVersions(models.TransientModel):

    _name = 'sync.versions'
    _description = 'Synchronize Versions'
    hashed_ver = hashlib.sha256()
    hashed_op_ver = hashlib.sha256()
    limit=200

    def get_project_id(self,href):
        project_id = href.split('/')[-1]
        return project_id

    def get_project_versions_url(self,project):
        base_path = "http://localhost:3000"
        endpoint_url = "/api/v3/projects/%s/versions" % (project)

        return "%s%s" % (base_path,endpoint_url)

    def get_hashed(self,_id,project_id,name,description,status):
        hashable=json.dumps(_id) + json.dumps(project_id) + name + description + status
        hashed=hashlib.md5(hashable.encode("utf-8")).hexdigest()
        return hashed

    def cron_sync_versions(self):
        # Loop through every project 
        projects_url = self.env['op.project'].get_projects_url()
        response = self.env['op.project'].get_response(projects_url)
        for r in response['_embedded']['elements']:
            _id_project = r['id']
            main_url = self.get_project_versions_url(_id_project)
            response_ver = self.env['op.project.version'].get_response(main_url)
            if(response_ver['_type']!="Error"):
                for rv in response_ver['_embedded']['elements']:
                    _id = rv['id']
                    _name = rv['name']
                    _description = rv['description']['raw']
                    _status = rv['status']
                    start_date = rv['startDate']
                    end_date = rv['endDate']
                    _project_href = rv['_links']['definingProject']['href']
                    _project_id = int(self.get_project_id(_project_href))
                    versions=self.env['op.project.version'].get_data_to_update('op.project.version',self.limit)
                    version_search_id=self.env['op.project.version'].search([['db_id','=',_id]])
                    
                    if(version_search_id.exists()):
                        for v in versions:
                            print("Version id: ", len(json.dumps(v.db_id)))
                            if(v.db_id==_id):
                                hashed_ver = self.get_hashed(v.db_id,v.db_project_id,v.name,v.description,v.status)
                                hashed_op_ver = self.get_hashed(_id,_project_id,_name,_description,_status)
                                print(hashed_ver)
                                print(hashed_op_ver)
                                if(hashed_ver!=hashed_op_ver):
                                    try:
                                        print("Updating version...\n")
                                        vals = {
                                            'db_project_id':_project_id,
                                            'name':_name,
                                            'description':_description,
                                            'status':_status
                                        }
                                        version_search_id.write(vals)
                                    except NonStopException:
                                        _logger.error('Bypass Error: %s' % e)
                                    except Exception as e:
                                        _logger.error('Error: %s' % e)
                                        self.env.cr.rollback()
                                else:
                                    print("Version up to date\n")
                    else:
                        try:
                            print("Creating version...\n")
                            vals = {
                                'db_id':_id,
                                'db_project_id':_project_id,
                                'name':_name,
                                'description':_description,
                                'status':_status
                            }
                            versions.create(vals)
                        except Exception as e:
                            print("Exception has ocurred: ", e)
                            print("Exception type: ", type(e))
            else:
                print("Permission denied to project %d" % (_id_project))
        self.env.cr.commit()
        print("All data commited")