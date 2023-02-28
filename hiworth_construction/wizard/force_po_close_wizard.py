from openerp import models, fields, api,_
from openerp.exceptions import except_orm,ValidationError


class ForcePoClose(models.TransientModel):
    _name = 'force.po.close'

    @api.model
    def default_get(self,fields):
        res = super(ForcePoClose, self).default_get(fields)
        context = self._context
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        if active_model == 'purchase.order':
            for acti in active_ids:
                active = self.env['purchase.order'].browse(acti)
                value_list = []
                for line in active.order_line:
                    if (line.required_qty - (line.received_qty + line.closed_qty)) != 0:
                        value_list.append((0,0,{'product_id':line.product_id.id,
                                                'qty':line.required_qty - (line.received_qty + line.closed_qty)}))
                res.update({'force_po_close_ids':value_list})
        return res

    force_po_close_ids = fields.One2many('force.po.close.line','force_po_close_id',"Foreclosure")

    @api.multi
    def action_submit(self):
        context = self._context
        active_model = context.get('active_model')
        active_ids = context.get('active_ids')
        if active_model == 'purchase.order':
            for acti in active_ids:
                active = self.env['purchase.order'].browse(acti)
                flag = 0
                for line in active.order_line:
                    for rec in self.force_po_close_ids:
                        if line.product_id.id == rec.product_id.id:
                            line.closed_qty =line.closed_qty +  rec.closed_qty
                            if line.required_qty != (line.received_qty + line.closed_qty):
                                flag=1

                if flag==0:
                    active.state = 'done'
                    if active.site_purchase_id:
                        active.site_purchase_id.state = 'received'
                    else:
                        for site in active.site_purchase_ids:
                            site.state = 'received'



class ForcePoCloseLine(models.TransientModel):
    _name = 'force.po.close.line'

    @api.constrains('qty','closed_qty')
    def check_qty(self):
        for rec in self:
            if rec.qty < rec.closed_qty:
                raise ValidationError(_('Foreclosure Quantity cannot be greater than Remaining Quantity.'))

    product_id = fields.Many2one('product.product',"Product")
    qty = fields.Float("Remaining Quantity")
    closed_qty = fields.Float("Closed Quantity")
    force_po_close_id = fields.Many2one('force.po.close')
