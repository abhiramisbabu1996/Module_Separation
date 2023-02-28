from openerp import fields, models, api
import datetime, calendar
from openerp.osv import osv

class report_location_stock(models.TransientModel):
    _name='report.location.stock'


    from_date=fields.Date('Date From')
    to_date=fields.Date('Date To')
    location_id = fields.Many2one('stock.location', 'Location')
    company_id =fields.Many2one('res.company','Company')
    date_today = fields.Date('Date')
    category = fields.Many2one('product.category')

    _defaults = {
        'date_today': fields.Date.today(),
        'from_date': '2017-04-01',
        'to_date': fields.Date.today(),
    }

    @api.onchange('company_id')
    def onchange_field(self):
        if self.company_id.id != False:
            return {
                'domain': {
                'account_id': [('company_id', '=', self.company_id.id),('type', '=', 'view')],
                },
            }

    @api.multi
    def print_report_location_stock(self):
        self.ensure_one()
        if self.location_id.id == False:
            raise osv.except_osv(('Error'), ('Please select a proper location'))

        locations = self.env['stock.location']
        locationrecs = locations.search([('id','=',self.location_id.id)])

        datas = {
            'ids': locationrecs._ids,
            'model': locations._name,
            'form': locations.read(),
            'context':self._context,
        }

        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_location_stock',
            'datas': datas,
            'context':{'start_date': self.from_date, 'end_date': self.to_date, 'category': self.category.id}
        }
        
        
    @api.multi
    def view_report_location_stock(self):
        self.ensure_one()
        if self.location_id.id == False:
            raise osv.except_osv(('Error'), ('Please select a proper location'))

        locations = self.env['stock.location']
        locationrecs = locations.search([('id','=',self.location_id.id)])
                
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
        print "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",datas

        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_location_stock_view',
            'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date, 'category': self.category.id},
            'report_type': 'qweb-html',         
        }
        
    @api.multi
    def get_products(self):
        self.ensure_one()
        start_date = self.from_date
        end_date = self.to_date
        category = self.category

        if category.id != False:
            if category.name != 'ELECTRICAL':
                product_recs = self.env['product.product'].search([('type','=','product')]).filtered(lambda r: r.categ_id.id == category.id).sorted(lambda r: r.categ_id)
            else:
                product_recs = self.env['product.product'].search([('type', '=', 'consu')]).filtered(lambda r: r.categ_id.id == category.id).sorted(lambda r: r.categ_id)
                print "product listttttttttttttttttttttttttttttttttttttttttttttt", len(product_recs.ids)
        else:
            product_recs = self.env['product.product'].search([('type','=','product')]).sorted(lambda r: r.categ_id.name)
        
        
        for line in product_recs:
            temp_in = 0.0
            temp_out = 0.0
            line.temp_remain = 0.0
#             if line.balance!=0.0:
            move_lines = self.env['stock.move'].search([('location_id','=',self.location_id.id),('product_id','=',line.id),('date','>=',start_date),('date','<=',end_date),('state','=','done')])
            for moves in move_lines:
                
                temp_out+=moves.product_uom_qty

            move_lines = self.env['stock.move'].search([('location_dest_id','=',self.location_id.id),('product_id','=',line.id),('date','>=',start_date),('date','<=',end_date),('state','=','done')])
            for moves in move_lines:

                temp_in+=moves.product_uom_qty
            line.temp_remain = temp_in - temp_out
        
        return product_recs

class StockLocation(models.Model):
    _inherit='stock.location'

    @api.model
    def get_products(self, location_id):
        start_date = self._context['start_date']
        end_date = self._context['end_date']
        category = self._context['category']
        catagory_pool = self.env['product.category']
        category_id = catagory_pool.browse(category)
        if category:
            if category_id.name != 'ELECTRICAL':
                product_recs = self.env['product.product'].search([('type', '=', 'product')]).filtered(
                    lambda r: r.categ_id.id == category).sorted(lambda r: r.categ_id)
            else:
                product_recs = self.env['product.product'].search([('type', '=', 'consu')]).filtered(
                    lambda r: r.categ_id.id == category).sorted(lambda r: r.categ_id)
    
           
        else:
            product_recs = self.env['product.product'].search([('type','=','product')]).sorted(lambda r: r.categ_id.name)

        if category_id.name != 'ELECTRICAL':
            for line in product_recs:
                temp_in = 0.0
                temp_out = 0.0
                line.temp_remain = 0.0
    #             if line.balance!=0.0:
                move_lines = self.env['stock.move'].search([('location_id','=',location_id),('product_id','=',line.id),('date','>=',start_date),('date','<=',end_date),('state','=','done')])
                for moves in move_lines:
                    temp_out+=moves.product_uom_qty
    
                move_lines = self.env['stock.move'].search([('location_dest_id','=',location_id),('product_id','=',line.id),('date','>=',start_date),('date','<=',end_date),('state','=','done')])
                for moves in move_lines:
                    temp_in+=moves.product_uom_qty
                line.temp_remain = temp_in - temp_out
        else:

            for line in product_recs:
                    temp_in = 0.0
                    temp_out = 0.0
                    line.temp_remain = 0.0
                    #             if line.balance!=0.0:
                    move_lines = self.env['stock.move'].search(
                        [('location_id', '=', location_id), ('product_id', '=', line.id), ('date', '>=', start_date),
                         ('date', '<=', end_date), ('state', '=', 'done')])
                    for moves in move_lines:
                        print "qqqttttttttttttttttttttttttt",moves.product_uom_qty
                        temp_out += moves.product_uom_qty
        
                    move_lines = self.env['stock.move'].search(
                        [('location_dest_id', '=', location_id), ('product_id', '=', line.id), ('date', '>=', start_date),
                         ('date', '<=', end_date), ('state', '=', 'done')])
                    for moves in move_lines:
                        print "qqqttttttttttttttttttttttttt", moves.product_uom_qty
                        temp_in += moves.product_uom_qty
                    line.temp_remain = temp_in + temp_out


        return product_recs
