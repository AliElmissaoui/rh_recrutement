from odoo import models, fields


class RecruitmentDirection(models.Model):
    _name = 'recruitment.direction'
    _description = 'Direction'
    _order = 'name'

    name = fields.Char(
        string='Nom',
        required=True,
    )

    director_id = fields.Many2one(
        'res.users',
        string="Directeur d'entité",
        required=True,
    )

    project_ids = fields.One2many(
        'recruitment.project',
        'direction_id',
        string='Projets',
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )