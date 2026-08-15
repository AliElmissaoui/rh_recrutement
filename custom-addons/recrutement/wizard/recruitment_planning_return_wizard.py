from odoo import models, fields, api
from odoo.exceptions import ValidationError


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
        # DETERMINER L'ETAT PRECEDENT
        # =====================================================

        previous_states = {
            'rh_review': 'draft',
            'drh_validation': 'rh_review',
            'dg_validation': 'drh_validation',
        }

        if current_state not in previous_states:
            raise ValidationError(
                'Cette planification ne peut pas être retournée '
                'depuis son état actuel.'
            )

        previous_state = previous_states[current_state]

        # =====================================================
        # SECURITY
        # =====================================================

        if current_state == 'rh_review':

            if not self.env.user.has_group(
                'recrutement.group_recruitment_rh'
            ):
                raise ValidationError(
                    'Seul le RH peut retourner cette planification.'
                )

        elif current_state == 'drh_validation':

            if not self.env.user.has_group(
                'recrutement.group_recruitment_drh'
            ):
                raise ValidationError(
                    'Seul le DRH peut retourner cette planification.'
                )

        elif current_state == 'dg_validation':

            if not self.env.user.has_group(
                'recrutement.group_recruitment_dg'
            ):
                raise ValidationError(
                    'Seul le DG peut retourner cette planification.'
                )

        # =====================================================
        # HISTORIQUE
        # =====================================================

        message = (
            '<b>Retour de la planification</b><br/>'
            '<b>De :</b> %s<br/>'
            '<b>Vers :</b> %s<br/>'
            '<b>Utilisateur :</b> %s<br/>'
            '<b>Motif :</b><br/>%s'
        ) % (
            dict(
                planning._fields['state'].selection
            ).get(current_state),

            dict(
                planning._fields['state'].selection
            ).get(previous_state),

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
            'res_model': 'recruitment.planning.header',
            'res_id': planning.id,
            'view_mode': 'form',
            'target': 'current',
        }