from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RecruitmentPlanningHeader(models.Model):
    _name = 'recruitment.planning.header'
    _description = 'Recruitment Planning Header'
    _order = 'year desc, sequence, id'

    # =========================================================
    # IDENTIFICATION
    # =========================================================

    ref = fields.Char(
        string='Référence',
        required=True,
        copy=False,
        readonly=True,
        default='PLA',
    )

    name = fields.Char(
        string='Nom',
        required=True,
    )

    year = fields.Integer(
        string='Année',
        required=True,
    )

    sequence = fields.Integer(
        string='Séquence',
        default=10,
    )

    # =========================================================
    # GENERAL
    # =========================================================

    entity_id = fields.Many2one(
        'res.company',
        string='Entité',
        required=True,
        default=lambda self: self.env.company,
    )

    director_id = fields.Many2one(
        'res.users',
        string="Directeur d'entité",
        required=True,
    )

    # =========================================================
    # STATE
    # =========================================================

    state = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('rh_review', 'Contrôle RH'),
            ('dg_validation', 'Validation DG'),
            ('drh_validation', 'Validation DRH'),
            ('active', 'Active'),
            ('closed', 'Clôturée'),
            ('cancelled', 'Annulée'),
        ],
        string='État',
        default='draft',
        required=True,
    )

    # =========================================================
    # PLANNING LINES
    # =========================================================

    line_ids = fields.One2many(
        'recruitment.planning.line',
        'header_id',
        string='Postes planifiés',
    )

    # =========================================================
    # TOTAL PLANIFIÉ
    # =========================================================

    total_planned = fields.Integer(
        string='Total planifié',
        compute='_compute_totals',
        store=True,
        readonly=True,
    )

    # =========================================================
    # COÛT SALARIAL ANNUEL
    # =========================================================

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        related='entity_id.currency_id',
        store=True,
        readonly=True,
    )

    annual_salary_cost = fields.Float(
        string='Coût salarial annuel total',
        compute='_compute_totals',
        store=True,
        readonly=True,
    )

    # =========================================================
    # VALIDATION DG
    # =========================================================

    dg_validator_id = fields.Many2one(
        'res.users',
        string='Validé par DG',
        readonly=True,
    )

    dg_validation_date = fields.Datetime(
        string='Date validation DG',
        readonly=True,
    )

    # =========================================================
    # VALIDATION DRH
    # =========================================================

    drh_validator_id = fields.Many2one(
        'res.users',
        string='Validé par DRH',
        readonly=True,
    )

    drh_validation_date = fields.Datetime(
        string='Date validation DRH',
        readonly=True,
    )

    budget_validated = fields.Boolean(
        string='Budget validé',
        default=False,
        readonly=True,
    )

    # =========================================================
    # OTHER
    # =========================================================

    note = fields.Text(
        string='Note',
    )

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    # =========================================================
    # CREATE
    # =========================================================

    @api.model
    def create(self, vals):
        if vals.get('ref', 'PLA') == 'PLA':
            vals['ref'] = self.env[
                'ir.sequence'
            ].next_by_code(
                'recruitment.planning.header'
            ) or 'PLA'

        return super().create(vals)

    # =========================================================
    # COMPUTE TOTALS
    # =========================================================

    @api.depends(
        'line_ids.planned_qty',
        'line_ids.annual_salary_cost',
    )
    def _compute_totals(self):
        for record in self:
            record.total_planned = sum(
                record.line_ids.mapped('planned_qty')
            )

            record.annual_salary_cost = sum(
                record.line_ids.mapped('annual_salary_cost')
            )

    # =========================================================
    # CONSTRAINT YEAR
    # =========================================================

    @api.constrains('year')
    def _check_year(self):
        for record in self:
            if record.year < 2000:
                raise ValidationError(
                    "L'année doit être valide."
                )

    # =========================================================
    # CONSTRAINT UNIQUE YEAR / ENTITY
    # =========================================================

    @api.constrains('year', 'entity_id')
    def _check_unique_year_entity(self):
        for record in self:

            existing = self.search(
                [
                    ('id', '!=', record.id),
                    ('year', '=', record.year),
                    ('entity_id', '=', record.entity_id.id),
                    ('state', '!=', 'cancelled'),
                ],
                limit=1,
            )

            if existing:
                raise ValidationError(
                    "Une planification existe déjà pour "
                    "cette entité et cette année."
                )

    # =========================================================
    # WORKFLOW - DIRECTEUR
    # =========================================================

    def action_submit_rh(self):
        for record in self:

            if record.state != 'draft':
                raise ValidationError(
                    'Seul un planning en brouillon '
                    'peut être soumis au RH.'
                )

            if not record.line_ids:
                raise ValidationError(
                    'Vous devez ajouter au moins une ligne '
                    'de planification.'
                )

            record.write({
                'state': 'rh_review',
            })

    # =========================================================
    # WORKFLOW - RH
    # =========================================================

    def action_submit_dg(self):
        for record in self:

            if record.state != 'rh_review':
                raise ValidationError(
                    'Le planning doit être en contrôle RH.'
                )

            # Vérification des salaires
            for line in record.line_ids:
                if line.estimated_salary <= 0:
                    raise ValidationError(
                        'Le salaire estimé doit être renseigné '
                        'par le RH pour toutes les lignes.'
                    )

            record.sudo().write({
                'state': 'dg_validation',
            })

    # =========================================================
    # WORKFLOW - DG
    # =========================================================

    def action_validate_dg(self):
        for record in self:

            if record.state != 'dg_validation':
                raise ValidationError(
                    'Le planning doit être en validation DG.'
                )

            record.sudo().write({
                'dg_validator_id': self.env.user.id,
                'dg_validation_date': fields.Datetime.now(),
                'state': 'drh_validation',
            })

    # =========================================================
    # WORKFLOW - DRH
    # =========================================================

    def action_validate_drh(self):
        for record in self:

            if record.state != 'drh_validation':
                raise ValidationError(
                    'Le planning doit être en validation DRH.'
                )

            record.sudo().write({
                'drh_validator_id': self.env.user.id,
                'drh_validation_date': fields.Datetime.now(),
                'budget_validated': True,
                'state': 'active',
            })

    # =========================================================
    # CLOSE
    # =========================================================

    def action_close(self):
        for record in self:

            if record.state != 'active':
                raise ValidationError(
                    'Seul un planning actif peut être clôturé.'
                )

            record.sudo().write({
                'state': 'closed',
            })

    # =========================================================
    # CANCEL
    # =========================================================

    def action_cancel(self):
        for record in self:

            if record.state == 'closed':
                raise ValidationError(
                    'Un planning clôturé ne peut pas être annulé.'
                )

            record.sudo().write({
                'state': 'cancelled',
            })