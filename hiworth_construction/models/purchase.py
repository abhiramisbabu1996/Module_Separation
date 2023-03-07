from openerp import fields, models, api
from openerp.tools import amount_to_text_en


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    supplier_quotation_reference = fields.Char()

    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].next_by_code('purchase.order').split('/')
        project_number = self.env['project.project'].browse(vals.get('project_id')).project_number
        if project_number:
            project_number = project_number.split('-')
            name = sequence[0]+"/"+sequence[1]+"/"+project_number[1]+"/"+sequence[2]
        else:
            name = sequence
        vals['name'] = name
        return super(PurchaseOrder,self).create(vals)


    def amount_to_text(self, amount, currency):
        cur = currency.name
        res = self.env['account.invoice'].amount_to_text(amount, cur)
        return res
