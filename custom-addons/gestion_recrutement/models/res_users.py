from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    recruitment_group_ids = fields.Many2many(
        'res.groups',
        string='Recruitment Groups',
        compute='_compute_recruitment_groups',
    )

    @api.depends('groups_id')
    def _compute_recruitment_groups(self):

        recruitment_category = self.env.ref(
            'recrutement.module_category_recruitment',
            raise_if_not_found=False,
        )

        for user in self:
            if not recruitment_category:
                user.recruitment_group_ids = False
                continue

            user.recruitment_group_ids = user.groups_id.filtered(
                lambda group:
                    group.category_id == recruitment_category
            )