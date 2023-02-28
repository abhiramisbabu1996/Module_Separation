from openerp import fields, models, api
from openerp.exceptions import except_orm, ValidationError
from openerp.tools.translate import _

class MaterialCostTransfer(models.Model):
    _name = 'material.cost.transfer'

    @api.model
    def create(self, vals):
        res = super(MaterialCostTransfer, self).create(vals)

        res.name = str(self.env['ir.sequence'].next_by_code('mct.code'))

        return res

    @api.model
    def default_get(self, fields_list):
        res = super(MaterialCostTransfer, self).default_get(fields_list)

        res.update(
            {'source_location_id': self.env['stock.location'].search([('is_warehouse', '=', True)], limit=1).id})
        return res

    @api.onchange('project_id')
    def onchange_project(self):
        for rec in self:
            if rec.project_id:
                return {'domain': {'location_id': [('id', 'in', rec.project_id.project_location_ids.ids)]}}

    name = fields.Char('Name')
    date = fields.Datetime('Date', default=lambda self: fields.datetime.now())
    project_id = fields.Many2one('project.project', 'Project')
    employee_id = fields.Many2one('hr.employee', 'Supervisor')
    source_location_id = fields.Many2one('stock.location', "Source Location",)
    location_id = fields.Many2one('stock.location', "Location")
    material_cost_transfer_lines_ids = fields.One2many('material.cost.transfer.line', 'material_cost_transfer_id',
                                                    string="Item List")
    user_id = fields.Many2one('res.users', "Users")
    store_manager_id = fields.Many2one('res.users', "Supervisor")
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')], default='draft', string="Status")
    category_ids = fields.Many2many('product.category', 'material_cost_transfer_category_rel', 'category_id',
                                    'material_cost_transfer_id', "Category")
    picking_id = fields.Many2one('stock.picking',"Picking")
    state = fields.Selection([('draft', 'Draft'),
                              ('request','Request'),
                              ('approved','Approved By Manager'),
                              ('done', 'Done')], default='draft', string="Status")

    account_move_id = fields.Many2one('account.move',"Account Entry")
    vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle")

    @api.multi
    def button_request(self):
        for res in self:
            res.state = 'request'

    @api.multi
    def button_approve(self):
        for res in self:
            res.state = 'approved'

    @api.multi
    def action_receive(self):
        for rec in self:
            journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
            location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
            stock = self.env['stock.picking'].create({

                'source_location_id': self.source_location_id.id,

                'site': rec.location_id.id,
                'order_date': rec.date,
                'account_id': rec.location_id.related_account.id,
                'supervisor_id': self.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': rec.project_id.id,
            })
            total = 0
            for req in rec.material_cost_transfer_lines_ids:
                total += req.rate
                stock_move = self.env['stock.move'].create({
                    'location_id': self.source_location_id.id,
                    'category_id':req.item_id.categ_id.id,
                    'date': rec.date,
                    'date_expected': rec.date,
                    'project_id': rec.project_id.id,
                    'product_id': req.item_id.id,
                    'available_qty': req.item_id.with_context(
                        {'location': self.source_location_id.id}).qty_available,
                    'name': req.desc,
                    'product_uom_qty': req.quantity,
                    'product_uom': req.unit_id.id,
                    'price_unit': (req.rate/req.quantity),
                    'account_id': rec.location_id.related_account.id,
                    'location_dest_id': location.id,
                    'picking_id': stock.id
                })
                stock_move.action_done()
                req.move_id = stock_move.id
                for line in req.rate_disposable_line_ids:
                    line.move_id.select_qty = line.move_id.select_qty + line.select_qty


            stock.action_done()
            self.picking_id = stock.id
            move_line_list = []
            if self.location_id:

                move_line_list.append((0, 0, {'name': self.location_id.name,
                                              'account_id': self.location_id.related_account.id,
                                              'credit': 0,
                                              'debit': total,
                                              }))
            for move_goods in  self.material_cost_transfer_lines_ids:
                move_line_list.append((0, 0, {'name': move_goods.item_id.name,
                                              'account_id': move_goods.item_id.property_account_expense.id,
                                              'credit': move_goods.rate,
                                              'debit': 0,
                                              }))
            if self.vehicle_id:
                move_line_list.append((0, 0, {'name': self.vehicle_id.name,
                                              'account_id': self.vehicle_id.related_account.id,
                                              'credit': 0,
                                              'debit': total,
                                              }))
                move = {
                    'journal_id':journal_id.id,
                    'date': self.date,
                    'line_id': move_line_list
                }

                move_obj = self.env['account.move'].create(move)
                self.account_move_id = move_obj.id

            rec.state = 'done'

class MaterialCostTransferLine(models.Model):
    _name = 'material.cost.transfer.line'

    @api.onchange('item_id')
    def onchange_date(self):
        for rec in self:

            if rec.item_id:
                rec.desc = rec.item_id.name
                rec.unit_id = rec.item_id.uom_id.id

                stock_history = self.env['stock.history'].search([('product_id', '=', rec.item_id.id), (
                'location_id', '=', rec.material_cost_transfer_id.source_location_id.id),
                                                                  ('date', '<=', rec.material_cost_transfer_id.date)])
                qty = 0
                for stock in stock_history:
                    qty += stock.quantity
                rec.available_quantity = qty

        if self._context.get('source_location', False) or self._context.get('category_id', False):

            location = self.env['stock.location'].browse(self._context.get('source_location', False))
            category = self._context.get('category_id', False)

            history = self.env['stock.history'].search(
                [('location_id', '=', location.id), ('product_categ_id', 'in', category[0][2]),
                 ('date', '<=', rec.material_cost_transfer_id.date)])
            product_list = []
            for his in history:
                product_list.append(his.product_id.id)

            return {'domain': {'item_id': [('id', 'in', product_list)]}}

    @api.constrains('available_quantity')
    def check_available_quantity(self):
        for rec in self:
            if rec.available_quantity <= 0:
                raise ValidationError(_('%s Out of Stock' % (rec.item_id.name)))


    @api.constrains('quantity', 'available_quantity')
    def check_required_quantity_stock(self):
        for rec in self:

            if rec.available_quantity < rec.quantity:
                raise ValidationError(_('Issued quantity greater than  available quantity'))



    @api.depends('quantity',)
    def compute_rem_qty(self):
        for rec in self:
            rec.rem_qty = rec.available_quantity - rec.quantity

    @api.depends('quantity', 'rate')
    def compute_amount(self):
        for rec in self:

            rec.amount = rec.quantity * rec.rate




    material_cost_transfer_id = fields.Many2one('material.cost.transfer',"Material Cost Transfer")
    item_id = fields.Many2one('product.product', string="Product")
    available_quantity = fields.Float(string="Stock Balance")
    quantity = fields.Float(string="Quantity")
    unit_id = fields.Many2one('product.uom')
    desc = fields.Char(string="Description")
    remarks = fields.Text(string="Remarks")
    rate = fields.Float('Amount')
    amount = fields.Float('Amount', compute='compute_amount')

    rem_qty = fields.Float('Remaining Quantity', compute='compute_rem_qty')
    move_id = fields.Many2one('stock.move',"Stock Move")
    rate_disposable_line_ids = fields.One2many('rate.disposable.line', 'material_cost_transfer_line_id',
                                               "Item Rate details")

    @api.multi
    def action_submit(self):
        for rec in self:
            qty = 0
            unit_price = 0
            for line in rec.rate_disposable_line_ids:
                qty += line.select_qty
                unit_price += line.select_qty * line.unit_price
            if qty > rec.quantity:
                raise ValidationError(_('Disposable quantity greater than Select quantity'))
            rec.rate = unit_price

    @api.multi
    def process_view_price(self):
        for rec in self:
            stock_history = self.env['stock.history'].search([('product_id', '=', rec.item_id.id), ('location_id', '=', rec.material_cost_transfer_id.source_location_id.id),
                                                              ('date', '<=', rec.material_cost_transfer_id.date),('quantity','>',0)],order='date asc')
            stock_history_zero = self.env['stock.history'].search([('product_id', '=', rec.item_id.id), ('location_id', '=', rec.material_cost_transfer_id.source_location_id.id),
                                                              ('date', '<=', rec.material_cost_transfer_id.date)],order='date asc')

            stock_moves_from_list = []
            stock_moves_to_list = []
            for move_stock in stock_history_zero:
                stock_moves_to_list.append(move_stock.id)



            stock_history_zero = list(stock_history_zero)
            values_list = []
            index_list = []
            for stock in stock_history:
                qty = stock.quantity - stock.move_id.select_qty
                if qty > 0:
                    stock_moves_from_list.append({'rem_quantitity': qty, 'move_id': stock.move_id})

            for stock_list in stock_moves_from_list:
                values_list.append((0, 0, {'item_id': stock_list['move_id'].product_id.id,
                                           'origin': stock_list['move_id'].origin,
                                           'quantity': stock_list['rem_quantitity'],
                                           'unit_price': stock_list['move_id'].price_unit,
                                           'amount': stock_list['move_id'].inventory_value,
                                           'material_cost_transfer_line_id': rec.id ,
                                           'move_id':stock_list['move_id'].id}))

            if not rec.rate_disposable_line_ids:
                rec.write({'rate_disposable_line_ids': values_list})

            res = {
                'type': 'ir.actions.act_window',
                'name': 'Rate Details',
                'res_model': 'material.cost.transfer.line',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'res_id': rec.id,

            }

            return res
