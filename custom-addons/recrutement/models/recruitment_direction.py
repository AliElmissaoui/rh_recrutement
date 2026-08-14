from odoo import models, fields
from odoo.exceptions import ValidationError


class RecruitmentDirection(models.Model):
    _name = 'recruitment.direction'
    _description = 'Direction'
    _order = 'name'

    # =========================================================
    # IDENTIFICATION
    # =========================================================

    name = fields.Char(
        string='Direction',
        required=True,
        index=True,
    )

    # =========================================================
    # DIRECTEUR
    # =========================================================

    director_id = fields.Many2one(
        'res.users',
        string="Directeur d'entité",
        required=True,
        domain="[('share', '=', False)]",
    )

    # =========================================================
    # PROJECTS
    # =========================================================

    project_ids = fields.One2many(
        'recruitment.project',
        'direction_id',
        string='Projets',
    )

    # =========================================================
    # ACTIVE
    # =========================================================

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    # =========================================================
    # CONSTRAINTS
    # =========================================================

    _sql_constraints = [
        (
            'unique_direction_name',
            'unique(name)',
            'Le nom de la direction doit être unique.',
        ),
    ]

    # =========================================================
    # DISPLAY NAME
    # =========================================================

    def name_get(self):
        result = []

        for record in self:
            name = record.name

            if record.director_id:
                name = f"{name} - {record.director_id.name}"

            result.append((record.id, name))

        return result