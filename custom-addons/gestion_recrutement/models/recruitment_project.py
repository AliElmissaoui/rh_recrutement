from odoo import models, fields

class RecruitmentProject(models.Model):
    _name = 'recruitment.project'
    _description = 'Projet'
    _order = 'name'

    name = fields.Char(
        string='Nom du projet',
        required=True,
    )

    code = fields.Char(
        string='Code',
    )

    direction_id = fields.Many2one(
        'recruitment.direction',
        string='Direction',
        required=True,
        ondelete='restrict',
    )

    user_id = fields.Many2many(
        'res.users',
        string='Utilisateurs autorisés',
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )