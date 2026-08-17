from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError


class RecruitmentPlanningLine(models.Model):
    _name = 'recruitment.planning.line'
    _description = 'Recruitment Planning Line'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )

    header_id = fields.Many2one(
        'recruitment.planning.header',
        string='Planification',
        required=True,
        ondelete='cascade',
    )

   
    job = fields.Char(
    string='Poste',
    )


    planned_qty = fields.Integer(
        string='Nombre planifié',
        required=True,
        default=0,
       
    )

    date_previsionnelle = fields.Date(
        string='Date prévisionnelle',
        help='Date prévue pour le lancement du recrutement.',
        
    )

    estimated_salary = fields.Float(
        string='Salaire estimé',
       
    )

    salary_currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id,
    )

    annual_salary_cost = fields.Float(
        string='Coût salarial annuel',
        compute='_compute_annual_salary_cost',
        store=True,
        readonly=True,
    )

    note = fields.Text(
        string='Note',
       
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    planning_state = fields.Selection(
    related='header_id.state',
    string='Planning State',
    readonly=True,
    store=False,
    )

    # =========================================================
    # SECURITY : RH PEUT MODIFIER UNIQUEMENT LE SALAIRE
    # =========================================================

    def write(self, vals):

        # RH uniquement
        if self.env.user.has_group(
            'recrutement.group_recruitment_rh'
        ):

            # Champs que RH a le droit de modifier
            allowed_fields = {
                'estimated_salary',
            }

            # Tous les autres champs sont interdits
            forbidden_fields = set(vals.keys()) - allowed_fields

            if forbidden_fields:
                raise AccessError(
                    "Le profil RH peut uniquement modifier "
                    "le champ « Salaire estimé »."
                )

        return super().write(vals)

    # =========================================================
    # COMPUTE
    # =========================================================

    @api.depends(
        'estimated_salary',
        'planned_qty',
    )
    def _compute_annual_salary_cost(self):
        for line in self:
            line.annual_salary_cost = (
                line.estimated_salary
                * line.planned_qty
                * 12
            )

    # =========================================================
    # CONSTRAINT
    # =========================================================

    @api.constrains('planned_qty')
    def _check_planned_qty(self):
        for line in self:
            if line.planned_qty < 0:
                raise ValidationError(
                    'Le nombre planifié ne peut pas être négatif.'
                )

    



    