import itertools
import math
from lxml import etree

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from openerp.osv import fields as old_fields, osv, expression
from pychart.arrow import default
from datetime import datetime
import datetime

TYPE2JOURNAL = {
    'out_invoice': 'sale',
    'in_invoice': 'purchase',
    'out_refund': 'sale_refund',
    'in_refund': 'purchase_refund',
}

class hiworth_invoice(models.Model):
    _name = 'hiworth.invoice'
    _order = 'write_date desc'

    READONLY_STATES = {
        'approve': [('readonly', True)],
        'partial': [('readonly', True)],
        'paid': [('readonly', True)],
        'cancel': [('readonly', True)]
    }

    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return journal.currency or journal.company_id.currency_id

    @api.model
    def _default_journal(self):
        if self._context.get('type2') == 'out':
            inv_type = ['purchase']
        if self._context.get('type2') != 'out':
            inv_type = ['sale']

        # inv_types = inv_type if isinstance(inv_type, list) else [inv_type]
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', inv_type),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)

    @api.model
    def _default_write_off_account(self):
        return self.env['res.company'].browse(self.env['res.company']._company_default_get('hiworth.invoice')).write_off_account_id

    @api.model
    def _default_discount_account(self):
        return self.env['res.company'].browse(self.env['res.company']._company_default_get('hiworth.invoice')).discount_account_id

    @api.onchange('project_id')
    def _onchange_task_selection(self):
        if self.project_id.id != False:
            return {
                'domain': {
                    'task_id': [('project_id','=',self.project_id.id)]
                }
            }


    @api.multi
    @api.depends('invoice_line')
    def _compute_invoiced_amount(self):
        for line in self:
            line.invoiced_amount = 0
            for lines in line.invoice_line:
                line.invoiced_amount += lines.total_amount_with_tax - lines.tax_amount

    @api.multi
    @api.depends('account_move_lines')
    def _compute_paid_amount(self):
        for line in self:
            line.paid_amount = 0
            for lines in line.account_move_lines:
                line.paid_amount += lines.debit


    @api.multi
    @api.depends('account_move_lines')
    def _compute_reduction_amount(self):
        for line in self:
            line.reduction_amount = 0
            for lines in line.account_move_lines:
                line.reduction_amount += lines.credit

    @api.multi
    @api.depends('grand_total','reduction_amount')
    def _compute_amount_tobe_paid(self):
        for line in self:
            line.amount_to_be_paid = 0
            line.amount_to_be_paid = line.amount_total-line.reduction_amount

    @api.multi
    @api.depends('paid_amount','amount_to_be_paid')
    def _compute_balance(self):
        for line in self:
            line.balance = line.amount_to_be_paid - line.paid_amount

    @api.onchange('work_order_id')
    def onchange_work_order(self):
        if self.work_order_id:
            self.project_id = self.work_order_id.project_id.id
            self.partner_id = self.work_order_id.partner_id.id
            self.customer_id = self.work_order_id.project_id.partner_id.id
    @api.multi
    @api.depends('invoiced_amount','discount')
    def _compute_diccount_amount(self):
        for line in self:
            line.diccount_amount = line.invoiced_amount*(line.discount/100)

    @api.multi
    @api.depends('invoiced_amount','diccount_amount')
    def _compute_total_amount(self):
        for line in self:
            line.total_amount = line.invoiced_amount-line.diccount_amount

    @api.multi
    @api.depends('retention','total_amount')
    def _compute_retention_amount(self):
        for line in self:
            line.retention_amount = line.total_amount*(line.retention/100)

    @api.multi
    @api.depends('retention_amount','total_amount')
    def _compute_net_amount(self):
        for line in self:
            line.net_total = line.total_amount-line.retention_amount

    @api.multi
    @api.depends('net_total','addition')
    def _compute_addition_amount(self):
        for line in self:
            line.addition_amount = line.net_total*(line.addition/100)
    @api.multi
    @api.depends('net_total','addition_amount','invoice_lines2','round_off_amount')
    def _compute_grand_total_amount(self):
        for line in self:
            if line.is_purchase_bill == True:
                line.grand_total = 0.0
                for lines in line.invoice_lines2:
                    line.grand_total += lines.price_subtotal
                    line.amount_tax += lines.tax_amount
                line.amount_total = line.grand_total + line.amount_tax + line.round_off_amount - line.discount_amount
            if line.is_purchase_bill == False:
                for lines in line.invoice_line:
                    line.amount_tax += lines.tax_amount
                line.grand_total = line.net_total+line.addition_amount
                line.amount_total = line.grand_total + line.amount_tax + line.round_off_amount


    name = fields.Char(string='Reference/Description', index=True,
       states=READONLY_STATES)
    date_invoice = fields.Date('Date', states=READONLY_STATES)
    partner_id = fields.Many2one('res.partner', string='Partner', change_default=True,
        required=True, states=READONLY_STATES,
        track_visibility='always')
#         readonly=True, states={'draft': [('readonly', False)]},
    origin = fields.Char(string='Source Document',
        help="Reference of the document that produced this invoice.",
        readonly=True, states={'draft': [('readonly', False)]})
    reference = fields.Char(string='Invoice Reference', states=READONLY_STATES,
        help="The partner reference of this invoice.")
    comment = fields.Text('Additional Information', states=READONLY_STATES)
    state = fields.Selection(copy=False, selection=[
            ('draft','Draft'),
            ('waiting','Waiting Approval'),
            ('approve','Approved'),
            ('partial','Partially Paid'),
            ('paid','Paid'),
            ('cancel','Rejected'),
        ], string='Status',  readonly=True, default='draft')
#         compute='_compute_state__get',
    invoice_line = fields.One2many('hiworth.invoice.line', 'invoice_id', string='Invoice Lines', copy=True,states=READONLY_STATES)
#     readonly=True, states={'draft': [('readonly', False)]},
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
    company_id = fields.Many2one('res.company', string='Company', change_default=True,
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env['res.company']._company_default_get('hiworth.invoice'))
    user_id = fields.Many2one('res.users', string='Salesperson', track_visibility='onchange',
        readonly=True, states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user)
    project_id = fields.Many2one('project.project', 'Project', states=READONLY_STATES)
#     task_id = fields.Many2one('project.task', 'Task')
#     agreed_amount = fields.Float(related='task_id.estimated_cost', string="Agreement Amount")
    journal_id = fields.Many2one('account.journal', string='Journal',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_journal,
        domain="[('type', 'in', {'out_invoice': ['sale'], 'out_refund': ['sale_refund'], 'in_refund': ['purchase_refund'], 'in_invoice': ['purchase']}.get(type, [])), ('company_id', '=', company_id)]")
    invoiced_amount = fields.Float(compute='_compute_invoiced_amount', string='Invoiced Amount', states=READONLY_STATES)
    customer_id = fields.Many2one('res.partner', string='Client', states=READONLY_STATES)
    work_order_id = fields.Many2one('work.order', 'Work Order No', states=READONLY_STATES, domain=[('state','in',['approved','start','done'])])
    work_order_id = fields.Many2one('work.order', 'Work Order No', states=READONLY_STATES, domain=[('state','in',['approved','start','done'])])
    generated_lines = fields.Boolean('Generated Invoice Lines', default=False, states=READONLY_STATES)
    discount =  fields.Float('Discount %',states=READONLY_STATES)
    diccount_amount = fields.Float(compute='_compute_diccount_amount', string='Dicount Amount')
    total_amount = fields.Float(compute='_compute_total_amount', string='Total Bill Amount')
    retention = fields.Float('Retention %',states=READONLY_STATES)
    retention_amount = fields.Float(compute='_compute_retention_amount', string='Retention Amount')
    net_total = fields.Float(compute='_compute_net_amount', string='Net Amount')
    addition = fields.Float('Additions %',states=READONLY_STATES)
    addition_amount = fields.Float(compute='_compute_addition_amount', string='Additions Amount')
    grand_total = fields.Float(compute='_compute_grand_total_amount', string='Grand Amount')
    amount_total = fields.Float(compute='_compute_grand_total_amount', string='Total')
    amount_tax = fields.Float(compute='_compute_grand_total_amount', string='Tax Amount')


    balance = fields.Float(compute='_compute_balance', string="Balance", states=READONLY_STATES)
    reduction_amount = fields.Float(compute='_compute_reduction_amount', string='Paid Amount', states=READONLY_STATES)
    amount_to_be_paid = fields.Float(compute='_compute_amount_tobe_paid', string='Amount To Pay', states=READONLY_STATES)
    paid_amount = fields.Float(compute='_compute_paid_amount', string='Paid Amount', states=READONLY_STATES)
    move_id = fields.Many2one('account.move', 'Journal Entry')
    is_purchase_bill = fields.Boolean('Purchase Bill', default=False)
    invoice_lines2 = fields.One2many('hiworth.invoice.line2','invoice_id','Invoice Lines', states=READONLY_STATES)
    purchase_order_date = fields.Datetime('Purchase Order Date', states=READONLY_STATES)
    account_move_lines = fields.One2many('account.move.line', 'invoice_no_id2', 'Payments', states={'paid':[('readonly',True)]})
    account_id = fields.Many2one('account.account', related='partner_id.property_account_payable',  string="Account", states=READONLY_STATES)
    inv_type = fields.Selection(copy=False, selection=[
            ('out','Out'),
            ('in','In'),
        ], string='Type',  readonly=True, default='out', help="out for Supplier Invoice, In for Customer invoice")

    _defaults = {
        'date_invoice': fields.Date.today(),
        }
    round_off_amount = fields.Float('Round off Amount (+/-)', states=READONLY_STATES)
    round_off_account = fields.Many2one('account.account', 'Retention Account', states=READONLY_STATES,
     default=_default_write_off_account)
    discount_amount = fields.Float('Discount Amount', states=READONLY_STATES)
    discount_account = fields.Many2one('account.account', 'Discount Account', states=READONLY_STATES,
     default=_default_discount_account)
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order') 
    trasport_cost_entered = fields.Boolean('Transport Cost Entered', default=False)

    site_purchase_id = fields.Many2one('site.purchase')

    @api.multi
    def open_purchase_order(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['purchase.order'].search([('name','=',self.origin)])

        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Purchase Order view',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'purchase.order',
            'view_id':'purchase_order_form_changed',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':context,
        }

    @api.multi
    def generate_invoice_lines(self):
        self.ensure_one()
        if len(self.invoice_line) > 0:
            raise osv.except_osv(_('Warning!'),
                            _('Some invoice lines are already there. If you want to generate the all lines in work order, First delete the present lines.'))
        order_lines = self.env['work.order.line'].search([('work_order_id','=',self.work_order_id.id)])
        for line in order_lines:
#             invoice_lines = []
#             invoice_lines = self.env['hiworth.invoice.line'].search([('work_order_id','=',self.work_order_id.id),('product_id','=',line.product_id.id),('state','!=','cancel')])
#             pre_qty = 0.0
#             for invoice_line in invoice_lines:
#                 pre_qty += invoice_line.quantity
            values = {'product_id': line.product_id.id,
                      'name':line.product_id.name,
                      'total_assigned_qty':line.qty,
                      'uod_id':line.uom_id.id,
                      'price_unit':line.rate,
                      'pre_amount':line.paid_amount,
                      'pre_qty':line.paid_amount/line.rate,
                      'invoice_id':self.id,
                      'account_id': self.journal_id.default_debit_account_id.id
                      }
            invoice_line_id = self.env['hiworth.invoice.line'].create(values)
            self.generated_lines = True

    @api.multi
    def action_for_approval(self):
        for line in self:
            line.state = 'waiting'

    @api.multi
    def action_approve(self):

        move = self.env['account.move']
        move_line = self.env['account.move.line']
        values = {
                'journal_id': self.journal_id.id,
                'date': self.date_invoice,
                }
        move_id = move.create(values)
        cheque_no = False
        debit = 0
        credit = 0
        if self.inv_type == 'in':
            debit = self.amount_total
        if self.inv_type == 'out':
            credit = self.amount_total
        name = ""
        for line in self.invoice_lines2:
            if line.product_id.categ_id.name  not in name:
                name += line.product_id.categ_id.name +', '
        # for line in self.invoice_line:
        #     name += line.product_id.name +', '
        values2 = {
                'account_id': self.account_id.id,
                'name': name+' from '+self.partner_id.name+' Bill No '+ self.name+' dated '+ self.date_invoice+'.',
                'debit': debit,
                'credit': credit,
                'move_id': move_id.id,
                }
        line_id = move_line.create(values2)
        if self.round_off_amount != 0 and not self.round_off_account:
            raise osv.except_osv(_('Warning!'),
                            _('There is no Account defined for amount write off.'))
        if self.round_off_amount != 0 and self.round_off_account:
            debit4 = 0
            credit4 = 0
            if self.inv_type == 'out' and self.round_off_amount < 0:
                credit4 = abs(self.round_off_amount)
            if self.inv_type == 'out' and self.round_off_amount > 0:
                debit4 = self.round_off_amount
            values4 = {
                'account_id': self.round_off_account.id,
                'name': 'Amount Write off on Bill No '+ self.name+' dated '+ self.date_invoice+' From '+self.partner_id.name,
                'debit': debit4,
                'credit': credit4,
                'move_id': move_id.id,
                }
            line_id = move_line.create(values4)

        if self.discount_amount != 0 and not self.discount_account:
            raise osv.except_osv(_('Warning!'),
                            _('There is no Account defined for discount amount.'))

        if self.discount_amount != 0 and self.discount_account:
            values5 = {
                'account_id': self.discount_account.id,
                'name': 'Discount Amount on Bill No '+ self.name+' dated '+ self.date_invoice+' From '+self.partner_id.name,
                'debit': 0,
                'credit': self.discount_amount,
                'move_id': move_id.id,
                }
            line_id = move_line.create(values5)

        list = []
        acc_list = []
        debit2 = 0
        credit2 = 0
        for line in self.invoice_lines2:

            debit3 = 0
            credit3 = 0
            for tax in  line.tax_ids:
                
                    if tax.child_ids:
                        for lines in tax.child_ids: 
                            if not lines.account_collected_id:
                                raise osv.except_osv(_('Warning!'),
                                        _('There is no account linked to the taxes.'))             
                            if lines.account_collected_id: 
                                tax_list = filter(lambda x: x['account_id'] == lines.account_collected_id.id, list)
                                if self.inv_type == 'out':
                                    # if lines.price_include == True:
                                    debit3 = round(line.price_subtotal*lines.amount, 2)
                                if self.inv_type == 'in':
                                    credit3 = round(line.price_subtotal*lines.amount, 2)
                                if len(tax_list) == 0:
                                    list.append({'account_id':lines.account_collected_id.id, 'debit': debit3, 'credit': credit3, 'move_id': move_id.id, 'name': lines.account_collected_id.name})
                                if len(tax_list) != 0:

                                    a = list.index(tax_list[0])
                                    list[a]['debit'] += debit3
                                    list[a]['credit'] += credit3 
                    else:  
                        if not tax.account_collected_id:
                            raise osv.except_osv(_('Warning!'),
                                    _('There is no account linked to the taxes.'))             
                        if tax.account_collected_id:
                            tax_list = filter(lambda x: x['account_id'] == tax.account_collected_id.id, list)
                            if self.inv_type == 'out':
                                # if tax.price_include == True:
                                debit3 = round(line.price_subtotal*tax.amount, 2)
                            if self.inv_type == 'in':
                                credit3 = round(line.price_subtotal*tax.amount, 2)
                            if len(tax_list) == 0:
                                list.append({'account_id':tax.account_collected_id.id, 'debit': debit3, 'credit': credit3, 'move_id': move_id.id, 'name': tax.account_collected_id.name})
                            if len(tax_list) != 0:

                                a = list.index(tax_list[0])
                                list[a]['debit'] += debit3
                                list[a]['credit'] += credit3

            if self.inv_type == 'in':
                credit2 = line.price_subtotal
            if self.inv_type == 'out':
                debit2 = line.price_subtotal

            entry_list = filter(lambda x: x['account_id'] == line.account_id.id, acc_list)
            
            if len(entry_list) == 0:
                acc_list.append({'account_id':line.account_id.id, 'debit': debit2, 'credit': credit2, 'move_id': move_id.id, 'name': line.product_id.categ_id.name+' From '+line.invoice_id.partner_id.name+' Bill no '+line.invoice_id.name+' dated. '+line.invoice_id.date_invoice+'.',})
            
            if len(entry_list) != 0:
                                a = acc_list.index(entry_list[0])
                                acc_list[a]['debit'] += debit2
                                acc_list[a]['credit'] += credit2
        for entry_line in acc_list:
            line_id = move_line.create(entry_line)

            # line_id = move_line.create(values3)
            
        for line in self.invoice_line:

            if self.inv_type == 'in':
                credit2 = line.total_amount_with_tax - line.tax_amount
            if self.inv_type == 'out':
                debit2 = line.total_amount_with_tax - line.tax_amount
            values3 = {
                    'account_id': line.account_id.id,
                    'name': line.product_id.name,
                    'debit': debit2,
                    'credit': credit2,
                    'move_id': move_id.id,
                  }
            line_id = move_line.create(values3)
            taxi = 0
            taxe = 0
            for tax in line.tax_ids:
                if tax.child_ids:
                    for lines in tax.child_ids:
                        if lines.price_include == True:
                            taxi += lines.amount
                        if lines.price_include == False:
                            taxe += lines.amount
                else:
                    if tax.price_include == True:
                        taxi += tax.amount
                    if tax.price_include == False:
                        taxe += tax.amount
            price_subtotal = line.price_subtotal/(1+taxi)
            print 'price_subtotal=============', price_subtotal
            debit3 = 0
            credit3 = 0
            for tax in  line.tax_ids:

                if tax.child_ids:
                    for lines in tax.child_ids: 
                        if not lines.account_collected_id:
                            raise osv.except_osv(_('Warning!'),
                                    _('There is no account linked to the taxes.')) 

                        if lines.account_collected_id: 
                            tax_list = filter(lambda x: x['account_id'] == lines.account_collected_id.id, list)
                            if self.inv_type == 'out':
                                # if lines.price_include == True:
                                if lines.price_include == True:
                                    debit3 = round(price_subtotal*lines.amount, 2)
                                else:
                                    debit3 = round(price_subtotal*lines.amount, 2)
                            if self.inv_type == 'in':
                                if lines.price_include == True:
                                    credit3 = round(price_subtotal*lines.amount, 2)
                                else:
                                    credit3 = round(price_subtotal*lines.amount, 2)
                            if len(tax_list) == 0:
                                list.append({'account_id':lines.account_collected_id.id, 'debit': debit3, 'credit': credit3, 'move_id': move_id.id, 'name': lines.account_collected_id.name})
                            if len(tax_list) != 0:

                                a = list.index(tax_list[0])
                                list[a]['debit'] += debit3
                                list[a]['credit'] += credit3 
                else:  
                    if not tax.account_collected_id:
                        raise osv.except_osv(_('Warning!'),
                                _('There is no account linked to the taxes.'))             
                    if tax.account_collected_id:
                        tax_list = filter(lambda x: x['account_id'] == tax.account_collected_id.id, list)
                        if self.inv_type == 'out':
                            if tax.price_include == True:
                                debit3 = round(price_subtotal*tax.amount, 2)
                            else:
                                debit3 = round(price_subtotal*tax.amount, 2)
                        if self.inv_type == 'in':
                            if tax.price_include == True:
                                credit3 = round(price_subtotal*tax.amount, 2)
                            else:
                                credit3 = round(price_subtotal*tax.amount, 2)
                        if len(tax_list) == 0:
                            list.append({'account_id':tax.account_collected_id.id, 'debit': debit3, 'credit': credit3, 'move_id': move_id.id, 'name': tax.account_collected_id.name})
                        if len(tax_list) != 0:

                            a = list.index(tax_list[0])
                            list[a]['debit'] += debit3
                            list[a]['credit'] += credit3
        for tax_line in list:
            line_id = move_line.create(tax_line)

        move_id.button_validate()
        self.move_id = move_id.id

        if self.is_purchase_bill == True:
            if self.amount_tax != 0:
                print 'aaaaaaaaaaaaaaaaa', self.company_id.gst_account_id.id
                if not self.company_id.gst_account_id.id:
                    raise osv.except_osv(_('Warning!'),
                            _('There is no default GST Account defined for company.'))                    
                values10 = {
                    'journal_id': self.journal_id.id,
                    'date': self.date_invoice,
                    'invoice_id': self.id,
                    }
                move_id2 = move.create(values10)

                values11 = {
                    'account_id': self.company_id.gst_account_id.id,
                    'name': 'GST Amount on Bill No '+ self.name+' dated '+ self.date_invoice+' From '+self.partner_id.name,
                    'debit': 0,
                    'credit': self.amount_tax,
                    'move_id': move_id2.id,
                    }
                line_id = move_line.create(values11)

                if not self.purchase_order_id.location_id.default_gst_account.id:
                    raise osv.except_osv(_('Warning!'),
                            _('There is no default GST Account defined for destination location.')) 
                values12 = {
                    'account_id': self.purchase_order_id.location_id.default_gst_account.id,
                    'name': 'GST Amount on Bill No '+ self.name+' dated '+ self.date_invoice+' From '+self.partner_id.name,
                    'debit': self.amount_tax,
                    'credit': 0,
                    'move_id': move_id2.id,
                    }
                line_id = move_line.create(values12)

                for lines in self.invoice_lines2:
                    transport = self.env['product.location.transport'].search([('expense_account_id','=',self.purchase_order_id.location_id.default_gst_account.id),('product_id','=',lines.product_id.id)])
                    if len(transport) == 0:
                        values13 = {'expense_account_id': self.purchase_order_id.location_id.default_gst_account.id,
                                  'product_id': lines.product_id.id,
                                  'avg_trasport': lines.tax_amount,
                                  'product_qty': lines.quantity}
                        transport.create(values13)

                    else:
                        # print 'test=================3', transport
                        transport.avg_trasport += lines.tax_amount
                        transport.product_qty += lines.quantity

                    move_id2.button_validate()


        for line in self:
            line.state = 'approve'

    @api.multi
    def action_paid_partial(self):
        for line in self:
            line.state = 'partial'
            # if self.origin != False:
            #     purchase_order =  self.env['purchase.order'].search([('name','=',self.origin)])
            #     purchase_order.state = 'done'
            for invoice_line in line.invoice_line:
                invoice_line.state = 'partial'

    @api.multi
    def action_payment(self):
        user = self.env['res.users'].sudo().search([('id','=',self.env.user.id)])
        vals = False
        # if user:
        #     if user.employee_id or user.id == 1:
        #         vals = user.employee_id.id if user.id !=1 else self.env['hr.employee'].search([('id','=',1)]).id
        #     else:
        #         raise except_orm(_('Warning'),_('User have To Be Linked With Employee.'))

        # res_id = False
        print 'chck-----------------------------------------', user.employee_id, user.id
        print 'chck111-----------------------------------------', self.id, vals, self.balance
        res = {
            'name': 'Invoice Payment',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'hiworth.invoice.payment.wizard',
            # 'domain': [('line_id', '=', self.id),('date','=',_self.date)],
            'context': {'default_invoice_id': self.id, 'default_user_id': vals, 'default_payment_amount': self.balance},
            # 'res_id': res_id,
            'target': 'new',
            'type': 'ir.actions.act_window',

        }

        return res


    @api.multi
    def action_paid(self):
        for line in self:
            for inv in line.invoice_line:
                if (inv.stage_id.approximated_amnt - inv.stage_id.amount_paid) < inv.price_subtotal:
                    raise osv.except_osv(_('Warning!'),
                            _('Amount To Pay is higher'))
                else:
                    inv.stage_id.amount_paid += inv.price_subtotal 
            line.state = 'paid'
            if self.origin != False:
                purchase_order =  self.env['purchase.order'].search([('name','=',self.origin)])
                purchase_order.state = 'paid'
            for invoice_line in line.invoice_line:
                invoice_line.state = 'paid'


    @api.multi
    def action_cancel(self):
        for line in self:
            line.state = 'cancel'
            for invoice_line in line.invoice_line:
                invoice_line.state = 'cancel'
            line.move_id.button_cancel()
            line.move_id.unlink()
            move_id2 = self.env['account.move'].search([('invoice_id','=',line.id)])
            move_id2.button_cancel()
            move_id2.unlink()
            for lines in line.invoice_lines2:
                transport = self.env['product.location.transport'].search([('expense_account_id','=',line.purchase_order_id.location_id.default_gst_account.id),('product_id','=',lines.product_id.id)])
                if len(transport) != 0:
                    # print 'test=================3', transport
                    transport.avg_trasport -= lines.tax_amount
                    transport.product_qty -= lines.quantity


    @api.multi
    def set_to_draft(self):
        for line in self:
            line.state = 'draft'
            for invoice_line in line.invoice_line:
                invoice_line.state = 'draft'

    @api.model
    def create(self,vals):
        if vals.get('is_purchase_bill') != True:
            now = datetime.datetime.now()
            cb_no = self.env['ir.sequence'].get('cb_no')
            vals['name'] = "INV/CB/TECH/" + str(cb_no)+"/" + str(now.year)
        if 'name' in vals:
            if len(self.env['hiworth.invoice'].search([('name','=',vals['name'])])) > 0:
                raise osv.except_osv(_('Warning!'),
                            _('There is already present an invoice with the same Invoice No.'))
        return super(hiworth_invoice, self).create(vals)

    @api.multi
    def write(self,vals):
        if 'name' in vals:
            if len(self.env['hiworth.invoice'].search([('name','=',vals['name'])])) > 1:
                raise osv.except_osv(_('Warning!'),
                            _('There is already present an invoice with the same Invoice No.'))
        super(hiworth_invoice, self).write(vals)
        return True

    

class InvoicePaymentWizard(models.TransientModel):
    _name = 'hiworth.invoice.payment.wizard'

    invoice_id = fields.Many2one('hiworth.invoice','Invoice No')
    user_id = fields.Many2one('hr.employee','User')
    journal_id = fields.Many2one('account.journal', 'Mode of Payment', domain=[('type','in',['cash','bank'])])
    account_id = fields.Many2one('account.account', 'Account')
    bank_id = fields.Many2one('res.partner.bank', 'Bank')
    payment_amount = fields.Float('Payment Amount')
    date = fields.Date('Date',default=fields.Date.today())
    bank_bool = fields.Boolean('Bank bool', default=False)


    @api.onchange('journal_id','bank_id')
    def onchange_account(self):
        if self.journal_id.type == 'cash':
            self.account_id = self.user_id.petty_cash_account.id
        elif self.journal_id.type == 'bank':
            self.account_id = self.bank_id.journal_id.default_credit_account_id.id
            self.bank_bool = True
        else:
            pass

    @api.multi
    def button_payment(self):
        if not self.invoice_id.partner_id.property_account_receivable:
            raise except_orm(_('Warning'),_('Please Configure Suppliers Account..!!'))  
        
        
        move_expense = self.env['account.move'].create({'journal_id': self.journal_id.id,'date':fields.Date.today()})
        move_line = self.env['account.move.line']
        move_line.create({
                        'move_id':move_expense.id,
                        'state': 'valid',
                        'name': 'Purchase Payment',
                        'account_id':self.invoice_id.partner_id.property_account_receivable.id,
                        'journal_id': self.journal_id.id,
                        'period_id' : move_expense.period_id.id,
                        'debit':self.payment_amount,
                        'credit':0,
                        'invoice_no_id2': self.invoice_id.id,
                        })
        move_line.create({
                        'move_id':move_expense.id,
                        'state': 'valid',
                        'name': 'Purchase Payment',
                        'account_id':self.account_id.id,
                        'journal_id':  self.journal_id.id,
                        'period_id' : move_expense.period_id.id,
                        'debit':0,
                        'credit':self.payment_amount,
                        })
        move_expense.button_validate()
        # move_expense.state = 'posted'
        paid_amount = 0
        for lines in self.invoice_id.account_move_lines:
            paid_amount += lines.debit
        if self.invoice_id.amount_to_be_paid == paid_amount:
            self.invoice_id.state = 'paid'
        else:
            self.invoice_id.state = 'partial'




class hiworth_invoice_line(models.Model):
    _name = 'hiworth.invoice.line'
    _order = "sequence, id"
    # price_subtotal

    # @api.one
    # @api.depends('price_unit', 'discount', 'invoice_line_tax_id', 'quantity',
    #     'product_id')
    # def _compute_price(self):
    #     for line in self:
    #         line.price_subtotal = line.price_unit*line.quantity

    @api.model
    def _default_price_unit(self):
        if not self._context.get('check_total'):
            return 0
        total = self._context['check_total']
        for l in self._context.get('invoice_line', []):
            if isinstance(l, (list, tuple)) and len(l) >= 3 and l[2]:
                vals = l[2]
                price = vals.get('price_unit', 0) * (1 - vals.get('discount', 0) / 100.0)
                total = total - (price * vals.get('quantity'))
                taxes = vals.get('invoice_line_tax_id')
                if taxes and len(taxes[0]) >= 3 and taxes[0][2]:
                    taxes = self.env['account.tax'].browse(taxes[0][2])
                    tax_res = taxes.compute_all(price, vals.get('quantity'),
                        product=vals.get('product_id'), partner=self._context.get('partner_id'))
                    for tax in tax_res['taxes']:
                        total = total - tax['amount']
        return total

    @api.multi
    @api.depends('pre_qty', 'quantity')
    def _compute_upto_date_qty(self):
        for line in self:
            line.upto_date_qty = line.pre_qty + line.quantity

    @api.multi
    @api.depends('pre_qty', 'price_unit')
    def _compute_pre_amount(self):
        for line in self:
            line.pre_amount = line.pre_qty*line.price_unit


    @api.multi
    @api.depends('pre_amount', 'price_subtotal')
    def _compute_upto_date_amount(self):
        for line in self:
            line.upto_date_amount = line.pre_amount+line.price_subtotal

    @api.multi
    @api.depends('price_unit', 'total_assigned_qty')
    def _compute_total_amount(self):
        for line in self:
            line.total_amount = line.price_unit*line.total_assigned_qty

    # @api.model
    # def _default_account(self):
    #     # XXX this gets the default account for the user's company,
    #     # it should get the default account for the invoice's company
    #     # however, the invoice's company does not reach this point
    #     print 'invocie========================', self.invoice_id 

    #     if self._context.get('type2') == 'out':
    #         return self.env['ir.property'].get('property_account_expense_categ', 'product.category')
    #     else:
    #         return self.env['ir.property'].get('property_account_income_categ', 'product.category')
            
    @api.one
    @api.depends('price_unit', 'discount', 'quantity','product_id','tax_ids')
    def _compute_price(self):
        for line in self:
            taxi = 0
            taxe = 0
            for tax in line.tax_ids:
                if tax.child_ids:
                    for lines in tax.child_ids:
                        if lines.price_include == True:
                            taxi += lines.amount
                        if lines.price_include == False:
                            taxe += lines.amount
                else:
                    if tax.price_include == True:
                        taxi += tax.amount
                    if tax.price_include == False:
                        taxe += tax.amount
            price_subtotal = line.price_subtotal/(1+taxi)
            # print 'test========================', price_subtotal, taxe, taxi
            line.tax_amount = price_subtotal*(taxe+taxi) 
            line.total_amount_with_tax = price_subtotal + line.tax_amount



    name = fields.Char('Name')
    sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
    origin = fields.Char(string='Source Document',
        help="Reference of the document that produced this invoice.")
    sequence = fields.Integer(string='Sequence', default=10,
        help="Gives the sequence of this line when displaying the invoice.")
    invoice_id = fields.Many2one('hiworth.invoice', string='Invoice Reference',
        ondelete='cascade', index=True)
    uos_id = fields.Many2one('product.uom', string='Unit of Measure',
        ondelete='set null', index=True)
    product_id = fields.Many2one('product.product', string='Product',
        ondelete='restrict', index=True)

    price_unit = fields.Float(string='Unit Price', required=True,
        digits= dp.get_precision('Product Price'),
        default=_default_price_unit)
    price_subtotal = fields.Float(string='Amount')
    quantity = fields.Float(string='Work Order Qty', digits= dp.get_precision('Product Unit of Measure'))
    discount = fields.Float(string='Discount (%)', digits= dp.get_precision('Discount'),
        default=0.0)
    tax_ids = fields.Many2many('account.tax',
        'hiworth_invoice_line_tax', 'invoice_line_id', 'tax_id',
        string='Taxes')
    state = fields.Selection([
            ('draft','Draft'),
            ('partial','Partially Paid'),
            ('paid','Paid'),
            ('cancel','Cancelled'),
        ], string='Status', readonly=True, default='draft')
    company_id = fields.Many2one('res.company', string='Company',
        related='invoice_id.company_id', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner',
        related='invoice_id.partner_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        related='invoice_id.currency_id', store=True, readonly=True)
#     task_id = fields.Many2one('project.task', string='Task',
#         related='invoice_id.task_id', store=True, readonly=True)
    date = fields.Date('Date')
    total_assigned_qty = fields.Float('Assigned Qty')
    remarks = fields.Text('Description')
    shd_no = fields.Char('Shd No.')
    pre_qty = fields.Float('Previous Qty')
    upto_date_qty = fields.Float(compute='_compute_upto_date_qty', store=True, string='Balance Qty')
    pre_amount = fields.Float(compute='_compute_pre_amount', store=True, string='Previous Amount')
    upto_date_amount = fields.Float(compute='_compute_upto_date_amount', store=True, string='Up to Date Amount')
    total_amount = fields.Float(compute='_compute_total_amount',store=True, string='Total Amount')
    remark = fields.Char('Remarks')

    work_order_id = fields.Many2one(related='invoice_id.work_order_id', store=True, string="Work Order")
    stage_id = fields.Many2one('stage.line.prime','Stage')



    
    account_id = fields.Many2one('account.account', string='Account',
        required=True, domain=[('type', 'not in', ['view', 'closed'])],
        help="The income or expense account related to the selected product.")
    # tax_ids = fields.Many2many('account.tax', 'invoice_line_tax_rel',  'line_id', 'tax_id', 'Taxes')
    tax_amount = fields.Float(string='Tax Amount',
        store=True, compute='_compute_price', digits= dp.get_precision('Account'))
    total_amount_with_tax = fields.Float(string='Total With Tax Amount',
        store=True, compute='_compute_price', digits= dp.get_precision('Account'))



    @api.onchange('stage_id','price_unit','total_assigned_qty','price_subtotal')
    def _onchange_stages(self):
        if self.stage_id and self.total_amount !=0:
            if self.stage_id.approximated_amnt < self.price_subtotal:
                self.price_subtotal = 0
                print "self.stage_id.id===========", self.stage_id
                return {
                    'warning': {
                                'title': 'Warning',
                                'message': "The Amount Exceeds The Stage Total Limit"
                                    }
                                }
#     @api.model
#     def create(self,vals):
# #         print 'self============================',vals['invoice_id'],rgrfsfdf
# #         if vals['invoice_id']:
#         print 'asdddd================== ',self.invoice_id,self.env['hiworth.invoice'].search([('id','=',vals['invoice_id'])])
#         self.env['hiworth.invoice'].search([('id','=',vals['invoice_id'])]).compute_state__get()
#
#         return super(hiworth_invoice_line, self).create(vals)

    @api.onchange('price_subtotal')
    def amount_change(self):
#         print 'aaaaaaaaaaaa=============='
        if self.price_unit != 0.0 and self.price_subtotal != 0.0:
            self.quantity = self.price_subtotal/self.price_unit

    # @api.onchange('price_unit','quantity')
    # def quantity_change(self):
    #     if self.price_unit != 0.0 and self.price_subtotal != 0:
    #         self.price_subtotal = float(str(round(self.quantity*self.price_unit, 2)))



    @api.onchange('product_id')
    def product_id_change(self):

        if self.partner_id.id == False:
            raise except_orm(_('No Partner Defined!'), _("You must first select a partner."))
        if self.invoice_id.work_order_id.id == False:
            raise except_orm(_('No Work Order Selected!'), _("You must first select a Work Order."))
        values = {}


#         if uom_id:
#             uom = self.env['product.uom'].browse(uom_id)
#             if product.uom_id.category_id.id == uom.category_id.id:
#                 values['uos_id'] = uom_id

#         dom/ain = {'uos_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}

        self.company = self.env['res.company'].browse(self.company_id.id)
        self.currency = self.env['res.currency'].browse(self.currency_id.id)

#         if company and currency:
#             if company.currency_id != currency:
#                 values['price_unit'] = values['price_unit'] * currency.rate
#
#             if values['uos_id'] and values['uos_id'] != product.uom_id.id:
#                 values['price_unit'] = self.env['product.uom']._compute_price(
#                     product.uom_id.id, values['price_unit'], values['uos_id'])

#         order_lines = self.env['work.order.line'].search([('work_order_id','=',self.invoice_id.work_order_id.id)])
        if self.product_id.id != False:
            product_spec = self.env['work.order.line'].search([('work_order_id','=',self.invoice_id.work_order_id.id),('product_id','=',self.product_id.id)])[0]
#             print 'product_spec========================', product_spec
            self.uos_id = product_spec.uom_id.id
            self.remarks = product_spec.remarks
            self.price_unit =  product_spec.rate
            self.name = product_spec.product_id.name
            self.total_assigned_qty = product_spec.qty

#         invoice_lines = []
        invoice_lines = self.env['hiworth.invoice.line'].search([('work_order_id','=',self.work_order_id.id),('product_id','=',self.product_id.id),('state','!=','cancel')])
        # print 'invoice_lines============================', invoice_lines
        pre_qty = 0.0
        for invoice_line in invoice_lines:
            pre_qty += invoice_line.quantity
        self.pre_qty = pre_qty

        product_ids = []
        if self.invoice_id.work_order_id.id != False:
#             print 'test======================',task_id,product
            order_lines = self.env['work.order.line'].search([('work_order_id','=',self.invoice_id.work_order_id.id)])
            product_ids = [order_line.product_id.id for order_line in order_lines]
            return {'domain': {'product_id': [('id','in',product_ids)]}}

    @api.onchange('quantity')
    def _onchange_qty(self):
        if self.quantity > self.total_assigned_qty-self.pre_qty:
            self.quantity = self.total_assigned_qty-self.pre_qty
            return {
                    'warning': {
                                'title': 'Warning',
                                'message': "Qty is greater than Qty to be invoiced."
                                    }
                                }


#             task_id = self.invoice_id.task_id
# #             print 'task_id===================', self.invoice_id,self.invoice_id.task_id
#
#             estimation = self.env['project.task.estimation'].search([('task_id','=',task_id.id),('pro_id','=',self.product_id.id)])
# #             print 'estimation========================', estimation
#             if estimation.invoiced_qty == 0.0:
#                 if estimation.qty == 0.0:
#                     self.quantity = 0.0
#                     return {
#                         'warning': {
#                                 'title': 'Warning',
#                                 'message': "Please enter some Qty in the Estimation."
#                                     }
#                                 }
#                 if estimation.qty < self.quantity:
#                     self.quantity = estimation.qty
# #                     estimation.write({'invoiced_qty': self.quantity})
#                     return {
#                         'warning': {
#                                 'title': 'Warning',
#                                 'message': "Entered qty is greater than the qty to invoice."
#                                     }
#                                 }
#                 if estimation.qty > self.quantity:
#                     print 'qweqeqweqeqwe'
# #                     estimation.write({'invoiced_qty': self.quantity})
# #                 print 'estimation=======================', estimation,estimation.invoiced_qty
#             if estimation.invoiced_qty != 0.0:
#                 if self.quantity > estimation.qty - estimation.invoiced_qty:
#                     self.quantity = estimation.qty - estimation.invoiced_qty
# #                     print 'asdasd========================', self.quantity
#                     return {
#                         'warning': {
#                                 'title': 'Warning',
#                                 'message': "Entered qty is greater than the qty to invoice."
#                                     }
#                                 }
#

class hiworth_invoice_line2(models.Model):
    _name = 'hiworth.invoice.line2'

    @api.one
    @api.onchange('product_id')
    def onchange_product(self):
        if self.product_id:
            self.uos_id = self.product_id.uom_id.id
            self.price_unit = self.product_id.standard_price

    # @api.one
    # @api.depends('price_unit', 'discount', 'quantity','product_id','tax_ids')
    # def _compute_price(self):
    #     for line in self:
    #         taxi = 0
    #         taxe = 0
    #         for tax in line.tax_ids:
    #             if tax.cZZZZZ
    #             if tax.price_include == True:
    #                 taxi += tax.amount
    #             if tax.price_include == False:
    #                 taxe = tax.amount
    #         line.price_subtotal = line.price_unit*line.quantity/(1+taxi)
            # line.tax_amount = (line.quantity*line.price_unit-line.price_subtotal) + (line.price_subtotal*taxe)

    @api.one
    @api.depends('price_unit', 'discount', 'quantity','product_id','tax_ids')
    def _compute_price(self):
        for line in self:
            taxi = 0
            taxe = 0
            for tax in line.tax_ids:
                if tax.child_ids:
                    for lines in tax.child_ids:
                        if lines.price_include == True:
                            taxi += lines.amount
                        if lines.price_include == False:
                            taxe += lines.amount
                else:
                    if tax.price_include == True:
                        taxi += tax.amount
                    if tax.price_include == False:
                        taxe += tax.amount
            # print 'test========================'
            line.price_subtotal = line.price_unit*line.quantity/(1+taxi)
            line.tax_amount = (line.quantity*line.price_unit-line.price_subtotal) + (line.price_subtotal*taxe)
    
    @api.model
    def _default_account(self):
        # XXX this gets the default account for the user's company,
        # it should get the default account for the invoice's company
        # however, the invoice's company does not reach this point
        if self._context.get('type2') == 'out':
            return self.env['ir.property'].get('property_account_expense_categ', 'product.category')
        else:
            return self.env['ir.property'].get('property_account_income_categ', 'product.category')
            

    name = fields.Char('Name')
    invoice_id = fields.Many2one('hiworth.invoice', string='Invoice Reference',
        ondelete='cascade', index=True)
    uos_id = fields.Many2one('product.uom', string='Unit of Measure',
        ondelete='set null', index=True)
    product_id = fields.Many2one('product.product', string='Product',
        ondelete='restrict', index=True)
    account_id = fields.Many2one('account.account', string='Account',
        required=True, domain=[('type', 'not in', ['view', 'closed'])],
        default=_default_account,
        help="The income or expense account related to the selected product.")
    price_unit = fields.Float(string='Unit Price', required=True,
        digits= dp.get_precision('Product Price'))
    price_subtotal = fields.Float(string='Amount', digits= dp.get_precision('Account'),
        store=True, readoinvoice_idnly=True, compute='_compute_price')
    quantity = fields.Float(string='Quantity', digits= dp.get_precision('Product Unit of Measure'))
    discount = fields.Float(string='Discount (%)', digits= dp.get_precision('Discount'),
        default=0.0)

    company_id = fields.Many2one('res.company', string='Company',
        related='invoice_id.company_id', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Partner',
        related='invoice_id.partner_id', store=True, readonly=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        related='invoice_id.currency_id', store=True, readonly=True)
    task_id = fields.Many2one('project.task', 'Task')
    location_id = fields.Many2one(related='task_id.project_id.location_id', string="Location")
    # account_id = fields.Many2one('account.account', 'Account')
    tax_ids = fields.Many2many('account.tax', 'invoice_line_tax_rel',  'line_id', 'tax_id', 'Taxes')
    tax_amount = fields.Float(string='Tax Amount',
        store=True, compute='_compute_price', digits= dp.get_precision('Account'))

    # _defaults = {
    #     'account_id': _default_account,
    # }