from openerp import fields, models, api,_
from datetime import date,datetime
from openerp.exceptions import except_orm,ValidationError
from openerp.osv import fields as osv
from lxml import etree

class GoodsTransferDummy(models.Model):

    _name = 'goods.transfer.dummy'

    @api.constrains('stock_balance')
    def check_available_quantity(self):
        for rec in self:
            if rec.stock_balance <= 0:
                raise ValidationError(_('%s Out of Stock' % (rec.item_id.name)))

    @api.constrains('qty')
    def check_required_quantity(self):
        for rec in self:
            if rec.qty > rec.stock_balance:
                raise ValidationError(_('Transfer Quantity is greater than Available Quantity'))


    @api.onchange('item_id')
    def onchange_item_id(self):
        for rec in self:
            rec.desc = rec.item_id.name
            # rec.specs = rec.item_id.part_no
            rec.rate = rec.item_id.standard_price
            if rec.item_id:
                rec.stock_balance = rec.item_id.with_context({'location' : rec.transfer_list_id.site_from.id}).qty_available
            product_list = []
            if self._context.get('source_location', False) and self._context.get('category_id', []):
                location = self.env['stock.location'].browse(self._context.get('source_location', False))

                history = self.env['stock.history'].search([('location_id', '=', location.id), (
                'product_categ_id', 'in', self._context.get('category_id', False)[0][2])])

                for his in history:
                    product_list.append(his.product_id.id)

            return {'domain': {'item_id': [('id', 'in', product_list)]}}



    @api.one
    def get_total(self):
        for s in self :
            s.value= s.rate * s.qty

    item_id = fields.Many2one('product.product', 'Material Code')
    desc = fields.Char('Material Name')
    specs = fields.Char('Specification')
    qty = fields.Float('Qty')
    rate = fields.Float('Rate')
    value = fields.Float('Value',compute='get_total')
    remarks = fields.Char('Remarks')
    transfer_list_id = fields.Many2one('goods.transfer.note.in')
    transfer_recieve_id = fields.Many2one('goods.recieve.report')
    stock_balance = fields.Float('Stock Balance')
    
    

class GoodsTransferNoteIn(models.Model):
    _name = 'goods.transfer.note.in'
    _rec_name = 'gtn_no'
    _inherit = ['mail.thread', 'ir.needaction_mixin']



    
    @api.model
    def create(self, vals):
        #res = super(GoodsTransferNoteIn,self).create(fields)
        vals.update({'user_id':self.env.user.id})
        if vals.get('gtn_no',False) == False:

            vals.update({'gtn_no' :str(self.env['ir.sequence'].next_by_code('gtn.code'))})
        res = super(GoodsTransferNoteIn,self).create(vals)
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            for material_issue in rec.transfer_list_ids:
                quant = self.env['stock.quant'].search([('product_id', '=', material_issue.item_id.id),
                                                        ('qty', '=', -(material_issue.qty)),
                                                        ('in_date', '>', rec.date),
                                                        ('location_id', '=', rec.site_from.id)])

                quant2 = self.env['stock.quant'].search([('product_id', '=', material_issue.item_id.id),
                                                        ('qty', '=', material_issue.qty),
                                                        ('in_date', '>', rec.date),
                                                        ('location_id', '=', rec.site_to.id)])
                quant.with_context({'force_unlink':True}).unlink()
        return super(GoodsTransferNoteIn, self).unlink()
    


    @api.depends('transfer_list_ids')
    def compute_item_list(self):
        for rec in self:
            item = ''
            for lines in rec.transfer_list_ids:
                item += lines.item_id.name + ','
            rec.item_list = item

    @api.depends('transfer_list_ids')
    def compute_item_qty(self):
        for rec in self:
            quantity = 0
            for lines in rec.transfer_list_ids:
                quantity += lines.qty
            rec.total_quantity = quantity
    





    


    project_id = fields.Many2one('project.project', 'Project',track_visibility='onchange')
    to_project_id = fields.Many2one('project.project', 'To Project',track_visibility='onchange')
    site_from = fields.Many2one('stock.location', 'From',track_visibility='onchange')
    site_to = fields.Many2one('stock.location', 'To',track_visibility='onchange')
    gtn_no = fields.Char('GTN NO',track_visibility='onchange')
    date = fields.Datetime('Date',default=lambda self: fields.datetime.now())
    transfer_list_ids = fields.One2many('goods.transfer.dummy','transfer_list_id',track_visibility='onchange')
    user_created = fields.Many2one('res.users', 'Prepared by')
    project_manager = fields.Many2one('res.users', 'Project Manager')
    purchase_manager = fields.Many2one('res.users', 'Purchase Manager')
    dgm_id = fields.Many2one('res.users', 'GM')
    state = fields.Selection([('draft', 'Draft'),
                              ('transfer', 'Transferred'),
                              ('recieve', 'Recieved'),
                             ], default="draft", string="Status")
    goods_transfer_bool = fields.Boolean('Goods transfer',default="True" )
    user_id = fields.Many2one('res.users',string="Issuer",track_visibility='onchange')
    store_manager_id = fields.Many2one('res.users',"Receiver")
    transfer_gtn_id = fields.Many2one('goods.transfer.note.in',"Transfer ")
    item_list = fields.Char(string="Items", compute='compute_item_list')
    total_quantity = fields.Char(string="Quantity", compute='compute_item_qty')
    category_ids = fields.Many2many('product.category','goods_transfer_product_category_rel','goods_transfer_id','category_id',"Category")
    # project_location_ids = fields.Many2many('stock.location','stock_location_goods_transfer_note_rel','location_id','transfer_id',"From Location")
    # to_project_location_ids = fields.Many2many('stock.location','to_project_location_goods_transfer_rel','location_id','project_id',"To Location",related='to_project_id.project_location_ids')
    @api.multi
    def set_draft(self):
        self.state = 'draft'
        self.request_not_in_draft = False
    @api.multi
    def confirm_purchase(self):
            self.user_created = self.env.user.id
            self.state = 'confirm'
            self.request_not_in_draft = True

    @api.multi
    def approve_purchase1(self):
        self.project_manager = self.env.user.id
        self.state = 'approved1'
    @api.multi
    def action_transfer(self):
        for rec in self:
            rec.state = 'transfer'

    @api.multi
    def approve_purchase3(self):
        for rec in self:
            journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
            stock = self.env['stock.picking'].create({
        
                'source_location_id': rec.site_from.id,
        
                'site': rec.site_to.id,
                'order_date': rec.date,
                'account_id': rec.site_to.related_account.id,
                'supervisor_id': self.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
        
            })
            for req in rec.transfer_list_ids:
                stock_move = self.env['stock.move'].create( {
                    'location_id': rec.site_from.id,
            
                    'product_id': req.item_id.id,
                    'available_qty': req.item_id.with_context(
                        {'location': rec.site_to.id}).qty_available,
                    'name': req.desc,
                    'product_uom_qty': req.qty,
                    'product_uom': req.item_id.uom_id.id,
                    'price_unit': req.rate,
                    'date': rec.date,
                    'date_expected': rec.date,
                    'account_id': rec.site_to.related_account.id,
                    'location_dest_id': rec.site_to.id,
                    'picking_id':stock.id
                })
                stock_move.action_done()
            stock.action_done()



        self.state = 'recieve'


    @api.multi
    def cancel_process(self):
        self.state = 'cancel'

    @api.multi
    def goods_transfer_report(self):

        transfer_list=[]
        for rec in self:
            for tlist in rec.transfer_list_ids:

                transfer_dict={
                            'item_id':tlist.item_id.name,
                            'desc':tlist.desc,
                            'specs':tlist.specs,
                            'qty':tlist.qty,
                            'rate':tlist.rate,
                            'value':tlist.value,
                            'remarks':tlist.remarks,

                            }
                transfer_list.append(transfer_dict)

        return transfer_list
        
class GoodsRecieveReport(models.Model):

    _name = "goods.recieve.report"
    _rec_name = 'grr_no'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'Date desc'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
                        submenu=False):
        res = super(GoodsRecieveReport, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if view_type == 'form':
            # Check if user is in group that allow creation
            has_my_group = self.env.user.has_group('base.group_erp_manager')
            if has_my_group:
                root = etree.fromstring(res['arch'])
                root.set('edit', 'true')
                res['arch'] = etree.tostring(root)
        return res

    @api.model
    def default_get(self, fields_list):
        res = super(GoodsRecieveReport, self).default_get(fields_list)
        journal = self.env['account.journal'].search([('type', '=', 'purchase')], limit=1, order='id asc')
        res.update({'journal': journal.id})
        return res

    @api.model
    def create(self,vals):

        if vals.get('grr_no',False)==False:


            location_id = self.env['stock.location'].search([('usage', '=', 'supplier')],order='id asc' ,limit=1)
            vals['supplier_location_id'] = location_id.id
        order = super(GoodsRecieveReport, self).create(vals)
        order.grr_no =str(self.env['ir.sequence'].next_by_code('grr.code')) + "/"+  str(datetime.now().year)

        journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
        # location_id = self.env['stock.location'].search([('usage','=','supplier')])
        # order.supplier_location_id = location_id.id
        total_qty =0
        unit_price = 0
        total_other_charge = 0

        for lines in order.goods_recieve_report_line_ids:
            total_qty +=lines.quantity_accept
        for other in order.other_charge_details_ids:
            total_other_charge +=other.total_amount

        for rec in order:

            stock = self.env['stock.picking'].create({

                'source_location_id': rec.supplier_location_id.id,

                'site': rec.site.id,
                'order_date': rec.Date,
                'account_id': rec.site.related_account.id,
                'supervisor_id': rec.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': rec.project_id.id,
            })
            for line in rec.goods_recieve_report_line_ids:
                unit_price = (line.amount / line.quantity_accept) + (total_other_charge/total_qty)
                line.item_id.sudo().standard_price = unit_price
                stock_move = self.env['stock.move'].create({
                    'location_id': rec.supplier_location_id.id,
                    'category_id':line.item_id.categ_id.id,

                    'project_id': rec.project_id.id,
                    'product_id': line.item_id.id,
                    'available_qty': line.item_id.with_context(
                        {'location': rec.supplier_location_id.id}).qty_available,
                    'name': line.desc,
                    'product_uom_qty': line.quantity_accept,
                    'product_uom': line.item_id.uom_id.id,
                    'price_unit': unit_price,
                    'date': rec.Date,
                    'date_expected': rec.Date,
                    'account_id': rec.site.related_account.id,
                    'location_dest_id': rec.site.id,
                    'picking_id': stock.id
                })
                stock_move.action_done()
                line.move_id = stock_move.id
            stock.action_done()
            rec.picking_id= stock.id
            flag=0
            amt =0
            for po in rec.purchase_id.order_line:
                for line in rec.goods_recieve_report_line_ids:
                    amt += line.amount

                    if po.product_id.id == line.item_id.id:

                        po.received_qty =po.received_qty +line.quantity_accept
                        po.received_rate = line.rate
                        if po.required_qty != (po.received_qty+po.closed_qty):

                            flag=1


            if flag==0:
                rec.purchase_id.state = 'done'
                if rec.mpr_id:
                    rec.mpr_id.state = 'received'
                else:
                    for site in rec.site_purchase_ids:
                        site.state = 'received'

        po = self.env['purchase.order'].search([('site_purchase_id', '=', order.mpr_id.id), ('state', '=', 'approved')],limit=1)

        move_line_list = []
        if order.total_amount != 0.0:
            move_line_list.append((0, 0, {'name': order.purchase_id.name,
                                          'account_id': order.purchase_id.partner_id.property_account_payable.id,
                                          'credit': order.total_amount,
                                          'debit': 0,
                                          }))


            if not order.vehicle_id:
                move_line_list.append((0, 0, {'name': order.grr_no,
                                          'account_id': order.site.related_account.id,
                                          'credit': 0,
                                          'debit': order.total_amount}))
            else:
                move_line_list.append((0, 0, {'name': order.grr_no,
                                              'account_id': order.vehicle_id.related_account.id,
                                              'credit': 0,
                                              'debit': order.total_amount}))
            move = {
                'journal_id': order.journal.id,
                'date': order.Date,
                'line_id':move_line_list
            }

            move_obj = self.env['account.move'].create(move)
            order.account_move_id = move_obj.id

        
        return order




    @api.multi
    def write(self, vals):

        res =  super(GoodsRecieveReport, self).write(vals)
        if self.account_move_id:
            for line in self.account_move_id.line_id:
                if line.debit ==0:
                    line.credit = self.total_amount
                else:
                    line.debit = self.total_amount
        return res

    @api.multi
    def unlink(self):
        for rec in self:
            for material_issue in rec.goods_recieve_report_line_ids:
                quant = self.env['stock.quant'].search([('product_id', '=', material_issue.item_id.id),
                                                        ('qty', '=', material_issue.quantity_accept),
                                                        ('in_date', '>', rec.Date),
                                                        ('location_id', '=', rec.project_location_id.id)
                                                        ],limit=1)
                quant.with_context({'force_unlink':True}).unlink()
        return super(GoodsRecieveReport, self).unlink()

    @api.onchange('supplier_id')
    def onchange_supplier(self):
        for rec in self:
            if rec.supplier_id:
                rec.supplier_location_id = self.env['stock.location'].search([('usage','=','supplier')]).id
    



    @api.onchange('mpr_id')
    def onchange_mpr_id(self):
        for rec in self:
            if rec.mpr_id:
                rec.merged_po = False
                rec.vehicle_id = rec.mpr_id.vehicle_id.id
                po=self.env['purchase.order'].search([('site_purchase_id','=',rec.mpr_id.id),('state','=','approved')])
                if len(po) ==1:
                    rec.purchase_id = po.id
                else:
                    return {'domain':{'purchase_id':[('id','in',po.ids)]}}




    @api.onchange('purchase_id')
    def onchange_material_procurement(self):
        for rec in self:
            if rec.purchase_id:
                values=[]
                prev_list = []


                rec.supplier_id = rec.purchase_id.partner_id.id

                rec.project_id = rec.purchase_id.project_id.id
                rec.company_contractor_id = rec.purchase_id.company_contractor_id.id
                for mpr_lines in rec.purchase_id.order_line:

                    values.append((0,0,{'item_id':mpr_lines.product_id.id,
                                        'desc':mpr_lines.name,
                                        'tax_ids':[(6,0,mpr_lines.taxes_id.ids)],
                                        'po_quantity':mpr_lines.required_qty - mpr_lines.received_qty - mpr_lines.closed_qty,
                                        'rate':mpr_lines.expected_rate,
                                        'unit_id':mpr_lines.product_uom.id

                                        }))
                    prev_list.append((0,0,{'item_id':mpr_lines.product_id.id,
                                        'desc':mpr_lines.name,
                                        'tax_ids':[(6,0,mpr_lines.taxes_id.ids)],
                                        'po_quantity':mpr_lines.required_qty,
                                           'quantity_accept':mpr_lines.received_qty,
                                           'quantity_reject':mpr_lines.closed_qty,
                                        'rate':mpr_lines.expected_rate,
                                        'unit_id':mpr_lines.product_uom.id

                                        }))
                rec.goods_recieve_report_line_ids = values
                rec.previous_goods_receipt_entries_ids = prev_list






    

            
            
    @api.depends('goods_recieve_report_line_ids')
    def compute_item_list(self):
        for rec in self:
            item = ''
            for lines in  rec.goods_recieve_report_line_ids:
                item += lines.item_id.name + ','
            rec.item_list = item

    @api.depends('goods_recieve_report_line_ids')
    def compute_item_qty(self):
        for rec in self:
            quantity = 0
            for lines in rec.goods_recieve_report_line_ids:
                quantity += lines.quantity_accept
            rec.total_quantity = quantity




    @api.depends('other_charge_details_ids','goods_recieve_report_line_ids','round_off_amount')
    def compute_amount(self):
        for rec in self:
            taxable_amount = 0
            igst_amount = 0
            cgst_amount = 0
            sgst_amount = 0
            other_charge = 0
            non_taxable_amount =0
            for line in rec.goods_recieve_report_line_ids:

                if line.tax_ids:
                    taxable_amount += line.taxable_amount
                else:
                    non_taxable_amount += line.non_taxable_amount
                igst_amount += line.igst_amount
                cgst_amount += line.cgst_amount
                sgst_amount += line.sgst_amount


            for other in rec.other_charge_details_ids:
                if other.is_tax_applicable:
                    taxable_amount += other.taxable_amount
                    igst_amount += other.igst_amount
                    cgst_amount += other.cgst_amount
                    sgst_amount += other.sgst_amount
                else:
                    other_charge += other.amount
            rec.taxable_amount = taxable_amount
            rec.igst_amount = igst_amount
            rec.cgst_amount = cgst_amount
            rec.sgst_amount = sgst_amount
            rec.other_charge = other_charge
            rec.non_taxable_amount = non_taxable_amount
            rec.total_amount = taxable_amount + igst_amount +  cgst_amount+sgst_amount+ other_charge + non_taxable_amount - rec.round_off_amount


    project_id = fields.Many2one('project.project', 'Project',track_visibility='onchange')
    supplier_id = fields.Many2one('res.partner','Supplier',track_visibility='onchange')
    supplier_location_id = fields.Many2one('stock.location','Location',track_visibility='onchange')
    site = fields.Many2one('stock.location','Project Location',required=True,track_visibility='onchange')
    mpr_id = fields.Many2one('site.purchase',"Purchase Request No",domain="[('state','=','order')]")
    purchase_id = fields.Many2one('purchase.order','PO No',domain="[('state','=','approved')]")
    po_no = fields.Char('P.O.No')
    grr_no = fields.Char('GRR No',track_visibility='onchange')
    Date = fields.Datetime('Date' , default=lambda self: fields.datetime.now())
    picking_id = fields.Many2one('stock.picking',"Picking")
    invoice_no = fields.Char(string="Supplier Invoice Number")
    goods_recieve_report_line_ids = fields.One2many('goods.recieve.report.line','goods_recieve_report_id')
    item_list = fields.Char(string="Items",compute='compute_item_list')
    total_quantity = fields.Char(string="Quantity",compute='compute_item_qty')

    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")
    without_po = fields.Boolean("without PO",default=False)
    partner_daily_statement_id = fields.Many2one('partner.daily.statement', string="Partner Daily Statement")
    invoice_date = fields.Date('Invoice Date')
    journal = fields.Many2one('account.journal','Journal')
    is_tax_invoice = fields.Boolean("Is Tax Invoice?",default=True)
    account_move_id = fields.Many2one('account.move',"Move")
    previous_goods_receipt_entries_ids = fields.One2many('goods.recieve.report.line','prev_goods_recieve_report_id',"Previous Entries")
    other_charge_details_ids = fields.One2many('other.charge.details','goods_recieve_report_id',"Other Charge Details")


    taxable_amount = fields.Float("Taxable amount",compute='compute_amount',store=True)
    total_amount = fields.Float("Total amount", compute='compute_amount', store=True)
    other_charge = fields.Float("Other Charge", compute='compute_amount', store=True)
    cgst_amount = fields.Float("CGST Amount", compute='compute_amount', store=True)
    sgst_amount = fields.Float("SGST Amount", compute='compute_amount', store=True)
    igst_amount = fields.Float("IGST Amount", compute='compute_amount', store=True)
    non_taxable_amount = fields.Float("Non-Taxable Amount", compute='compute_amount', store=True)
    round_off_amount = fields.Float("Round Off Amount")
    foreclosure_bool = fields.Boolean("Forclosure")
    vehicle_agent_id = fields.Many2one('res.partner',"Vehicle Agent")
    company_contractor_id = fields.Many2one('res.partner',domain=[('company_contractor','=',True)],string="Company")
    site_purchase_ids = fields.Many2many('site.purchase','goods_transfer_site_purchase_rel','goods_transfer','site_purchase_id',"Purchase Request")
    merged_po = fields.Boolean("Merged PO",default=False)
    state = fields.Selection([('received','Received'),
                              ('cancel','Cancel')],default='received',string="Status")



    @api.multi
    def action_return(self):
        for goods_receive in self:
            stock = self.env['stock.picking'].create({
                'request_id': self.mpr_id.id,
                'source_location_id': goods_receive.site.id,
                'partner_id': goods_receive.supplier_id.id,
                'site': goods_receive.site.id,
                'order_date': self.Date,
                'account_id': goods_receive.supplier_id.property_account_payable.id,
                'supervisor_id': self.env.user.employee_id.id,
                'is_purchase': True,
                'project_id': goods_receive.project_id.id,
                })
            for req in goods_receive.goods_recieve_report_line_ids:
                req.entry_created_fleet = False
                if req.battery_id:
                    req.battery_id.unlink()
                if req.gps_id:
                    req.gps_id.unlink()
                if req.tyre_id:
                    req.tyre_id.unlink()
                if req.retread_tyre_id:
                    req.retread_tyre_id.unlink()
                if req.quantity_accept != 0.0:
                    stock_move = self.env['stock.move'].create({
                    'location_id': goods_receive.site.id,
                    'project_id': goods_receive.project_id.id,
                    'product_id': req.item_id.id,
                    'available_qty': req.item_id.with_context(
                        {'location': goods_receive.site.id}).qty_available,
                    'name': req.desc,
                        'date':goods_receive.Date,
                        'date_expected':goods_receive.Date,
                    'product_uom_qty': req.quantity_accept,
                    'product_uom': req.item_id.uom_id.id,
                    'price_unit': req.rate,
                    'account_id': goods_receive.supplier_id.property_account_payable.id,
                    'location_dest_id': goods_receive.supplier_location_id.id,
                    'picking-id':stock.id
                })
                    stock_move.action_done()
            stock.action_done()
            goods_receive.state = 'cancel'

    
    
class GoodsRecieveReportLine(models.Model):

    _name = "goods.recieve.report.line"



    @api.onchange('item_id')
    def onchange_item_id(self):
        for rec in self:
            if rec.item_id:
                rec.desc = rec.item_id.name
                rec.unit_id = rec.item_id.uom_id.id

    @api.onchange('tax_ids')
    def onchange_tax_ids(self):
        for rec in self:
            taxl =[]
            if rec.tax_ids:
                for tax in rec.tax_ids:
                    if tax.parent_id:
                        tax_ids = self.env['account.tax'].search([('parent_id','=',tax.parent_id.id)])
                        rec.tax_ids = [(6,0,tax_ids.ids)]


    @api.constrains('quantity_accept','po_quantity')
    def constraints_quantity(self):
        if self.po_quantity < self.quantity_accept:
            raise ValidationError(_('Received Quantity cannot be greater than PO Quantity.'))

    @api.constrains('quantity_accept', 'quantity_reject')
    def constraints_quantity_quantity_reject(self):
        if self.po_quantity < (self.quantity_reject + self.quantity_accept):
            raise ValidationError(_('Forclosure Quantity cannot be greater than PO Quantity.'))


    @api.depends('rate','quantity_accept','tax_ids')
    def compute_total_amount(self):
        for rec in self:
            if rec.item_id.battery or rec.item_id.tyre or rec.item_id.tyre_retread:
                rec.entry_created_fleet = False
            tax_amt = 0
            cgst =0
            sgst = 0
            igst = 0
            non_tax = 0
            if rec.tax_ids:
                for tax in rec.tax_ids:

                    if tax.price_include:
                        tax_amt = tax.amount
                        if tax.tax_type == 'gst':
                            cgst = ((rec.quantity_accept * (rec.rate / (tax_amt+1))) * tax_amt)/2
                            sgst = ((rec.quantity_accept * (rec.rate / (tax_amt + 1))) * tax_amt) / 2
                        if tax.tax_type == 'igst':
                            igst = ((rec.quantity_accept * (rec.rate / (tax_amt + 1))) * tax_amt)
                    else:
                        if tax.tax_type == 'gst':
                            cgst = (rec.quantity_accept * (rec.rate * tax.amount)) / 2
                            sgst = (rec.quantity_accept * (rec.rate * tax.amount)) / 2
                        if tax.tax_type == 'igst':
                            igst = (rec.quantity_accept * (rec.rate * tax.amount))

            else:
                non_tax += rec.rate * rec.quantity_accept

            rec.taxable_amount = rec.quantity_accept * (rec.rate / (tax_amt+1))
            rec.cgst_amount = cgst
            rec.sgst_amount = sgst
            rec.igst_amount = igst
            rec.non_taxable_amount = non_tax
            rec.amount = rec.taxable_amount +cgst + sgst +igst

    @api.depends('tyre_id','battery_id','retread_tyre_id')
    def compute_entry_created(self):
        for rec in self:
            if rec.item_id.tyre or rec.item_id.tyre_retread or rec.item_id.battery or rec.item_id.gps:
                if rec.tyre_id or rec.battery_id or rec.retread_tyre_id or rec.gps_id:
                    rec.entry_created_fleet = True
                else:
                    rec.entry_created_fleet=False
            else:
                rec.entry_created_fleet = True

    item_id = fields.Many2one('product.product', 'Material Code')
    desc = fields.Char('Material Name')
    specs = fields.Char('Specification')
    unit_id = fields.Many2one('product.uom',string="Unit of Measure")
    tax_ids= fields.Many2many('account.tax','goods_receive_report_line_tax_ids','goods_receive_report_id','tax_id',"Tax")
    quantity_rec = fields.Float('Quantity Received')
    quantity_accept = fields.Float('Quantity Accepted')
    quantity_reject = fields.Float('Foreclosure Qty')
    rate = fields.Float('Price')
    amount = fields.Float("Amount",compute='compute_total_amount',store=True)
    taxable_amount = fields.Float("Taxable Amount",compute='compute_total_amount',store=True)
    cgst_amount = fields.Float("CGST Amount", compute='compute_total_amount', store=True)
    sgst_amount = fields.Float("SGST Amount", compute='compute_total_amount', store=True)
    igst_amount = fields.Float("IGST Amount", compute='compute_total_amount', store=True)
    non_taxable_amount = fields.Float("Non-Taxable Amount",compute='compute_total_amount',store=True)
    remarks = fields.Char('Remarks')
    goods_recieve_report_id = fields.Many2one('goods.recieve.report',string="Goods Recieve Report")
    date = fields.Datetime(string="Date",related = 'goods_recieve_report_id.Date')
    po_quantity = fields.Float(string='PO Quantity')
    project_id = fields.Many2one('project.project', 'Project')
    received = fields.Boolean(string="Received",default=False)
    grr_no = fields.Char('GRR.No.',related = 'goods_recieve_report_id.grr_no')
    mpr_id = fields.Many2one(string='MPR.No.',related = 'goods_recieve_report_id.mpr_id')
    purchase_id = fields.Many2one(string='PO.No.',related = 'goods_recieve_report_id.purchase_id')
    supplier_id = fields.Many2one(string='Supplier',related = 'goods_recieve_report_id.supplier_id')
    supplier_location_id = fields.Many2one(string='Supplier Store',related = 'goods_recieve_report_id.supplier_location_id')
    invoice_no = fields.Char('Supplier Invoive Number',related = 'goods_recieve_report_id.invoice_no')
    project_id = fields.Many2one(string='Project Name',related = 'goods_recieve_report_id.project_id')
    site = fields.Many2one(string='Project Name',related = 'goods_recieve_report_id.site')
    move_id = fields.Many2one('stock.move',"Move")
    prev_goods_recieve_report_id = fields.Many2one('goods.recieve.report', string="Goods Recieve Report")
    entry_created_fleet = fields.Boolean("Entry Created",compute='compute_entry_created')
    tyre_id = fields.Many2one('vehicle.tyre',"Tyre")
    battery_id = fields.Many2one('vehicle.battery',"Battery")
    retread_tyre_id = fields.Many2one('retreading.tyre.line',"Retread")
    gps_id = fields.Many2one('vehicle.gps',"GPS")
    brand_name = fields.Many2one('material.brand')


    @api.multi
    def button_entry_created(self):
        for rec in self:
            if rec.item_id.battery:
                return {
                    'name': 'Battery Entry',
                    'view_type': 'form',
                    'view_mode': 'form',

                    'res_model': 'vehicle.battery',

                    'type': 'ir.actions.act_window',
                    'context': {'default_vehicle_id': rec.goods_recieve_report_id.vehicle_id.id,
                                'default_supplier_id': rec.goods_recieve_report_id.supplier_id.id,
                                'default_amount': rec.amount,
                                'goods_receive_line':rec.id,

                                }

                }
            if rec.item_id.tyre:

                return {
                    'name': 'Tyre Entry',
                    'view_type': 'form',
                    'view_mode': 'form',

                    'res_model': 'vehicle.tyre',

                    'type': 'ir.actions.act_window',
                    'context': {'default_vehicle_id': rec.goods_recieve_report_id.vehicle_id.id,
                                'default_supplier': rec.goods_recieve_report_id.supplier_id.id,
                                'default_tyre_cost': rec.amount,
                                'default_purchase_date':rec.goods_recieve_report_id.Date,
                                'goods_receive_line': rec.id,
                                'default_purchase_mileage':rec.goods_recieve_report_id.vehicle_id.odometer,
                                }

                }
            if rec.item_id.tyre_retread:
                return {
                    'name': 'Retread Tyre Entry',
                    'view_type': 'form',
                    'view_mode': 'form',

                    'res_model': 'retreading.tyre.line',

                    'type': 'ir.actions.act_window',
                    'context': {'default_vehicle_id': rec.goods_recieve_report_id.vehicle_id.id,
                                'default_manufacture_id': rec.goods_recieve_report_id.supplier_id.id,
                                'default_retrading_cost': rec.amount,
                                'goods_receive_line': rec.id,
                                'default_retreading_km':rec.goods_recieve_report_id.vehicle_id.odometer,
                                }

                }

            if rec.item_id.gps:
                return {
                    'name': 'GPS Entry',
                    'view_type': 'form',
                    'view_mode': 'form',

                    'res_model': 'vehicle.gps',

                    'type': 'ir.actions.act_window',
                    'context': {'default_vehicle_id': rec.goods_recieve_report_id.vehicle_id.id,
                                'default_supplier_id': rec.goods_recieve_report_id.supplier_id.id,

                                'goods_receive_line': rec.id,
                                'default_purchase_date':rec.goods_recieve_report_id.Date,
                                'default_gps_cost':rec.amount,
                                }

                }
            return True



class OtherChargeDetails(models.Model):
        _name = 'other.charge.details'

        @api.depends('amount')
        def get_total(self):
            for rec in self:
                tax_amt = 0
                cgst = 0
                sgst = 0
                igst = 0
                taxable_amt = 0
                other_charge =0
                if rec.is_tax_applicable:



                    if rec.tax_id.price_include:
                        tax_amt = rec.tax_id.amount
                        if rec.tax_id.tax_type == 'gst':
                            cgst =  ((rec.amount / (1 + tax_amt)) * tax_amt)/2
                            sgst = ((rec.amount / (1 + tax_amt)) * tax_amt) / 2
                        if rec.tax_id.tax_type == 'igst':
                            igst = ((rec.amount / (1 + tax_amt)) * tax_amt)
                    else:

                        if rec.tax_id.tax_type == 'gst':
                            cgst = (rec.amount * rec.tax_id.amount) / 2
                            sgst = (rec.amount*  rec.tax_id.amount) / 2
                        if rec.tax_id.tax_type == 'igst':
                            igst = (rec.amount * rec.tax_id.amount)
                    taxable_amt = rec.amount / (1 + tax_amt)
                else:
                    other_charge = rec.amount
                rec.taxable_amount = taxable_amt
                rec.cgst_amount = cgst
                rec.sgst_amount = sgst
                rec.igst_amount = igst
                rec.total_amount = other_charge + taxable_amt + cgst + sgst +igst

        other_charge_id = fields.Many2one('other.charge',"Other charge")
        is_tax_applicable= fields.Boolean("GST Applicable",default=False)
        tax_id = fields.Many2one('account.tax',"Tax",domain="[('parent_id','=',False)]")
        amount = fields.Float("Amount")
        taxable_amount = fields.Float("Taxable Amount",compute='get_total',store=True)

        cgst_amount = fields.Float("CGST Amount", compute='get_total', store=True)
        sgst_amount = fields.Float("SGST Amount", compute='get_total', store=True)
        igst_amount = fields.Float("IGST Amount", compute='get_total', store=True)

        total_amount = fields.Float("Total Amount",compute='get_total',store=True)
        goods_recieve_report_id = fields.Many2one('goods.recieve.report',"Goods ")



class OtherCharge(models.Model):
        _name='other.charge'

        name=fields.Char("Name")