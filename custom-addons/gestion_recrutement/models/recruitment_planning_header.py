from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError


class RecruitmentPlanningHeader(models.Model):
    _name = 'recruitment.planning.header'
    _description = 'Recruitment Planning Header'
    _inherit = [
        'mail.thread',
        'mail.activity.mixin',
    ]
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

    year = fields.Char(
    string='Année',
    required=True,
    size=4,
    default=lambda self: str(fields.Date.today().year + 1),
)

    sequence = fields.Integer(
        string='Séquence',
        default=10,
    )

    # =========================================================
    # PROJECT / RESPONSABLE
    # =========================================================

    created_by_id = fields.Many2one(
        'res.users',
        string='Demandeur',
        required=True,
        default=lambda self: self.env.user,
        readonly=True,
    )

    project_id = fields.Many2one(
        'recruitment.project',
        string='Projet',
        required=True,
        ondelete='restrict',
        
    )

    director_id = fields.Many2one(
        'res.users',
        string="Directeur d'entité",
        readonly=True,
        default=lambda self: (
        self.env.user
        if self.env.user.has_group(
            'gestion_recrutement.group_recruitment_directeur_entite'
        )
        else False
        ),
    )

    # =========================================================
    # STATE
    # =========================================================

    state = fields.Selection(
        [
            ('draft', 'Brouillon'),
            ('director_validation', 'Validation Directeur'),
            ('rh_review', 'Contrôle RH'),
            ('drh_validation', 'Validation DRH'),
            ('dg_validation', 'Validation DG'),
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
    # TOTAL PLANIFIÉ
    # =========================================================

    total_planned = fields.Integer(
        string='Total planifié',
        compute='_compute_totals',
        store=True,
        readonly=True,
    )

    # =========================================================
    # DEVISE
    # =========================================================

    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id,
        readonly=True,
    )

    # =========================================================
    # COÛT SALARIAL ANNUEL
    # =========================================================

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


    created_by = fields.Many2one(
    'res.users',
    string='Demandeur',
    readonly=True,
    default=lambda self: self.env.user,
   )

    created_by_role = fields.Selection(
    [
        ('directeur', "Directeur d'entité"),
        ('chef_service', 'Chef de service'),
    ],
    string='Profil créateur',
    readonly=True,
    )

    # =========================================================
    # GET DIRECTOR
    # =========================================================

    def _get_planning_director(self, project):

        user = self.env.user

        # -----------------------------------------------------
        # 1. DIRECTEUR D'ENTITÉ
        # -----------------------------------------------------

        if user.has_group(
            'gestion_recrutement.group_recruitment_directeur_entite'
        ):
            return user
        # -----------------------------------------------------
        # 2. CHEF DE SERVICE
        # -----------------------------------------------------

        if user.has_group(
            'gestion_recrutement.group_recruitment_chef_service'
        ):
            if not project.direction_id:
                raise ValidationError(
                    "Le projet sélectionné n'est associé "
                    "à aucune direction."
                )
            if not project.direction_id.director_id:
                raise ValidationError(
                    "La direction du projet ne possède "
                    "aucun directeur d'entité."
                )
            return project.direction_id.director_id
        # -----------------------------------------------------
        # 3. USER SANS RÔLE
        # -----------------------------------------------------
        raise AccessError(
            "Votre utilisateur ne possède aucun rôle "
            "autorisé pour créer une planification."
        )

    # =========================================================
    # CHECK PROJECT ACCESS
    # =========================================================
    def _check_project_access(self, project):
        if self.env.user not in project.user_id:
            raise AccessError(
                "Vous n'êtes pas autorisé à utiliser "
                "ce projet."
            )

    # =========================================================
    # ONCHANGE PROJECT
    # =========================================================
    @api.onchange('project_id')
    def _onchange_project_id(self):
    # -----------------------------------------------------
    # DIRECTEUR D'ENTITÉ
    # -----------------------------------------------------
     if self.env.user.has_group(
        'gestion_recrutement.group_recruitment_directeur_entite'
     ):
        self.director_id = self.env.user
        return
    # -----------------------------------------------------
    # CHEF DE SERVICE
    # -----------------------------------------------------
     if self.env.user.has_group(
        'gestion_recrutement.group_recruitment_chef_service'
     ):
        if not self.project_id:
            self.director_id = False
            return
        if not self.project_id.direction_id:
            self.director_id = False
            return {
                'warning': {
                    'title': 'Attention',
                    'message': (
                        "Le projet sélectionné n'est associé "
                        "à aucune direction."
                    ),
                }
            }

        if not self.project_id.direction_id.director_id:
            self.director_id = False

            return {
                'warning': {
                    'title': 'Attention',
                    'message': (
                        "La direction du projet ne possède "
                        "aucun directeur d'entité."
                    ),
                }
            }
        self.director_id = (
            self.project_id.direction_id.director_id
        )
    # =========================================================
    # CREATE
    # =========================================================

    # 
    

    @api.model
    def create(self, vals):

     user = self.env.user

    # =====================================================
    # DIRECTEUR D'ENTITÉ
    # =====================================================

     if user.has_group(
        'gestion_recrutement.group_recruitment_directeur_entite'
    ):

        vals.update({
            'created_by_id': user.id,
            'created_by_role': 'directeur',
            'director_id': user.id,
        })

    # =====================================================
    # CHEF DE SERVICE
    # =====================================================

     elif user.has_group(
        'gestion_recrutement.group_recruitment_chef_service'
    ):

        project_id = vals.get('project_id')

        if not project_id:
            raise ValidationError(
                "Vous devez sélectionner un projet."
            )

        project = self.env[
            'recruitment.project'
        ].browse(project_id).exists()

        if not project:
            raise ValidationError(
                "Le projet sélectionné n'existe pas."
            )
        if user not in project.user_id:
            raise AccessError(
                "Vous n'êtes pas autorisé à utiliser "
                "ce projet."
            )

        if not project.direction_id:
            raise ValidationError(
                "Le projet sélectionné n'est associé "
                "à aucune direction."
            )

        if not project.direction_id.director_id:
            raise ValidationError(
                "La direction du projet ne possède "
                "aucun directeur d'entité."
            )

        vals.update({
            'created_by_id': user.id,
            'created_by_role': 'chef_service',
            'director_id': project.direction_id.director_id.id,
        })

     else:

        raise AccessError(
            "Votre utilisateur ne possède aucun rôle "
            "autorisé à créer une planification."
        )

    # =====================================================
    # REFERENCE
    # =====================================================

     if vals.get('ref', 'PLA') == 'PLA':

        vals['ref'] = (
            self.env[
                'ir.sequence'
            ].next_by_code(
                'recruitment.planning.header'
            ) or 'PLA'
        )

     return super().create(vals)
    # =========================================================
    # WRITE
    # =========================================================

    def write(self, vals):
        vals = dict(vals)
        if (
            'director_id' in vals
            and not self.env.context.get(
                'auto_director'
            )
        ):
            raise AccessError(
                "Le directeur d'entité est déterminé "
                "automatiquement par le système."
            )
        if 'project_id' in vals:
            project = self.env[
                'recruitment.project'
            ].browse(
                vals['project_id']
            ).exists()
            if not project:
                raise ValidationError(
                    "Le projet sélectionné n'existe pas."
                )
            self._check_project_access(project)
            director = self._get_planning_director(
                project
            )

            vals['director_id'] = director.id

            return super(
                RecruitmentPlanningHeader,
                self.with_context(
                    auto_director=True
                )
            ).write(vals)

        return super().write(vals)

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
                record.line_ids.mapped(
                    'planned_qty'
                )
            )

            record.annual_salary_cost = sum(
                record.line_ids.mapped(
                    'annual_salary_cost'
                )
            )

    # =========================================================
    # CONSTRAINT YEAR
    # =========================================================

    @api.constrains('year')
    def _check_year(self):
      for record in self:
        if not record.year:
            continue
        if not record.year.isdigit() or len(record.year) != 4:
            raise ValidationError(
                "L'année doit contenir exactement 4 chiffres. "
                "Exemple : 2026."
            )
        year = int(record.year)
        if year < 2000 or year > 2100:
            raise ValidationError(
                "L'année doit être comprise entre 2000 et 2100."
            )
     # =========================================================
     # WORKFLOW 1 : DIRECTEUR → RH
     # =========================================================

    def action_submit_rh(self):
     for record in self:

        if record.state != 'draft':
            raise ValidationError(
                'Seul un planning en brouillon peut être soumis.'
            )

        if record.created_by_role != 'directeur':
            raise AccessError(
                'Cette action est réservée aux planifications '
                'créées directement par un directeur.'
            )

        if not record.line_ids:
            raise ValidationError(
                'Vous devez ajouter au moins une ligne de planification.'
            )

        record.write({
            'state': 'rh_review',
        })


         # =========================================================
         # WORKFLOW 2 : RH → DRH
         # =========================================================

    def action_submit_drh(self):

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

        record.write({
            'state': 'drh_validation',
        })


    # =========================================================
    # WORKFLOW 3 : DRH → DG
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
            'state': 'dg_validation',
        })


    # =========================================================
    # WORKFLOW 4 : DG → ACTIVE
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
            'budget_validated': True,
            'state': 'active',
        })



    def action_return(self):
     self.ensure_one()

     if self.state not in [
        'rh_review',
        'director_validation',
        'drh_validation',
        'dg_validation',
    ]:
        raise ValidationError(
            'Cette planification ne peut pas être retournée '
            'depuis son état actuel.'
        )

    # =====================================================
    # SECURITY
    # =====================================================

     if self.state == 'rh_review':

        if not self.env.user.has_group(
            'gestion_recrutement.group_recruitment_rh'
        ):
            raise AccessError(
                'Seul le RH peut retourner cette planification.'
            )

     elif self.state == 'director_validation':

        if not self.env.user.has_group(
            'gestion_recrutement.group_recruitment_directeur_entite'
        ):
            raise AccessError(
                "Seul le Directeur d'entité peut retourner "
                "cette planification."
            )

        if self.director_id != self.env.user:
            raise AccessError(
                "Seul le Directeur d'entité désigné "
                "peut retourner cette planification."
            )

        elif self.state == 'drh_validation':

         if not self.env.user.has_group(
            'gestion_recrutement.group_recruitment_drh'
        ):
            raise AccessError(
                'Seul le DRH peut retourner cette planification.'
            )

     elif self.state == 'dg_validation':

        if not self.env.user.has_group(
            'gestion_recrutement.group_recruitment_dg'
        ):
            raise AccessError(
                'Seul le DG peut retourner cette planification.'
            )

    # =====================================================
    # OUVRIR LE WIZARD
    # =====================================================

     return {
        'type': 'ir.actions.act_window',
        'name': 'Retour de la planification',
        'res_model': 'recruitment.planning.return.wizard',
        'view_mode': 'form',
        'view_id': self.env.ref(
            'gestion_recrutement.view_recruitment_planning_return_wizard_form'
        ).id,
        'target': 'new',
        'context': {
            'default_planning_id': self.id,
        },
    }

     # =========================================================
     # WORKFLOW 5 : CLOSE
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
    def action_submit_director(self):

     for record in self:

        if record.state != 'draft':
            raise ValidationError(
                "Seul un planning en brouillon "
                "peut être soumis au Directeur."
            )

        if record.created_by_role != 'chef_service':
            raise ValidationError(
                "Cette action est réservée "
                "aux plannings créés par un Chef de service."
            )

        if not record.line_ids:
            raise ValidationError(
                "Vous devez ajouter au moins une ligne "
                "de planification."
            )

        if not record.director_id:
            raise ValidationError(
                "Aucun Directeur d'entité n'est défini."
            )

        record.write({
            'state': 'director_validation',
        })

         # =========================================================

    def action_validate_director(self):

       for record in self:

        if record.state != 'director_validation':
            raise ValidationError(
                "Cette planification n'est pas "
                "en attente de validation du Directeur."
            )

        if record.director_id != self.env.user:
            raise AccessError(
                "Seul le Directeur d'entité désigné "
                "peut valider cette planification."
            )

        record.write({
            'state': 'rh_review',
        })




    