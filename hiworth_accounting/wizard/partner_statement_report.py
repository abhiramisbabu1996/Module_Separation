from openerp import fields, models, api
import datetime, calendar
from openerp.osv import osv


class partner_statement_report(models.TransientModel):
    _name='partner.statement.report'


    @api.onchange('company_id')
    def onchange_field(self):

        if self.company_id.id != False:
            return {
                'domain': {
                    'account_id': [('company_id', '=', self.company_id.id)],
                },
            }

    from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    to_date=fields.Date(default=lambda self: self.default_time_range('to'))
#     project_id = fields.Many2one('project.project', 'Project')
    account_id = fields.Many2one('account.account', 'Related Account')
    company_id =fields.Many2one('res.company','Company')

    _defaults = {
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        }


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
    def print_partner_statement(self):
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
            'report_name' : 'hiworth_accounting.partner_statement_report',
            'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date, 'plot': self.location_id.name,}
        }


    @api.multi
    def get_account_move_lines(self):
        self.ensure_one()
        stockmove = self.env['account.move.line']
        if self.account_id.id != False:
            move_linerecs = stockmove.search([('account_id','=',self.account_id.id),
                                              ('date','>=',self.from_date),('date','<=',self.to_date),('credit','!=',0.0)])

        recordset = move_linerecs.sorted(key=lambda r: r.date)
        return recordset


    @api.multi
    def get_statement_entries(self):
        self.ensure_one()
        statement_obj = self.env['partner.statement'].search([('account_id', '=', self.account_id.id)])
        statements = []
        statements = [statement.id for statement in statement_obj.statement_ids.search([('date','>=',self.from_date),('date','<=',self.to_date)])]

        statements_recs = self.env['partner.statement.line'].search([('id','in',statements)])
#         print 'task_objs========================', task_objs
        recordset = statements_recs.sorted(key=lambda r: r.date)
        return statements_recs

    @api.multi
    def view_partner_statement(self):
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
            'report_name' : 'hiworth_accounting.partner_statement_report',
            'datas': datas,
            'report_type': 'qweb-html',
        }
