from openerp import fields, models, api
import datetime, calendar
from openerp.osv import osv




class account_account_type(models.Model):
    _inherit = "account.account.type"
    
    account_ids = fields.One2many('account.account', 'user_type', 'Accounts')
        
class project_report(models.TransientModel):
    _name='project.report'
    
    
    @api.onchange('company_id')
    def onchange_field(self):

        if self.company_id.id != False:
            return {
                'domain': {
                    'project_id': [('company_id', '=', self.company_id.id)],
                },
            }
        
    from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    to_date=fields.Date(default=lambda self: self.default_time_range('to'))
    project_id = fields.Many2one('project.project', 'Project') 
#     account_id = fields.Many2one('account.account', 'Parent Account')
    company_id =fields.Many2one('res.company','Company')
    show_material_allocation = fields.Boolean('Show Material Allocation')
    show_expenses = fields.Boolean('Show Expenses')
    show_contract_bill = fields.Boolean('Show Contractor Bills')
#     fiscalyear_id =fields.Many2one('account.fiscalyear','Fisal Year')
    
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
    def print_project_report(self):
        self.ensure_one()

#         move_line = self.env['account.move.line']
#         move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('location_id','=',self.location_id.id),('company_id','=',self.company_id.id)])
#         recordset = move_linerecs.sorted(key=lambda r: r.date)
 
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
        
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.project_complete_report',
            'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date, 'plot': self.location_id.name,}
        }
        
    @api.multi
    def get_stock_moves(self):
        self.ensure_one()
        stockmove = self.env['stock.move']
        if self.project_id.location_id == False:
            raise osv.except_osv(('Error'), ('The project is not linked to any location'))
        if self.project_id.location_id != False:
            stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
                                                  ('location_dest_id','=',self.project_id.location_id.id)])
        recordset = stockmoverecs.sorted(key=lambda r: r.date)
        return recordset
        
    @api.multi
    def get_account_move_lines(self):
        self.ensure_one()
        stockmove = self.env['stock.move']
        if self.project_id.location_id == False:
            raise osv.except_osv(('Error'), ('The project is not linked to any location'))
        if self.project_id.location_id != False:
            move_line = self.env['account.move.line']
            expense_accounts = []
            account_types = self.env['account.account.type'].search([('report_type','=','expense')])
#             print 'account_types==========', account_types
            for type in account_types:
#                 print 'accouts====================', type.account_ids
                expense_accounts += [account.id for account in type.account_ids]
#                 print 'expense_accounts=========================', expense_accounts
#             print 'expense_accounts=========================2', expense_accounts
            move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),
                                              ('location_id','=',self.project_id.location_id.id),
                                              ('company_id','=',self.company_id.id),
                                              ('account_id','in',expense_accounts)])

        recordset = move_linerecs.sorted(key=lambda r: r.date)
        return recordset  
        
        
    @api.multi
    def get_task(self):
        self.ensure_one()
        tasks = []
        tasks = [invoice.task_id.id for invoice in self.env['account.invoice'].search([('project_id','=',self.project_id.id),
                                                                                       ('date_invoice','>=',self.from_date),('date_invoice','<=',self.to_date)])] 
        if tasks == []:
            raise osv.except_osv(('Error'), ('There is no contract bills related to this project in this date range'))
        task_objs = self.env['project.task'].search([('id','in',tasks)]) 
#         print 'task_objs========================', task_objs
        return task_objs
        
    @api.multi
    def get_account_invoice_lines(self,task_id):
        self.ensure_one()
#         print 'task_id===========', task_id
        invoices =self.env['account.invoice'].search([('task_id','=',task_id)])
        lines = []
        for invoice in invoices:
            lines = [line.id for line in invoice.invoice_line]
#             print 'lines==================', lines
        invoice_lines = self.env['account.invoice.line'].search([('id','in',lines)])
        
        return invoice_lines
    
    @api.multi
    def view_project_report(self):
        self.ensure_one()
 
#         move_line = self.env['account.move.line']
#         move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('location_id','=',self.location_id.id),('company_id','=',self.company_id.id)])
  
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
         
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.project_complete_report',
            'datas': datas,
            'report_type': 'qweb-html',
        }
#         
#         
#     @api.model
#     def get_account_move_lines(self):
#         move_line = self.env['account.move.line']
#         move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('location_id','=',self.location_id.id),('company_id','=',self.company_id.id)])
#         recordset = move_linerecs.sorted(key=lambda r: r.date)
#         
#         return recordset
        
        
        
