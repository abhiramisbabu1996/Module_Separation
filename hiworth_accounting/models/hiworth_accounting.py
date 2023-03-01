from openerp.exceptions import except_orm, ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import models, fields, api, _
from openerp import workflow
import time
import datetime
from datetime import date
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import timedelta
from pychart.arrow import default
from openerp.osv import osv, expression



class Opening_Entry(models.Model):
    _name = 'opening.entry'
    
    name = fields.Char('Name')
    account_id = fields.Many2one('account.account', 'Account' ,readonly="True")
    Date = fields.Date('Date')
    debit = fields.Float('Debit')
    credit = fields.Float('Credit')
#     journal = fields.Many2one('account.journal','Journal')
    remarks = fields.Text('Remarks')
    done = fields.Boolean('Made Opening Entry')
    move_line = fields.Many2one('account.move.line', 'Entry')
    
    @api.multi
    def make_entry(self):
        self.ensure_one()
        
        opening_journal = self.env['account.journal'].search([('company_id','=',self.account_id.company_id.id),
                                                              ('type','=','situation')])
                                                             
        journal_entry = self.env['account.move'].search([('journal_id','=', opening_journal.id)])
        journal_entry[0].button_cancel()

        values = {
                    'name': 'Opening Balance',
                    'account_id': self.account_id.id,
                    'debit': self.debit,
                    'credit' : self.credit,
                    'move_id':journal_entry[0].id}
        move_line = self.env['account.move.line'].create(values)

        journal_entry[0].button_validate()
        self.move_line = move_line.id
        self.done = True
        
    @api.multi
    def edit_entry(self):
        self.ensure_one()
        
        self.move_line.move_id.button_cancel()
        self.move_line.debit = self.debit
        self.move_line.credit = self.credit
        self.move_line.move_id.button_validate()

    


class account_account(models.Model):
    _inherit = 'account.account'
    
       
    @api.multi
    @api.depends('child_id')
    def _compute_childs(self): 
        for line in self:
            for lines in line.child_id:
                if lines.id != False: 
                    line.is_child = True
                    
               
    @api.multi
    def action_opening_entry_form(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['opening.entry'].search([('account_id','=',self.id)])

 
        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Opening Entry',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'opening.entry',
            'view_id':'opening_entry_form',
            'type':'ir.actions.act_window',
#             'account_id':self.id,
            'res_id':res_id,
            'context':{'default_account_id':self.id},
        }
                
    @api.onchange('parent_id')
    def onchange_field(self):
        temp = 0
        list = []
        code = ""
        if self.parent_id:
            if len(self.parent_id.child_id) <= 1:
                code = self.parent_id.code + '001'
                if not self.code:
                    self.code = code
            if len(self.parent_id.child_id) > 1:
                for child in self.parent_id.child_id:
                    if child.code:
                        temp = int(child.code)
                        list.append(temp)                    
                code = str(max(list)+1)
                if not self.code:
                    self.code = code
        if self.parent_id.user_type.report_type != 'none':
            return {
                'domain': {
                    'user_type': [('report_type', '=', self.parent_id.user_type.report_type)],
                },
            }
        else:
#             print 'test==============='
            return {
                'domain': {
                    'user_type': [('report_type', '!=', 'none')],
                }
            }
            
            
    @api.multi
    @api.depends('debit','credit')
    def compute_theoretical_balance(self):
        for rec in self:
            if rec.user_type.report_type == 'asset' or rec.user_type.report_type == 'expense':
                rec.theoretical_balance = rec.debit - rec.credit
            if rec.user_type.report_type == 'liability' or rec.user_type.report_type == 'income':
                rec.theoretical_balance = rec.credit - rec.debit      
    
    @api.multi
    @api.depends('balance')
    def get_bal_code(self):
        for lines in self:
            if lines.balance < 0:
                lines.bal_code = 'Cr'
            if lines.balance > 0:
                lines.bal_code = 'Dr'


    @api.multi
    @api.depends('debit')
    def compute_balance1(self):
        for rec in self:
            if rec.balance < 0:
                rec.balance1 = -1 * rec.balance
                # rec.balance_type = 'Cr'
            if rec.balance > 0:
                rec.balance1 = rec.balance
    
    move_lines = fields.One2many('account.move.line', 'account_id', 'Journal Items')
#    parent_type = fields.Char(compute='_compute_parent_type', store=True, string='Parent Type')
#    is_move_lines = fields.Boolean(compute='_compute_move_lines', store=True, string='Is Journal Items')
    is_child = fields.Boolean(compute='_compute_childs', store=True, string='Is Child Accounts')
    type = fields.Selection([
            ('view', 'View'),
            ('asset', 'Asset'),
            ('liability', 'Liability'),
            ('income', 'Income'),
            ('expense', 'Expense'),
            ('other', 'Regular'),
            ('receivable', 'Receivable'),
            ('payable', 'Payable'),
            ('liquidity','Liquidity'),
            ('consolidation', 'Consolidation'),
            ('closed', 'Closed'),
        ], 'Internal Type', required=True, help="The 'Internal Type' is used for features available on "\
            "different types of accounts: view can not have journal items, consolidation are accounts that "\
            "can have children accounts for multi-company consolidations, payable/receivable are for "\
            "partners accounts (for debit/credit computations), closed for depreciated accounts.")
            
    liability_ids = fields.One2many('account.account', 'many_id1',  store=True, string='Liabilities')
 #   lia_ids = fields.Many2one('account.account', compute='get_liability_ids', store=True, string="Child Accounts")
    asset_ids = fields.One2many('account.account', 'many_id2',  string='Assets')
    many_id1 = fields.Many2one('account.account')
    many_id2 = fields.Many2one('account.account')
    parent_type = fields.Char('Parent Type')
    parent_balance = fields.Float('Balance Of parent')
    child_balance = fields.Float('Balance Of Child')
    expense_ids = fields.One2many('account.account', 'many_id3',  store=True, string='Expenses')
    lia_ids = fields.Date('Date')
    income_ids = fields.One2many('account.account', 'many_id4',  string='Income')
    many_id3 = fields.Many2one('account.account')
    many_id4 = fields.Many2one('account.account')
    temp_balance = fields.Float('Temp Balance')
    temp_debit = fields.Float('Temp Debit')
    temp_credit = fields.Float('Temp Credit')
    temp_start_date = fields.Date('Temp Start Date')
    temp_end_date = fields.Date('Temp End Date')
    date_today = fields.Date('Date')
    opening_entry = fields.Many2one('opening.entry', 'Opening Entry')
    theoretical_balance = fields.Float(compute='compute_theoretical_balance', string="Balance")
    code = fields.Char('Code', size=64, required=False)
    balance1 = fields.Float(compute='compute_balance1', string="Balance")
    credit_limit = fields.Float('Credit Limit')
    debit_limit = fields.Float('Debit Limit')
    bal_code = fields.Char(compute="get_bal_code", string='Dr/Cr')
    opening_debit = fields.Char(string="Opening Debit")
    opening_credit = fields.Char(string="Opening Credit")
    total_balance = fields.Char(string="Opening Balance")
    temp_open_credit = fields.Float("Opening Credit")
    temp_open_debit = fields.Float("Opening Debit")
    temp_open_balance = fields.Float("Opening Balance")
    # balance_type = fields.Char(compute='compute_balance1', string='Type')
    _defaults = {
            'date_today': fields.Date.today(),
        }
    
    _sql_constraints = [
        ('code_company_uniq', 'Check(1=1)', 'The code of the account must be unique per company !')
    ]
    
    
    def _check_type(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
   #     print '================================================================'
#         accounts = self.browse(cr, uid, ids, context=context)
#         for account in accounts:
#             if account.child_id and account.type not in ('view', 'consolidation'):
#                 print 'sdfaasdasdasdasdaada'
#         return False
        return True
        
    def _check_allow_code_change(self, cr, uid, ids, context=None):
#         print 'test===================='
#         line_obj = self.pool.get('account.move.line')
#         for account in self.browse(cr, uid, ids, context=context):
#             account_ids = self.search(cr, uid, [('id', 'child_of', [account.id])], context=context)
#             if line_obj.search(cr, uid, [('account_id', 'in', account_ids)], context=context):
#                 raise osv.except_osv(_('Warning !'), _("You cannot change the code of account which contains journal items!"))
        return True
    
    _constraints = [
     #   (_check_recursion, 'Error!\nYou cannot create recursive accounts.', ['parent_id']),
         (_check_type, 'cgfxgf', ['type']),
     #   (_check_account_type, 'Configuration Error!\nYou cannot select an account type with a deferral method different of "Unreconciled" for accounts with internal type "Payable/Receivable".', ['user_type','type']),
      #  (_check_company_account, 'Error!\nYou cannot create an account which has parent account of different company.', ['parent_id']),
    ]
    

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if isinstance(ids, (int, long)):
                    ids = [ids]
        reads = self.read(cr, uid, ids, ['name', 'code'], context=context)
        res = []
        for record in reads:
            name = record['name']
            if record['code']:
                name = name
            res.append((record['id'], name))
        return res

    @api.multi
    def get_childs(self):
        from_date = self._context.get('start_date')
        to_date  = self._context.get('end_date')
        parent_obj = self.env['account.account'].search([('id', '=', self.id)])
        parent = self.id
        data_list = []
        for line in self.env['account.account'].search([('user_type', '=', 31)]):
            if line.type == 'view':
                parent = line.id
                continue

            line.temp_debit = 0.0
            line.temp_credit = 0.0
            line.temp_balance = 0.0
            #             if line.balance!=0.0:
            move_lines = self.env['account.move.line'].search(
                [('account_id', '=', line.id), ('date', '>=',from_date), ('date', '<=', to_date)])
            #             if actual_status == True:
            #                 move_lines = self.env['account.move.line'].search([('account_id','=',line.id),('date','>=',date_from), ('date','<=',date_to),('review','=',False)])
            #             print 'move_lines======================', move_lines
            total_debit = 0.0
            total_credit = 0.0
            #                     line.temp_balance = 0.0
            for moves in move_lines:
                if moves.debit != 0.0:
                    total_debit += moves.debit
                if moves.credit != 0.0:
                    total_credit += moves.credit
            #                 print 'total_debit=========================',total_debit,total_credit
            line.temp_debit = total_debit
            line.temp_credit = total_credit
            line.temp_balance = total_debit - total_credit
            data_list.append(line)
        #             line.temp_start_date = start_date
        #             line.temp_end_date = end_date
        #             print 'temp_balance -=============================',line, line.temp_balance
        #         for line in acc_obj:
        #             if line.child_id and line.temp_balance == 0.0:
        #                 for child in line.child_id:
        #                     line.temp_balance += child.temp_balance
        res = self.env['account.account'].search([('parent_id', '=', self.id)])
        recordset = res.sorted(key=lambda r: r.name)
        return data_list
    
    
#     @api.multi
#     def refresh_balance_sheet(self):     
#         print 'context=======================',self._context
#         objs2=self.env['account.account'].search([('id','=',2)])
#         objs3=self.env['account.account'].search([('id','=',34)])
#         date_from = self._context['date_from']
#         date_to = self._context['date_to']
#         period_from = self._context['period_from']
#         period_to = self._context['period_to']
#         filter = self._context['filter']
#         actual_status = self._context['actual_status']
    
#         acc_obj=self.env['account.account'].search([('id','!=',0)])
        
#         if filter == 'filter_no':
#       #      print 'qqqqqq1111111111111111111111111111111111'
#             for line in acc_obj:
#                 line.temp_balance = 0.0
#                 if line.balance!=0.0:
#                     move_lines = self.env['account.move.line'].search([('account_id','=',line.id)])
#                     if actual_status == True:
#                         move_lines = self.env['account.move.line'].search([('account_id','=',line.id),('review','=',False)])
# #                     print 'move_lines==================5444444444565555====', move_lines
#                     total_debit = 0.0
#                     total_credit = 0.0
                    
#                     for moves in move_lines:
#                         if moves.debit != 0.0:
#                             total_debit += moves.debit
#                         if moves.credit != 0.0:
#                             total_credit += moves.credit
#         #                print 'total_debit=========================',total_debit,total_credit
#                     line.temp_balance =  total_debit - total_credit
# #                     if line.temp_balance < 0.0:
# #                         line.temp_balance = line.temp_balance * -1
#          #           print 'temp_balance -=============================',line, line.temp_balance
#             for line in acc_obj:
#                 if line.child_id and line.temp_balance == 0.0:
#                     for child in line.child_id:
#                         line.temp_balance += child.temp_balance
            
#             check_id=self.env['account.account'].search([('name','=','Profit (Loss) to report')])
#     #         print 'check_id=========================',check_id,check_id.id
#             if check_id.id != False:
#                 check_id.unlink()
#             excess = 0.0
#             exp_balance=0.0
#             inc_balance = 0.0
#             for lines in objs3.child_id:
#                 print 'lines=======================', lines,lines.user_type.report_type,lines.balance,lines.temp_balance
#                 if lines.user_type.report_type == 'income' and lines.balance != 0.0:                   
#                     print'li_balance=======================================',lines,lines.temp_balance
#                     inc_balance += lines.temp_balance
#                 if lines.user_type.report_type == 'expense' and lines.balance != 0.0:
#                     print 'wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww',lines.temp_balance
#                     exp_balance += lines.temp_balance
#             exp_balance2 = exp_balance
#             inc_balance2 = inc_balance 
            
#             if exp_balance < 0.0:
#                  exp_balance2 = exp_balance2 * -1                 
#             if inc_balance < 0.0:
#                  inc_balance2 = inc_balance2 * -1
             
#             excess = exp_balance2 - inc_balance2
            
#             print 'excess===================================', exp_balance2, inc_balance2,excess
            
#             vals = {
#                   'name':'Profit (Loss) to report',
#                   'code': 10,
#                   'type': 'other',
#                   'user_type': 13,
#                   'company_id':lines.company_id.id,
#                   'active': True,
#                   'balance': excess,
#                   'level':2,
#                   'parent_id':2,
#                   'parent_balance':excess,
#                   'temp_balance': excess,}
#             id99=self.env['account.account'].create(vals)
#             print 'ooooooooooooooooooooooooooo', id99
            
#             objs=self.env['account.account'].search([('id','!=',1),('id','!=',2),('id','!=',34),('id','!=',id99.id)])
            
#             for line in objs:
#                 line.parent_balance=0
#           #      line.child_balance=0
#          #       print 'linewwwwwwwww=', line.child_id
#                 for chil in line.child_id:
#          #           print 'test1================',chil.id
#                     if chil.id != False:
#           #              print 'chil=====================', chil
#                         chil.child_balance=chil.temp_balance
#                 if line.child_id:
#                     for child in line.child_id:
#                #         print 'child========================',child.temp_balance,child,line
#                         line.parent_balance += child.temp_balance
                            
#             #print 'objs2=============================',objs2,objs2.child_id
#             objs2.liability_ids = False
#             objs2.liability_ids = objs2.liability_ids + id99
#             objs2.asset_ids = False
#             for childs in objs2.child_id:
# #                 print 'childs============================',childs,childs.name,childs.balance,childs.user_type.report_type
#                 if childs.user_type.report_type == 'liability' and (childs.debit != 0.0 or childs.credit != 0.0):
    
#                    objs2.liability_ids += childs
# #                    print 'grand child================', childs.child_id
#                    for childss in childs.child_id:
#                        objs2.liability_ids += childss
#               #     print 'asdasdasds=======================',objs2.liability_ids,childs
#                 elif childs.user_type.report_type == 'asset' and (childs.debit != 0.0 or childs.credit != 0.0):
#                     objs2.asset_ids += childs
# #                     print 'grand child================', childs.child_id
#                     for childss in childs.child_id:
#                        objs2.asset_ids += childss
        
#         ''' based on date '''
#         if date_from != False and date_to != False:
#             for line in acc_obj:
#                 line.temp_balance = 0.0
#                 if line.balance!=0.0:
#                     move_lines = self.env['account.move.line'].search([('account_id','=',line.id), ('date','>=',date_from), ('date','<=',date_to)])
#                     if actual_status == True:
#                         move_lines = self.env['account.move.line'].search([('account_id','=',line.id),('date','>=',date_from), ('date','<=',date_to),('review','=',False)])
#                 #    print 'move_lines======================', move_lines
#                     total_debit = 0.0
#                     total_credit = 0.0
# #                     line.temp_balance = 0.0
#                     for moves in move_lines:
#                         if moves.debit != 0.0:
#                             total_debit += moves.debit
#                         if moves.credit != 0.0:
#                             total_credit += moves.credit
#                         print 'total_debit=========================',total_debit,total_credit
#                     line.temp_balance =  total_debit - total_credit
#                     print 'temp_balance -=============================',line, line.temp_balance
#             for line in acc_obj:
#                 if line.child_id and line.temp_balance == 0.0:
#                     for child in line.child_id:
#                         line.temp_balance += child.temp_balance
            
#             check_id=self.env['account.account'].search([('name','=','Profit (Loss) to report')])
#     #         print 'check_id=========================',check_id,check_id.id
#             if check_id.id != False:
#                 check_id.unlink()
            
#             excess = 0.0
#             exp_balance=0.0
#             inc_balance = 0.0
#             for lines in objs3.child_id:
#                 print 'lines=======================', lines,lines.user_type.report_type,lines.balance,lines.temp_balance
#                 if lines.user_type.report_type == 'income' and lines.balance != 0.0:                   
#                     print'li_balance=======================================',lines,lines.temp_balance
#                     inc_balance += lines.temp_balance
#                 if lines.user_type.report_type == 'expense' and lines.balance != 0.0:
#                     print 'wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww',lines.temp_balance
#                     exp_balance += lines.temp_balance
#             exp_balance2 = exp_balance
#             inc_balance2 = inc_balance 
            
#             if exp_balance < 0.0:
#                  exp_balance2 = exp_balance2 * -1                 
#             if inc_balance < 0.0:
#                  inc_balance2 = inc_balance2 * -1
             
#             excess = exp_balance2 - inc_balance2
#           #  print 'excess===================================', li_balance,as_balance,excess
            
#             vals = {
#                   'name':'Profit (Loss) to report',
#                   'code': 10,
#                   'type': 'other',
#                   'user_type': 13,
#                   'company_id':lines.company_id.id,
#                   'active': True,
#                   'balance': excess,
#                   'level':2,
#                   'parent_id':2,
#                   'parent_balance':excess,
#                   'temp_balance': excess,}
#             id99=self.env['account.account'].create(vals)
#             print 'ooooooooooooooooooooooooooo', id99
            
#             objs=self.env['account.account'].search([('id','!=',1),('id','!=',2),('id','!=',34),('id','!=',id99.id)])
            
#             for line in objs:
#                 line.parent_balance=0
#           #      line.child_balance=0
#          #       print 'linewwwwwwwww=', line.child_id
#                 for chil in line.child_id:
#          #           print 'test1================',chil.id
#                     if chil.id != False:
#           #              print 'chil=====================', chil
#                         chil.child_balance=chil.temp_balance
#                 if line.child_id:
#                     for child in line.child_id:
#                #         print 'child========================',child.temp_balance,child,line
#                         line.parent_balance += child.temp_balance
                            
#             #print 'objs2=============================',objs2,objs2.child_id
#             objs2.liability_ids = False
#             objs2.asset_ids = False
#             for childs in objs2.child_id:
#              #   print 'childs============================',childs,childs.balance,childs.user_type.report_type
#                 if childs.user_type.report_type == 'liability' and (childs.debit != 0.0 or childs.credit != 0.0):
    
#                    objs2.liability_ids += childs
#          #          print 'grand child================', childs.child_id
#                    for childss in childs.child_id:
#                        objs2.liability_ids += childss
#               #     print 'asdasdasds=======================',objs2.liability_ids,childs
#                 elif childs.user_type.report_type == 'asset' and (childs.debit != 0.0 or childs.credit != 0.0):
#                     objs2.asset_ids += childs
#           #          print 'grand child================', childs.child_id
#                     for childss in childs.child_id:
#                        objs2.asset_ids += childss
        
#         ''' calculation based on Period '''               
#         if period_from != False and period_to != False:
            
#             print 'period_from===========================',period_from,period_to
#             date_start = self.env['account.period'].search([('id','=',period_from)]).date_start
#             date_stop = self.env['account.period'].search([('id','=',period_to)]).date_stop
            
#             print 'date_start===============================', date_start,date_stop
            
#             for line in acc_obj:
#                 line.temp_balance = 0.0
#                 if line.balance!=0.0:
#                     move_lines = self.env['account.move.line'].search([('account_id','=',line.id), ('date','>=',date_start), ('date','<=',date_stop)])
#                     if actual_status == True:
#                         move_lines = self.env['account.move.line'].search([('account_id','=',line.id),('date','>=',date_start), ('date','<=',date_stop),('review','=',False)])
#                 #    print 'move_lines======================', move_lines
#                     total_debit = 0.0
#                     total_credit = 0.0
#     #                     line.temp_balance = 0.0
#                     for moves in move_lines:
#                         if moves.debit != 0.0:
#                             total_debit += moves.debit
#                         if moves.credit != 0.0:
#                             total_credit += moves.credit
#      #                   print 'total_debit=========================',total_debit,total_credit
#                     line.temp_balance =  total_debit - total_credit
#       #              print 'temp_balance -=============================',line, line.temp_balance
#             for line in acc_obj:
#                 if line.child_id and line.temp_balance == 0.0:
#                     for child in line.child_id:
#                         line.temp_balance += child.temp_balance
            
#             check_id=self.env['account.account'].search([('name','=','Profit (Loss) to report')])
#     #         print 'check_id=========================',check_id,check_id.id
#             if check_id.id != False:
#                 check_id.unlink()
#             excess = 0.0
#             exp_balance=0.0
#             inc_balance = 0.0
#             for lines in objs3.child_id:
#        #         print 'lines=======================', lines,lines.user_type.report_type,lines.balance,lines.temp_balance
#                 if lines.user_type.report_type == 'income' and lines.balance != 0.0:                   
#          #           print'li_balance=======================================',lines,lines.temp_balance
#                     inc_balance += lines.temp_balance
#                 if lines.user_type.report_type == 'expense' and lines.balance != 0.0:
#         #            print 'wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww',lines.temp_balance
#                     exp_balance += lines.temp_balance
#             exp_balance2 = exp_balance
#             inc_balance2 = inc_balance 
            
#             if exp_balance < 0.0:
#                  exp_balance2 = exp_balance2 * -1                 
#             if inc_balance < 0.0:
#                  inc_balance2 = inc_balance2 * -1
             
#             excess = exp_balance2 - inc_balance2
#           #  print 'excess===================================', li_balance,as_balance,excess
            
#             vals = {
#                   'name':'Profit (Loss) to report',
#                   'code': 10,
#                   'type': 'other',
#                   'user_type': 13,
#                   'company_id':lines.company_id.id,
#                   'active': True,
#                   'balance': excess,
#                   'level':2,
#                   'parent_id':2,
#                   'parent_balance':excess,
#                   'temp_balance': excess,}
#             id99=self.env['account.account'].create(vals)
#     #        print 'ooooooooooooooooooooooooooo', id99
            
#             objs=self.env['account.account'].search([('id','!=',1),('id','!=',2),('id','!=',34),('id','!=',id99.id)])
            
#             for line in objs:
#                 line.parent_balance=0
#           #      line.child_balance=0
#          #       print 'linewwwwwwwww=', line.child_id
#                 for chil in line.child_id:
#          #           print 'test1================',chil.id
#                     if chil.id != False:
#           #              print 'chil=====================', chil
#                         chil.child_balance=chil.temp_balance
#                 if line.child_id:
#                     for child in line.child_id:
#                #         print 'child========================',child.temp_balance,child,line
#                         line.parent_balance += child.temp_balance
                            
#             #print 'objs2=============================',objs2,objs2.child_id
#             objs2.liability_ids = False
#             objs2.asset_ids = False
#             for childs in objs2.child_id:
#              #   print 'childs============================',childs,childs.balance,childs.user_type.report_type
#                 if childs.user_type.report_type == 'liability' and (childs.debit != 0.0 or childs.credit != 0.0):
    
#                    objs2.liability_ids += childs
#          #          print 'grand child================', childs.child_id
#                    for childss in childs.child_id:
#                        objs2.liability_ids += childss
#               #     print 'asdasdasds=======================',objs2.liability_ids,childs
#                 elif childs.user_type.report_type == 'asset' and (childs.debit != 0.0 or childs.credit != 0.0):
#                     objs2.asset_ids += childs
#           #          print 'grand child================', childs.child_id
#                     for childss in childs.child_id:
#                        objs2.asset_ids += childss
                                
        
#         return True
        
    # @api.multi
    # def refresh_profit_loss(self):
        
    #     date_from = self._context['date_from']
    #     date_to = self._context['date_to']
    #     period_from = self._context['period_from']
    #     period_to = self._context['period_to']
    #     filter = self._context['filter']
    #     actual_status = self._context['actual_status']
        
    #     acc_obj=self.env['account.account'].search([('id','!=',0)])
        
    #     if filter == 'filter_no':
    #         for line in acc_obj:
                
    #             if line.balance!=0.0:
    #                 move_lines = self.env['account.move.line'].search([('account_id','=',line.id)])
    #                 if actual_status == True:
    #                     move_lines = self.env['account.move.line'].search([('account_id','=',line.id),('review','=',False)])
    #                 print 'move_lines======================', move_lines
    #                 total_debit = 0.0
    #                 total_credit = 0.0
    #                 for moves in move_lines:
    #                     if moves.debit != 0.0:
    #                         total_debit += moves.debit
    #                     if moves.credit != 0.0:
    #                         total_credit += moves.credit
    #                 line.temp_balance =  total_debit - total_credit
            
    #         objs=self.env['account.account'].search([('id','!=',1),('id','!=',2),('id','!=',34)])
    #        # print 'self.move_lines=======================', self.move_lines.id,self.child_id , objs
    #         for line in objs:
    #             line.parent_balance=0
    #       #      line.child_balance=0
    #      #       print 'linewwwwwwwww=', line.child_id
    #             for chil in line.child_id:
    #      #           print 'test1================',chil.id
    #                 if chil.id != False:
    #       #              print 'chil=====================', chil
    #                     chil.child_balance=chil.temp_balance
    #             if line.child_id:
    #                 for child in line.child_id:
    #            #         print 'child========================',child.temp_balance,child,line
    #                     line.parent_balance += child.temp_balance
                            
    #         objs2=self.env['account.account'].search([('id','=',34)])
    #      #   print 'objs2=============================',objs2,objs2.child_id
    #         objs2.expense_ids = False
    #         objs2.income_ids = False
    #         for childs in objs2.child_id:
    #             #print 'childs============================', childs.user_type.report_type
    #             if childs.user_type.report_type == 'expense' and childs.balance != 0.0:
    
    #                objs2.expense_ids += childs
    #      #          print 'grand child================', childs.child_id
    #                for childss in childs.child_id:
    #                    objs2.expense_ids += childss
    #              #  print 'asdasdasds=======================',objs2.liability_ids,childs
    #             elif childs.user_type.report_type == 'income' and childs.balance != 0.0:
    #                 objs2.income_ids += childs
    #       #          print 'grand child================', childs.child_id
    #                 for childss in childs.child_id:
    #                    objs2.income_ids += childss
            
    #     ''' based on date '''
    #     if date_from != False and date_to != False:
    #         for line in acc_obj:
                
    #             if line.balance!=0.0:
    #                 move_lines = self.env['account.move.line'].search([('account_id','=',line.id), ('date','>=',date_from), ('date','<=',date_to)])
    #                 if actual_status == True:
    #                     move_lines = self.env['account.move.line'].search([('account_id','=',line.id),('date','>=',date_from), ('date','<=',date_to),('review','=',False)])
    #                 print 'move_lines======================', move_lines
    #                 total_debit = 0.0
    #                 total_credit = 0.0
    #                 for moves in move_lines:
    #                     if moves.debit != 0.0:
    #                         total_debit += moves.debit
    #                     if moves.credit != 0.0:
    #                         total_credit += moves.credit
    #                 line.temp_balance =  total_debit - total_credit
            
    #         objs=self.env['account.account'].search([('id','!=',1),('id','!=',2),('id','!=',34)])
    #        # print 'self.move_lines=======================', self.move_lines.id,self.child_id , objs
    #         for line in objs:
    #             line.parent_balance=0
    #       #      line.child_balance=0
    #      #       print 'linewwwwwwwww=', line.child_id
    #             for chil in line.child_id:
    #      #           print 'test1================',chil.id
    #                 if chil.id != False:
    #       #              print 'chil=====================', chil
    #                     chil.child_balance=chil.temp_balance
    #             if line.child_id:
    #                 for child in line.child_id:
    #            #         print 'child========================',child.temp_balance,child,line
    #                     line.parent_balance += child.temp_balance
                            
    #         objs2=self.env['account.account'].search([('id','=',34)])
    #      #   print 'objs2=============================',objs2,objs2.child_id
    #         objs2.expense_ids = False
    #         objs2.income_ids = False
    #         for childs in objs2.child_id:
    #             #print 'childs============================', childs.user_type.report_type
    #             if childs.user_type.report_type == 'expense' and childs.balance != 0.0:
    
    #                objs2.expense_ids += childs
    #      #          print 'grand child================', childs.child_id
    #                for childss in childs.child_id:
    #                    objs2.expense_ids += childss
    #              #  print 'asdasdasds=======================',objs2.liability_ids,childs
    #             elif childs.user_type.report_type == 'income' and childs.balance != 0.0:
    #                 objs2.income_ids += childs
    #       #          print 'grand child================', childs.child_id
    #                 for childss in childs.child_id:
    #                    objs2.income_ids += childss
                 
    #     ''' report based on period '''
                       
    #     if period_from != False and period_to != False:
            
    #         print 'period_from===========================',period_from,period_to
    #         date_start = self.env['account.period'].search([('id','=',period_from)]).date_start
    #         date_stop = self.env['account.period'].search([('id','=',period_to)]).date_stop
            
    #         print 'date_start===============================', date_start,date_stop
            
    #         for line in acc_obj:
                
    #             if line.balance!=0.0:
    #                 move_lines = self.env['account.move.line'].search([('account_id','=',line.id), ('date','>=',date_start), ('date','<=',date_stop)])
    #                 if actual_status == True:
    #                     move_lines = self.env['account.move.line'].search([('account_id','=',line.id),('date','>=',date_start), ('date','<=',date_stop),('review','=',False)])
    #                 print 'move_lines======================', move_lines
    #                 total_debit = 0.0
    #                 total_credit = 0.0
    #                 for moves in move_lines:
    #                     if moves.debit != 0.0:
    #                         total_debit += moves.debit
    #                     if moves.credit != 0.0:
    #                         total_credit += moves.credit
    #                 line.temp_balance =  total_debit - total_credit
            
    #         objs=self.env['account.account'].search([('id','!=',1),('id','!=',2),('id','!=',34)])
    #        # print 'self.move_lines=======================', self.move_lines.id,self.child_id , objs
    #         for line in objs:
    #             line.parent_balance=0
    #       #      line.child_balance=0
    #      #       print 'linewwwwwwwww=', line.child_id
    #             for chil in line.child_id:
    #      #           print 'test1================',chil.id
    #                 if chil.id != False:
    #       #              print 'chil=====================', chil
    #                     chil.child_balance=chil.temp_balance
    #             if line.child_id:
    #                 for child in line.child_id:
    #            #         print 'child========================',child.temp_balance,child,line
    #                     line.parent_balance += child.temp_balance
                            
    #         objs2=self.env['account.account'].search([('id','=',34)])
    #      #   print 'objs2=============================',objs2,objs2.child_id
    #         objs2.expense_ids = False
    #         objs2.income_ids = False
    #         for childs in objs2.child_id:
    #             #print 'childs============================', childs.user_type.report_type
    #             if childs.user_type.report_type == 'expense' and childs.balance != 0.0:
    
    #                objs2.expense_ids += childs
    #      #          print 'grand child================', childs.child_id
    #                for childss in childs.child_id:
    #                    objs2.expense_ids += childss
    #              #  print 'asdasdasds=======================',objs2.liability_ids,childs
    #             elif childs.user_type.report_type == 'income' and childs.balance != 0.0:
    #                 objs2.income_ids += childs
    #       #          print 'grand child================', childs.child_id
    #                 for childss in childs.child_id:
    #                    objs2.income_ids += childss
                
        
    #     return True    
    
    
#     @api.multi
#     def function_call_new(self):
#    #     ldry_total=0.0 
#         objs=self.env['account.account'].search([('id','!=',False)])
#        # print 'self.move_lines=======================', self.move_lines.id,self.child_id , objs
#         for line in objs:
#            # print 'line====================================',line
#             line.is_child = False
#             if line.type == 'view':
#                 line.is_child = True
#            #     print 'is_child==================================',line.is_child
# #             for lines in line.child_id:
# #                 print 'line====================================',line
# #                 if lines.id != False: 
# #                     line.is_child = True
# #                     print 'is_child==================================',line.is_child
#     #        print 'move_lines============================', line.move_lines
#             for lines2 in line.move_lines:
#                     if lines2.id != False: 
#                         line.is_move_lines = True
#             for type in line.user_type:
#       #          print 'type=====================', type.report_type
#                 line.parent_type = type.report_type
                        
#         objs2=self.env['account.account'].search([('id','=',2)])
#  #       print 'objs2=============================',objs2,objs2.child_id
#        # objs2.liability_ids=objs2.child_id
#         objs2.liability_ids = False
#         for childs in objs2.child_id:
#   #          print 'childs============================', childs.user_type.report_type
#             if childs.user_type.report_type == 'liability':
#                # objs2.write({'liability_ids' : childs.id})
#            #    [objs2.liability_ids].append(childs.id)
#                objs2.liability_ids += childs
#    #            print 'asdasdasds=======================',objs2.liability_ids,childs
#             elif childs.user_type.report_type == 'asset':
#                 objs2.asset_ids += childs
                
        
#         return True
    
    
    @api.multi
    def open_selected_accounts(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['account.account'].search([('id','=',self.id)])

        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Acount Form view',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'account.account',
            'view_id':'view_account_form_changed',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':context,
        }
        
        
    @api.multi
    def open_selected_accounts2(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['account.account'].search([('id','=',self.id)])

    #    context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Acount Form view2',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'account.account',
            'view_id':'view_account_form_hiworth',
            'type':'ir.actions.act_window',
            'res_id':res_id,
          #  'context':context,
        }
        
        
class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    
    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None: 
            context = {}
        line_num = 1    
    
        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context) 
            line_num = 1
            for line_rec in first_line_rec.move_id.attachment_ids: 
                line_rec.line_no = line_num 
                line_num += 1
            line_num = 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    move_line_id = fields.Many2one('account.move.line', 'Entry')
    move_id = fields.Many2one('account.move', 'Entry')
    
    
class account_move(models.Model):
    _inherit = "account.move" 
    _order = 'date desc'
    
    
    @api.onchange('company_id')
    def onchange_field(self):            
           
        if self.company_id.id != False:
            return {
                'domain': {
                    'journal_id': [('company_id', '=', self.company_id.id)],
                },
            }
            
    @api.multi
    @api.depends('line_id')
    def _compute_account_names(self):
        for line in self:
            line.accounts_names = ''
            for lines in line.line_id:
                line.accounts_names = line.accounts_names + lines.account_id.name + ' '
#                 print 'accounts=================', line.accounts_names
    
    
    review = fields.Boolean('Review')
    line_id = fields.One2many('account.move.line', 'move_id', 'Entries',
                                   copy=True)
    accounts_names = fields.Char(compute='_compute_account_names', store=True, string='Accounts')
    attachment_ids = fields.One2many('ir.attachment', 'move_id', 'Attachments')
    tds_id = fields.Many2one('payment.vouchers.bill', 'Tds Refereance')
#     '''states={'posted':[('readonly',True)]},'''
    
    def write(self, cr, uid, ids, vals, context=None):
        if context is None:
            context = {}
        c = context.copy()
        c['novalidate'] = True
        result = super(account_move, self).write(cr, uid, ids, vals, c)
        self.validate(cr, uid, ids, context=context)
       
        if 'review' in vals:
            for line in self.browse(cr, uid, ids, context):
                for lines in line.line_id:
                    lines.review = line.review
        return result
    
    @api.multi
    def post_moves(self):
        for line in self:
            if line.state == 'draft':
                line.post()
    @api.multi
    def cancel_moves(self):
        for line in self:
            if line.state == 'posted':
                line.button_cancel()
    
    def post(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoice = context.get('invoice', False)
        valid_moves = self.validate(cr, uid, ids, context)

        if not valid_moves:
            raise osv.except_osv(_('Error!'), _('You cannot validate a non-balanced entry.\nMake sure you have configured payment terms properly.\nThe latest payment term line should be of the "Balance" type.'))
        obj_sequence = self.pool.get('ir.sequence')
        for move in self.browse(cr, uid, valid_moves, context=context):
            if move.name =='/':
                new_name = False
                journal = move.journal_id

                if invoice and invoice.internal_number:
                    new_name = invoice.internal_number
                else:
                    if journal.sequence_id:
                        c = {'fiscalyear_id': move.period_id.fiscalyear_id.id}
                        new_name = obj_sequence.next_by_id(cr, uid, journal.sequence_id.id, c)
                    else:
                        raise osv.except_osv(_('Error!'), _('Please define a sequence on the journal.'))

                if new_name:
                    self.write(cr, uid, [move.id], {'name':new_name})
            cr.execute('UPDATE account_move_line '\
                   'SET is_posted=True '\
                   'WHERE move_id = %s',
                   (move.id,))
                   
        cr.execute('UPDATE account_move '\
                   'SET state=%s '\
                   'WHERE id IN %s',
                   ('posted', tuple(valid_moves),))
                   
        
        self.invalidate_cache(cr, uid, ['state', ], valid_moves, context=context)
        return True
        
    def button_cancel(self, cr, uid, ids, context=None):
        for line in self.browse(cr, uid, ids, context=context):
            cr.execute('UPDATE account_move_line '\
                   'SET is_posted=False '\
                   'WHERE move_id = %s',
                   (line.id,))
            if not line.journal_id.update_posted:
                raise osv.except_osv(_('Error!'), _('You cannot modify a posted entry of this journal.\nFirst you should set the journal to allow cancelling entries.'))
        if ids:
            cr.execute('UPDATE account_move '\
                       'SET state=%s '\
                       'WHERE id IN %s', ('draft', tuple(ids),))
            
            self.invalidate_cache(cr, uid, context=context)
        return True
     
class account_invoice_no(models.Model):
    _name = 'account.invoice.no'
    
    @api.multi
    @api.depends('move_line_id')
    def _compute_credit(self):
        for line in self:
            for move in line.move_line_id:
#                 print 'rse========================='
                if move.account_id.type == 'payable':
#                     print '============================'
                    line.credit += move.credit
                
    @api.multi
    @api.depends('move_line_id')
    def _compute_debit(self):
        for line in self:
            for move in line.move_line_id:
                if move.account_id.type == 'payable':
                    line.debit += move.debit
                
    @api.multi
    @api.depends('debit','credit')
    def _compute_balance(self):
        for line in self:
            for move in line.move_line_id:
                line.balance = line.debit - line.credit 
                
                
    name = fields.Char('Name')
    move_line_id = fields.One2many('account.move.line', 'invoice_no_id', 'Move Lines')
    credit = fields.Float(compute='_compute_credit', string="Credit")
    debit = fields.Float(compute='_compute_debit', string="debit")
    account_id = fields.Many2one('account.account', 'Account')
    balance = fields.Float(compute='_compute_balance', string="Balance")
    
#     @api.model
#     def create(self,vals):
#         print 'vals======================', vals,self
#         if 'move_line_id' in vals:
#             move_obj = self.env['account.move.line'].search([('id','=',vals['move_line_id'])])
#             print '2222222---------------------------', move_obj.account_id,asdd
#             
#         return super(account_invoice_no, self).create(vals)
    
#     debit = 
      
      
class account_move_line(models.Model):
    _inherit = "account.move.line"
    
    
    @api.onchange('account_id')
    def onchange_account(self):            
           
        if self.move_id.company_id.id != False:
            return {
                'domain': {
                    'account_id': [('company_id', '=', self.move_id.company_id.id)],
                },
            }
    
    @api.multi
    @api.depends('move_id')
    def _get_review(self):
        for line in self:
            for lines in line.move_id:
                line.review = lines.review
                
    @api.multi
    @api.depends('move_id')
    def _get_opposite_accounts(self):
        for temp in self:
            temp.opp_acc = ""

            for line in temp.move_id:
                flag = 0

                if temp.debit != 0.0:
                    for lines in line.line_id:
                        if lines.credit == temp.debit:
                            flag=1
                            temp.opp_acc = lines.account_id.name + "Or" + temp.opp_acc
                    if flag!=1:
                        for lines in line.line_id:
                            if lines.credit!=0.0:
                                temp.opp_acc = lines.account_id.name + "," + temp.opp_acc
                if temp.credit != 0.0:
                    for lines in line.line_id:
                        if lines.debit == temp.credit:
                            flag=1
                            temp.opp_acc = lines.account_id.name + "Or" + temp.opp_acc
                    if flag!=1:
                        for lines in line.line_id:
                            if lines.debit!=0.0:
                                temp.opp_acc = lines.account_id.name + "," + temp.opp_acc

#                         print'opp_acc=============================', temp.opp_acc

    @api.multi
    @api.depends('acc_balance','debit','credit')
    def _compute_current_balance(self):
        for line in self:
                line.current_balance = line.acc_balance + line.debit - line.credit
                
#     @api.multi
# #     @api.depends('move_id')
#     def _find_is_posted(self):
#         for line in self:
#             if line.move_id.state == 'posted':
#                 line.is_posted = True
                        
    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None: 
            context = {}
        line_num = 1    
    
        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context) 
            for line_rec in first_line_rec.move_id.line_id: 
                line_rec.line_no = line_num 
                line_num += 1 

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    review = fields.Boolean(compute='_get_review', store=True, string='Review')
    acc_balance = fields.Float(related='account_id.balance', string='Available Balance', store=True)
    opp_acc = fields.Char(compute='_get_opposite_accounts', string='Account Opposite')
    current_balance = fields.Float(compute='_compute_current_balance', string='Balance', store=True)
    ref_no = fields.Char('Reference No')
    invoice_no_id = fields.Many2one('account.invoice.no', 'Invoice No')
    invoice_balance = fields.Float(related='invoice_no_id.balance', string="Invoice Balance")
    is_posted = fields.Boolean(string="Is Posted", default=False)
    attachment_ids = fields.One2many('ir.attachment', 'move_line_id', 'Attachments')
      
    @api.multi
    def open_journal_entries(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['account.move'].search([('id','=',self.move_id.id)])

        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Staff payments form view',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'account.move',
            'view_id':'account.view_move_form',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':context,
        }
    
    
class res_partner(models.Model):
    _inherit = 'res.partner'
       
    property_account_payable = fields.Many2one('account.account','Account Payable',
            domain="",
            help="This account will be used instead of the default one as the payable account for the current partner",
            required=True)
    property_account_receivable = fields.Many2one('account.account','Account Receivable',
            domain="",
            help="This account will be used instead of the default one as the receivable account for the current partner",
            required=True)


    # @api.model
    # def create(self, vals):
    #     payable_account = False
    #     receivable_account = False
    #     if vals.get('contractor') or vals.get('supplier'):
    #         user_type = self.env['account.account.type'].search([('name','=','Payable')])
    #         parent = self.env['account.account'].search([('name','=','Sundry Creditors'),('company_id','=',vals.get('company_id'))])
    #         temp = 0
    #         list = []
    #         code = ""
    #         for child in parent.child_id:
    #             temp = int(child.code)
    #             list.append(temp)    
    #             if max(list) == 0:
    #                 code = self.parent.code + '001'
    #             if max(list) != 0:
    #                 code = str(max(list)+1)
    #         values = {'parent_id': parent.id,
    #                   'name': vals.get('name'),
    #                   'code': code,
    #                   'type': 'payable',
    #                   'user_type': user_type.id,
    #                   'reconcile':True,
    #                   }
    #         payable_account = self.env['account.account'].create(values)
            
    #     if vals.get('customer'):
    #         user_type = self.env['account.account.type'].search([('name','=','Receivable')])
    #         parent = self.env['account.account'].search([('name','=','Sundry Debtors'),('company_id','=',vals.get('company_id'))])
    #         temp = 0
    #         list = []
    #         code = ""
    #         for child in parent.child_id:
    #             temp = int(child.code)
    #             list.append(temp)    
    #             if max(list) == 0:
    #                 code = self.parent.code + '001'
    #             if max(list) != 0:
    #                 code = str(max(list)+1)
    #         values = {'parent_id': parent.id,
    #                   'name': vals.get('name'),
    #                   'code': code,
    #                   'type': 'receivable',
    #                   'user_type': user_type.id,
    #                   'reconcile':True,
    #                   }
    #         receivable_account = self.env['account.account'].create(values)
        
    #     partner = super(res_partner, self).create(vals)
    #     if payable_account != False:
    #         partner.write({'property_account_payable':payable_account})
    #     if receivable_account != False:
    #         partner.write({'property_account_receivable':receivable_account})
    #     return partner
            
            
class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    
    @api.multi
    @api.depends('payment_ids','residual')
    def _paid_amount(self): 
        for line in self:
            for lines in line.payment_ids:
                if lines.id != False:
                    if lines.credit != False:
                        line.payment_total+=lines.credit
                    if lines.debit != False:
                        line.payment_total-=lines.debit
                        
    @api.multi
    @api.depends('origin')
    def _compute_purchase_order_date(self): 
        for line in self:
            if line.origin != False:
                purchase = self.env['purchase.order'].search([('name','=',line.origin)])
                line.purchase_order_date = purchase.date_order
                
            
                        
                    
    payment_total = fields.Float(compute='_paid_amount', store=True, string="Paid Amount")
    purchase_order_date = fields.Datetime(compute='_compute_purchase_order_date', store=True, string='Purchase Order Date')

            
class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'
    
    
    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None: 
            context = {}
        line_num = 1    
    
        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context) 
            for line_rec in first_line_rec.invoice_id.invoice_line: 
                line_rec.line_no = line_num 
                line_num += 1 

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    
    
    
    
class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    voucher_ids = fields.One2many('payment.vouchers', 'purchase_id', 'Vouchers', domain=[('state','not in',['draft','cancel'])])
    