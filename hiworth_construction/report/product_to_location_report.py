from openerp import fields, models, api
from datetime import datetime
import calendar
from openerp.osv import osv
from decimal import Decimal
from dateutil import tz

class stock_locaton(models.Model):
    _inherit = 'stock.location'
    
    temp_product_qty = fields.Float('Temp Product Qty', default=0.0)
    temp_inventry_value = fields.Float('Temp Inventory Value', default=0.0)
    temp_avg_unit_price = fields.Float('Temp Avg Price', default=0.0)


    default_transportation_account = fields.Many2one('account.account', 'Transportation Account')
    default_unloading_account = fields.Many2one('account.account', 'Unloading Account')
    default_gst_account = fields.Many2one('account.account', 'GST Account')


class report_product(models.TransientModel):
    _name = 'report.product'
    
    @api.onchange('product_id')
    def onchange_category(self):
        if self.report_id.category_id.id != False:
            return {
                'domain': {
                        'product_id':[('categ_id','=', self.report_id.category_id.id)]
                    }
                }
    
    product_id = fields.Many2one('product.product', 'Product')
    report_id = fields.Many2one('product.to.location.report')
    
    
class report_locaton(models.TransientModel):
    _name = 'report.location'
    
    location_id = fields.Many2one('stock.location', 'Location')
    report_id = fields.Many2one('product.to.location.report')
    


class product_to_location_report(models.TransientModel):
    _name='product.to.location.report'
    

    from_date = fields.Date(default=lambda self: self.default_time_range('from'))
    to_date = fields.Date(default=lambda self: self.default_time_range('to'))
    select_product = fields.Boolean('Select Product')
    category_id = fields.Many2one('product.category', 'Category')
    product_ids = fields.One2many('report.product', 'report_id', 'Products') 
    select_location = fields.Boolean('Select Location')
    location_ids = fields.One2many('report.location', 'report_id', 'Location')
    
    


    # Calculate default time ranges
    @api.model
    def default_time_range(self, type):
        year = datetime.today().year
        month = datetime.today().month
        last_day = calendar.monthrange(datetime.today().year,datetime.today().month)[1]
        first_day = 1
        if type=='from':
            return datetime(year, month, first_day)
        elif type=='to':
            return datetime(year, month, last_day)

    @api.multi
    def print_product_to_location_report(self):
        self.ensure_one()
    
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_product_to_location_template',
            'datas': datas,
#             'report_type': 'qweb-pdf',
            
        }
        
    @api.multi
    def view_product_to_location_report(self):
        self.ensure_one()
        
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_product_to_location_template',
            'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date,'source': self.source.name,'destination': self.destination.name}
            'report_type': 'qweb-html',
        }
        
        
    @api.multi
    def get_products(self,location):
        if self.category_id:
            category = self.category_id
            products = self.env['product.product'].search([('categ_id','=',self.category_id.id)])
        else:
            category = self.env['product.category'].search([])
        if self.select_product:
            products = []
            for pro in self.product_ids:
                products.append(pro.product_id)
            products = list(set(products))
        else:
            products = self.env['product.product'].search([])
        item_list = []
        item_dict = {}
        for prod in products:
            item_dict = {}
            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Asia/Kolkata')
            # from_zone = tz.tzutc()
            # to_zone = tz.tzlocal()
            utc = datetime.strptime(self.from_date, '%Y-%m-%d')
            utc = utc.replace(tzinfo=from_zone)
            central = utc.astimezone(to_zone)
            from_date = central.strftime("%Y-%m-%d 00:00:00")
            from_zone = tz.gettz('UTC')
            to_zone = tz.gettz('Asia/Kolkata')
            # from_zone = tz.tzutc()
            # to_zone = tz.tzlocal()
            utc = datetime.strptime(self.to_date, '%Y-%m-%d')
            utc = utc.replace(tzinfo=from_zone)
            central = utc.astimezone(to_zone)
            to_date = central.strftime("%Y-%m-%d 23:59:59")
            stock_move_in = self.env['stock.move'].search([('location_dest_id','=',location.id),
                                                           ('product_id','=',prod.id),
                                                           ('state','=','done'),
                                                           ('date','>=',from_date),
                                                           ('date','<=',to_date)])
            qty_in = 0
            for stock_in in stock_move_in:
                qty_in += stock_in.product_uom_qty

            stock_move_out = self.env['stock.move'].search([('location_id', '=', location.id),
                                                           ('product_id', '=', prod.id),
                                                           ('state', '=', 'done'),
                                                           ('date', '>=', from_date),
                                                           ('date', '<=', to_date)])
            qty_out = 0
            for stock_out in stock_move_out:
                qty_out += stock_out.product_uom_qty

            stock_current = self.env['stock.history'].search([('product_id','=',prod.id),
                                                              ('date','<=',to_date),
                                                              ('location_id','=',location.id)])
            qty_curr = 0
            for stock_out in stock_current:
                qty_curr += stock_out.quantity
            if not qty_in==0 or not qty_out ==0 or not qty_curr==0:
                item_dict.update({'item':prod.name,
                                  'category':prod.categ_id.name,
                                  'qty_in':qty_in,
                                    'qty_out':qty_out,
                                    'current':qty_curr,
                                    'unit_price':prod.uom_id.name,
                                    'total':qty_curr * prod.standard_price *qty_curr })
                item_list.append(item_dict)
        return item_list



            
    @api.multi
    def get_locations(self):
       if self.select_location:

           location_list =[]

           for loc in self.location_ids:
               location_list.append(loc.location_id)
           location_list = list(set(location_list))

           return location_list

       else:
            location_list = self.env['stock.location'].search([])
            print "gggggggggggggggggggggggggggggg", location_list
            return location_list
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
