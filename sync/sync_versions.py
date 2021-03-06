from odoo import models, exceptions
import hashlib
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class NonStopException(exceptions.UserError):
    """Will bypass the record"""


class SyncVersions(models.AbstractModel):
    _name = 'sync.versions'
    _description = 'Synchronize Versions'
    hashed_ver = hashlib.sha256()
    hashed_op_ver = hashlib.sha256()
    limit = 10

    @staticmethod
    def get_hashed(_id, project_id, name, description, status):
        hashable = str(_id) + str(project_id) + name + description + status
        hashed = hashlib.md5(hashable.encode("utf-8")).hexdigest()
        print("Inside Hash", hashed)
        return hashed

    def cron_sync_versions(self):
        # Loop through every project
        env_version = self.env['op.project.version']
        next_offset = True
        while next_offset:
            main_url = env_version.get_versions_url()
            response_ver = env_version.get_response(main_url)
            if response_ver['_type'] != "Error":
                for rv in response_ver['_embedded']['elements']:
                    _id = rv['id']
                    _name = rv['name']
                    _description = rv['description']['raw']
                    _status = rv['status']
                    _id_project = env_version.get_id_href(rv['_links']['definingProject']['href'])
                    versions = env_version.get_data_to_update('op.project.version', self.limit)
                    version_search_id = env_version.search([['db_id', '=', _id]])
                    if version_search_id.exists():
                        for v in versions:
                            if v.db_id == _id:
                                v_db_id = v.db_id
                                v_db_project_id = str(v.db_project_id)
                                v_name = v.name
                                v_description = env_version.verify_field_empty(v.description)
                                v_status = v.status
                                _description = env_version.verify_field_empty(_description)

                                hashed_ver = self.get_hashed(v_db_id, v_db_project_id, v_name, v_description, v_status)
                                hashed_op_ver = self.get_hashed(_id, _id_project, _name, _description, _status)
                                if hashed_ver != hashed_op_ver:
                                    try:
                                        print("Updating version: %s\n" % v_db_id)
                                        values = {
                                            'db_project_id': _id_project,
                                            'name': _name,
                                            'description': _description,
                                            'status': _status
                                        }
                                        self.env.cr.savepoint()
                                        version_search_id.write(values)
                                    except NonStopException as e:
                                        _logger.error('Bypass Error: %s' % e)
                                        continue
                                    except Exception as e:
                                        _logger.error('Error: %s' % e)
                                        self.env.cr.rollback()
                                else:
                                    print("Version up to date: %s\n" % _id)
                                    version_search_id.write({'write_date': datetime.now()})
                    else:
                        try:
                            print("Creating version: %s\n" % _id)
                            values = {
                                'db_id': _id,
                                'db_project_id': _id_project,
                                'name': _name,
                                'description': _description,
                                'status': _status
                            }
                            self.env.cr.savepoint()
                            versions.create(values)
                        except Exception as e:
                            print("Exception has occurred: ", e)
                            print("Exception type: ", type(e))
                            self.env.cr.rollback()
            else:
                print("Permission denied to project %d" % _id_project)
            next_offset, response_ver = env_version.check_next_offset(response_ver)
            self.env.cr.commit()
            print("All data committed")
