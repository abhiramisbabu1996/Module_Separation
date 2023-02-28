from openerp import fields, models, api
from datetime import datetime
from openerp.exceptions import Warning as UserError
from openerp.osv import osv
from openerp.tools.translate import _
from dateutil import relativedelta
from openerp.exceptions import except_orm, ValidationError


class MaterialIssueSlip(models.Model):
    _name = 'material.issue.slip'
    _order = 'date desc'



    def action_purchase_receipts(self):
        categories = self.env['purchase.order'].search([('location_id', '=',self.env['stock.location'].search([('is_warehouse','=',True)],limit=1).id)]).ids
        return {
            'name': 'Purchase Orders',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', categories),('state','in',['approved','done']),('merged_po','=',False)],
            'res_model': 'purchase.order',
            'target': 'current'
        }

    def action_merge_purchase_order(self):
        categories = self.env['purchase.order'].search([('location_id', '=',self.env['stock.location'].search([('is_warehouse','=',True)],limit=1).id)]).ids
        return {
            'name': 'Merged - Purchase Orders',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', categories),('merged_po','=',True)],
            'res_model': 'purchase.order',
            'target': 'current'
        }

    def action_goods_receipts(self):
        categories = self.env['goods.recieve.report'].search([('site', '=',self.env['stock.location'].search([('is_warehouse','=',True)],limit=1).id)]).ids
        return {
            'name': 'Goods Receipt & Invoice Entry',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', categories)],
            'res_model': 'goods.recieve.report',
            'target': 'current'
        }

    @api.model
    def default_get(self, fields_list):
        res = super(MaterialIssueSlip, self).default_get(fields_list)
        if not res.get('is_receive',False):
            res.update({'source_location_id':self.env['stock.location'].search([('is_warehouse','=',True)],limit=1).id})
        else:
            res.update({'location_id':self.env['stock.location'].search([('is_warehouse','=',True)],limit=1).id})
        return res

    @api.onchange('project_id')
    def onchange_project(self):
        for rec in self:

            if rec.is_receive:
                if rec.project_id:
                    return {'domain':{'source_location_id':[('id','in',rec.project_id.project_location_ids.ids)]}}
            else:
                if rec.project_id:
                    return {'domain':{'location_id':[('id','in',rec.project_id.project_location_ids.ids)]}}

    @api.depends('material_issue_slip_lines_ids')
    def compute_item_list(self):
        for rec in self:
            item = ''
            for lines in rec.material_issue_slip_lines_ids:
                item += lines.item_id.name + ','
            rec.item_list = item

    @api.depends('material_issue_slip_lines_ids')
    def compute_item_qty(self):
        for rec in self:
            quantity = 0
            for lines in rec.material_issue_slip_lines_ids:
                quantity += lines.quantity
            rec.total_quantity = quantity


    @api.multi
    def unlink(self):
        for rec in self:
            if rec.project_id and not rec.is_receive:

                journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
                location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
                stock = self.env['stock.picking'].create({

                    'source_location_id': rec.source_location_id.id,

                    'site': location.id,
                    'order_date': rec.date,
                    'account_id': rec.source_location_id.related_account.id,
                    'supervisor_id': self.env.user.employee_id.id,
                    'is_purchase': False,
                    'journal_id': journal_id.id,
                    'project_id': rec.project_id.id,
                })
                for req in rec.material_issue_slip_lines_ids:
                    stock_move = self.env['stock.move'].create({
                        'location_id': rec.source_location_id.id,
                        'project_id': rec.project_id.id,
                        'product_id': req.item_id.id,
                        'available_qty': req.item_id.with_context(
                            {'location': rec.source_location_id.id}).qty_available,
                        'name': req.desc,
                        'product_uom_qty': req.req_qty,
                        'product_uom': req.unit_id.id,
                        'date': rec.date,
                        'date_expected': rec.date,
                        'price_unit': 1,
                        'account_id': rec.source_location_id.related_account.id,
                        'location_dest_id': self.location_id.id,
                        'picking_id': stock.id
                    })
                    stock_move.action_done()
            if rec.is_receive and rec.project_id:
                journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
                location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
                stock = self.env['stock.picking'].create({

                    'source_location_id':self.location.id,

                    'site': rec.source_location_id.id,
                    'order_date': rec.date,
                    'account_id': rec.source_location_id.related_account.id,
                    'supervisor_id': self.env.user.employee_id.id,
                    'is_purchase': False,
                    'journal_id': journal_id.id,
                    'project_id': rec.project_id.id,
                })
                for req in rec.material_issue_slip_lines_ids:
                    stock_move = self.env['stock.move'].create({
                        'location_id': self.location.id,
                        'project_id': rec.project_id.id,
                        'product_id': req.item_id.id,
                        'available_qty': req.item_id.with_context(
                            {'location': res.source_location_id.id}).qty_available,
                        'name': req.desc,
                        'product_uom_qty': req.req_qty,
                        'product_uom': req.unit_id.id,
                        'price_unit': 1,
                        'date': rec.date,
                        'date_expected': rec.date,
                        'account_id': rec.source_location_id.related_account.id,
                        'location_dest_id': rec.source_location_id.id,
                        'picking_id': stock.id
                    })
                    stock_move.action_done()

        return super(MaterialIssueSlip, self).unlink()



    name = fields.Char('Name')
    date = fields.Datetime('Date', default=lambda self: fields.datetime.now())
    project_id = fields.Many2one('project.project','Project')
    employee_id = fields.Many2one('hr.employee', 'Supervisor')
    source_location_id = fields.Many2one('stock.location',"Source Location")
    location_id = fields.Many2one('stock.location',"Location")
    material_issue_slip_lines_ids = fields.One2many('material.issue.slip.line','material_issue_slip_id',string="Item List")

    grr_no_id = fields.Many2one('goods.recieve.report','GRR NO')
    user_id = fields.Many2one('res.users',"Users")
    store_manager_id = fields.Many2one('res.users',"Supervisor")
    is_debit_note = fields.Boolean("Is a Debit Note",default=False)
    is_receive = fields.Boolean("Receive")
    item_list = fields.Char(string="Items", compute='compute_item_list')
    total_quantity = fields.Char(string="Quantity", compute='compute_item_qty')
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle No")
    state = fields.Selection([('draft','Draft'),
                              ('done','Done')],default='draft',string="Status")
    category_ids = fields.Many2many('product.category','material_issue_category_rel','category_id','material_issue_id',"Category")


    @api.multi
    def action_receive(self):
        for rec in self:
            journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
            location = self.env['stock.location'].search([('usage','=','inventory')],limit=1)
            stock = self.env['stock.picking'].create({

                'source_location_id': self.location_id.id,

                'site': rec.source_location_id.id,
                'order_date': rec.date,
                'account_id': rec.source_location_id.related_account.id,
                'supervisor_id': self.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': rec.project_id.id,
            })


            for req in rec.material_issue_slip_lines_ids:

                stock_move = self.env['stock.move'].create({
                    'location_id':rec.source_location_id.id ,
                    'date':rec.date,
                    'date_expected':rec.date,
                    'project_id': rec.project_id.id,
                    'product_id': req.item_id.id,
                    'available_qty': req.item_id.with_context(
                        {'location': location.id}).qty_available,
                    'name': req.desc,
                    'product_uom_qty': req.req_qty,
                    'product_uom': req.unit_id.id,
                    'price_unit': (req.rate/req.req_qty),
                    'account_id': rec.source_location_id.related_account.id,
                    'location_dest_id': self.location_id.id,
                    'picking_id':stock.id
                })
                stock_move.action_done()
                for rec_line in req.rate_disposable_line_ids:
                    rec_line.move_id.select_qty = rec_line.move_id.select_qty + rec_line.select_qty

            stock.action_done()
            rec.state = 'done'

    @api.multi
    def button_request(self):
        for res in self:
            journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
            location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
            stock = self.env['stock.picking'].create({

                'source_location_id': res.source_location_id.id,

                'site': self.location_id.id,
                'order_date': res.date,
                'account_id': res.source_location_id.related_account.id,
                'supervisor_id': self.env.user.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': res.project_id.id,
            })

            for req in res.material_issue_slip_lines_ids:
                stock_move = self.env['stock.move'].create({
                    'location_id': res.source_location_id.id,
                    'project_id': res.project_id.id,
                    'product_id': req.item_id.id,
                    'available_qty': req.item_id.with_context(
                        {'location': res.source_location_id.id}).qty_available,
                    'name': req.desc,
                    'product_uom_qty': req.req_qty,
                    'product_uom': req.unit_id.id,
                    'price_unit': (req.rate/req.req_qty),
                    'date': res.date,
                    'date_expected': res.date,
                    'account_id': res.source_location_id.related_account.id,
                    'location_dest_id': self.location_id.id,
                    'picking_id': stock.id
                })
                stock_move.action_done()
                for rec_line in req.rate_disposable_line_ids:
                   rec_line.move_id.select_qty = rec_line.move_id.select_qty + rec_line.select_qty
            stock.action_done()

        self.state = 'done'



    @api.model
    def create(self,vals):
        res =super(MaterialIssueSlip, self).create(vals)
        location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
        if res.is_receive == False:
            # vals.update({'name': 'MRN' + str(self.env['ir.sequence'].next_by_code('mrn.code'))})
            res.name = str(self.env['ir.sequence'].next_by_code('min.code'))


        else:
            # res.project_id.mrn_no+=1
            # mrn_no=str(res.project_id.mrn_no).zfill(3)  +'/'+str(datetime.now().year)
            res.name = str(self.env['ir.sequence'].next_by_code('mrn.code'))

        return res

    @api.constrains('quantity_rec','po_quantity')
    def constraints_quantity(self):
        if self.po_quantity < self.quantity_rec:
            raise ValidationError(_('Received Quantity cannot be greater than PO Quantity.'))




        return res



                

class MaterialIssuelipLine(models.Model):
    _name = 'material.issue.slip.line'


    @api.onchange('item_id')
    def onchange_date(self):
        for rec in self:
            if rec.material_issue_slip_id.date:
                rec.date = rec.material_issue_slip_id.date
            if rec.item_id:
                rec.desc = rec.item_id.name
                rec.unit_id = rec.item_id.uom_id.id

                stock_history = self.env['stock.history'].search([('product_id','=',rec.item_id.id),('location_id','=',rec.material_issue_slip_id.source_location_id.id),('date','<=',rec.material_issue_slip_id.date)])
                qty = 0
                for stock in stock_history:
                    qty += stock.quantity
                rec.available_quantity =qty

        if self._context.get('source_location',False) or self._context.get('category_id',False):
          
            location = self.env['stock.location'].browse(self._context.get('source_location',False))
            category = self._context.get('category_id',False)
      
            history = self.env['stock.history'].search([('location_id','=',location.id),('product_categ_id','in',category[0][2]) ,('date','<=',rec.material_issue_slip_id.date)])
            product_list = []
            for his in history:
                product_list.append(his.product_id.id)

            return {'domain':{'item_id':[('id','in',product_list)]}}


    
    @api.constrains('available_quantity')
    def check_available_quantity(self):
        for rec in self:
            if rec.available_quantity<=0:
                raise ValidationError(_('%s Out of Stock'%(rec.item_id.name)))



    @api.constrains('req_qty')
    def check_required_quantity(self):
        for rec in self:
            if not rec.material_issue_slip_id.is_receive:
                if rec.quantity < rec.req_qty:
                    raise ValidationError(_('Issued quantity greater than requested quantity'))

    @api.constrains('req_qty','available_quantity')
    def check_required_quantity_stock(self):
        for rec in self:
            if not rec.material_issue_slip_id.is_receive:
                if rec.available_quantity < rec.req_qty:
                    raise ValidationError(_('Issued quantity greater than  available quantity'))


    @api.onchange('project_id')
    def onchange_product(self):
        for rec in self:
            if rec.material_issue_slip_id.project_id:
                rec.project_id = rec.material_issue_slip_id.project_id
                


    @api.depends('quantity','req_qty')
    def compute_rem_qty(self):
        for rec in self:
            rec.rem_qty =  rec.available_quantity - rec.req_qty


    @api.depends('quantity','rate')
    def compute_amount(self):
        for rec in self:
            if rec.material_issue_slip_id.is_receive:
                rec.amount = rec.req_qty * rec.rate
            else:
                rec.amount = rec.quantity * rec.rate




    item_id = fields.Many2one('product.product',string="Product")
    available_quantity = fields.Float(string="Stock Balance")
    quantity = fields.Float(string="Requested Quantity")
    unit_id = fields.Many2one('product.uom')
    desc = fields.Char(string="Description")
    remarks = fields.Text(string="Remarks")
    material_issue_slip_id = fields.Many2one('material.issue.slip',string="Material Issue Slip")
    date = fields.Date('Date')
    project_id = fields.Many2one('project.project')

    rate = fields.Float('Amount')
    amount = fields.Float('Amount',compute='compute_amount')
    req_qty = fields.Float('Received Quantity')
    rem_qty = fields.Float('Remaining Quantity',compute='compute_rem_qty')
    mrn_no = fields.Char(string='MRN NO',related = "material_issue_slip_id.name")
    date_export =  fields.Datetime('Date',related = "material_issue_slip_id.date")
    project_id_export = fields.Many2one(string="Project" ,related = "material_issue_slip_id.project_id")
    source_location_id = fields.Many2one(string="Project Store" ,related = "material_issue_slip_id.source_location_id")
    employee_id = fields.Many2one(string="Reciever" ,related = "material_issue_slip_id.employee_id")
    location_id = fields.Many2one(string="Chainage" ,related = "material_issue_slip_id.location_id")
    rate_disposable_line_ids = fields.One2many('rate.disposable.line', 'material_issue_slip_line_id',
                                               "Item Rate details")

    @api.multi
    def process_view_price(self):
        for rec in self:
            stock_history = self.env['stock.history'].search([('product_id', '=', rec.item_id.id), (
                'location_id', '=', rec.material_issue_slip_id.source_location_id.id),
                                                              ('date', '<=', rec.material_issue_slip_id.date),
                                                              ('quantity', '>', 0)], order='date asc')


            stock_moves_from_list = []
            stock_moves_to_list = []

            values_list = []
            index_list = []

            for stock in stock_history:
                qty = stock.quantity - stock.move_id.select_qty
                if qty>0:

                    stock_moves_from_list.append({'rem_quantitity': qty, 'move_id': stock.move_id})

            for stock_list in stock_moves_from_list:
                values_list.append((0, 0, {'item_id': stock_list['move_id'].product_id.id,
                                           'origin': stock_list['move_id'].origin,
                                           'quantity': stock_list['rem_quantitity'],
                                           'unit_price': stock_list['move_id'].price_unit,
                                           'amount': stock_list['move_id'].inventory_value,
                                           'material_issue_slip_line_id': rec.id,
                                           'move_id': stock_list['move_id'].id}))
            if not rec.rate_disposable_line_ids:
                rec.write({'rate_disposable_line_ids': values_list})

            res = {
                'type': 'ir.actions.act_window',
                'name': 'Rate Details',
                'res_model': 'material.issue.slip.line',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'res_id': rec.id,

            }

            return res

    @api.multi
    def action_submit(self):
        for rec in self:
            qty = 0
            unit_price = 0
            for line in rec.rate_disposable_line_ids:
                qty += line.select_qty
                unit_price += line.select_qty * line.unit_price
            if qty > rec.req_qty:
                raise ValidationError(_('Disposable quantity greater than Select quantity'))
            rec.rate = unit_price
