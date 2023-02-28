from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
from openerp.osv import osv
from datetime import datetime
from lxml import etree


class InventoryDepartment(models.Model):
    _name = 'inventory.department'

    name = fields.Many2one('product.product','Product')
    date = fields.Date('Date')
    location_id = fields.Many2one('stock.location','Location')
    qty = fields.Float('Quantity')
    rate = fields.Float('Rate')
    inventory_value = fields.Float('Inventory Value')
    department = fields.Selection([('general','General'),
                                   ('vehicle','Vehicle'),
                                   ('telecom','Telecom'),
                                   ('interlocks','Interlocks'),
                                   ('workshop','Workshop')],string="Department")
    site_purchase_id = fields.Many2one('site.purchase')





class SitePurchasegroup(models.Model):
    _name = 'site.purchase.group'

    @api.multi
    def merge_orders(self):
        site_requests = self.env.context.get('active_ids')
        record = []
        supplier = False
        for request in site_requests:
            site_record = self.env['site.purchase'].search([('id','=',request)])
            if site_record:
                if site_record.state != 'approved2':
                    raise except_orm(_('Warning'),_('Site Requests Must Be In Draft State.Please Check..!!'))           
                if not site_record.expected_supplier:
                    raise except_orm(_('Warning'),_('One of the site requests not have supplier.Please configure..!!'))         
                if supplier == False:
                    supplier = site_record.expected_supplier.id
                elif supplier != site_record.expected_supplier.id:
                    raise except_orm(_('Warning'),_('Supplers are different..!!'))          
                
                line_record = {
                    'product_id':site_record.item_id.id,
                    'product_qty':site_record.quantity,
                    'name':site_record.item_id.name,
                    'site_purchase_id':site_record.id,
                    'product_uom':site_record.unit.id,
                    'pro_old_price':site_record.item_id.standard_price,
                    'unit_price':site_record.item_id.standard_price,
                    'price_unit':site_record.item_id.standard_price,
                    'location_id':False,
                    'account_id':site_record.item_id.categ_id.stock_account_id.id,
                    'state':'draft'
                    }
                record.append((0, False, line_record ))


        view_ref = self.env['ir.model.data'].get_object_reference('purchase', 'purchase_order_form')
        view_id = view_ref[1] if view_ref else False
        res = {
           'type': 'ir.actions.act_window',
           'name': _('Purchase Order'),
           'res_model': 'purchase.order',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': view_id,
           'target': 'current',
           'context': {'default_partner_id':supplier,'default_order_line':record,'default_date_order':fields.Date.today(),'default_state':'draft'}
       }

        return res
class SitePurchaseItemLine(models.Model):
    _name = 'site.purchase.item.line'
    
    @api.onchange('quantity')
    def onchange_quantity_rate(self):
        if self.quantity == 0:
            self.estimated_amt = 0
        else:
            if self.estimated_amt != 0 and self.rate != 0 and self.quantity != round((self.estimated_amt / self.rate),
                                                                                     2):
                self.quantity = 0.0
                return {
                    'warning': {
                        'title': 'Warning',
                        'message': "For Entering value to quantity field, Rate or estimated_amt should be Zero"
                    }
                }
            if self.quantity != 0 and self.rate != 0:
                if self.rate * self.quantity != self.estimated_amt:
                    pass
                if self.estimated_amt == 0.0:
                    self.estimated_amt = round((self.quantity * self.rate), 2)
            if self.estimated_amt != 0 and self.quantity != 0:
                if self.rate == 0.0:
                    self.rate = round((self.estimated_amt / self.quantity), 2)
    
    @api.onchange('rate')
    def onchange_rate_estimated_amt(self):
        if self.rate == 0:
            self.estimated_amt = 0
        else:
            if self.estimated_amt != 0 and self.quantity != 0 and self.rate != round(
                    (self.estimated_amt / self.quantity), 2):
                self.rate = 0.0
                return {
                    'warning': {
                        'title': 'Warning',
                        'message': "For Entering value to Rate field, quantity or estimated_amt should be Zero."
                    }
                }
            if self.quantity != 0 and self.rate != 0:
                if self.rate * self.quantity != self.estimated_amt:
                    pass
                if self.estimated_amt == 0.0:
                    self.estimated_amt = round((self.quantity * self.rate), 2)
            if self.estimated_amt != 0 and self.rate != 0:
                if self.quantity == 0.0:
                    self.quantity = round((self.estimated_amt / self.rate), 2)
    
    @api.onchange('estimated_amt')
    def onchange_qty_estimated_amt(self):
        if self.estimated_amt != 0:
            if self.rate * self.quantity != self.estimated_amt:
                if self.rate != 0 and self.quantity != 0:
                    self.estimated_amt = 0.0
                    return {
                        'warning': {
                            'title': 'Warning',
                            'message': "For Entering value to estimated_amt field, quantity or Rate should be Zero."
                        }
                    }
                elif self.rate == 0 and self.quantity != 0:
                    self.rate = round((self.estimated_amt / self.quantity), 2)
                elif self.quantity == 0 and self.rate != 0:
                    self.quantity = round((self.estimated_amt / self.rate), 2)
                else:
                    pass
    
    @api.onchange('item_id')
    def onchange_product_id(self):
        for rec in self:
            item = self.env['site.purchase.item.line'].search([('item_id','=',rec.item_id.id)],limit=1,order='id desc')
            if rec.item_id:
                rec.unit = self.item_id.uom_id.id
                rec.desc = self.item_id.name
                if item:
                    rec.rate = item.rate

            
                
                

    @api.multi
    @api.depends('tax_ids', 'received_total')
    def get_tax_amount(self):
        for lines in self:
            taxi = 0
            taxe = 0
            for tax in lines.tax_ids:
                if tax.price_include == True:
                    taxi = tax.amount
                if tax.price_include == False:
                    taxe += tax.amount
            lines.tax_amount = (lines.received_total) / (1 + taxi) * (taxi + taxe)
            lines.sub_total = (lines.received_total) / (1 + taxi)
            lines.total_amount = lines.tax_amount + lines.sub_total

    @api.multi
    @api.depends('received_qty', 'invoiced_amount')
    def get_received_total(self):
        for rec in self:
            if rec.received_qty != 0:
                rec.received_rate = rec.invoiced_amount / rec.received_qty
            
    brand_name = fields.Many2one('material.brand')
    model_name = fields.Many2one('material.model')
    item_id = fields.Many2one('product.product', 'Item')
    quantity = fields.Float('Quantity')
    unit = fields.Many2one('product.uom', 'Unit')
    desc = fields.Char('Description')
    rate = fields.Float('Rate')
    estimated_amt = fields.Float('Estimated Amount')
    received_qty = fields.Float('Received Qty')
    tax_ids = fields.Many2many('account.tax', string="Tax")
    tax_amount = fields.Float('Tax Amount', compute="get_tax_amount")
    sub_total = fields.Float('Sub Total', compute="get_tax_amount")
    total_amount = fields.Float('Total', compute="get_tax_amount")
    received_rate = fields.Float('Received Rate',compute='get_received_total',)
    invoiced_amount = fields.Float(string='Invoiced Amount')
    received_total = fields.Float(string="Total Received Qty")
    received_bool = fields.Boolean(string="Received Bool")
    state = fields.Selection(related='site_purchase_id.state', string="Status")
    site_purchase_id = fields.Many2one('site.purchase',string="Site Purchase")
    project_approved_qty = fields.Float("Approved Quantity")
    processed_qty = fields.Float("Processed Quantity")


class MaterialBrand(models.Model):
    _name = 'material.brand'

    name = fields.Char()


class MaterialModel(models.Model):
    _name = 'material.model'

    name = fields.Char()



class SitePurchase(models.Model):
    _name = 'site.purchase'
    _order = 'id desc'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(SitePurchase, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            # Check if user is in group that allow creation
            doc = etree.XML(res['arch'])
            has_my_group = self.env.user.has_group('base.group_erp_manager')
            if has_my_group:

                for sheet in doc.xpath("//sheet/group/group[2]/field[@name='max_expected_date']"):

                    sheet.set('modifiers', '{}')
            res['arch'] = etree.tostring(doc)
        return res

    @api.onchange('site_purchase_item_line_ids')
    def onchange_site_purchase_item_line(self):
        for rec in self:
            item_list = []
            estimated_amount = 0
            estimated_qty = 0
            received_qty = 0
            for site_purchase_item in rec.site_purchase_item_line_ids:
                if site_purchase_item.item_id:
                    item_list.append(site_purchase_item.item_id.id)
                if site_purchase_item.estimated_amt:
                    estimated_amount += site_purchase_item.estimated_amt
                if site_purchase_item.quantity:
                    estimated_qty += site_purchase_item.quantity
                if site_purchase_item.received_qty:
                    received_qty += site_purchase_item.received_qty
            rec.item_ids = [(6,0,item_list)]
            rec.estimated_amt  = estimated_amount
            rec.quantity = estimated_qty
            if rec.received_qty:
                rec.received_qty += received_qty
            
            
    @api.onchange('site_purchase_item_ids')
    def onchange_site_purchsae(self):
        for rec in self:
            total = 0
            for purchase in rec.site_purchase_item_line_ids:
                total += purchase.received_qty
                
            if rec.received_qty:
                rec.received_qty += total

    
    

    @api.model
    def default_get(self, default_fields):
        vals = super(SitePurchase, self).default_get(default_fields)
        user = self.env['res.users'].search([('id','=',self.env.user.id)])
        if user:
            vals.update({'responsible' : user.id})
            # if user.employee_id or user.id == 1:
            #     vals.update({'supervisor_id' : user.employee_id.id if user.id != 1 else self.env['hr.employee'].search([('id','=',1)]).id })
            #
        return vals


    @api.multi
    @api.depends('tax_ids','received_total')
    def get_tax_amount(self):
        for lines in self:
            taxi = 0
            taxe = 0
            for tax in lines.tax_ids:
                if tax.price_include == True:
                    taxi = tax.amount
                if tax.price_include == False:
                    taxe += tax.amount
            lines.tax_amount = (lines.received_total)/(1+taxi)*(taxi+taxe)
            lines.sub_total = (lines.received_total)/(1+taxi)
            lines.total_amount = lines.tax_amount + lines.sub_total

    @api.multi
    @api.depends('received_qty','received_rate')
    def get_received_total(self):
        for rec in self:
            rec.received_total = rec.received_qty*rec.received_rate

    @api.constrains('min_expected_date')
    def constrain_min_expected_date(self):
        for rec in self:
            date = datetime.strptime(rec.order_date,"%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            if rec.min_expected_date < date:
                raise ValidationError(_("Minimum Expected Date must be equal or greater than  Order Date"))

    @api.constrains('max_expected_date')
    def constrain_max_expected_date(self):
        for rec in self:
            if rec.max_expected_date < rec.min_expected_date:
                raise ValidationError(_("Maximum Expected Date must be equal or greater than Order Date and Minimum Expected Date"))
    # 
    # @api.onchange('project_id')
    # def onchange_project_id(self):
    #     for rec in self:
    #         return {'domain':{'site':[('id','in',rec.project_id.project_location_ids.ids)]}}


    name = fields.Char('Name', readonly=True)
    supervisor_id = fields.Many2one('hr.employee', 'User', readonly=True)
    project_id = fields.Many2one('project.project',"Project")
    responsible = fields.Many2one('res.users', 'Responsible', readonly=True)
    order_date = fields.Datetime('Order Date', default=lambda self: fields.datetime.now())
    min_expected_date = fields.Date('Minimum Expected Date', required=True)
    max_expected_date = fields.Date('Maximum Expected Date')
    received_date = fields.Date('Received Date')
    item_id = fields.Many2one('product.product','Item')
    item_ids = fields.Many2many('product.product','site_purchase_product_rel','site_purchase_id','item_id',"Items")
    quantity = fields.Float('Quantity')
    unit = fields.Many2one('product.uom','Unit')
    state = fields.Selection([('draft','Draft'),('approve','Approved'),
                              ('confirm','Requested'),
                              ('accept','Request Intiated'),
                              ('order','PO'),
                              ('received','Received'),
                              ('cancel','Cancelled')],default="draft",string="Status")

    site_id = fields.Many2one('partner.daily.statement')
    site_new_id = fields.Many2one('partner.daily.statement')
    desc = fields.Char('Description')
    site = fields.Many2one('stock.location','Location')
    received_qty = fields.Float('Received Qty')
    received_rate = fields.Float('Received Rate')
    received_total = fields.Float(compute='get_received_total', string='Amount')
    tax_ids = fields.Many2many('account.tax', string="Tax")
    tax_amount = fields.Float('Tax Amount', compute="get_tax_amount")
    sub_total = fields.Float('Sub Total', compute="get_tax_amount")
    total_amount = fields.Float('Total', compute="get_tax_amount")
    general_purchase = fields.Boolean(default=False)
    vehicle_purchase = fields.Boolean(default=False)
    telecom_purchase = fields.Boolean(default=False)
    interlocks_purchase = fields.Boolean(default=False)
    site_request = fields.Boolean(default=False)
    bitumen_purchase = fields.Boolean(default=False)
    expected_supplier = fields.Many2one('res.partner','Supplier')
    rate = fields.Float('Rate')
    estimated_amt = fields.Float('Estimated Amount')

    purchase_manager = fields.Many2one('res.users','Second Approval')
    sign_general_manager = fields.Binary('Sign')
    project_manager = fields.Many2one('res.users','First Approval')
    sign_purchase_manager = fields.Binary('Sign')
    invoice_no = fields.Char('Invoice No.')
    invoice_date = fields.Date('Invoice Date')
    stock_move_id = fields.Many2one('stock.move', 'Stock Move')
    account_move_id = fields.Many2one('account.move', 'Journal Entry')
    tax_ids = fields.Many2many('account.tax',string="Tax")
    tax_amount = fields.Float('Tax Amount',compute="get_tax_amount")
    sub_total = fields.Float('Sub Total',compute="get_tax_amount")
    total_amount = fields.Float('Total',compute="get_tax_amount")
    bitumen_agent = fields.Many2one('res.partner', 'Supplier')
    vehicle_agent = fields.Many2one('res.partner', 'Vehicle Agent')
    bank_id = fields.Many2one('res.partner.bank', 'Bank')
    doc_no = fields.Char('Doc No.')
    site_purchase_item_line_ids = fields.One2many('site.purchase.item.line','site_purchase_id',"Site Purchase")
    vehicle_id = fields.Many2one('fleet.vehicle','Vehicle')
    invoice_ids = fields.Many2many('account.invoice', 'site_purchase_account_invoice_rel', 'site_purchase_id',
                                   'invoice_id', string="Invoices")
    order_by = fields.Char('Order By')
    mode_of_order =fields.Char('Mode of Order')
    quotation_id = fields.Many2one('purchase.order', "Request for Quotation")

    @api.multi
    def cancel_purchase(self):
        if self.state == 'order' or self.state == 'received':
            purchase_order = self.env['purchase.order'].search([('state','in',['confirmed','approved']),('site_purchase_id','=',self.id)])
            if purchase_order:
                raise except_orm(_('Warning'), _("PO Generated. Cancel PO First"))
            request_quiot = self.env['purchase.order'].search([('state','in',['draft','bid','sent']),('site_purchase_id','=',self.id)])
            for req in request_quiot:
                req.state = 'cancel'
            purchase_comp = self.env['purchase.comparison'].search([('state','not in',['cancel']),('mpr_id','=',self.id)])
            for comp in purchase_comp:
                comp.state = 'cancel'
            self.state = 'cancel'
        else:
            self.state = 'cancel'

    @api.multi
    def set_draft(self):
        self.state = 'draft'

    @api.multi
    def action_request_init(self):
        for rec in self:
            rec.state = 'accept'

    @api.multi
    def action_approved(self):
        for rec in self:
            rec.state = 'approve'
            # rec.state = 'accept'


    @api.multi
    def button_create_comparison(self):

        if datetime.strptime(self.max_expected_date,"%Y-%m-%d") < datetime.strptime(datetime.now().strftime("%Y-%m-%d"),"%Y-%m-%d"):
            raise except_orm(_('Warning'), _("Max Expected Date is greater than Today Date"))

        self.state = 'order'
        value_list = []
        for purchase in self.site_purchase_item_line_ids:
            value_list.append((0, 0, {'product_id': purchase.item_id.id,
                                  'name': purchase.item_id.name,
                                  'required_qty': purchase.quantity,
                                  'product_uom': purchase.unit.id,
                                  'state': 'confirmed'}))

        values = {'site_purchase_id':self.id,
                  'location_id':self.site.id,
                  'vehicle_id':self.vehicle_id.id,
                  'minimum_plann_date':self.min_expected_date,
                  'maximum_planned_date':self.max_expected_date,
                  'order_line':value_list,
                  'origin':self.name,
                  'project_id':self.project_id.id,
                  'state':'confirmed',
                  'vehicle_agent_id':self.vehicle_agent.id,
                  # 'company_contractor_id':self.project_id.company_contractor_id.id,
                  }

        quotation = self.env['purchase.order'].create(values)
        self.quotation_id = quotation.id
        res = {
            'name': 'Purchase Order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'target': 'current',

            'res_id':self.quotation_id.id,
            'type': 'ir.actions.act_window',
            'context': {'default_site_purchase_id': self.id,
                        'default_location_id':self.site.id,
                        'default_vehicle_id':self.vehicle_id.id,
                        'default_minimum_plann_date':self.min_expected_date,
                        'default_maximum_planned_date':self.max_expected_date}
        }

        return res



    @api.multi
    def button_create_purchase(self):

        if datetime.strptime(self.max_expected_date,"%Y-%m-%d") < datetime.strptime(datetime.now().strftime("%Y-%m-%d"),"%Y-%m-%d"):
            raise except_orm(_('Warning'), _("Max Expected Date should be greater than Order Date"))

        self.state = 'order'
        res = {
            'name': 'Purchase Order',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order',
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {'default_site_purchase_id': self.id,
                        'form_view_ref':'hiworth_construction.form_new_request_for_quotation',
                        'default_location_id':self.site.id,
                        'default_vehicle_id':self.vehicle_id.id,
                        'default_state':'draft',
                        'default_origin':self.site_id.name,
                        'default_company_contractor_id': self.project_id.company_contractor_id.id,
                        },
        }

        return res

    @api.multi
    def confirm_purchase(self):

        self.state = 'confirm'
        # supervisor_record = self.env['partner.daily.statement'].sudo().search(
        #     [('date', '=', self.order_date), ('location_ids', '=', self.site.id)])
        # if supervisor_record:
        #     self.site_new_id = supervisor_record.id
            
            

            

    @api.multi
    def order_generate(self):
        if not self.expected_supplier.property_account_payable:
            raise except_orm(_('Warning'),_('No Payable Account is linked with the supplier.'))
        vehicle = False
        
        if self.vehicle_id:
            vehicle=self.vehicle_id.id
            
        values = {
            'partner_id': self.expected_supplier.id,
            'vehicle_id':vehicle,
            'location_id': self.site and self.site.id or False,
            'date_order': self.order_date,
            'account_id': self.expected_supplier.property_account_payable.id,
            'minimum_planned_date': self.min_expected_date,
            'maximum_planned_date': self.max_expected_date,
            'date_order': self.order_date,
            'origin':self.name,
            'pricelist_id': self.expected_supplier.property_product_pricelist_purchase.id,
            }
        order = self.env['purchase.order'].create(values)
        for item in self.site_purchase_item_line_ids:
            values2 = {
                    'product_id':item.item_id.id,
                    'name': item.desc,
                    'required_qty':item.quantity,
                    'product_uom':item.unit.id,
                    'expected_rate': item.rate,
                    'price_unit': 0.0,
                    'order_id': order.id,
                    'date_planned': self.min_expected_date,
                    'site_purchase_id': self.id,
                    }
            order_line = self.env['purchase.order.line'].create(values2)
        order.signal_workflow('purchase_confirm')
        self.state = 'order'
        
    @api.multi
    def invoice_generate(self):
        if not self.expected_supplier.property_account_payable:
            raise except_orm(_('Warning'), _('No Payable Account is linked with the supplier.'))
        values = {
            'partner_id': self.expected_supplier.id,
            'location_id': self.site.id,
            'type':'in_invoice',
            'date_due': self.order_date,
            'account_id': self.expected_supplier.property_account_payable.id,
            'journal_id':self.env['account.journal'].search([('type','=','purchase')],limit=1).id,
            'date_invoice': self.invoice_date,
            'maximum_planned_date': self.max_expected_date,
            'date_order': self.order_date,
            'origin': self.name,
            'pricelist_id': self.expected_supplier.property_product_pricelist_purchase.id,
            'state':'draft',
        }
        order = self.env['account.invoice'].create(values)
        for item in self.site_purchase_item_line_ids:
            values2 = {
                'product_id': item.item_id.id,
                'name': item.desc,
                'quantity': item.received_qty,
                'uos_id': item.unit.id,
                'account_id': self.expected_supplier.property_account_payable.id,
                'price_unit': item.received_rate,
                'invoice_line_tax_id':[(6,0,item.tax_ids.ids)],
                'invoice_id': order.id,
                'date_planned': self.min_expected_date,
                'site_purchase_id': self.id,
            }
            order_line = self.env['account.invoice.line'].create(values2)
        invoice_list = []
        if self.invoice_ids:
            invoice_list = self.invoice_ids.ids
            invoice_list.append(order.id)
            self.invoice_ids = [(6, 0, invoice_list)]
        else:
            invoice_list.append(order.id)
            self.invoice_ids = [(6,0,invoice_list)]
            
        if self.received_qty == self.quantity:
            self.state = 'received'
        
        

    @api.multi
    def approve_purchase1(self):
        self.project_manager = self.env.user.id
        self.state = 'accept'

    @api.multi
    def approve_purchase2(self):
        self.purchase_manager = self.env.user.id
        self.state = 'approved2'

    @api.multi
    def view_order(self):
        order =  self.env['purchase.order.line'].search([('site_purchase_id','=',self.id)])
        # print 'record=============', order.order_id,asd
        if order:
            record = order[0].order_id
            print 'record=============', record.id
            res = {
                'name': 'Purchase Order',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'purchase.order',
                'res_id': record.id,
                'target': 'current',
                'type': 'ir.actions.act_window',
                'view_id': self.env.ref('hiworth_construction.purchase_order_form_changed').id,
            }

        return res


    @api.multi
    def view_invoices(self):
        order = self.env['purchase.order.line'].search([('site_purchase_id', '=', self.id)],limit=1)
        invoice = self.env['account.invoice'].search([('purchase_id', '=', order.order_id.id)])
        print "wwwwwwwwwwwwwwwwwwwwwwwwwwwwww",order.order_id.invoice_ids.ids
        invoice_list = []
        # for pick in  picking:
        #     print "wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww",pick
        #     if pick.invoice_id:
        #         invoice_list.append(pick.invoice_id.id)
            
        
        res = {
            'name': 'Supplier Invoices',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'domain': [('id','in',invoice.ids)],
            'res_id': False,
            'target': 'current',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'context': {},

        }

        return res

    @api.multi
    def view_detailed_report(self):
        order = self.env['purchase.order.line'].search([('site_purchase_id', '=', self.id)])
        invoice_list = []
        # for pick in  picking:
        #     print "wwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwwww",pick
        #     if pick.invoice_id:
        #         invoice_list.append(pick.invoice_id.id)
    
        res = {
            'name': 'Detailed Report',
            'view_type': 'tree',
            'view_mode': 'tree',
            'res_model': 'purchase.order.line',
            'domain': [('id', 'in', order.ids)],
            'res_id': False,
            'target': 'current',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'context': {'tree_view_ref':'hiworth_construction.tree_purchase_order_line_detail'},
        
        }
    
        return res



    @api.model
    def create(self, vals):
        if vals.get('supervisor_id') == False:
            user = self.env['res.users'].sudo().search([('id','=',self.env.user.id)])
            # if user:
            #     if user.employee_id or user.id == 1:
            #         vals['supervisor_id'] = user.employee_id.id if user.id !=1 else self.env['hr.employee'].search([('id','=',1)]).id
            #     else:
            #         raise except_orm(_('Warning'),_('User have To Be Linked With Employee.'))
            #
        if vals.get('site') == False:
            if vals.get('site_id'):
                vals['site'] = self.env['partner.daily.statement'].search([('id','=',vals['site_id'])]).location_ids.id

        result = super(SitePurchase, self).create(vals)
        if result.name == False:
            if result.bitumen_purchase == True:
                result.name = str('BPR-') + str(result.site.loc_barcode)+"/" + self.env['ir.sequence'].next_by_code(
                    'site.purchase') or '/'
            if result.general_purchase == True:
                result.name = str('GPR-')+str(result.site.loc_barcode)+"/"+self.env['ir.sequence'].next_by_code('site.purchase') or '/'
            if result.vehicle_purchase == True:
                result.name = str('VPR-')+str(result.site.loc_barcode)+"/"+self.env['ir.sequence'].next_by_code('site.purchase') or '/'
            if result.telecom_purchase == True:
                result.name = str('TPR-')+str(result.site.loc_barcode)+"/"+self.env['ir.sequence'].next_by_code('site.purchase') or '/'
            if result.interlocks_purchase == True:
                result.name = str('IPR-')+str(result.site.loc_barcode)+"/"+self.env['ir.sequence'].next_by_code('site.purchase') or '/'
            if result.site_request == True:
                result.name = str('SR-')+str(result.site.loc_barcode)+"/"+self.env['ir.sequence'].next_by_code('site.purchase') or '/'

        if len(result.site_purchase_item_line_ids) ==0:
            raise except_orm(_('Warning'), _('Please Add any Item'))
        return result


class BcplAccountDetails(models.Model):
    _name = 'bcpl.account.details'


    item = fields.Char('Item')
    invoice_no=fields.Integer('Invoice No')
    doc = fields.Integer('Doc')
    order_date= fields.Date('Order Date')
    supplier = fields.Many2one('res.partner','Supplier')
    site_name = fields.Char('Site Name')
    qty = fields.Integer('Qty')
    rate = fields.Float('Rate')
    amount = fields.Float('Amount',compute= 'onchange_amount')
    agent = fields.Char('Agent')
    vehicle_no = fields.Char('Vehicle No')
    date = fields.Date('Date')
    bank = fields.Char('Bank')
    total_amount = fields.Float('Toatal Amount')


    @api.onchange('qty','rate')
    def onchange_amount(self):
        self.amount= self.qty*self.rate



