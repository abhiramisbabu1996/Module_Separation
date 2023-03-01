from openerp import fields, models, api
import datetime, calendar
from openerp.osv import osv

class report_receivabls_payables(models.TransientModel):
    _name='report.receivabls.payables'


    @api.onchange('company_id')
    def onchange_field(self):

        if self.company_id.id != False:
            return {
                'domain': {
                    'account_id': [('company_id', '=', self.company_id.id),('type', '=', 'view')],
                },
            }
#         else:
# #             print 'test==============='
#             return {
#                 'domain': {
#                     'user_type': [('report_type', '!=', 'none')],
#                 }
#             }

    from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    to_date=fields.Date(default=lambda self: self.default_time_range('to'))
    account_id = fields.Many2one('account.account', 'Parent Account')
    company_id =fields.Many2one('res.company','Company')
    fiscalyear_id =fields.Many2one('account.fiscalyear','Fisal Year')
    date_today = fields.Date('Date')
    opening_balance = fields.Float("Opening Balance")
    credit = fields.Float("Credit")
    debit = fields.Float("Debit")


    _defaults = {
        'date_today': fields.Date.today(),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        }


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
    def print_receivables_payables_report(self):
        self.ensure_one()
        if self.account_id.id == False:
            raise osv.except_osv(('Error'), ('There are no child accounts to display. Please select a proper parent account'))

        opening_debit = 0
        opening_credit = 0
        opening_balnce = 0
        accounts = self.get_childs()
        for acc in accounts:
            if acc.type != 'view':
                opening_debit += acc.temp_open_debit
                opening_credit += acc.temp_open_credit
                opening_balnce += acc.temp_open_balance
            else:
                p_opening_debit = 0
                p_opening_credit = 0
                p_opening_balnce = 0
                p_accouts = self.get_account_childs(acc)
                for pcc in p_accouts:
                    p_opening_debit += pcc.temp_open_debit
                    p_opening_credit += pcc.temp_open_credit
                    p_opening_balnce += pcc.temp_open_balance
                    opening_debit += pcc.temp_open_debit
                    opening_credit += pcc.temp_open_credit
                    opening_balnce += pcc.temp_open_balance
                acc.temp_open_debit = p_opening_debit
                acc.temp_open_credit = p_opening_credit
                acc.temp_open_balance = p_opening_balnce
        self.account_id.temp_open_debit = opening_debit
        self.account_id.temp_open_credit = opening_credit
        self.account_id.temp_open_balance = opening_balnce

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_accounting.report_receivables_and_payables',
            'datas': datas,
            'context':{'start_date': self.from_date, 'end_date': self.to_date}
        }



    @api.multi
    def view_receivables_payables_report(self):
        self.ensure_one()
        if self.account_id.id == False:
            raise osv.except_osv(('Error'), ('There are no child accounts to display. Please select a proper parent account'))

        opening_debit = 0
        opening_credit = 0
        opening_balnce =0
        accounts = self.get_childs()
        for acc in accounts:
            if acc.type != 'view':
                opening_debit += acc.temp_open_debit
                opening_credit += acc.temp_open_credit
                opening_balnce += acc.temp_open_balance
            else:
                p_opening_debit = 0
                p_opening_credit = 0
                p_opening_balnce =0
                p_accouts = self.get_account_childs(acc)
                for pcc in p_accouts:
                    p_opening_debit += pcc.temp_open_debit
                    p_opening_credit += pcc.temp_open_credit
                    p_opening_balnce += pcc.temp_open_balance
                    opening_debit += pcc.temp_open_debit
                    opening_credit += pcc.temp_open_credit
                    opening_balnce += pcc.temp_open_balance
                acc.temp_open_debit = p_opening_debit
                acc.temp_open_credit = p_opening_credit
                acc.temp_open_balance = p_opening_balnce

        self.account_id.temp_open_debit = opening_debit
        self.account_id.temp_open_credit = opening_credit
        self.account_id.temp_open_balance = opening_balnce

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }


        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_accounting.report_receivables_and_payables_view',
            'datas': datas,
            'report_type': 'qweb-html',
        }


    @api.model
    def get_childs(self):
        parent_obj = self.env['account.account'].search([('id','=',self.account_id.id)])
        data_list = []
        for acc in self.env['account.account'].search([('parent_id','=',self.account_id.id)]):
            if acc.type != 'view':
                temp_open_debit = 0
                temp_open_credit = 0
                temp_open_balance = 0
                temp_debit = 0
                temp_credit = 0
                temp_balance = 0
                move_lines = self.env['account.move.line'].search(
                    [('account_id', '=', acc.id), ('date', '<', self.from_date)])

                for move in move_lines:
                    temp_open_debit += move.debit
                    temp_open_credit += move.credit
                    temp_open_balance +=move.debit - move.credit
                acc.temp_open_balance = temp_open_balance
                acc.temp_open_debit = temp_open_debit
                acc.temp_open_credit = temp_open_credit
                move_lines = self.env['account.move.line'].search(
                        [('account_id', '=', acc.id), ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
                for move in move_lines:
                    temp_debit += move.debit
                    temp_credit += move.credit
                    temp_balance +=move.debit - move.credit
                acc.temp_debit = temp_debit
                acc.temp_credit = temp_credit
                acc.temp_balance = temp_balance

        return self.env['account.account'].search([('parent_id','=',self.account_id.id)])

    @api.model
    def get_account_childs(self, parent_id):
        for acc in self.env['account.account'].search([('parent_id', '=', parent_id.id)]):
            temp_open_debit = 0
            temp_open_credit = 0
            temp_open_balance = 0
            temp_debit = 0
            temp_credit = 0
            temp_balance = 0
            move_lines = self.env['account.move.line'].search(
                [('account_id', '=', acc.id), ('date', '<', self.from_date)])

            for move in move_lines:
                temp_open_debit += move.debit
                temp_open_credit += move.credit
                temp_open_balance += move.debit - move.credit
            acc.temp_open_balance = temp_open_balance
            acc.temp_open_debit = temp_open_debit
            acc.temp_open_credit = temp_open_credit
            move_lines = self.env['account.move.line'].search(
                [('account_id', '=', acc.id), ('date', '>=', self.from_date), ('date', '<=', self.to_date)])
            for move in move_lines:
                temp_debit += move.debit
                temp_credit += move.credit
                temp_balance += move.debit - move.credit
            acc.temp_debit = temp_debit
            acc.temp_credit = temp_credit
            acc.temp_balance = temp_balance

        res = self.env['account.account'].search([('parent_id', '=', parent_id.id)])
        recordset = res.sorted(key=lambda r: r.name)
        return recordset



class report_day_book(models.TransientModel):
    _name='report.day.book'


    @api.onchange('company_id')
    def onchange_field(self):

        if self.company_id.id != False:
            return {
                'domain': {
                    'account_id': [('company_id', '=', self.company_id.id),('type', '=', 'view')],
                },
            }

    date=fields.Date('Date')
    from_date=fields.Date('Date From')
    to_date=fields.Date('Date To')
#     account_id = fields.Many2one('account.account', 'Parent Account')
    company_id =fields.Many2one('res.company','Company')
    fiscalyear_id =fields.Many2one('account.fiscalyear','Fisal Year')

    _defaults = {
        'date': fields.Date.today(),
        'from_date': fields.Date.today(),
        'to_date': fields.Date.today(),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        }

    @api.multi
    def print_report_day_book(self):
        self.ensure_one()

        move_line = self.env['account.move.line']
        move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('company_id','=',self.company_id.id)])
        recordset = move_linerecs.sorted(key=lambda r: (r.date,r.move_id.id))

        datas = {
            'ids': recordset._ids,
            'model': move_line._name,
            'form': move_line.read(),
            'context':self._context,
        }

        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_accounting.report_day_book',
            'datas': datas,
            'context':{'start_date': self.from_date, 'end_date': self.to_date}
        }


    @api.multi
    def view_report_day_book(self):
        self.ensure_one()

#         move_line = self.env['account.move.line']
#         move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('company_id','=',self.company_id.id)])
#         recordset = move_linerecs.sorted(key=lambda r: r.date)

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_accounting.report_day_book_view',
            'datas': datas,
            'report_type': 'qweb-html',
#             'res_model': 'account.move.line',
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
        }

    @api.model
    def get_account_move_lines(self):

#         print 'qqqqqqqqqqqqqq855555555555555555555', self.env['account.account'].search([('parent_id','=',parent_id)]), self._context
        move_line = self.env['account.move.line']
        move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('company_id','=',self.company_id.id)])
        recordset = move_linerecs.sorted(key=lambda r: (r.date,r.move_id.id))
        return recordset


class report_ledger_hiworth(models.TransientModel):
    _name='report.ledger.hiworth'


    @api.onchange('company_id')
    def onchange_field(self):

        if self.company_id.id != False:
            return {
                'domain': {
                    'account_id': [('company_id', '=', self.company_id.id),('type', '!=', 'view')],
                },
            }

    from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    to_date=fields.Date(default=lambda self: self.default_time_range('to'))
    account_id = fields.Many2one('account.account', 'Parent Account')
    company_id =fields.Many2one('res.company','Company')
    fiscalyear_id =fields.Many2one('account.fiscalyear','Fisal Year')
    date_today = fields.Date('Date')
    opening_debit = fields.Float('Opening Debit')
    opening_credit = fields.Float('Opening Credit')
    total_balance = fields.Float('Total Balance')
    narration = fields.Char('Narration')


    _defaults = {
        'date_today': fields.Date.today(),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
        'narration': 'Opening Balance'
        }


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
    def print_ledger_report(self):
        self.ensure_one()
        if self.account_id.id == False:
            raise osv.except_osv(('Error'), ('Please select a proper account'))

        move_line = self.env['account.move.line']
        move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('account_id','=',self.account_id.id),('company_id','=',self.company_id.id)])
        recordset = move_linerecs.sorted(key=lambda r: (r.date,r.id))

        opening_move_linerecs = move_line.search([('date','<',self.from_date),('account_id','=',self.account_id.id),('company_id','=',self.company_id.id)])
        total_debit = 0.0
        total_credit = 0.0
        total_balance = 0.0
        opening_debit = 0.0
        opening_credit = 0.0
        for line in opening_move_linerecs:
            total_debit+=line.debit
            total_credit+=line.credit

        opening_debit =  total_debit
        opening_credit =  total_credit
        total_balance = total_debit - total_credit


        datas = {
            'ids': recordset._ids,
            'model': move_line._name,
            'form': move_line.read(),
            'context':self._context,
        }

        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_accounting.report_hiworth_ledger',
            'datas': datas,
            'context':{'start_date': self.from_date, 'end_date': self.to_date, 'account': self.account_id.name, 'opening_debit': opening_debit, 'opening_credit': opening_credit, 'narration': 'Opening Balance', 'total_balance': total_balance}
        }


    @api.multi
    def view_ledger_report(self):
        self.ensure_one()
        if self.account_id.id == False:
            raise osv.except_osv(('Error'), ('Please select a proper account'))

        move_line = self.env['account.move.line']
        opening_move_linerecs = move_line.search([('date','<',self.from_date),('account_id','=',self.account_id.id),('company_id','=',self.company_id.id)])
        total_debit = 0.0
        total_credit = 0.0
        total_balance = 0.0
        opening_debit = 0.0
        opening_credit = 0.0
        for line in opening_move_linerecs:
            total_debit+=line.debit
            total_credit+=line.credit

        opening_debit =  total_debit
        opening_credit =  total_credit
        total_balance = total_debit - total_credit


        self.opening_debit = opening_debit
        self.opening_credit = opening_credit
        self.total_balance = total_balance


        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }

        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_accounting.report_hiworth_ledger_view',
            'datas': datas,
            'report_type': 'qweb-html',
#             'context':{'start_date': self.from_date, 'end_date': self.to_date, 'account': self.account_id.name, 'opening_debit': opening_debit, 'opening_credit': opening_credit, 'narration': 'Opening Balance', 'total_balance': total_balance}
        }

    @api.model
    def get_account_move_lines(self):


        move_line = self.env['account.move.line']
        move_linerecs = move_line.search([('date','>=',self.from_date),('date','<=',self.to_date),('account_id','=',self.account_id.id),('company_id','=',self.company_id.id)])
        recordset = move_linerecs.sorted(key=lambda r: (r.date,r.id))

        return recordset

class outstanding_report(models.TransientModel):
    _name='outstanding.report'


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
    account_id = fields.Many2one('account.account', 'Parent Account')
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
    def print_outstanding_report(self):
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
            'report_name' : 'hiworth_accounting.outstanding_report',
            'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date, 'plot': self.location_id.name,}
        }

    @api.multi
    def get_invoice_nos(self):
        self.ensure_one()
        invoice_no = []
        moves = self.env['account.move.line'].search([('account_id','=',self.account_id.id)])

        for move in moves:
            if move.invoice_no_id.id != False:
                invoice_no += [move.invoice_no_id.id]
        new_list = list(set(invoice_no))

        invoices_rec = self.env['account.invoice.no'].search([('id','in',new_list)])


#
#         if self.project_id.location_id == False:
#             raise osv.except_osv(('Error'), ('The project is not linked to any location'))
#         if self.project_id.location_id != False:
#             stockmoverecs = stockmove.search([('date','>=',self.from_date),('date','<=',self.to_date),('state','=','done'),
#                                                   ('location_dest_id','=',self.project_id.location_id.id)])
        recordset = invoices_rec.sorted(key=lambda r: r.name)
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
    def view_outstanding_report(self):
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
            'report_name' : 'hiworth_accounting.outstanding_report',
            'datas': datas,
            'report_type': 'qweb-html',
        }
