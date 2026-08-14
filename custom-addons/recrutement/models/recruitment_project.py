from odoo import models, fields, api
from odoo.exceptions import ValidationError


class RecruitmentProject(models.Model):
    _name = 'recruitment.project'
    _description = 'Projet de recrutement'
    _order = 'name'

    # =========================================================
    # IDENTIFICATION
    # =========================================================

    name = fields.Char(
        string='Projet',
        required=True,
        index=True,
    )

    description = fields.Text(
        string='Description',
    )

    # =========================================================
    # TYPE DE RESPONSABLE
    # =========================================================

    owner_type = fields.Selection(
        [
            ('chef_service', 'Chef de service'),
            ('directeur', 'Directeur'),
        ],
        string='Responsable du projet',
        required=True,
        default='chef_service',
    )

    # =========================================================
    # CHEF DE SERVICE
    # =========================================================

    chef_service_id = fields.Many2one(
        'res.users',
        string='Chef de service',
        domain="[('share', '=', False)]",
    )

    # =========================================================
    # DIRECTION
    # =========================================================

    direction_id = fields.Many2one(
        'recruitment.direction',
        string='Direction',
    )

    # =========================================================
    # DIRECTEUR
    # =========================================================

    director_id = fields.Many2one(
        'res.users',
        string="Directeur d'entité",
        domain="[('share', '=', False)]",
    )

    # =========================================================
    # ACTIVE
    # =========================================================

    active = fields.Boolean(
        string='Actif',
        default=True,
    )

    # =========================================================
    # ONCHANGE RESPONSABLE
    # =========================================================

    @api.onchange('owner_type')
    def _onchange_owner_type(self):

        for record in self:

            if record.owner_type == 'chef_service':

                # Le projet appartient au Chef de service.
                # La direction sera sélectionnée.
                # Le directeur sera récupéré automatiquement.

                record.director_id = False

            elif record.owner_type == 'directeur':

                # Projet directement rattaché au Directeur.

                record.chef_service_id = False
                record.direction_id = False

    # =========================================================
    # ONCHANGE DIRECTION
    # =========================================================

    @api.onchange('direction_id')
    def _onchange_direction_id(self):

        for record in self:

            if (
                record.owner_type == 'chef_service'
                and record.direction_id
            ):

                # Directeur automatique depuis la Direction.

                record.director_id = (
                    record.direction_id.director_id
                )

    # =========================================================
    # ONCHANGE CHEF DE SERVICE
    # =========================================================

    @api.onchange('chef_service_id')
    def _onchange_chef_service_id(self):

        for record in self:

            if record.owner_type == 'chef_service':

                # Si le chef change, on garde la direction
                # sélectionnée et on recalcule le directeur.

                if record.direction_id:
                    record.director_id = (
                        record.direction_id.director_id
                    )

    # =========================================================
    # CREATE
    # =========================================================

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:

            owner_type = vals.get('owner_type')

            # -------------------------------------------------
            # CHEF DE SERVICE
            # -------------------------------------------------

            if owner_type == 'chef_service':

                direction_id = vals.get('direction_id')

                if direction_id:

                    direction = self.env[
                        'recruitment.direction'
                    ].browse(direction_id)

                    if direction.exists():

                        vals['director_id'] = (
                            direction.director_id.id
                        )

            # -------------------------------------------------
            # DIRECTEUR
            # -------------------------------------------------

            elif owner_type == 'directeur':

                vals['chef_service_id'] = False
                vals['direction_id'] = False

        return super().create(vals_list)

    # =========================================================
    # WRITE
    # =========================================================

    def write(self, vals):

        for record in self:

            owner_type = vals.get(
                'owner_type',
                record.owner_type,
            )

            # -------------------------------------------------
            # CAS CHEF DE SERVICE
            # -------------------------------------------------

            if owner_type == 'chef_service':

                direction_id = vals.get(
                    'direction_id',
                    record.direction_id.id,
                )

                if direction_id:

                    direction = self.env[
                        'recruitment.direction'
                    ].browse(direction_id)

                    if direction.exists():

                        vals['director_id'] = (
                            direction.director_id.id
                        )

                # Un projet Chef de service doit garder
                # son chef.

                if (
                    'chef_service_id' not in vals
                    and not record.chef_service_id
                ):
                    raise ValidationError(
                        'Un chef de service est obligatoire '
                        'pour ce projet.'
                    )

            # -------------------------------------------------
            # CAS DIRECTEUR
            # -------------------------------------------------

            elif owner_type == 'directeur':

                vals['chef_service_id'] = False
                vals['direction_id'] = False

        return super().write(vals)

    # =========================================================
    # CONSTRAINTS
    # =========================================================

    @api.constrains(
        'owner_type',
        'chef_service_id',
        'direction_id',
        'director_id',
    )
    def _check_project_configuration(self):

        for project in self:

            # =================================================
            # CAS 1 : CHEF DE SERVICE
            # =================================================

            if project.owner_type == 'chef_service':

                if not project.chef_service_id:
                    raise ValidationError(
                        'Un chef de service est obligatoire '
                        'pour ce type de projet.'
                    )

                if not project.direction_id:
                    raise ValidationError(
                        'Une direction est obligatoire '
                        'pour un projet de Chef de service.'
                    )

                if not project.direction_id.director_id:
                    raise ValidationError(
                        'La direction sélectionnée ne possède '
                        'pas encore de directeur.'
                    )

                if (
                    project.director_id
                    != project.direction_id.director_id
                ):
                    raise ValidationError(
                        'Le directeur doit correspondre '
                        'au directeur de la direction sélectionnée.'
                    )

            # =================================================
            # CAS 2 : DIRECTEUR
            # =================================================

            elif project.owner_type == 'directeur':

                if not project.director_id:
                    raise ValidationError(
                        'Un directeur est obligatoire '
                        'pour ce type de projet.'
                    )

                if project.chef_service_id:
                    raise ValidationError(
                        'Un projet appartenant directement '
                        'à un directeur ne peut pas avoir '
                        'de chef de service.'
                    )

                if project.direction_id:
                    raise ValidationError(
                        'Un projet appartenant directement '
                        'à un directeur ne doit pas avoir '
                        'de direction.'
                    )

    # =========================================================
    # DISPLAY NAME
    # =========================================================

    def name_get(self):

        result = []

        for record in self:

            name = record.name

            if record.owner_type == 'chef_service':

                if record.chef_service_id:
                    name += (
                        f" - {record.chef_service_id.name}"
                    )

            elif record.owner_type == 'directeur':

                if record.director_id:
                    name += (
                        f" - {record.director_id.name}"
                    )

            result.append((record.id, name))

        return result