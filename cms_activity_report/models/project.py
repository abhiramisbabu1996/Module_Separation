from openerp import fields, models, api


class TaskLineInherit(models.Model):
    _inherit = "task.line.custom"

    partner_statement_id = fields.Many2one('partner.daily.statement')
