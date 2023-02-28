from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
# from openerp.osv import fields, osv
import time
from openerp.osv.orm import browse_record_list, browse_record, browse_null
from datetime import datetime

from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
#from openerp.osv import fields
from openerp import tools
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

# from pygments.lexer import _default_analyse
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
# from openerp.osv import osv
from openerp import SUPERUSER_ID

from lxml import etree

class ProjectFormInherits(models.Model):
    _inherit = 'project.project'

    project_number = fields.Char()

class purchase_item_category(models.Model):
    _name = 'purchase.item.category'

    name = fields.Char('Name')
    account_id = fields.Many2one('account.account','Related Account')


class purchase_order(models.Model):
    _inherit = 'purchase.order'
    _order = 'name desc'

    READONLY_STATES = {
        'confirmed': [('readonly', True)],
        'approved': [('readonly', True)],
        'done': [('readonly', True)]
    }


    def do_merge(self, cr, uid, ids, context=None):
        """
        To merge similar type of purchase orders.
        Orders will only be merged if:
        * Purchase Orders are in draft
        * Purchase Orders belong to the same partner
        * Purchase Orders are have same stock location, same pricelist, same currency
        Lines will only be merged if:
        * Order lines are exactly the same except for the quantity and unit

         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: the ID or list of IDs
         @param context: A standard dictionary

         @return: new purchase order id

        """

        # TOFIX: merged order line should be unlink
        def make_key(br, fields):
            list_key = []
            for field in fields:
                field_val = getattr(br, field)
                if field in ('product_id', 'account_analytic_id'):
                    if not field_val:
                        field_val = False
                if isinstance(field_val, browse_record):
                    field_val = field_val.id
                elif isinstance(field_val, browse_null):
                    field_val = False
                elif isinstance(field_val, browse_record_list):
                    field_val = ((6, 0, tuple([v.id for v in field_val])),)
                list_key.append((field, field_val))
            list_key.sort()
            return tuple(list_key)

        context = dict(context or {})

        # Compute what the new orders should contain
        new_orders = {}

        order_lines_to_move = {}
        purchase_request_list = []
        for porder in [order for order in self.browse(cr, uid, ids, context=context) if order.state == 'approved']:
            order_key = make_key(porder, ('partner_id', 'location_id', 'pricelist_id', 'currency_id'))
            new_order = new_orders.setdefault(order_key, ({}, []))

            new_order[1].append(porder.id)
            order_infos = new_order[0]
            purchase_request_list.append(porder.site_purchase_id.id)
            order_lines_to_move.setdefault(order_key, [])
            minimum_plann_date = datetime.strptime(porder.date_order,"%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            if not order_infos:


                order_infos.update({
                    'origin': porder.origin,
                    'date_order': porder.date_order,
                    'minimum_plann_date':minimum_plann_date,
                    'partner_id': porder.partner_id.id,
                    'dest_address_id': porder.dest_address_id.id,
                    'picking_type_id': porder.picking_type_id.id,
                    'location_id': porder.location_id.id,
                    'pricelist_id': porder.pricelist_id.id,
                    'currency_id': porder.currency_id.id,
                    'state': 'approved',
                    'packing_charge':porder.packing_charge,
                    'packing_tax_id':porder.packing_tax_id.id,
                    'loading_tax':porder.loading_tax,
                    'loading_tax_id':porder.loading_tax_id.id,
                    'transport_cost':porder.transport_cost,
                    'transport_cost_tax_id':porder.transport_cost_tax_id,
                    'order_line': {},
                    'merged_po':True,
                    'project_id':porder.project_id.id,
                    'company_contractor_id':porder.project_id.company_contractor_id.id,
                    'notes': '%s' % (porder.notes or '',),
                    'minimum_plann_date':minimum_plann_date,
                    'maximum_planned_date':minimum_plann_date,
                    'vehicle_id':porder.vehicle_id.id,
                    'vehicle_agent_id':porder.vehicle_agent_id.id,
                    'fiscal_position': porder.fiscal_position and porder.fiscal_position.id or False,
                })
            else:
                if porder.partner_id.id != order_infos['partner_id']:
                    raise ValidationError(_(
                        "Supplier is not equal"))
                if porder.date_order < order_infos['date_order']:
                    order_infos['date_order'] = porder.date_order
                if porder.notes:
                    order_infos['notes'] = (order_infos['notes'] or '') + ('\n%s' % (porder.notes,))
                if porder.origin:
                    order_infos['origin'] = (order_infos['origin'] or '') + ' ' + porder.origin
                if porder.packing_charge:
                    order_infos['packing_charge'] = order_infos['packing_charge'] + porder.packing_charge
                if porder.loading_tax:
                    order_infos['loading_tax'] = order_infos['loading_tax'] + porder.loading_tax
                if porder.packing_charge:
                    order_infos['transport_cost'] = order_infos['transport_cost'] + porder.transport_cost



            order_lines_to_move[order_key] += [order_line.id for order_line in porder.order_line
                                               if order_line.state != 'cancel']

        allorders = []
        orders_info = {}
        for order_key, (order_data, old_ids) in new_orders.iteritems():
            # skip merges with only one order
            if len(old_ids) < 2:
                allorders += (old_ids or [])
                continue

            # cleanup order line data
            for key, value in order_data['order_line'].iteritems():
                del value['uom_factor']
                value.update(dict(key))


            order_list = []
            order_line = {}
            for line in order_lines_to_move[order_key]:
                order_line_obj = self.pool.get('purchase.order.line').browse(cr, uid, line, context=context)
                if not order_line_obj.product_id.id in order_line.keys():
                    order_line.update({order_line_obj.product_id.id:{'product_id':order_line_obj.product_id.id,
                                                                 'rate':order_line_obj.expected_rate,
                                                                     'name':order_line_obj.product_id.name,
                                                                     'unit':order_line_obj.product_id.uom_id.id,
                                                                     'qty':order_line_obj.required_qty,
                                                                 'taxes_id':[(6,0,order_line_obj.taxes_id.ids)]}})
                else:

                    if order_line_obj.expected_rate != order_line[order_line_obj.product_id.id]['rate'] or order_line_obj.taxes_id.ids != order_line[order_line_obj.product_id.id]['taxes_id'][0][2]:
                        raise ValidationError(_(
                            "Rate or taxes is not equal"))
                    else:
                        order_line[order_line_obj.product_id.id]['qty'] = order_line[order_line_obj.product_id.id]['qty'] +order_line_obj.required_qty

                # c[2244444444444444]
            line_list = []
            line_values={}
            print "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu",order_line
            for key,item in order_line.items():
                print "ooooooooooooooooooooooooooooooooo",order_line[key]['product_id']
                line_values ={'product_id':order_line[key]['product_id'],
                                    'expected_rate':order_line[key]['rate'],
                                    'required_qty':order_line[key]['qty'],
                                    'name':order_line[key]['name'],
                                    'product_uom':order_line[key]['unit'],
                                    'taxes_id':order_line[key]['taxes_id']}
                line_list.append((0,0,line_values))


            order_data['order_line'] = line_list
            order_data['state'] = 'approved'

            order_data['site_purchase_ids']=[(6,0,purchase_request_list)]

            # create the new order
            context.update({'mail_create_nolog': True})
            neworder_id = self.create(cr, uid, order_data)
            self.message_post(cr, uid, [neworder_id], body=_("RFQ created"), context=context)
            orders_info.update({neworder_id: old_ids})
            allorders.append(neworder_id)
            # neworder_id.write({'state':'approved'})
            # make triggers pointing to the old orders point to the new order
            for old_id in old_ids:

                self.signal_workflow(cr, uid, [old_id], 'purchase_cancel')
        if not orders_info:
            raise ValidationError(_(
                "Supplier or Location is not equal"))
        return orders_info

    # @api.multi
    # @api.depends('name')
    # def _count_invoices(self):
    #     for line in self:
    #         line.invoice_count = 0
    #         invoice_ids = self.env['hiworth.invoice'].search([('origin','=',line.name)])
    #         line.invoice_count = len(invoice_ids)


    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return journal.currency or journal.company_id.currency_id or self.env.user.company_id.currency_id

    @api.model
    def _default_journal(self):
        inv_type = ['purchase']
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', inv_type),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)


    @api.onchange('minimum_plann_date')
    def onchage_minimum_plann_date(self):
        if self.date_order:
            self.minimum_planned_date = datetime.strptime(self.date_order,"%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")

    @api.model
    def create(self,vals):
        if vals.get('supplier_ids'):
            vals['name'] =self.env['ir.sequence'].next_by_code('rfq.code')

        if vals.get('partner_id'):
            vals.update({'state':'confirmed'})
        if vals.get('merged_po',False):
            vals.update({'state': 'approved'})
        res = super(purchase_order, self).create(vals)
        return res

    @api.multi
    def purchase_confirm(self):

        self.minimum_planned_date = self.minimum_plann_date
        if self.amount_total > 1000:
            if not self.env.user.has_group('base.group_erp_manager') and not self.comparison_id:
                raise Warning(_('You have not access to approve this Purchase Order.'))
            else:
                self.state = 'approved1'
        else:
            self.state = 'approved'
        return True

    @api.multi
    def purchase_approve(self):
        for rec in self:
            self.state = 'approved'
        return True

    @api.multi
    @api.depends('order_line','packing_tax_id','loading_tax_id','transport_cost_tax_id','packing_charge','loading_tax','transport_cost')
    def compute_new_gross_total(self):
        for rec in self:
            additonal_charge = 0
            other_charge = 0
            if rec.packing_tax_id:
                if rec.packing_tax_id.price_include:

                    additonal_charge += rec.packing_charge / (1+rec.packing_tax_id.amount)
                else:
                    additonal_charge += rec.packing_charge
            else:
                other_charge += rec.packing_charge

            if rec.loading_tax_id:
                if rec.loading_tax_id.price_include:
                    additonal_charge += rec.loading_tax / (1+rec.loading_tax_id.amount)
                else:
                    additonal_charge += rec.loading_tax
            else:
                other_charge += rec.loading_tax

            if rec.transport_cost_tax_id:
                if rec.transport_cost_tax_id.price_include:
                    additonal_charge += rec.transport_cost / (1+rec.transport_cost_tax_id.amount)
                else:
                    additonal_charge += rec.transport_cost
            else:
                other_charge += rec.transport_cost

            amount_untaxed = 0

            non_taxabale = 0
            # for line in rec.order_line:
            #
            #     if line.non_taxable_amount == 0:
            #         amount_untaxed += line.new_sub_total
            #
            #     else:
            #         non_taxabale +=line.non_taxable_amount
            rec.tax_amount = sum(rec.order_line.mapped('tax_amount'))
            rec.other_charge = other_charge
            if amount_untaxed >0:
                rec.new_gross_total = amount_untaxed
            else:
                rec.new_gross_total = sum(rec.order_line.mapped('new_sub_total'))
            rec.non_taxable_amount =non_taxabale
    # @api.multi
    # @api.depends('packing_tax_id','loading_tax_id','transport_cost_tax_id','order_line','packing_charge','loading_tax','transport_cost')
    # def compute_new_gst(self):
    #     for line in self:
    #         sgst_tax = 0
    #         cgst_tax= 0
    #         igst_tax=0
    #         if line.packing_tax_id:
    #             if line.packing_tax_id.price_include:
    #                 if line.packing_tax_id.tax_type == 'gst':
    #                     cgst_tax += ((line.packing_charge / (
    #                                 1 + line.packing_tax_id.amount)) * line.packing_tax_id.amount) / 2
    #                     sgst_tax += ((line.packing_charge / (1 + line.packing_tax_id.amount)) * line.packing_tax_id.amount)/2
    #                 else:
    #                     igst_tax += ((line.packing_charge / (
    #                             1 + line.packing_tax_id.amount)) * line.packing_tax_id.amount)
    #
    #             else:
    #                 if line.packing_tax_id.tax_type == 'gst':
    #                     cgst_tax += (line.packing_charge * line.packing_tax_id.amount) / 2
    #                     sgst_tax += (line.packing_charge * line.packing_tax_id.amount) / 2
    #                 else:
    #                     igst_tax += (line.packing_charge * line.packing_tax_id.amount)
    #
    #         if line.loading_tax_id:
    #             if line.loading_tax_id.price_include:
    #                 if line.loading_tax_id.tax_type == 'gst':
    #                     cgst_tax += ((line.loading_tax / (
    #                                 1 + line.loading_tax_id.amount)) * line.loading_tax_id.amount) / 2
    #                     sgst_tax += ((line.loading_tax / (1 + line.loading_tax_id.amount)) * line.loading_tax_id.amount)/2
    #                 else:
    #                     igst_tax += ((line.loading_tax / (
    #                             1 + line.loading_tax_id.amount)) * line.loading_tax_id.amount)
    #
    #
    #             else:
    #                 if line.loading_tax_id.tax_type == 'gst':
    #                     cgst_tax += (line.loading_tax  * line.loading_tax_id.amount) / 2
    #                     sgst_tax += (line.loading_tax  * line.loading_tax_id.amount) / 2
    #
    #                 else:
    #                     igst_tax += (line.loading_tax  * line.loading_tax_id.amount)
    #
    #         if line.transport_cost_tax_id:
    #             if line.transport_cost_tax_id.price_include:
    #                 if line.transport_cost_tax_id.tax_type == 'gst':
    #                     cgst_tax += ((line.transport_cost / (
    #                             1 + line.transport_cost_tax_id.amount)) * line.transport_cost_tax_id.amount) / 2
    #                     sgst_tax += ((line.transport_cost / (
    #                                 1 + line.transport_cost_tax_id.amount)) * line.transport_cost_tax_id.amount) / 2
    #                 else:
    #                     igst_tax += ((line.transport_cost / (
    #                             1 + line.transport_cost_tax_id.amount)) * line.transport_cost_tax_id.amount)
    #
    #
    #             else:
    #                 if line.transport_cost_tax_id.tax_type == 'gst':
    #                     cgst_tax += (line.transport_cost * line.transport_cost_tax_id.amount) / 2
    #                     sgst_tax += (line.transport_cost * line.transport_cost_tax_id.amount) / 2
    #                 else:
    #                     igst_tax += (line.transport_cost * line.transport_cost_tax_id.amount)
    #
    #
    #         for order in line.order_line:
    #
    #             if order.non_taxable_amount == 0:
    #                 sgst_tax += order.gst_tax /2
    #                 cgst_tax += order.gst_tax / 2
    #                 igst_tax += order.igst_tax
    #
    #
    #
    #
    #         line.new_sgst_tax =  sgst_tax
    #         line.new_cgst_tax =cgst_tax
    #         line.new_igst_tax =igst_tax
    # @api.multi
    # @api.depends('order_line','round_off_amount','discount_amount','packing_charge','loading_tax','transport_cost')
    # def compute_gst(self):
    #     for rec in self:
    #         rec.sgst_tax = 0.0
    #         rec.cgst_tax = 0.0
    #         rec.igst_tax = 0.0
    #         if rec.order_line:
    #             for line in rec.order_line:
    #                 rec.sgst_tax += line.gst_tax/2
    #                 rec.cgst_tax += line.gst_tax/2
    #                 rec.igst_tax += line.igst_tax
    #
    #         rec.amount_total = round(rec.new_sgst_tax + rec.new_cgst_tax +rec.new_igst_tax+rec.new_gross_total +rec.non_taxable_amount + rec.other_charge+  rec.round_off_amount - rec.discount_amount, 2)
    #         if rec.amount_total2 == 0.0:
    #             rec.amount_total2 =rec.amount_total

    # @api.model
    # def _default_write_off_account(self):
    #     return self.env['res.company'].browse(self.env['res.company']._company_default_get('hiworth.invoice')).write_off_account_id
    #
    # @api.model
    # def _default_discount_account(self):
    #     return self.env['res.company'].browse(self.env['res.company']._company_default_get('hiworth.invoice')).discount_account_id

    @api.onchange('account_id')
    def onchange_account(self):
        account_ids = []
        account_ids = [account.id for account in self.env['account.account'].search([('company_id','=',self.company_id.id)])]
        return {
                'domain': {
                    'account_id': [('id','in',account_ids)]
                }
            }

    @api.constrains('bid_validity')
    def constrain_bid_validity(self):
        for rec in self:
            if rec.bid_validity:
                date = datetime.strptime(rec.date_order, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                if date > rec.bid_validity:
                    raise ValidationError(
                        _("Qutotation Valid Date must be equal or greater than Order Date"))



    @api.constrains('maximum_planned_date')
    def constrain_maximum_planned_date(self):
        for rec in self:
            if rec.maximum_planned_date:
                date = datetime.strptime(rec.date_order, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                if date > rec.maximum_planned_date:
                    raise ValidationError(
                        _("Maximum Expected Date must be equal or greater than Order Date"))


    STATE_SELECTION = [
        ('draft', 'Waiting'),
        ('sent', 'RFQ'),
        ('bid', 'Bid Received'),
        ('confirmed', 'First Approval'),
    ('approved1', 'Second  Approval'),
        ('approved', 'Order Placed'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Received'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
    ]

    READONLY_STATES = {

    }

    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
                                  help="The status of the purchase order or the quotation request. "
                                       "A request for quotation is a purchase order in a 'Draft' status. "
                                       "Then the order has to be confirmed by the user, the status switch "
                                       "to 'Confirmed'. Then the supplier must confirm the order to change "
                                       "the status to 'Approved'. When the purchase order is paid and "
                                       "received, the status becomes 'Done'. If a cancel action occurs in "
                                       "the invoice or in the receipt of goods, the status becomes "
                                       "in exception.",
                                  select=True, copy=False)
    journal_id2 = fields.Many2one('account.journal', string='Journal',
        default=_default_journal, states=READONLY_STATES,
        domain="[('type', '=', 'purchase')]")
    partner_id = fields.Many2one('res.partner', 'Supplier', required=False,
            change_default=True, track_visibility='always',states=READONLY_STATES,)
    invoice_created = fields.Boolean('Invoice Created', default=False)
    # invoice_count = fields.Integer(compute='_count_invoices', string='Invoice Nos')
    invoice_count = fields.Integer(string='Invoice Nos')
    order_line = fields.One2many('purchase.order.line', 'order_id', 'Order Lines',
                                      states=READONLY_STATES,
                                      copy=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
    is_requisition = fields.Boolean('Is Requisition', default = True)
    requisition_id = fields.Many2one('purchase.order', 'Purchase Requisition')
    account_id = fields.Many2one('account.account', 'Account', states=READONLY_STATES)
    # sgst_tax = fields.Float(compute="compute_gst", store=True, string="SGST Amount")
    sgst_tax = fields.Float(store=True, string="SGST Amount")
    # cgst_tax = fields.Float(compute="compute_gst", store=True, string="CGST Amount")
    cgst_tax = fields.Float(store=True, string="CGST Amount")
    # igst_tax = fields.Float(compute="compute_gst", store=True, string="IGST Amount")
    igst_tax = fields.Float(store=True, string="IGST Amount")
    # new_sgst_tax = fields.Float(compute='compute_new_gst',store=True,string="SGST Amount")
    new_sgst_tax = fields.Float(store=True,string="SGST Amount")
    # new_cgst_tax = fields.Float(compute='compute_new_gst', store=True, string="CGST Amount")
    new_cgst_tax = fields.Float(store=True, string="CGST Amount")
    # new_igst_tax = fields.Float(compute='compute_new_gst', store=True, string="IGST Amount")
    new_igst_tax = fields.Float(store=True, string="IGST Amount")
    other_tax_charge = fields.Float("Other Tax")
    additional_charge = fields.Float("Additonal charge")
    other_igst_tax = fields.Float("Other Tax IGST")
    # non_taxable_amount = fields.Float(compute='compute_new_gross_total',store=True,string="Non-Taxable Amount")
    non_taxable_amount = fields.Float(store=True,string="Non-Taxable Amount")
    # new_gross_total = fields.Float(compute='compute_new_gross_total',store=True,string="Gross Total")
    new_gross_total = fields.Float(store=True,string="Gross Total")
    # tax_amount = fields.Float(compute='compute_new_gross_total',store=True,string="Tax")
    tax_amount = fields.Float(store=True,string="Tax")
    # amount_total2 = fields.Float(compute="compute_gst", string='Total', store=True, help="The total amount")
    amount_total2 = fields.Float(string='Total', store=True, help="The total amount")
    # amount_total = fields.Float(compute="compute_gst", string='Total', store=True, help="The total amount")
    amount_total = fields.Float(string='Total', store=True, help="The total amount")
    invoice_date = fields.Date('Invoice Date')
    round_off_amount = fields.Float('Round off Amount (+/-)', )
    round_off_account = fields.Many2one('account.account', 'Round off Account', states=READONLY_STATES,
     )

    discount_amount = fields.Float('Discount Amount',)
    discount_account = fields.Many2one('account.account', 'Discount Account', states=READONLY_STATES,
     )
    order_line = fields.One2many('purchase.order.line', 'order_id', 'Order Lines',
                        readonly=False, copy=True)
    maximum_planned_date = fields.Date('Maximum Expected Date')
    project_id = fields.Many2one('project.project',"Project")
    location_id = fields.Many2one('stock.location', domain=[('usage','=','internal')])
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=False, states=READONLY_STATES, help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities.")
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")
    site_purchase_id = fields.Many2one('site.purchase',"Site Purchase")
    other_charge = fields.Float(String="Other Charge")
    deliver_to = fields.Text("Deliver To")
    company_contractor_id = fields.Many2one('res.partner',domain="[('company_contractor','=',True)]",string="Company")
    supplier_ids = fields.Many2many('res.partner','purchase_order_res_partner_rel','order_id','partner_id',domain="[('supplier','=',True)]",string="Suppliers")
    minimum_plann_date = fields.Date(string='Minimum Expected Date')
    comparison_id = fields.Many2one('purchase.comparison',"Comparison No")
    quotation_id = fields.Many2one('purchase.order',"RFQ No")
    packing_charge = fields.Float("Packing Charge")
    packing_tax_id = fields.Many2one('account.tax',"Tax")
    loading_tax = fields.Float("Loading Charge")
    loading_tax_id = fields.Many2one('account.tax',"Tax")
    transport_cost = fields.Float("Transport Cost")
    transport_cost_tax_id = fields.Many2one('account.tax',"Tax")
    vehicle_agent_id = fields.Many2one('res.partner', 'Vehicle Agent')
    merged_po = fields.Boolean("Merged PO",default=False)
    site_purchase_ids = fields.Many2many('site.purchase','purase_order_site_purchase_rel','order_id','site_purchase_id',"Purchase Request No/s")
    additional_terms = fields.Text()


    @api.multi
    def write(self,vals):
        if not self.quotation_id and not self.comparison_id:
            if vals.get('order_line',False):
                for li in vals.get('order_line',False):
                    if li[0]==1:
                        line_id = self.env['purchase.order.line'].browse(li[1])
                        if li[2].get('required_qty') >= 0:
                            for req_list in self.site_purchase_id.site_purchase_item_line_ids:
                                if req_list.item_id.id == line_id.product_id.id:
                                    req_list.quantity = li[2].get('required_qty')
                    if li[0]==0:
                        values = {'item_id':li[2].get('product_id'),
                                  'brand_name':li[2].get('brand_name'),
                                  'desc':li[2].get('name'),
                                  'unit':li[2].get('product_uom'),
                                  'quantity':li[2].get('required_qty'),
                                  'site_purchase_id':self.site_purchase_id.id}
                        req_line = self.env['site.purchase.item.line'].create(values)
                    if li[0] == 2:
                        line_id = self.env['purchase.order.line'].browse(li[1])
                        for req_list in self.site_purchase_id.site_purchase_item_line_ids:
                            if req_list.item_id.id == line_id.product_id.id:
                                req_list.unlink()
        else:
            if vals.get('order_line',False) :
                for li in vals.get('order_line',False):
                    if li[0]==0 and self.state =='approved':

                        raise ValidationError(
                            _("Only Purchase Order created through Direct PO can add item"))


        res = super(purchase_order, self).write(vals)

        return res

    @api.multi
    def force_po_close(self):
        return {
            'name': 'Foreclosure',
            'view_type': 'form',
            'view_mode': 'form',

            'res_model': 'force.po.close',

            'type': 'ir.actions.act_window',
            'target':'new',


        }

    @api.multi
    def button_view_invoice(self):
        value_list = []
        prev_list = []
        for line in self.order_line:

            value_list.append((0, 0, {'item_id': line.product_id.id,
                                  'desc': line.name,
                                      'brand_name':line.brand_name.id,
                                  'tax_ids': [(6, 0, line.taxes_id.ids)],
                                  'po_quantity': line.required_qty - line.received_qty,
                                  'rate': line.expected_rate,
                                  'unit_id': line.product_uom.id

                                  }))
            prev_list.append((0, 0, {'item_id': line.product_id.id,
                                     'desc': line.name,
                                     'brand_name': line.brand_name.id,
                                     'tax_ids': [(6, 0, line.taxes_id.ids)],
                                     'po_quantity': line.required_qty,
                                     'quantity_accept': line.received_qty,
                                     'quantity_reject': line.closed_qty,
                                     'rate': line.expected_rate,
                                     'unit_id': line.product_uom.id

                                     }))
        merged_po = False
        for site_pur in self.site_purchase_ids:
            merged_po = True
        context = {'default_mpr_id':self.site_purchase_id.id,
                  'default_supplier_id' : self.partner_id.id,
                'default_purchase_id':self.id,
                   'default_company_contractor_id':self.company_contractor_id.id,
                   'default_site':self.site_purchase_id.site.id,
                  'default_project_id' : self.project_id.id,
                  'default_goods_recieve_report_line_ids':value_list,
                  'default_previous_goods_receipt_entries_ids':prev_list,
                   'default_vehicle_id':self.site_purchase_id.vehicle_id.id,
                   'default_vehicle_agent_id':self.vehicle_agent_id.id,
                   'default_site':self.location_id.id,
                   'default_merged_po':merged_po,
                   'default_site_purchase_ids':[(6,0,self.site_purchase_ids.ids)]
                  }
        print "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",self.company_contractor_id,self.project_id
        # daily_stmt_supervisor = self.env['partner.daily.statement'].search([('project_id','=',self.project_id.id)])
        res = {
            'type': 'ir.actions.act_window',
            'name': 'Goods Receipt & Invoice Entry',
            'res_model': 'goods.recieve.report',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'context':context
            # 'res_id': goods_receipt.id,

        }

        return res



    @api.multi
    def button_create_comparison(self):
        self.state = 'bid'
        value_list = []
        for line in self.order_line:
            value_list.append((0,0,{'product_id':line.product_id.id,
                                    'brand_name':line.brand_name.id,
                                    'qty':line.product_qty,
                                    'uom':line.product_uom.id}))
        values = {'mpr_id':self.site_purchase_id.id,
                  'quotation_id':self.id,
                  'vehicle_id':self.vehicle_id.id,
                  'project_id':self.site_purchase_id.project_id.id,
                  'location_id':self.location_id.id,
                  'comparison_line':value_list,
                  'remark':self.notes,
                  }

        comparison = self.env['purchase.comparison'].create(values)

        self.comparison_id = comparison.id

        res = {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Comparison',
            'res_model': 'purchase.comparison',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id':self.comparison_id.id,
            'context': {'default_supplier_ids': self.supplier_ids.ids}
        }

        return res

    @api.multi
    def view_comparison(self):
        res = {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Comparison',
            'res_model': 'purchase.comparison',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id':self.comparison_id.id,
            # 'domain': [('id', '=', self.comparison_id.id)],
            'context': {'default_supplier_ids': self.supplier_ids.ids,
                        'current_id': self.comparison_id.id}
        }

        return res


    @api.onchange('site_purchase_id')
    def onchange_mpr_id(self):
        for rec in self:
            if rec.site_purchase_id:
                values = []
                rec.project_id = rec.site_purchase_id.project_id.id
                for mpr_line in rec.site_purchase_id.site_purchase_item_line_ids:
                    values.append((0, 0, {'product_id': mpr_line.item_id.id,
                                          'name':mpr_line.item_id.name,
                                          'product_qty': mpr_line.quantity,
                                          'product_uom': mpr_line.unit.id,
                                          'brand_name': mpr_line.brand_name.id,
                                          'state':'draft'}))
                rec.order_line = values



    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            user_obj = self.pool.get('res.users')

            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:

                    parent.insert(index, child)
                    index += 1
                    for she_root in child.xpath("//notebook"):

                        for line in she_root.xpath("//field[@name='order_line']"):


                            if self.pool['res.users'].has_group(cr, uid, 'base.group_erp_manager'):

                                line.set('modifiers','{}')



                parent.remove(sheet)
            order_line_tree = etree.XML(res['fields']['order_line']['views']['tree']['arch'])
            if self.pool['res.users'].has_group(cr, uid, 'base.group_erp_manager'):

                order_line_tree.set('create', 'true')
                order_line_tree.set('delete', 'true')
            res['fields']['order_line']['views']['tree']['arch'] = etree.tostring(order_line_tree)


            res['arch'] = etree.tostring(doc)
        return res


    def wkf_send_rfq(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        if not context:
            context= {}
        ir_model_data = self.pool.get('ir.model.data')
        try:
            if context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference(cr, uid, 'hiworth_construction', 'email_template_edi_purchase15')[1]
            else:
                template_id = ir_model_data.get_object_reference(cr, uid, 'hiworth_construction', 'email_template_edi_purchase_done2')[1]
        except ValueError:
            template_id = False
        try:
#
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }



    def picking_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'shipped':1,'state':'done'}, context=context)
        # Do check on related procurements:
        proc_obj = self.pool.get("procurement.order")
        po_lines = []
        for po in self.browse(cr, uid, ids, context=context):
            po_lines += [x.id for x in po.order_line if x.state != 'cancel']
        if po_lines:
            procs = proc_obj.search(cr, uid, [('purchase_line_id', 'in', po_lines)], context=context)
            if procs:
                proc_obj.check(cr, uid, procs, context=context)
        self.message_post(cr, uid, ids, body=_("Products received"), context=context)
        return True

#     @api.multi
#     def create_invoice(self):
#         '''
#         This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
#         '''
#         if not self.partner_ref:
#             raise osv.except_osv(_('Warning!'),
#                         _('You must enter a Invoice Number'))
#
#         invoice_line = self.env['hiworth.invoice.line2']
#         invoice = self.env['hiworth.invoice']
#         now = datetime.datetime.now()
#         for line in self:
#             values1 = {
#                         'is_purchase_bill': True,
#                         'partner_id': line.partner_id.id,
#                         'purchase_order_date':line.date_order,
#                         'origin': line.name,
#                         'name': self.partner_ref,
#                         'journal_id': line.journal_id2.id,
#                         'account_id': line.account_id.id,
#                         'date_invoice': line.invoice_date,
#                         'round_off_amount': line.round_off_amount,
#                         'round_off_account': line.round_off_account.id,
#                         'discount_amount': line.discount_amount,
#                         'discount_account': line.discount_account.id,
#                         'purchase_order_id': line.id,
# #                         'grand_total': line.amount_total
#                         }
#             invoice_id = invoice.create(values1)
#             for lines in line.order_line:
#                 taxes_ids = []
#                 taxes_ids = [tax.id for tax in lines.taxes_id]
#                 values2={
#                         'product_id': lines.product_id.id,
#                         'name': lines.product_id.name,
#                         'price_unit': lines.price_unit,
#                         'uos_id': lines.product_uom.id,
#                         'quantity': lines.product_qty,
#                         'price_subtotal':lines.price_subtotal,
#                         'task_id': lines.task_id.id,
#                         'location_id': lines.location_id.id,
#                         'invoice_id': invoice_id.id,
#                         'account_id': lines.account_id.id,
#                         'tax_ids':  [(6, 0, taxes_ids)]
#                         }
#                 invoice_line_id = invoice_line.create(values2)
#             invoice_id.action_for_approval()
#             # invoice_id.action_approve()
#             line.invoice_created = True

    # @api.multi
    # def action_sanction(self):
    # 	for line in self:
    # 		line.state = 'sanction'



    # @api.multi
    # def invoice_open(self):
    #     self.ensure_one()
    #     # Search for record belonging to the current staff
    #     record =  self.env['hiworth.invoice'].search([('origin','=',self.name)])
    #
    #     context = self._context.copy()
    #     context['type2'] = 'out'
    #     #context['default_name'] = self.id
    #     if record:
    #         res_id = record[0].id
    #     else:
    #         res_id = False
    #     # Return action to open the form view
    #     return {
    #         'name':'Invoice view',
    #         'view_type': 'form',
    #         'view_mode':'form',
    #         'views' : [(False,'form')],
    #         'res_model':'hiworth.invoice',
    #         'view_id':'hiworth_invoice_form',
    #         'type':'ir.actions.act_window',
    #         'res_id':res_id,
    #         'context':context,
    #     }


    def view_invoice(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        context = dict(context or {})
        mod_obj = self.pool.get('ir.model.data')
        wizard_obj = self.pool.get('purchase.order.line_invoice')
        #compute the number of invoices to display
        inv_ids = []
        for po in self.browse(cr, uid, ids, context=context):
            if po.invoice_method == 'manual':
                if not po.invoice_ids:
                    context.update({'active_ids' :  [line.id for line in po.order_line if line.state != 'cancel']})
                    wizard_obj.makeInvoices(cr, uid, [], context=context)

        for po in self.browse(cr, uid, ids, context=context):
            inv_ids+= [invoice.id for invoice in po.invoice_ids]
            invoice = self.pool.get('account.invoice').search(cr, uid, [('purchase_id','=',po.id)])
            if self.pool.get('account.invoice').browse(cr, uid, invoice).not_visible == True:
                for line in self.pool.get('account.invoice').browse(cr, uid, invoice).invoice_line:
                    line.quantity = line.purchase_line_id.product_qty
                    line.price_unit = line.purchase_line_id.price_unit

                self.pool.get('account.invoice').browse(cr, uid, invoice).not_visible = False
                self.pool.get('account.invoice').browse(cr, uid, invoice).number = po.partner_ref
                self.pool.get('account.invoice').browse(cr, uid, invoice).date_invoice = po.invoice_date
            self.pool.get('account.invoice').browse(cr, uid, invoice).other_charge = po.other_charge
            self.pool.get('account.invoice').browse(cr, uid, invoice).amount_total = po.amount_total
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
        res_id = res and res[1] or False

        return {
            'name': _('Supplier Invoices'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'in_invoice', 'journal_type': 'purchase'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': inv_ids and inv_ids[0] or False,
        }
