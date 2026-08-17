import json

from odoo import http
from odoo.http import request


class RecruitmentAPI(http.Controller):

    @http.route(
        '/api/recruitment/setup',
        type='http',
        auth='public',
        methods=['POST'],
        csrf=False,
    )
    def setup_recruitment(self, **kwargs):

        try:
            # =====================================================
            # READ JSON
            # =====================================================

            raw_data = request.httprequest.get_data(
                as_text=True
            )

            if not raw_data:
                return request.make_json_response(
                    {
                        'success': False,
                        'message': 'JSON body is empty.',
                    },
                    status=400,
                )

            try:
                data = json.loads(raw_data)

            except json.JSONDecodeError as error:
                return request.make_json_response(
                    {
                        'success': False,
                        'message': 'Invalid JSON.',
                        'error': str(error),
                    },
                    status=400,
                )

            # =====================================================
            # VALIDATE ROOT
            # =====================================================

            if not isinstance(data, dict):
                return request.make_json_response(
                    {
                        'success': False,
                        'message': 'JSON must be an object.',
                    },
                    status=400,
                )

            directions_data = data.get('directions', [])
            projects_data = data.get('projects', [])

            # =====================================================
            # MODELS
            # =====================================================

            Direction = request.env[
                'recruitment.direction'
            ].sudo()

            Project = request.env[
                'recruitment.project'
            ].sudo()

            Users = request.env[
                'res.users'
            ].sudo()

            # =====================================================
            # COUNTERS
            # =====================================================

            directions_created = 0
            directions_updated = 0

            projects_created = 0
            projects_updated = 0

            # =====================================================
            # DIRECTIONS
            # =====================================================

            for direction_data in directions_data:

                name = direction_data.get('name')
                director_email = direction_data.get(
                    'director_email'
                )

                if not name:
                    raise ValueError(
                        'Direction name is required.'
                    )

                if not director_email:
                    raise ValueError(
                        f"director_email is required "
                        f"for direction '{name}'."
                    )

                # -------------------------------------------------
                # FIND DIRECTOR
                # -------------------------------------------------

                director = Users.search(
                    [
                        (
                            'login',
                            '=',
                            director_email,
                        )
                    ],
                    limit=1,
                )

                if not director:
                    director = Users.search(
                        [
                            (
                                'email',
                                '=',
                                director_email,
                            )
                        ],
                        limit=1,
                    )

                if not director:
                    raise ValueError(
                        f"Director not found: "
                        f"{director_email}"
                    )

                # -------------------------------------------------
                # FIND / CREATE DIRECTION
                # -------------------------------------------------

                direction = Direction.search(
                    [
                        (
                            'name',
                            '=',
                            name,
                        )
                    ],
                    limit=1,
                )

                if direction:

                    direction.write({
                        'director_id': director.id,
                    })

                    directions_updated += 1

                else:

                    Direction.create({
                        'name': name,
                        'director_id': director.id,
                    })

                    directions_created += 1

            # =====================================================
            # PROJECTS
            # =====================================================

            for project_data in projects_data:

                name = project_data.get('name')
                code = project_data.get('code')
                user_email = project_data.get(
                    'user_email'
                )
                direction_name = project_data.get(
                    'direction'
                )

                if not name:
                    raise ValueError(
                        'Project name is required.'
                    )

                if not code:
                    raise ValueError(
                        f"Project code is required "
                        f"for '{name}'."
                    )

                if not user_email:
                    raise ValueError(
                        f"user_email is required "
                        f"for project '{name}'."
                    )

                # -------------------------------------------------
                # FIND USER
                # -------------------------------------------------

                user = Users.search(
                    [
                        (
                            'login',
                            '=',
                            user_email,
                        )
                    ],
                    limit=1,
                )

                if not user:
                    user = Users.search(
                        [
                            (
                                'email',
                                '=',
                                user_email,
                            )
                        ],
                        limit=1,
                    )

                if not user:
                    raise ValueError(
                        f"User not found: {user_email}"
                    )

                # -------------------------------------------------
                # DIRECTION
                # -------------------------------------------------

                direction = False

                # Direction is optional for Director projects.
                # If direction is provided, it must exist.
                if direction_name:

                    direction = Direction.search(
                        [
                            (
                                'name',
                                '=',
                                direction_name,
                            )
                        ],
                        limit=1,
                    )

                    if not direction:
                        raise ValueError(
                            f"Direction not found: "
                            f"{direction_name}"
                        )

                # -------------------------------------------------
                # FIND PROJECT
                # -------------------------------------------------

                project = Project.search(
                    [
                        (
                            'code',
                            '=',
                            code,
                        )
                    ],
                    limit=1,
                )

                values = {
                    'name': name,
                    'code': code,
                    'user_id': user.id,
                    'direction_id': (
                        direction.id
                        if direction
                        else False
                    ),
                }

                # -------------------------------------------------
                # UPDATE
                # -------------------------------------------------

                if project:

                    project.write(values)

                    projects_updated += 1

                # -------------------------------------------------
                # CREATE
                # -------------------------------------------------

                else:

                    Project.create(values)

                    projects_created += 1

            # =====================================================
            # RESPONSE
            # =====================================================

            return request.make_json_response(
                {
                    'success': True,
                    'message': (
                        'Projects et directions '
                        'importés avec succès.'
                    ),
                    'directions': {
                        'created': directions_created,
                        'updated': directions_updated,
                    },
                    'projects': {
                        'created': projects_created,
                        'updated': projects_updated,
                    },
                },
                status=200,
            )

        except Exception as error:

            return request.make_json_response(
                {
                    'success': False,
                    'message': str(error),
                },
                status=400,
            )