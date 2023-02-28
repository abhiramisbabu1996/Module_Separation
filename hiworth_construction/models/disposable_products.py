from openerp import fields, models, api
from openerp.exceptions import except_orm, ValidationError
from openerp.tools.translate import _

class DisposableProducts(models.Model):
    _name = 'disposable.products'

    @api.model
    def create(self, vals):
        res = super(DisposableProducts, self).create(vals)

        res.name = str(self.env['ir.sequence'].next_by_code('dispose.code'))

        return res

    @api.model
    def default_get(self, fields_list):
        res = super(DisposableProducts, self).default_get(fields_list)

        res.update(
            {'source_location_id': self.env['stock.location'].search([('is_warehouse', '=', True)], limit=1).id})
        return res

    @api.onchange('project_id')
    def onchange_project(self):
        for rec in self:
            if rec.project_id:
                return {'domain': {'location_id': [('id', 'in', rec.project_id.project_location_ids.ids)]}}

    name=fields.Char("Disposable Name")
    date = fields.Datetime('Date', default=lambda self: fields.datetime.now())
    project_id = fields.Many2one('project.project', 'Project')
    employee_id = fields.Many2one('hr.employee', 'Supervisor')
    location_id = fields.Many2one('stock.location', "Location")
    state = fields.Selection([('draft', 'Draft'),
                              ('disposed', 'Disposed')], default='draft', String="Status")
    category_ids = fields.Many2many('product.category', 'disposable_products_category_rel', 'category_id',
                                    'disposable_id', "Category")
    picking_id = fields.Many2one('stock.picking',"Picking")
    state = fields.Selection([('draft', 'Draft'),
                              ('request', 'Request'),
                              ('approved', 'Approved By Manager'),
                              ('done', 'Done')], default='draft', string="Status")

    account_move_id = fields.Many2one('account.move', "Account Entry")
    source_location_id = fields.Many2one('stock.location', "Source Location")
    dispoable_product_line_ids = fields.One2many('disposable.products.line','disposable_product_id',"Item Details")

    @api.multi
    def button_request(self):
        for res in self:
            res.state = 'request'

    @api.multi
    def button_approve(self):
        for res in self:
            res.state = 'approved'

    @api.multi
    def action_dispose(self):
        for rec in self:
            journal_id = self.env['account.journal'].search([('type', '=', 'general'), ('code', '=', 'STJ')])
            location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)
            stock = self.env['stock.picking'].create({

                'source_location_id': rec.source_location_id.id,

                'site': rec.project_id.id,
                'order_date': rec.date,
                'account_id': rec.source_location_id.related_account.id,
                'supervisor_id': rec.employee_id.id,
                'is_purchase': False,
                'journal_id': journal_id.id,
                'project_id': rec.project_id.id,
            })
            self.picking_id = stock.id
            total = 0
            for req in rec.dispoable_product_line_ids:
                total += req.rate
                stock_move = self.env['stock.move'].create({
                    'location_id': self.source_location_id.id,
                    'date': rec.date,
                    'category_id':req.item_id.categ_id.id,
                    'date_expected': rec.date,
                    'project_id': rec.project_id.id,
                    'product_id': req.item_id.id,
                    'available_qty': req.available_quantity,
                    'name': req.desc,
                    'product_uom_qty': req.quantity,
                    'product_uom': req.unit_id.id,
                    'price_unit': (req.rate/req.quantity),
                    'account_id': rec.source_location_id.related_account.id,
                    'location_dest_id': location.id,
                    'picking_id': stock.id
                })
                stock_move.action_done()
                req.move_id  = stock_move.id
                for line in req.rate_disposable_line_ids:
                    line.move_id.select_qty = line.move_id.select_qty + line.select_qty

            stock.action_done()
            move_line_list = []
            move_line_list.append((0, 0, {'name': self.location_id.name,
                                          'account_id': self.location_id.related_account.id,
                                          'credit': 0,
                                          'debit': total,
                                          }))
            move_line_list.append((0, 0, {'name': self.source_location_id.name,
                                          'account_id': self.source_location_id.related_account.id,
                                          'credit': total,
                                          'debit': 0,
                                          }))
            move = {
                'journal_id': journal_id.id,
                'date': self.date,
                'line_id': move_line_list
            }

            move_obj = self.env['account.move'].create(move)
            self.account_move_id = move_obj.id

            rec.state = 'done'



class DisposableProductsLine(models.Model):
    _name='disposable.products.line'


    @api.multi
    def process_view_price(self):
        for rec in self:
            stock_history = self.env['stock.history'].search([('product_id', '=', rec.item_id.id), (
            'location_id', '=', rec.disposable_product_id.source_location_id.id),
                                                              ('date', '<=', rec.disposable_product_id.date),
                                                              ('quantity', '>', 0)], order='date asc')
            stock_history_zero = self.env['stock.history'].search([('product_id', '=', rec.item_id.id), (
            'location_id', '=', rec.disposable_product_id.source_location_id.id),
                                                                   ('date', '<=', rec.disposable_product_id.date)],
                                                                  order='date asc')

            stock_moves_from_list = []
            stock_moves_to_list = []
            for move_stock in stock_history_zero:
                stock_moves_to_list.append(move_stock.id)


            stock_history_zero = list(stock_history_zero)
            values_list = []
            index_list = []


            for stock in stock_history:
                qty = stock.quantity - stock.move_id.select_qty
                if qty>0:
                    stock_moves_from_list.append({'rem_quantitity': qty, 'move_id': stock.move_id})




            for stock_list in stock_moves_from_list:
                values_list.append((0,0,{'item_id':stock_list['move_id'].product_id.id,
                                         'origin':stock_list['move_id'].origin,
                                         'quantity':stock_list['rem_quantitity'] ,
                                         'unit_price':stock_list['move_id'].price_unit,
                                         'amount':stock_list['move_id'].inventory_value,
                                         'disposable_products_line_id':rec.id,
                                         'move_id':stock_list['move_id'].id}))


            if not rec.rate_disposable_line_ids:
                rec.write({'rate_disposable_line_ids':values_list})



            res = {
                'type': 'ir.actions.act_window',
                'name': 'Rate Details',
                'res_model': 'disposable.products.line',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'res_id':rec.id,


            }

            return res


    @api.onchange('item_id')
    def onchange_item(self):
        for rec in self:
            if rec.item_id:
                rec.desc = rec.item_id.name
                rec.unit_id = rec.item_id.uom_id.id


                stock_history = self.env['stock.history'].search([('product_id', '=', rec.item_id.id), ('location_id', '=', rec.disposable_product_id.source_location_id.id),
                                                                  ('date', '<=', rec.disposable_product_id.date)])
                qty = 0
                for stock in stock_history:
                    qty += stock.quantity
                rec.available_quantity = qty
        product_list = []
        if self._context.get('source_location', False) and self._context.get('category_id', False):

            location = self.env['stock.location'].browse(self._context.get('source_location', False))
            category = self._context.get('category_id', False)

            history = self.env['stock.history'].search(
                [('location_id', '=', location.id), ('product_categ_id', 'in', category[0][2]),
                 ('date', '<=', rec.disposable_product_id.date)])

            for his in history:
                product_list.append(his.product_id.id)

        return {'domain': {'item_id': [('id', 'in', product_list)]}}

    @api.depends('quantity', 'rate')
    def compute_amount(self):
        for rec in self:

            rec.amount = rec.quantity * rec.rate

    @api.constrains('available_quantity')
    def check_available_quantity(self):
        for rec in self:
            if rec.available_quantity <= 0:
                raise ValidationError(_('%s Out of Stock' % (rec.item_id.name)))

    @api.depends('quantity', )
    def compute_rem_qty(self):
        for rec in self:
            rec.rem_qty = rec.available_quantity - rec.quantity

    @api.constrains('quantity','available_quantity')
    def check_required_quantity(self):
        for rec in self:
            if rec.available_quantity < rec.quantity:
                raise ValidationError(_('Disposable quantity greater than available quantity'))



    item_id = fields.Many2one('product.product', string="Product")
    available_quantity = fields.Float(string="Stock Balance")
    quantity = fields.Float(string="Disposable Quantity")
    unit_id = fields.Many2one('product.uom')
    desc = fields.Char(string="Description")
    remarks = fields.Text(string="Remarks")
    disposable_products_id = fields.Many2one('disposable.products', string="Item List")
    rate = fields.Float('Amount')
    rem_qty = fields.Float('Remaining Quantity', compute='compute_rem_qty')
    amount = fields.Float('Amount', compute='compute_amount',store=True)
    move_id = fields.Many2one('stock.move',"Stock Move")
    disposable_product_id = fields.Many2one('disposable.products')
    rate_disposable_line_ids = fields.One2many('rate.disposable.line','disposable_products_line_id',"Item Rate details")

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


class RateDisposableLine(models.Model):
    _name = 'rate.disposable.line'

    item_id = fields.Many2one('product.product',"Product")
    origin = fields.Char("Origin")
    quantity = fields.Float("Product Quantity")
    select_qty = fields.Float("Select Quantity")
    unit_price = fields.Float("Unit Price")
    amount = fields.Float("Amount")
    disposable_products_line_id = fields.Many2one('disposable.products.line',)
    calcu = fields.Text("Calculation")
    move_id = fields.Many2one('stock.move',"Move")
    material_cost_transfer_line_id = fields.Many2one('material.cost.transfer.line',"Material Cost Transfer")
    material_issue_slip_line_id = fields.Many2one('material.isuue.slip.line')

    @api.constrains('quantity','select_qty')
    def check_quantity(self):
        for rec in self:
            if rec.quantity < rec.select_qty:
                raise ValidationError(_('Product quantity greater than Select quantity'))