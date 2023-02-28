from openerp import fields, models, api
from openerp.osv import fields as old_fields

import time
from datetime import datetime
from openerp.osv import osv
import datetime
#from openerp.osv import fields
from openerp import tools
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from pychart.arrow import default
from cookielib import vals_sorted_by_key
# from pygments.lexer import _default_analyse
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP



class account_account(models.Model):
    _inherit = 'account.account'

    @api.multi
    def view_accounts(self):
        view_id = self.env.ref('hiworth_accounting.view_account_form_hiworth').id
        return {
            'name':'Balance',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id,'form')],
            'res_model':'account.account',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id':self.id,
            'target':'current',
            'context':{},
        }

    @api.multi
    @api.depends('name')            
    def _count_no_of_invoices(self):
        for line in self:
#             print 'q=================', self.env['res.partner'].search([('property_account_payable','=', line.id)])
            partner_id = self.env['res.partner'].search([('property_account_payable','=', line.id)])
            
            if len(partner_id) != 0:
                # print 'partner========', partner_id[0].id
                invoice_ids = self.env['hiworth.invoice'].search([('partner_id','=',partner_id[0].id)])
                line.invoice_count = len(invoice_ids)
        
    location_id = fields.Many2one('stock.location', 'Plot')
    invoice_count = fields.Float(compute='_count_no_of_invoices',  string="Invoice Count")
    is_contractor_payable = fields.Boolean('Is Contractor Payable')
    is_cash_bank = fields.Boolean('Cash/Bank')
    rate = fields.Float('Rate')
    is_mason = fields.Boolean(default=False)
    mason_line = fields.One2many('mason.line','line_id')
    labour_categ = fields.Boolean(default=False)
    is_crusher = fields.Boolean('Is Crusher', default=False)
    is_fuel_pump = fields.Boolean('Is Fuel Pump', default=False)
    is_overhead = fields.Boolean(default=False)

class MasonLine(models.Model):
    _name = 'mason.line'

    line_id = fields.Many2one('account.account')
    name = fields.Many2one('mason.category')
    rate = fields.Float('Rate')
    qty = fields.Float('Qty')
    total = fields.Float('Total',compute='compute_total')
    line_ids = fields.Many2one('partner.daily.statement.line')

    @api.depends('qty','rate')
    def compute_total(self):
        for rec in self:
            if rec.qty and rec.rate:
                rec.total = rec.qty * rec.rate

class MasonCategory(models.Model):
    _name = 'mason.category'

    name = fields.Char('Name',required=True)
    code = fields.Char('Code',required=True)
 
class account_move(models.Model):
    _inherit = 'account.move'

    invoice_id = fields.Many2one('hiworth.invoice', 'Invoice')


class ReconcileCrusherEntries(models.Model):
    _name = 'reconcile.crusher.entries'

    value = fields.Selection([('crusher','Crusher'),
                              ('contractor','Contractor'),
                              ('gst','GST'),
                              ('qty','Quantity'),
                              ('rate','Rate'),
                              ('amount','Amount'),
                              ('bill_no','Bill No'),
                              ('vehicle','Vehicle'),
                              ('item','Item'),
                              ('site','Site'),
                              ('roundoff','Round Off')],required=True,default='qty')
    new_value = fields.Float('New value')
    bill_no = fields.Char('Bill No')
    vehicle_id = fields.Many2one('fleet.vehicle',string='Vehicle')
    site_id = fields.Many2one('stock.location',string="Site",domain=[('usage','=','internal')])
    product_id = fields.Many2one('product.product',string="Item")
    crusher_id = fields.Many2one('res.partner','Crusher')
    tax_ids = fields.Many2many('account.tax','tax_id_crusher_rel','crusher_id','tax_id','Tax')
    contractor_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Contractor')

    @api.multi
    def reconcile_crusher_entries(self):
        crusher_lines = self.env.context.get('active_ids')
        move_line = self.env['account.move.line']
        list = []
        list1 = []
        for request in crusher_lines:
            r = self.env['account.move.line'].search([('id','=',request)])
            if r:
                if r.driver_stmt_line_id:
                    if r.driver_stmt_line_id.line_id.id not in list:
                        list.append(r.driver_stmt_line_id.line_id.id)

                    if self.value == 'crusher':
                        r.driver_stmt_line_id.write({'from_id2':self.crusher_id.id})
                    if self.value == 'gst':
                        taxes_ids = [i.id for i in self.tax_ids]
                        r.write({'tax_ids':[(6, 0, taxes_ids)]})
                        r.driver_stmt_line_id.write({'tax_ids':[(6, 0, taxes_ids)]})
                    if self.value == 'roundoff':
                        if not self.env.user.company_id.write_off_account_id:
                            raise osv.except_osv(_('Error!'),_("Please enter companys write off account"))
                        
                        r.driver_stmt_line_id.write({'round_off':self.new_value})

                    if self.value == 'amount':
                        r.driver_stmt_line_id.write({'total':self.new_value,'rate':self.new_value/r.driver_stmt_line_id.qty})
                    if self.value == 'contractor':
                        r.driver_stmt_line_id.write({'contractor_id':self.contractor_id.id})
                        r.write({'contractor_id':self.contractor_id.id})
                    if self.value == 'item':
                        r.driver_stmt_line_id.write({'item_expense2':self.product_id.id})
                    if self.value == 'site':
                        r.driver_stmt_line_id.write({'to_id2':self.site_id.id})
                    if self.value == 'bill_no':
                        r.driver_stmt_line_id.write({'voucher_no':self.bill_no})
                        r.write({'bill_no':self.bill_no})
                    if self.value == 'vehicle':
                        r.driver_stmt_line_id.line_id.write({'vehicle_no':self.vehicle_id.id})
                    if self.value == 'qty':
                        r.driver_stmt_line_id.write({'qty':self.new_value,
                                                    'total':self.new_value*r.driver_stmt_line_id.rate})
                    if self.value == 'rate':
                        r.driver_stmt_line_id.write({'rate':self.new_value,
                                                    'total':self.new_value*r.driver_stmt_line_id.qty})

                if r.rent_stmt_id:
                    if r.rent_stmt_id.rent_id.id not in list1:
                        list1.append(r.rent_stmt_id.rent_id.id)

                    if self.value == 'crusher':
                        r.rent_stmt_id.write({'crusher':self.crusher_id.id})
                    if self.value == 'gst':
                        taxes_ids = [i.id for i in self.tax_ids]
                        r.write({'tax_ids':[(6, 0, taxes_ids)]})
                        r.rent_stmt_id.write({'tax_ids':[(6, 0, taxes_ids)]})
                    if self.value == 'roundoff':
                        if not self.env.user.company_id.write_off_account_id:
                            raise osv.except_osv(_('Error!'),_("Please enter companys write off account"))
                        
                        r.rent_stmt_id.write({'round_off':self.new_value})

                    if self.value == 'amount':
                        r.rent_stmt_id.write({'material_cost':self.new_value,'rate':self.new_value/r.rent_stmt_id.qty})
                    if self.value == 'contractor':
                        r.rent_stmt_id.write({'contractor_id':self.contractor_id.id})
                        r.write({'contractor_id':self.contractor_id.id})
                    if self.value == 'item':
                        r.rent_stmt_id.write({'item':self.product_id.id})
                    if self.value == 'site':
                        r.rent_stmt_id.write({'site_id':self.site_id.id})
                    if self.value == 'bill_no':
                        r.rent_stmt_id.write({'bill_no':self.bill_no})
                        r.write({'bill_no':self.bill_no})
                    if self.value == 'vehicle':
                        r.rent_stmt_id.write({'vehicle_no':self.vehicle_id.id})
                    if self.value == 'qty':
                        r.rent_stmt_id.write({'qty':self.new_value,
                                                    'material_cost':self.new_value*r.rent_stmt_id.rate})
                    if self.value == 'rate':
                        r.rent_stmt_id.write({'rate':self.new_value,
                                                    'total':self.new_value*r.rent_stmt_id.qty})

        if self.value not in ['contractor','bill_no']:
            for ids in list:
                rec = self.env['driver.daily.statement'].search([('id','=',ids)])
                rec.cancel_entry()
                rec.set_draft()
                rec.validate_entry()
                rec.approve_entry()
            for ids in list1:
                rec = self.env['partner.daily.statement'].search([('id','=',ids)])
                rec.cancel_entry()
                rec.set_draft()
                rec.action_confirm()
                rec.approve_entry()
        return True


class ReconcileFuelEntries(models.Model):
    _name = 'reconcile.fuel.entries'

    value = fields.Selection([('fuel_pump','Fuel Pump'),
                              ('qty','Quantity'),
                              ('rate','Rate'),
                              ('amount','Amount'),
                              ('bill_no','Bill No'),
                              ('vehicle','Vehicle'),
                              ('item','Item'),
                              ],required=True,default='qty')
    new_value = fields.Float('New value')
    pump_id = fields.Many2one('res.partner','Diesel Pump')
    bill_no = fields.Char('Bill No')
    vehicle_id = fields.Many2one('fleet.vehicle',string='Vehicle')
    product_id = fields.Many2one('product.product',string="Item")

    @api.multi
    def reconcile_fuel_entries(self):
        fuel_lines = self.env.context.get('active_ids')
        move_line = self.env['account.move.line']
        list = []
        list1 = []
        list2 = []
        for request in fuel_lines:
            r = self.env['account.move.line'].search([('id','=',request)])
            if r:
                if r.diesel_pump_line_id:
                    if r.diesel_pump_line_id.line_id.id not in list:
                        list.append(r.diesel_pump_line_id.line_id.id)

                    if self.value == 'fuel_pump':
                        r.diesel_pump_line_id.write({'diesel_pump':self.pump_id.id})
                    
                    if self.value == 'amount':
                        r.diesel_pump_line_id.write({'total_litre_amount':self.new_value,
                                                    'per_litre':self.new_value/r.diesel_pump_line_id.litre})
                    
                    if self.value == 'item':
                        r.diesel_pump_line_id.write({'fuel_item':self.product_id.id})
                    
                    if self.value == 'bill_no':
                        r.diesel_pump_line_id.write({'pump_bill_no':self.bill_no})
                    # if self.value == 'vehicle':
                    #     r.diesel_pump_line_id.line_id.write({'vehicle_no':self.vehicle_id.id})
                    if self.value == 'qty':
                        r.diesel_pump_line_id.write({'litre':self.new_value,
                                                    'total_litre_amount':self.new_value*r.diesel_pump_line_id.per_litre})
                    if self.value == 'rate':
                        r.diesel_pump_line_id.write({'per_litre':self.new_value,
                                                    'total_litre_amount':self.new_value*r.diesel_pump_line_id.litre})



                elif r.rent_stmt_id:
                    if r.rent_stmt_id.rent_id.id not in list1:
                        list1.append(r.rent_stmt_id.rent_id.id)

                    if self.value == 'fuel_pump':
                        r.diesel_pump_line_id.write({'diesel_pump':self.pump_id.id})
                    
                    if self.value == 'amount':
                        r.diesel_pump_line_id.write({'diesel':self.new_value,
                                                    'diesel_rate':self.new_value/r.diesel_pump_line_id.diesel_litre})
                    
                    if self.value == 'item':
                        r.diesel_pump_line_id.write({'fuel_item':self.product_id.id})
                    
                    if self.value == 'bill_no':
                        r.diesel_pump_line_id.write({'pump_bill_no':self.bill_no})
                    # if self.value == 'vehicle':
                    #     r.diesel_pump_line_id.line_id.write({'vehicle_no':self.vehicle_id.id})
                    if self.value == 'qty':
                        r.diesel_pump_line_id.write({'diesel_litre':self.new_value,
                                                    'diesel':self.new_value*r.diesel_pump_line_id.diesel_rate})
                    if self.value == 'rate':
                        r.diesel_pump_line_id.write({'diesel_rate':self.new_value,
                                                    'diesel':self.new_value*r.diesel_pump_line_id.diesel_litre})


                elif r.mach_fuel_collection_id:
                    if r.mach_fuel_collection_id.collection_id.id not in list2:
                        list2.append(r.mach_fuel_collection_id.collection_id.id)

                    if self.value == 'fuel_pump':
                        r.mach_fuel_collection_id.write({'pump_id':self.pump_id.id})
                    
                    if self.value == 'amount':
                        r.mach_fuel_collection_id.write({'total_amount':self.new_value,
                                                    'amount_per_unit':self.new_value/r.mach_fuel_collection_id.quantity})
                    
                    if self.value == 'item':
                        r.mach_fuel_collection_id.write({'product_id':self.product_id.id})
                    
                    if self.value == 'bill_no':
                        r.mach_fuel_collection_id.write({'pump_bill_no':self.bill_no})
                    # if self.value == 'vehicle':
                    #     r.mach_fuel_collection_id.line_id.write({'vehicle_no':self.vehicle_id.id})
                    if self.value == 'qty':
                        r.mach_fuel_collection_id.write({'quantity':self.new_value,
                                                    'total_amount':self.new_value*r.mach_fuel_collection_id.amount_per_unit})
                    if self.value == 'rate':
                        r.mach_fuel_collection_id.write({'amount_per_unit':self.new_value,
                                                    'total_amount':self.new_value*r.mach_fuel_collection_id.quantity})


                else:
                    raise osv.except_osv(_('Error!'),_("Reconciliation of payment entries is not possible."))

        if self.value not in ['contractor','bill_no']:
            for ids in list:
                rec = self.env['driver.daily.statement'].search([('id','=',ids)])
                rec.cancel_entry()
                rec.set_draft()
                rec.validate_entry()
                rec.approve_entry()
            # for ids in list1:
            #     rec = self.env['partner.daily.statement'].search([('id','=',ids)])
            #     rec.cancel_entry()
            #     rec.set_draft()
            #     rec.action_confirm()
            #     rec.approve_entry()

            rec = self.env['partner.daily.statement'].search(['|',('id','in',list1),('id','in',list2)])
            for ids in rec:
                ids.cancel_entry()
                ids.set_draft()
                ids.action_confirm()
                ids.approve_entry()

        return True

                

class account_move_line(models.Model):
    _inherit = 'account.move.line'

    @api.model
    def create(self,vals):
        res = super(account_move_line, self).create(vals)

        crusher = self.env['res.partner'].search([('crusher_bool','=', True),('property_account_payable','=',res.account_id.id)])
        if crusher:
            res.crusher_line = True

        fuel = self.env['res.partner'].search([('diesel_pump_bool','=', True),('property_account_payable','=',res.account_id.id)])
        if fuel:
            res.fuel_line = True
        return res
    
    @api.onchange('invoice_no_id2')
    def _onchange_invoice_no(self):
        invoice_ids = []
        invoice_obj = self.env['hiworth.invoice'].search([('state','in',['approve','partial'])])
        invoice_ids = [invoice.id for invoice in invoice_obj]
        if self.invoice_no_id2.id != False:
            self.invoice_no2_balance = self.invoice_no_id2.balance+self.debit
        return {'domain': {'invoice_no_id2': [('id','in',invoice_ids)]}}
        
    location_id = fields.Many2one('stock.location', 'Plot')
    invoice_no_id2 = fields.Many2one('hiworth.invoice', 'Invoice No')
    invoice_no_id3 = fields.Many2one('hiworth.invoice', 'Invoice No')
    invoice_no2_balance = fields.Float('Balance')
    cheque_no = fields.Char('Cheque No')
    reconcile_bool = fields.Boolean(default=False)
    crusher_line = fields.Boolean(default=False)
    fuel_line = fields.Boolean(default=False)
    # vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
    vehicle_owner = fields.Many2one('res.partner','Vehicle Owner')
    diesel_pump = fields.Many2one('res.partner','Diesel Pump')

    retention = fields.Float('Retention %')
    discount =  fields.Float('Discount %')
    
    
    @api.multi
    def open_invice(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['hiworth.invoice'].search([('id','=',self.invoice_no_id2.id)])

        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Invoice Form View',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'hiworth.invoice',
            'view_id':'hiworth_invoice_form',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':{'type2': 'out','default_inv_type': 'out'},
        }
        

    @api.multi
    def open_account(self):
        self.ensure_one()
        treeview_id = self.env.ref('hiworth_accounting.view_account_form_hiworth').id
         
        record =  self.env['account.account'].search([('id','=',self.account_id.id)])
 
        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        return {
            'name': 'Account',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.account',
            'views': [(treeview_id, 'form')],      
            'target': 'current',
            'res_id':res_id,
        }
        
        
     
        
# class AccountJournal(models.Model)
#     _inherit = 'account.journal'


#     @api.model
#     def contractor_payment_journal_creation(self):
#         company = self.env['res.company'].search([])
#         print 'company==============', company
#         for comp in company:
#             values1 = {'name': 'Contractor Payment',
#                         'company_id': company.id,
#                         'padding': 4,
#                         'number_next_actual':1,
#                         'prefix': 'AAAA/%(year)s/',
#                         'number_increment': 1,
#                         'implementation': 'no_gap'}
#             sequence = self.env['ir.sequence'].create(values1)

#             values = {'name': 'Contractor Payment',
#                       'code': 'CPJ',
#                       'type': 'general',
#                       'update_posted': True,
#                       'sequence_id': sequence.id,
#                       'company_id': company.id
#                       }
#         self.create(dict(name='demo.webkul.com'))


class AccountTax(models.Model):
    _inherit = 'account.tax'

    tax_type = fields.Selection([
            ('gst', 'GST'),
            ('igst', 'IGST'),
            ],default='gst', string="Type")



# class ResCompany(models.Model):
#     _inherit = 'res.company'

#     write_off_account_id = fields.Many2one('account.account', 'Default Write off Account')