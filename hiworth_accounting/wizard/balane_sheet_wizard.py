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


class accounting_report_wizard(models.Model):
    _name = "accounting.report.wizard"
    

    def _get_fiscalyear(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = time.strftime('%Y-%m-%d')
        company_id = False
        ids = context.get('active_ids', [])
        if ids and context.get('active_model') == 'account.account':
            company_id = self.pool.get('account.account').browse(cr, uid, ids[0], context=context).company_id.id
        else:  # use current company id
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        domain = [('company_id', '=', company_id), ('date_start', '<', now), ('date_stop', '>', now)]
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
        return fiscalyears and fiscalyears[0] or False
    
    def _get_account(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False), ('company_id', '=', user.company_id.id)], limit=1)
        return accounts and accounts[0] or False

#    'enable_filter': fields.Boolean('Enable Comparison'),
#    'account_report_id': fields.many2one('account.financial.report', 'Account Reports', required=True),
#    'label_filter': fields.char('Column Label', help="This label will be displayed on report to show the balance computed for the given comparison filter."),
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year', help='Keep empty for all open fiscal year')
 #   filter_cmp = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date'), ('filter_period', 'Periods')], "Filter by", required=True)
    period_from_cmp = fields.Many2one('account.period', 'Start Period')
    period_to_cmp = fields.Many2one('account.period', 'End Period')
    date_from_cmp = fields.Date("Start Date")
    date_to_cmp = fields.Date("End Date")
 #   'debit_credit': fields.boolean('Display Debit/Credit Columns', help="This option allows you to get more details about the way your balances are computed. Because it is space consuming, we do not allow to use it while doing a comparison."),
    chart_account_id = fields.Many2one('account.account', 'Chart of Account', help='Select Charts of Accounts', required=True, domain = [('parent_id','=',False)])
    company_id = fields.Many2one(related='chart_account_id.company_id', string='Company', store=True)
    fiscalyear_id = fields.Many2one('account.fiscalyear', 'Fiscal Year', help='Keep empty for all open fiscal year')
    filter = fields.Selection([('filter_no', 'No Filters'), ('filter_date', 'Date'), ('filter_period', 'Periods')], "Filter by", required=True)
    period_from = fields.Many2one('account.period', 'Start Period')
    period_to = fields.Many2one('account.period', 'End Period')
  #  journal_ids = fields.Many2many('account.journal', string='Journals', required=True)
    date_from = fields.Date("Start Date")
    date_to = fields.Date("End Date")
    show_actual_finance_status = fields.Boolean("Actual Status")
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                     ('all', 'All Entries'),
                                    ], 'Target Moves', required=True)
   
    
    _defaults = {
            'fiscalyear_id': _get_fiscalyear,
            'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.common.report',context=c),
  #          'journal_ids': _get_all_journal,
            'filter': 'filter_no',
            'chart_account_id': _get_account,
            'target_move': 'posted',
    }
    
    @api.multi
    def view_balance_sheet(self):
        print'vals==================',self.date_from,self.date_to
        view_id = self.env.ref('hiworth_accounting.view_balance_sheet').id
        context = self._context.copy()
      #  print'context===============================', context.update({'date_from': self.date_from,'date_to': self.date_to})
        return {
            'name':'Balance Sheet',
            'view_type':'form',
            'view_mode':'form',
            'views' : [(view_id,'form')],
            'res_model':'account.account',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id':2,
#             'target':'new',
            'context':context,
        } 
        
    @api.multi
    def view_profit_loss_account(self):
        view_id = self.env.ref('hiworth_accounting.view_profit_and_loss').id
        context = self._context.copy()
        return {
            'name':'Balance Sheet',
            'view_type':'form',
            'view_mode':'form',
            'views' : [(view_id,'form')],
            'res_model':'account.account',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id':34,
#             'target':'new',
            'context':context,
        }
         
    
 
#     def _get_account_report(self, cr, uid, context=None):
#         # TODO deprecate this it doesnt work in web
#         menu_obj = self.pool.get('ir.ui.menu')
#         report_obj = self.pool.get('account.financial.report')
#         report_ids = []
#         if context.get('active_id'):
#             menu = menu_obj.browse(cr, uid, context.get('active_id')).name
#             report_ids = report_obj.search(cr, uid, [('name','ilike',menu)])
#         return report_ids and report_ids[0] or False
#  
    
#      
#     def _build_comparison_context(self, cr, uid, ids, data, context=None):
#         if context is None:
#             context = {}
#         result = {}
#         result['fiscalyear'] = 'fiscalyear_id_cmp' in data['form'] and data['form']['fiscalyear_id_cmp'] or False
#         result['journal_ids'] = 'journal_ids' in data['form'] and data['form']['journal_ids'] or False
#         result['chart_account_id'] = 'chart_account_id' in data['form'] and data['form']['chart_account_id'] or False
#         result['state'] = 'target_move' in data['form'] and data['form']['target_move'] or ''
#         if data['form']['filter_cmp'] == 'filter_date':
#             result['date_from'] = data['form']['date_from_cmp']
#             result['date_to'] = data['form']['date_to_cmp']
#         elif data['form']['filter_cmp'] == 'filter_period':
#             if not data['form']['period_from_cmp'] or not data['form']['period_to_cmp']:
#                 raise osv.except_osv(_('Error!'),_('Select a starting and an ending period'))
#             result['period_from'] = data['form']['period_from_cmp']
#             result['period_to'] = data['form']['period_to_cmp']
#         return result
# 
#     def check_report(self, cr, uid, ids, context=None):
#         print 'test=========================121212===============1111111',context
#         if context is None:
#             context = {}
#         res = super(accounting_report, self).check_report(cr, uid, ids, context=context)
#         data = {}
#         data['form'] = self.read(cr, uid, ids, ['account_report_id', 'date_from_cmp',  'date_to_cmp',  'fiscalyear_id_cmp', 'journal_ids', 'period_from_cmp', 'period_to_cmp',  'filter_cmp',  'chart_account_id', 'target_move'], context=context)[0]
#         for field in ['fiscalyear_id_cmp', 'chart_account_id', 'period_from_cmp', 'period_to_cmp', 'account_report_id']:
#             if isinstance(data['form'][field], tuple):
#                 data['form'][field] = data['form'][field][0]
#         comparison_context = self._build_comparison_context(cr, uid, ids, data, context=context)
#         res['data']['form']['comparison_context'] = comparison_context
#         return res
# 
#     def _print_report(self, cr, uid, ids, data, context=None):
#    #     print 'contex=====================================', context['tpqqqqqqqqqqqqqqq']
#         
#         data['form'].update(self.read(cr, uid, ids, ['date_from_cmp',  'debit_credit', 'date_to_cmp',  'fiscalyear_id_cmp', 'period_from_cmp', 'period_to_cmp',  'filter_cmp', 'account_report_id', 'enable_filter', 'label_filter','target_move'], context=context)[0])
#         if context['tp'] == 'view':
#             return self.pool['report'].get_action(cr, uid, [], 'hiworth_accounting.report_financial2', data=data, context=context)
#             ''' not working blank page '''
#         else:
#             return self.pool['report'].get_action(cr, uid, [], 'account.report_financial', data=data, context=context)
# 
# # vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
