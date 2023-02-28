
from datetime import datetime
from openerp import tools
#from openerp.osv import fields, osv
from openerp import fields, models, api
from openerp.tools.translate import _

# class stock_history(models.Model):
#     _inherit = 'stock.history'
    
#     @api.multi
#     @api.depends('product_id')
#     def _compute_inventory_value_with_tax(self):
        
#         for line in self:
#             for product in self.product_id:
#                 self.env.cr.execute("SELECT tax_id from product_supplier_taxes_rel where prod_id = %d" % (product.id))
#                 taxes = self.env.cr.fetchone()
#                 print 'taxes================================', taxes
    
#     inventory_value_with_tax = fields.Float(compute='_compute_inventory_value_with_tax', store="True", string="Inventory Value With Tax")
    

