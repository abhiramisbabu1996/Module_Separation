from openerp import fields, models, api
import datetime, calendar
from openerp.osv import osv

class report_work_report(models.TransientModel):
    _name='report.work.report'

#     name = fields.Char('Name')
    project_id = fields.Many2one('project.project', 'Project')
    from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    to_date=fields.Date(default=lambda self: self.default_time_range('to'))
    company_id =fields.Many2one('res.company','Company')
    
    
#     _defaults = {
#         'date_today': fields.Date.today(),
#         }
         

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
            
            
    @api.model
    def print_work_report_summary(self):
        print 'context=============', self._context,self._context['active_id']
        project_id = self._context['active_id']
        return {
            "type": "ir.actions.act_window",
            "name": "Work Report",
            "res_model": "report.work.report",
            "views": [[False, "form"]],
            "target": "new",
            'context': {'default_project_id': project_id}
        }

    @api.multi
    def print_work_report(self):
        self.ensure_one()
#         if self.account_id.id == False:
#             raise osv.except_osv(('Error'), ('There are no child accounts to display. Please select a proper parent account'))
        
#         print 'project===========================', self.project_id.id
        projects = self.env['project.project']
        projectrecs = projects.search([('id','=',self.project_id.id)])
#         print 'projectrecs==============================', projectrecs
        
 
        datas = {
            'ids': projectrecs._ids,
            'model': projects._name,
            'form': projects.read(),
            'context':self._context,
        }
        
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_project_work_report',
            'datas': datas,
            'context':{'start_date': self.from_date, 'end_date': self.to_date}
        }
        
        
#         
#         
# class report_day_book(models.TransientModel):
#     _name='report.day.book'
#     
#     
#     @api.onchange('company_id')
#     def onchange_field(self):
# 
#         if self.company_id.id != False:
#             return {
#                 'domain': {
#                     'account_id': [('company_id', '=', self.company_id.id),('type', '=', 'view')],
#                 },
#             }
# 
#     date=fields.Date('Date')
#     from_date=fields.Date('Date From')
#     to_date=fields.Date('Date To')
# #     account_id = fields.Many2one('account.account', 'Parent Account')
#     company_id =fields.Many2one('res.company','Company')
#     fiscalyear_id =fields.Many2one('account.fiscalyear','Fisal Year')
#     
#     _defaults = {
#         'date': fields.Date.today(),
#         'from_date': fields.Date.today(),
#         'to_date': fields.Date.today(),
#         }
# 
#     @api.multi
#     def print_report_day_book(self):
#         self.ensure_one()
# 
#         move_line = self.env['account.move.line']
#         move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('company_id','=',self.company_id.id)])  
#  
#         datas = {
#             'ids': move_linerecs._ids,
#             'model': move_line._name,
#             'form': move_line.read(),
#             'context':self._context,
#         }
#         
#         return{
#             'type' : 'ir.actions.report.xml',
#             'report_name' : 'hiworth_accounting.report_day_book',
#             'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
#         }
#         
#         
# class report_ledger_hiworth(models.TransientModel):
#     _name='report.ledger.hiworth'
#     
#     
#     @api.onchange('company_id')
#     def onchange_field(self):
# 
#         if self.company_id.id != False:
#             return {
#                 'domain': {
#                     'account_id': [('company_id', '=', self.company_id.id),('type', '!=', 'view')],
#                 },
#             }
# #         else:
# # #             print 'test==============='
# #             return {
# #                 'domain': {
# #                     'user_type': [('report_type', '!=', 'none')],
# #                 }
# #             }
# 
#     from_date=fields.Date(default=lambda self: self.default_time_range('from'))
#     to_date=fields.Date(default=lambda self: self.default_time_range('to'))
#     account_id = fields.Many2one('account.account', 'Parent Account')
#     company_id =fields.Many2one('res.company','Company')
#     fiscalyear_id =fields.Many2one('account.fiscalyear','Fisal Year')
#     date_today = fields.Date('Date')
#     
#     _defaults = {
#         'date_today': fields.Date.today(),
#         }
#          
# 
#     # Calculate default time ranges
#     @api.model
#     def default_time_range(self, type):
#         year = datetime.date.today().year
#         month = datetime.date.today().month
#         last_day = calendar.monthrange(datetime.date.today().year,datetime.date.today().month)[1]
#         first_day = 1
#         if type=='from':
#             return datetime.date(year, month, first_day)
#         elif type=='to':
#             return datetime.date(year, month, last_day)
# 
#     @api.multi
#     def print_ledger_report(self):
#         self.ensure_one()
#         if self.account_id.id == False:
#             raise osv.except_osv(('Error'), ('Please select a proper account'))
#         
#         move_line = self.env['account.move.line']
#         move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('account_id','=',self.account_id.id),('company_id','=',self.company_id.id)])
#         recordset = move_linerecs.sorted(key=lambda r: r.date)
#         
#         opening_move_linerecs = move_line.search([('date','<',self.from_date),('account_id','=',self.account_id.id),('company_id','=',self.company_id.id)])
#         total_debit = 0.0
#         total_credit = 0.0
#         total_balance = 0.0
#         opening_debit = 0.0
#         opening_credit = 0.0
#         for line in opening_move_linerecs:
#             total_debit+=line.debit
#             total_credit+=line.credit
#         
#         opening_debit =  total_debit
#         opening_credit =  total_credit
#         total_balance = total_debit - total_credit
#         
#  
#         datas = {
#             'ids': recordset._ids,
#             'model': move_line._name,
#             'form': move_line.read(),
#             'context':self._context,
#         }
#         
#         return{
#             'type' : 'ir.actions.report.xml',
#             'report_name' : 'hiworth_accounting.report_hiworth_ledger',
#             'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date, 'account': self.account_id.name, 'opening_debit': opening_debit, 'opening_credit': opening_credit, 'narration': 'Opening Balance', 'total_balance': total_balance}
#         }        
# 
#         
#         
