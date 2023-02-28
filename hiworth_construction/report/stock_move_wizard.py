from openerp import fields, models, api
import datetime, calendar
from openerp.osv import osv
from decimal import Decimal

class Report_Tasks(models.TransientModel):
    _name='report.tasks'

    @api.onchange('task_id')
    def onchange_task_id(self):
        for rec in self:
            project_list = []
            if self._context.get('location_id'):
                project = self.env['project.project'].search([('project_location_ids','in',[self._context.get('location_id')])])
                for pro in project:
                    project_list.append(pro.id)
            return  {'domain':{'task_id':[('project_id','in',project_list)]}}
    task_id = fields.Many2one('project.task', 'Task')
    location_id = fields.Many2one(related='task_id.project_id.location_id', string='Location')
    report_id = fields.Many2one('stock.move.report.wizard', 'Report')
    

class StockMoveReportWizard(models.TransientModel):
    _name='stock.move.report.wizard'

    from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    to_date=fields.Date(default=lambda self: self.default_time_range('to'))
    source=fields.Many2one('stock.location', 'Source')
    destination=fields.Many2one('stock.location', 'Destination')
    is_task_wise = fields.Boolean('Task Wise')
    is_product_wise = fields.Boolean('Product Wise')
    task_ids = fields.One2many('report.tasks', 'report_id', 'Tasks')
    select_tasks = fields.Boolean('Select Tasks')
    
    

    # Calculate default time ranges
    @api.model
    def default_time_range(self, type):
        year = datetime.date.today().year
        month = datetime.date.today().month
        last_day = calendar.monthrange(datetime.date.today().year,datetime.date.today().month)[1]
        first_day = 1
        if type=='from':
            return datetime.date(year, month, first_day)
        elif type=='to':
            return datetime.date(year, month, last_day)

    @api.multi
    def print_stock_move_report(self):
        self.ensure_one()
        stockmove = self.env['stock.move']
        if self.source.id != False and self.destination.id != False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('location_id','=',self.source.id),('location_dest_id','=',self.destination.id)])
        if self.source.id != False and self.destination.id == False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('location_id','=',self.source.id)])
        if self.source.id == False and self.destination.id != False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('location_dest_id','=',self.destination.id)])
        if self.source.id == False and self.destination.id == False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done')])
        
        if not stockmoverecs:
            raise osv.except_osv(('Error'), ('There are no material requests to display. Please make sure material requests exist.'))
#         if is_task_wise == True:
#             task_ids = []
#             task_ids = [task.id for task in self.task_ids]
# #             print 'Task_ids==================', task_ids
#             if len(task_ids) == 0:
#                 raise osv.except_osv(('Error'), ('Please Add Tasks'))
#             if len(task_ids) != 0:
                
        recordset = stockmoverecs.sorted(key=lambda r: r.date)
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_stock_move_template_view',
            'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date,'source': self.source.name,'destination': self.destination.name}
            'report_type': 'qweb-pdf',
        }
        
        
        
    @api.multi
    def view_stock_move_report(self):
        self.ensure_one()
        stockmove = self.env['stock.move']
        if self.source.id != False and self.destination.id != False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('location_id','=',self.source.id),('location_dest_id','=',self.destination.id)])
        if self.source.id != False and self.destination.id == False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('location_id','=',self.source.id)])
        if self.source.id == False and self.destination.id != False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('location_dest_id','=',self.destination.id)])
        if self.source.id == False and self.destination.id == False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done')])
        
        if not stockmoverecs:
            raise osv.except_osv(('Error'), ('There are no material requests to display. Please make sure material requests exist.'))
        
        recordset = stockmoverecs.sorted(key=lambda r: r.date)
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_stock_move_template_view',
            'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date,'source': self.source.name,'destination': self.destination.name}
            'report_type': 'qweb-html',
        }
    
    
        
    @api.multi
    def get_moves_task_wise(self,task):
        self.ensure_one()
#         print 'task=======================', task
        stockmove = self.env['stock.move']
        if self.source.id != False and self.destination.id != False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                 ('task_id','=',task.id),('location_id','=',self.source.id),('location_dest_id','=',self.destination.id)])
        if self.source.id != False and self.destination.id == False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('task_id','=',task.id),('location_id','=',self.source.id)])
        if self.source.id == False and self.destination.id != False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('task_id','=',task.id),('location_dest_id','=',self.destination.id)])
        if self.source.id == False and self.destination.id == False:
            stockmoverecs = stockmove.search([('task_id','=',task.id),('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done')])
        
        recordset = stockmoverecs.sorted(key=lambda r: r.date)
#         print 'recordset======================', recordset
        return recordset
        
    @api.multi
    def get_moves(self):
        self.ensure_one()
        stockmove = self.env['stock.move']
        
        if self.select_tasks == True:
            task_ids = []
            task_ids = [task.task_id.id for task in self.task_ids]
            task_ids = set(task_ids)
            task_ids = list(task_ids)
            if len(task_ids) == 0:
                raise osv.except_osv(('Error'), ('Please select atleast one task otherwise uncheck Select Task box.'))
            task_objs = self.env['project.task'].search([('id','in',task_ids)])
            
            if self.source.id != False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                     ('task_id','in',task_ids), ('location_id','=',self.source.id)])
            
            if self.source.id == False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('task_id','in',task_ids)])
            
            recordset = stockmoverecs.sorted(key=lambda r: r.date)
            return recordset
            
        if self.select_tasks != True:
            if self.source.id != False and self.destination.id != False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('location_id','=',self.source.id),('location_dest_id','=',self.destination.id)])
            if self.source.id != False and self.destination.id == False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('location_id','=',self.source.id)])
            if self.source.id == False and self.destination.id != False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('location_dest_id','=',self.destination.id)])
            if self.source.id == False and self.destination.id == False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done')])
            
            recordset = stockmoverecs.sorted(key=lambda r: r.date)
            return recordset
    
    @api.multi
    def get_producs(self):
        self.ensure_one()
        stockmove = self.env['stock.move']
        
        if self.select_tasks == True:
            task_ids = []
            task_ids = [task.task_id.id for task in self.task_ids]
            task_ids = set(task_ids)
            task_ids = list(task_ids)
            if len(task_ids) == 0:
                raise osv.except_osv(('Error'), ('Please select atleast one task otherwise uncheck Select Task box.'))
            task_objs = self.env['project.task'].search([('id','in',task_ids)])
            
            if self.source.id != False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                     ('task_id','in',task_ids), ('location_id','=',self.source.id)])
            
            if self.source.id == False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('task_id','in',task_ids)])
            
            recordset = stockmoverecs.sorted(key=lambda r: r.date)
            
            product_ids = []
            product_ids = [record.product_id.id for record in recordset] 
            product_ids = set(product_ids)
            product_ids = list(product_ids)
    #         print 'product_ids====================',product_ids
    
            product_objects = self.env['product.product'].search([('id','in', product_ids)])
            
            for product in product_objects:
                product.tmp_stock_qty = 0.0
                product.temp_stock_value = 0.0
                product.temp_avg_price = 0.0
                if self.source.id != False:
                    recs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('product_id','=',product.id),('location_id','=',self.source.id),('task_id','in',task_ids)])
#                     print 'recs==============================', recs
                    for record in recs :
                        product.tmp_stock_qty += record.product_uom_qty
                        product.temp_stock_value += record.product_uom_qty*record.price_unit
                
                if self.source.id == False:
                    recs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                       ('product_id','=',product.id),('task_id','in',task_ids)])
#                     print 'recs================================', recs
                    for record in recs :
                        product.tmp_stock_qty += record.product_uom_qty
                        product.temp_stock_value += record.product_uom_qty*record.price_unit
    
                temp_avg_price_decimal = Decimal(product.temp_stock_value/product.tmp_stock_qty)
                product.temp_avg_price = round(temp_avg_price_decimal,2) 
            return product_objects
        
        if self.select_tasks != True:
            if self.source.id != False and self.destination.id != False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('location_id','=',self.source.id),('location_dest_id','=',self.destination.id)])
            if self.source.id != False and self.destination.id == False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('location_id','=',self.source.id)])
            if self.source.id == False and self.destination.id != False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('location_dest_id','=',self.destination.id)])
            if self.source.id == False and self.destination.id == False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done')])
            
            recordset = stockmoverecs.sorted(key=lambda r: r.date)
            
            product_ids = []
            product_ids = [record.product_id.id for record in recordset] 
            product_ids = set(product_ids)
            product_ids = list(product_ids)
    #         print 'product_ids====================',product_ids
    
            product_objects = self.env['product.product'].search([('id','in', product_ids)])
            
            for product in product_objects:
                product.tmp_stock_qty = 0.0
                product.temp_stock_value = 0.0
                product.temp_avg_price = 0.0
                if self.source.id != False and self.destination.id != False:
                    recs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('product_id','=',product.id),('location_id','=',self.source.id),('location_dest_id','=',self.destination.id)])
                    for record in recs :
                        product.tmp_stock_qty += record.product_uom_qty
                        product.temp_stock_value += record.product_uom_qty*record.price_unit
                if self.source.id != False and self.destination.id == False:
                    recs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                       ('product_id','=',product.id),('location_id','=',self.source.id)])
                    for record in recs :
                        product.tmp_stock_qty += record.product_uom_qty
                        product.temp_stock_value += record.product_uom_qty*record.price_unit
                if self.source.id == False and self.destination.id != False:
                    recs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                       ('product_id','=',product.id),('location_dest_id','=',self.destination.id)])
                    for record in recs :
                        product.tmp_stock_qty += record.product_uom_qty
                        product.temp_stock_value += record.product_uom_qty*record.price_unit
                if self.source.id == False and self.destination.id == False:
                    recs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),
                                                ('product_id','=',product.id),('state','=','done')])
                    for record in recs :
                        product.tmp_stock_qty += record.product_uom_qty
                        product.temp_stock_value += record.product_uom_qty*record.price_unit
                if product.tmp_stock_qty != 0:
                    temp_avg_price_decimal = Decimal(product.temp_stock_value/product.tmp_stock_qty)
                else:
                    temp_avg_price_decimal = 0
                product.temp_avg_price = round(temp_avg_price_decimal,2)
            return product_objects
        
        
    @api.multi
    def get_producs_task_wise(self,task):
        self.ensure_one()
        stockmove = self.env['stock.move']
        if self.source.id != False and self.destination.id != False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                 ('task_id','=',task.id),('location_id','=',self.source.id),('location_dest_id','=',self.destination.id)])
        if self.source.id != False and self.destination.id == False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('task_id','=',task.id),('location_id','=',self.source.id)])
        if self.source.id == False and self.destination.id != False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('task_id','=',task.id),('location_dest_id','=',self.destination.id)])
        if self.source.id == False and self.destination.id == False:
            stockmoverecs = stockmove.search([('task_id','=',task.id),('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done')])
        
        recordset = stockmoverecs.sorted(key=lambda r: r.date)
        
        product_ids = []
        product_ids = [record.product_id.id for record in recordset] 
        product_ids = set(product_ids)
        product_ids = list(product_ids)
#         print 'product_ids====================',product_ids

        product_objects = self.env['product.product'].search([('id','in', product_ids)])
        
        for product in product_objects:
            product.tmp_stock_qty = 0.0
            product.temp_stock_value = 0.0
            product.temp_avg_price = 0.0
            if self.source.id != False and self.destination.id != False:
                recs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('task_id','=',task.id),('product_id','=',product.id),('location_id','=',self.source.id),('location_dest_id','=',self.destination.id)])
                for record in recs :
                    product.tmp_stock_qty += record.product_uom_qty
                    product.temp_stock_value += record.product_uom_qty*record.price_unit
            if self.source.id != False and self.destination.id == False:
                recs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                   ('task_id','=',task.id),('product_id','=',product.id),('location_id','=',self.source.id)])
                for record in recs :
                    product.tmp_stock_qty += record.product_uom_qty
                    product.temp_stock_value += record.product_uom_qty*record.price_unit
            if self.source.id == False and self.destination.id != False:
                recs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                   ('task_id','=',task.id),('product_id','=',product.id),('location_dest_id','=',self.destination.id)])
                for record in recs :
                    product.tmp_stock_qty += record.product_uom_qty
                    product.temp_stock_value += record.product_uom_qty*record.price_unit
            if self.source.id == False and self.destination.id == False:
                recs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),
                                            ('task_id','=',task.id),('product_id','=',product.id),('state','=','done')])
                for record in recs :
                    product.tmp_stock_qty += record.product_uom_qty
                    product.temp_stock_value += record.product_uom_qty*record.price_unit
            temp_avg_price_decimal = Decimal(product.temp_stock_value/product.tmp_stock_qty)
            product.temp_avg_price = round(temp_avg_price_decimal,2)
        return product_objects
        
        
    @api.multi
    def get_tasks(self):
        self.ensure_one()
        stockmove = self.env['stock.move']
        if self.select_tasks == True:
            task_ids = []
            task_ids = [task.task_id.id for task in self.task_ids]
            task_ids = set(task_ids)
            task_ids = list(task_ids)
            if len(task_ids) == 0:
                raise osv.except_osv(('Error'), ('Please select atleast one task otherwise uncheck Select Task box.'))
            task_objs = self.env['project.task'].search([('id','in',task_ids)])
            task_objs= self.env['project.task'].search([('id','in', task_ids)])
            return task_objs
        if self.select_tasks != True:
            if self.source.id != False and self.destination.id != False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('location_id','=',self.source.id),('location_dest_id','=',self.destination.id)])
            if self.source.id != False and self.destination.id == False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('location_id','=',self.source.id)])
            if self.source.id == False and self.destination.id != False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                      ('location_dest_id','=',self.destination.id)])
            if self.source.id == False and self.destination.id == False:
                stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done')])
            
            recordset = stockmoverecs.sorted(key=lambda r: r.date)
            
            task_ids = []
            task_ids = [record.task_id.id for record in recordset] 
            task_ids = set(task_ids)
            task_ids = list(task_ids)
#         not_task_ids = []
#         print 'product_ids====================',product_ids

            task_objs= self.env['project.task'].search([('id','in', task_ids)])
            return task_objs
        
    
        
        
class Report_Tasks(models.Model):
    _inherit='product.product'
    
    tmp_stock_qty = fields.Float('Temp Stock Qty', default=0.0)
    temp_stock_value = fields.Float('Temp Stock Value', default=0.0)
    temp_avg_price = fields.Float('Temp Avg Unit Price', default=0.0)


    
        
        
