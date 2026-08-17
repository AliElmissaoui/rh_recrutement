from odoo import models, fields, api
from odoo.exceptions import ValidationError,AccessError


class RecruitmentPlanningReturnWizard(models.TransientModel):
    _name = 'recruitment.planning.return.wizard'
    _description = 'Retour de la planification de recrutement'

    planning_id = fields.Many2one(
        'recruitment.planning.header',
        string='Planification',
        required=True,
        readonly=True,
    )

    current_state = fields.Selection(
        related='planning_id.state',
        string='État actuel',
        readonly=True,
    )

    reason = fields.Text(
        string='Motif du retour',
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)

        planning = self.env[
            'recruitment.planning.header'
        ].browse(
            self.env.context.get('active_id')
        )

        if planning:
            res['planning_id'] = planning.id

        return res

    def action_confirm_return(self):
     self.ensure_one()

     if not self.reason or not self.reason.strip():
        raise ValidationError(
            'Veuillez renseigner le motif du retour.'
        )

     planning = self.planning_id

     if not planning:
        raise ValidationError(
            'Aucune planification sélectionnée.'
        )

     current_state = planning.state

    # =====================================================
    # DÉTERMINER L'ÉTAT DE RETOUR
    # =====================================================

     if current_state == 'rh_review':
        if planning.created_by_role == 'directeur':
            previous_state = 'draft'
        elif planning.created_by_role == 'chef_service':
            previous_state = 'director_validation'

        else:
            raise ValidationError(
                "Le profil du créateur de la planification "
                "n'est pas défini."
            )

     elif current_state == 'director_validation':
        previous_state = 'draft'

     elif current_state == 'drh_validation':
        previous_state = 'rh_review'

     elif current_state == 'dg_validation':
        previous_state = 'drh_validation'

     else:
        raise ValidationError(
            'Cette planification ne peut pas être retournée '
            'depuis son état actuel.'
        )

    # RH
     if current_state == 'rh_review':

        if not self.env.user.has_group(
            'gestion_recrutement.group_recruitment_rh'
        ):
            raise AccessError(
                'Seul le RH peut retourner cette planification.'
            )

    # DIRECTEUR
     elif current_state == 'director_validation':

        if not self.env.user.has_group(
            'gestion_recrutement.group_recruitment_directeur_entite'
        ):
            raise AccessError(
                'Seul le Directeur d’entité peut retourner '
                'cette planification.'
            )

        if planning.director_id != self.env.user:
            raise AccessError(
                'Seul le Directeur d’entité désigné peut '
                'retourner cette planification.'
            )

    # DRH
     elif current_state == 'drh_validation':

        if not self.env.user.has_group(
            'gestion_recrutement.group_recruitment_drh'
        ):
            raise AccessError(
                'Seul le DRH peut retourner cette planification.'
            )

    # DG
     elif current_state == 'dg_validation':

        if not self.env.user.has_group(
            'gestion_recrutement.group_recruitment_dg'
        ):
            raise AccessError(
                'Seul le DG peut retourner cette planification.'
            )

    # =====================================================
    # HISTORIQUE
    # =====================================================

     state_selection = dict(
        planning._fields['state'].selection
    )

     message = (
        '<b>Retour de la planification</b><br/>'
        '<b>De :</b> %s<br/>'
        '<b>Vers :</b> %s<br/>'
        '<b>Utilisateur :</b> %s<br/>'
        '<b>Motif :</b><br/>%s'
    ) % (
        state_selection.get(current_state),
        state_selection.get(previous_state),
        self.env.user.name,
        self.reason.strip(),
    )

    # =====================================================
    # CHANGE STATE
    # =====================================================

     planning.write({
        'state': previous_state,
    })

    # =====================================================
    # MESSAGE CHATTER
    # =====================================================

     planning.message_post(
        body=message,
        subtype_xmlid='mail.mt_note',
    )

     return {
    'type': 'ir.actions.act_window',
    'name': 'Planifications de recrutement',
    'res_model': 'recruitment.planning.header',
    'view_mode': 'list',
    'target': 'current',
   }