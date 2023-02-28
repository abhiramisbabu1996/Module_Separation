from openerp import fields, models, api
import datetime, calendar
from openerp.osv import osv


        
class report_location_based(models.TransientModel):
    _name='report.location.based'
    
    
    @api.onchange('company_id')
    def onchange_field(self):

        if self.company_id.id != False:
            return {
                'domain': {
                    'account_id': [('company_id', '=', self.company_id.id),('type', '=', 'view')],
                },
            }
        
    from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    to_date=fields.Date(default=lambda self: self.default_time_range('to'))
    location_id = fields.Many2one('stock.location', 'Plot') 
#     account_id = fields.Many2one('account.account', 'Parent Account')
    company_id =fields.Many2one('res.company','Company')
    fiscalyear_id =fields.Many2one('account.fiscalyear','Fisal Year')
    
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
    def print_report_location_baesd(self):
        self.ensure_one()

        move_line = self.env['account.move.line']
        move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('location_id','=',self.location_id.id),('company_id','=',self.company_id.id)])
        recordset = move_linerecs.sorted(key=lambda r: r.date)
 
        datas = {
            'ids': recordset._ids,
            'model': move_line._name,
            'form': move_line.read(),
            'context':self._context,
        }
        
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_location_wise',
            'datas': datas,
            'context':{'start_date': self.from_date, 'end_date': self.to_date, 'plot': self.location_id.name,}
        }
        
    @api.multi
    def view_report_location_baesd(self):
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
            'report_name' : 'hiworth_construction.report_location_wise_view',
            'datas': datas,
            'report_type': 'qweb-html',
        }
        
        
    @api.model
    def get_account_move_lines(self):
        move_line = self.env['account.move.line']
        move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('location_id','=',self.location_id.id),('company_id','=',self.company_id.id)])
        recordset = move_linerecs.sorted(key=lambda r: r.date)
        
        return recordset
        
        
        
