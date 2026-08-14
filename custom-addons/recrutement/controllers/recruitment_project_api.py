from odoo import http
from odoo.http import request


class RecruitmentProjectAPI(http.Controller):

    @http.route(
        '/api/recruitment/directions',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_directions(self, **kwargs):

        directions = request.env[
            'recruitment.direction'
        ].search([
            ('active', '=', True)
        ])

        data = []

        for direction in directions:
            data.append({
                'id': direction.id,
                'name': direction.name,
                'director_id': (
                    direction.director_id.id
                    if direction.director_id
                    else None
                ),
                'director_name': (
                    direction.director_id.name
                    if direction.director_id
                    else None
                ),
            })

        return request.make_json_response({
            'success': True,
            'count': len(data),
            'data': data,
        })

    @http.route(
        '/api/recruitment/projects',
        type='http',
        auth='user',
        methods=['GET'],
        csrf=False,
    )
    def get_projects(self, **kwargs):

        projects = request.env[
            'recruitment.project'
        ].search([
            ('active', '=', True)
        ])

        data = []

        for project in projects:

            data.append({
                'id': project.id,
                'name': project.name,
                'description': project.description,

                'owner_type': project.owner_type,

                'chef_service': (
                    {
                        'id': project.chef_service_id.id,
                        'name': project.chef_service_id.name,
                    }
                    if project.chef_service_id
                    else None
                ),

                'direction': (
                    {
                        'id': project.direction_id.id,
                        'name': project.direction_id.name,
                    }
                    if project.direction_id
                    else None
                ),

                'director': (
                    {
                        'id': project.director_id.id,
                        'name': project.director_id.name,
                    }
                    if project.director_id
                    else None
                ),
            })

        return request.make_json_response({
            'success': True,
            'count': len(data),
            'data': data,
        })