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
    # PROJECT
    # =========================================================

    project_id = fields.Many2one(
        'recruitment.project',
        string='Projet',
        required=True,
        ondelete='restrict',
    )

    # =========================================================
    # PROJECT INFORMATION
    # Automatically inherited from project
    # =========================================================

    owner_type = fields.Selection(
        related='project_id.owner_type',
        string='Responsable du projet',
        store=True,
        readonly=True,
    )

    chef_service_id = fields.Many2one(
        'res.users',
        string='Chef de service',
        related='project_id.chef_service_id',
        store=True,
        readonly=True,
    )

    direction_id = fields.Many2one(
        'recruitment.direction',
        string='Direction',
        related='project_id.direction_id',
        store=True,
        readonly=True,
    )

    director_id = fields.Many2one(
        'res.users',
        string="Directeur d'entité",
        related='project_id.director_id',
        store=True,
        readonly=True,
    )

    # =========================================================
    # DATES
    # =========================================================

    date_start = fields.Date(
        string='Date début',
    )

    date_end = fields.Date(
        string='Date fin',
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
        tracking=True,
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
    # TOTAL PLANNED
    # =========================================================

    total_planned = fields.Integer(
        string='Total planifié',
        compute='_compute_totals',
        store=True,
        readonly=True,
    )

    # =========================================================
    # CURRENCY
    # =========================================================

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        related='project_id.direction_id.director_id.company_id.currency_id',
        store=True,
        readonly=True,
    )

    # =========================================================
    # ANNUAL SALARY COST
    # =========================================================

    annual_salary_cost = fields.Float(
        string='Coût salarial annuel total',
        compute='_compute_totals',
        store=True,
        readonly=True,
    )

    # =========================================================
    # DG VALIDATION
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
    # DRH VALIDATION
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
            vals['ref'] = (
                self.env['ir.sequence'].next_by_code(
                    'recruitment.planning.header'
                ) or 'PLA'
            )

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
    # CONSTRAINT DATES
    # =========================================================

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if (
                record.date_start
                and record.date_end
                and record.date_end < record.date_start
            ):
                raise ValidationError(
                    "La date de fin doit être supérieure "
                    "ou égale à la date de début."
                )

    # =========================================================
    # CONSTRAINT PROJECT / YEAR
    # =========================================================

    @api.constrains('year', 'project_id')
    def _check_unique_year_project(self):
        for record in self:

            if not record.project_id:
                continue

            existing = self.search(
                [
                    ('id', '!=', record.id),
                    ('year', '=', record.year),
                    ('project_id', '=', record.project_id.id),
                    ('state', '!=', 'cancelled'),
                ],
                limit=1,
            )

            if existing:
                raise ValidationError(
                    "Une planification existe déjà pour "
                    "ce projet et cette année."
                )

    # =========================================================
    # WORKFLOW - SUBMIT TO RH
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
    # WORKFLOW - RH → DG
    # =========================================================

    def action_submit_dg(self):
        for record in self:

            if record.state != 'rh_review':
                raise ValidationError(
                    'Le planning doit être en contrôle RH.'
                )

            for line in record.line_ids:

                if line.estimated_salary <= 0:
                    raise ValidationError(
                        'Le salaire estimé doit être renseigné '
                        'par le RH pour toutes les lignes.'
                    )

            record.write({
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

            record.write({
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

            record.write({
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

            record.write({
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

            record.write({
                'state': 'cancelled',
            })