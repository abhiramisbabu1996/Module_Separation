from openerp import fields, models, api,_
from openerp.exceptions import except_orm,ValidationError

class PurchaseReturn(models.Model):
    _name = "purchase.return"
    _order = 'date desc'

    @api.model
    def default_get(self, fields_list):
        res = super(PurchaseReturn, self).default_get(fields_list)
        journal = self.env['account.journal'].search([('type', '=', 'purchase_refund')], limit=1, order='id asc')
        res.update({'journal': journal.id})
        return res

    @api.model
    def create(self, vals):

        if vals.get('name', False) == False:
            location_id = self.env['stock.location'].search([('usage', '=', 'supplier')], order='id asc', limit=1)
            vals['supplier_location_id'] = location_id.id
        order = super(PurchaseReturn, self).create(vals)
        order.name = str(self.env['ir.sequence'].next_by_code('dn.code'))

        journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
        # location_id = self.env['stock.location'].search([('usage','=','supplier')])
        # order.supplier_location_id = location_id.id
        for rec in order:

            stock = self.env['stock.picking'].create({

                'source_location_id':rec.site.id ,

                'site': rec.site.id,
                'order_date': rec.date,
                'account_id': rec.site.related_account.id,
                'supervisor_id': rec.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': rec.project_id.id,
            })
            for line in rec.goods_recieve_report_line_ids:
                stock_move = self.env['stock.move'].create({
                    'location_id': rec.site.id,
                    'project_id': rec.project_id.id,
                    'product_id': line.item_id.id,
                    'available_qty': line.item_id.with_context(
                        {'location': rec.supplier_location_id.id}).qty_available,
                    'name': line.desc,
                    'product_uom_qty': line.quantity_accept,
                    'product_uom': line.item_id.uom_id.id,
                    'price_unit': line.rate,
                    'date': rec.date,
                    'date_expected': rec.date,
                    'account_id': rec.site.related_account.id,
                    'location_dest_id': rec.supplier_location_id.id,
                    'picking_id': stock.id
                })
                stock_move.action_done()
                line.move_id = stock_move.id
            stock.action_done()
            rec.picking_id = stock.id
            flag = 1
            amt = 0
            for po in rec.purchase_id.order_line:
                for line in rec.goods_recieve_report_line_ids:

                    amt += line.amount
                    if po.product_id.id == line.item_id.id:

                        po.received_qty = po.received_qty - line.quantity_accept
                        po.returned_qty = po.returned_qty + line.quantity_accept
                        po.received_rate = line.rate
                    if not po.required_qty == (po.received_qty + po.closed_qty - po.returned_qty):
                        flag = 0
            if flag == 0:
                rec.purchase_id.state = 'approved'
                if rec.mpr_id:
                    rec.mpr_id.state = 'order'
                else:
                    for mpr_l in rec.site_purchase_ids:
                        mpr_l.state = 'order'




        move_line_list = []
        if order.total_amount != 0.0:
            move_line_list.append((0, 0, {'name': order.purchase_id.name,
                                          'account_id': order.purchase_id.partner_id.property_account_payable.id,
                                          'credit': 0,
                                          'debit': order.total_amount,
                                          }))

            if not order.vehicle_id:
                move_line_list.append((0, 0, {'name': order.name,
                                              'account_id': order.site.related_account.id,
                                              'credit': order.total_amount,
                                              'debit': 0}))
            else:
                move_line_list.append((0, 0, {'name': order.grr_no,
                                              'account_id': order.vehicle_id.related_account.id,
                                              'credit': order.total_amount,
                                              'debit': 0}))
            move = {
                'journal_id': order.journal.id,
                'date': order.date,
                'line_id': move_line_list
            }

            move_obj = self.env['account.move'].create(move)
            order.account_move_id = move_obj.id

        return order

    @api.depends('other_charge_details_ids', 'goods_recieve_report_line_ids', 'round_off_amount')
    def compute_amount(self):
        for rec in self:
            taxable_amount = 0
            igst_amount = 0
            cgst_amount = 0
            sgst_amount = 0
            other_charge = 0
            non_taxable_amount = 0
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
            rec.total_amount = taxable_amount + igst_amount + cgst_amount + sgst_amount + other_charge + non_taxable_amount - rec.round_off_amount

    @api.onchange('purchase_id')
    def onchange_material_procurement(self):
        for rec in self:
            if rec.purchase_id:
                values = []
                prev_list = []

                rec.supplier_id = rec.purchase_id.partner_id.id
                rec.mpr_id = rec.purchase_id.site_purchase_id.id
                rec.site = rec.purchase_id.location_id.id
                rec.project_id = rec.mpr_id.project_id.id
                rec.company_contractor_id = rec.project_id.company_contractor_id.id
                rec.site_purchase_ids = [(6,0,rec.purchase_id.site_purchase_ids.ids)]
                for mpr_lines in rec.purchase_id.order_line:
                    values.append((0, 0, {'item_id': mpr_lines.product_id.id,
                                          'desc': mpr_lines.name,
                                          'tax_ids': [(6, 0, mpr_lines.taxes_id.ids)],
                                          'po_quantity': mpr_lines.received_qty,
                                          'rate': mpr_lines.expected_rate,
                                          'unit_id': mpr_lines.product_uom.id

                                          }))
                    prev_list.append((0, 0, {'item_id': mpr_lines.product_id.id,
                                             'desc': mpr_lines.name,
                                             'tax_ids': [(6, 0, mpr_lines.taxes_id.ids)],
                                             'po_quantity': mpr_lines.received_qty,
                                             'quantity_accept': mpr_lines.returned_qty,

                                             'rate': mpr_lines.expected_rate,
                                             'unit_id': mpr_lines.product_uom.id

                                             }))
                rec.goods_recieve_report_line_ids = values
                rec.previous_goods_receipt_entries_ids = prev_list

    name = fields.Char("Name")
    date = fields.Date("Date",default=lambda self: fields.datetime.now())
    project_id = fields.Many2one('project.project', 'Project', track_visibility='onchange')
    supplier_id = fields.Many2one('res.partner', 'Supplier', track_visibility='onchange')
    supplier_location_id = fields.Many2one('stock.location', 'Location', track_visibility='onchange')
    site = fields.Many2one('stock.location', 'Project Location', required=True, track_visibility='onchange')
    mpr_id = fields.Many2one('site.purchase', "Purchase Request No", domain="[('state','=','order')]")
    purchase_id = fields.Many2one('purchase.order', 'PO No', domain="[('state','in',['approved','done'])]")
    picking_id = fields.Many2one('stock.picking', "Picking")
    journal = fields.Many2one('account.journal', 'Journal')
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    account_move_id = fields.Many2one('account.move', "Move")
    other_charge_details_ids = fields.One2many('other.charge.details.purchase', 'goods_recieve_report_id',
                                               "Other Charge Details")

    taxable_amount = fields.Float("Taxable amount", compute='compute_amount', store=True)
    total_amount = fields.Float("Total amount", compute='compute_amount', store=True)
    other_charge = fields.Float("Other Charge", compute='compute_amount', store=True)
    cgst_amount = fields.Float("CGST Amount", compute='compute_amount', store=True)
    sgst_amount = fields.Float("SGST Amount", compute='compute_amount', store=True)
    igst_amount = fields.Float("IGST Amount", compute='compute_amount', store=True)
    non_taxable_amount = fields.Float("Non-Taxable Amount", compute='compute_amount', store=True)
    round_off_amount = fields.Float("Round Off Amount")
    company_contractor_id = fields.Many2one('res.partner',string="Company")
    previous_goods_receipt_entries_ids = fields.One2many('purchase.return.line', 'prev_goods_recieve_report_id',
                                                         "Previous Entries")
    goods_recieve_report_line_ids = fields.One2many('purchase.return.line', 'goods_recieve_report_id')

    site_purchase_ids = fields.Many2many('site.purchase', 'purchase_return_site_purchase_rel', 'return_id',
                                         'site_purchase_id', "Purchase Requests")
class PurchaseReturnLine(models.Model):
    _name = "purchase.return.line"

    @api.onchange('item_id')
    def onchange_item_id(self):
        for rec in self:
            if rec.item_id:
                rec.desc = rec.item_id.name
                rec.unit_id = rec.item_id.uom_id.id
                rec.brand_name = rec.item_id.brand_name.id

    @api.onchange('tax_ids')
    def onchange_tax_ids(self):
        for rec in self:
            taxl = []
            if rec.tax_ids:
                for tax in rec.tax_ids:
                    if tax.parent_id:
                        tax_ids = self.env['account.tax'].search([('parent_id', '=', tax.parent_id.id)])
                        rec.tax_ids = [(6, 0, tax_ids.ids)]
    @api.one
    @api.constrains('quantity_accept', 'po_quantity')
    def constraints_quantity(self):
        for rec in self:
            if rec.po_quantity < rec.quantity_accept:
                print "ppppppppppppppppoooooooooooooooooooooooooooooooo",self.po_quantity,self.quantity_accept
                raise ValidationError(_('Returning Quantity cannot be greater than the P.O Quantity.'))


    @api.depends('rate', 'quantity_accept', 'tax_ids')
    def compute_total_amount(self):
        for rec in self:
            tax_amt = 0
            cgst = 0
            sgst = 0
            igst = 0
            non_tax = 0
            if rec.tax_ids:
                for tax in rec.tax_ids:

                    if tax.price_include:
                        tax_amt = tax.amount
                        if tax.tax_type == 'gst':
                            cgst = ((rec.quantity_accept * (rec.rate / (tax_amt + 1))) * tax_amt) / 2
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

            rec.taxable_amount = rec.quantity_accept * (rec.rate / (tax_amt + 1))
            rec.cgst_amount = cgst
            rec.sgst_amount = sgst
            rec.igst_amount = igst
            rec.non_taxable_amount = non_tax
            rec.amount = rec.taxable_amount + cgst + sgst + igst

    item_id = fields.Many2one('product.product', 'Material Code')
    desc = fields.Char('Material Name')
    specs = fields.Char('Specification')
    unit_id = fields.Many2one('product.uom', string="Unit of Measure")
    tax_ids = fields.Many2many('account.tax', 'purchase_return_line_tax_rel', 'purchase_return_line_id', 'tax_id',
                               "Tax")
    quantity_rec = fields.Float('Quantity Received')
    quantity_accept = fields.Float('Quantity Returned')
    quantity_reject = fields.Float('Foreclosure Qty')
    rate = fields.Float('Price')
    amount = fields.Float("Amount", compute='compute_total_amount', store=True)
    taxable_amount = fields.Float("Taxable Amount", compute='compute_total_amount', store=True)
    cgst_amount = fields.Float("CGST Amount", compute='compute_total_amount', store=True)
    sgst_amount = fields.Float("SGST Amount", compute='compute_total_amount', store=True)
    igst_amount = fields.Float("IGST Amount", compute='compute_total_amount', store=True)
    non_taxable_amount = fields.Float("Non-Taxable Amount", compute='compute_total_amount', store=True)
    remarks = fields.Char('Remarks')
    goods_recieve_report_id = fields.Many2one('purchase.return', string="Goods Recieve Report")
    date = fields.Date(string="Date")
    po_quantity = fields.Float(string='PO Quantity')
    project_id = fields.Many2one('project.project', 'Project')
    received = fields.Boolean(string="Received", default=False)

    move_id = fields.Many2one('stock.move', "Move")
    prev_goods_recieve_report_id = fields.Many2one('purchase.return', string="Goods Recieve Report")
    brand_name = fields.Many2one('material.brand')


    class OtherChargeDetails(models.Model):
        _name = 'other.charge.details.purchase'

        @api.depends('amount')
        def get_total(self):
            for rec in self:
                tax_amt = 0
                cgst = 0
                sgst = 0
                igst = 0
                taxable_amt = 0
                other_charge = 0
                if rec.is_tax_applicable:

                    if rec.tax_id.price_include:
                        tax_amt = rec.tax_id.amount
                        if rec.tax_id.tax_type == 'gst':
                            cgst = ((rec.amount / (1 + tax_amt)) * tax_amt) / 2
                            sgst = ((rec.amount / (1 + tax_amt)) * tax_amt) / 2
                        if rec.tax_id.tax_type == 'igst':
                            igst = ((rec.amount / (1 + tax_amt)) * tax_amt)
                    else:

                        if rec.tax_id.tax_type == 'gst':
                            cgst = (rec.amount * rec.tax_id.amount) / 2
                            sgst = (rec.amount * rec.tax_id.amount) / 2
                        if rec.tax_id.tax_type == 'igst':
                            igst = (rec.amount * rec.tax_id.amount)
                    taxable_amt = rec.amount / (1 + tax_amt)
                else:
                    other_charge = rec.amount
                rec.taxable_amount = taxable_amt
                rec.cgst_amount = cgst
                rec.sgst_amount = sgst
                rec.igst_amount = igst
                rec.total_amount = other_charge + taxable_amt + cgst + sgst + igst

        other_charge_id = fields.Many2one('other.charge', "Other charge")
        is_tax_applicable = fields.Boolean("GST Applicable", default=False)
        tax_id = fields.Many2one('account.tax', "Tax", domain="[('parent_id','=',False)]")
        amount = fields.Float("Amount")
        taxable_amount = fields.Float("Taxable Amount", compute='get_total', store=True)

        cgst_amount = fields.Float("CGST Amount", compute='get_total', store=True)
        sgst_amount = fields.Float("SGST Amount", compute='get_total', store=True)
        igst_amount = fields.Float("IGST Amount", compute='get_total', store=True)

        total_amount = fields.Float("Total Amount", compute='get_total', store=True)
        goods_recieve_report_id = fields.Many2one('purchase.return', "Goods ")


