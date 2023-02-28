from openerp import fields, models, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.osv import osv

class MaterialRequest(models.Model):
    _name = 'material.request'

    name = fields.Char('Request No',default="/")
    date = fields.Date('Date')
    scheduled_date = fields.Date('Scheduled Date')
    user_id = fields.Many2one('res.users', 'Requested By')
    line_ids = fields.One2many('material.request.line', 'request_id', 'Items')
    note = fields.Text('Note')
    allocation_name = fields.Many2one('stock.picking','Allocation Reference',readonly=True)
    state = fields.Selection([('draft','Draft'),('material_allo','Material Allocation'),('done','Done')],default='draft')

    _defaults = {
        'date': fields.Date.today(),
        'user_id': lambda self, cr, uid, ctx=None: uid,

        }

    @api.multi
    def view_tree_view(self):
        return {
            'name': 'Material Allocation',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('origin','=',self.name)],
            'target': 'current',
            'type': 'ir.actions.act_window',
            'context': {},

        }


    @api.model
    def create(self, vals):
        result = super(MaterialRequest, self).create(vals)
        if result.name == '/':
            result.name = self.env['ir.sequence'].next_by_code('material.request') or '/'        

        return result



    @api.multi
    def action_start(self):
        view_ref = self.env['ir.model.data'].get_object_reference('hiworth_construction', 'view_hiworth_material_allocation_wizard')
        view_id = view_ref[1] if view_ref else False
        res = {
           'type': 'ir.actions.act_window',
           'name': _('Material Allocation'),
           'res_model': 'material.allocation.wizard',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': view_id,
           'target': 'new',
           'context': {'default_rec':self.id,'material_o2m':self.line_ids.ids}
       }
     
        return res


    @api.multi
    def action_done(self):
        if self.allocation_name.state == 'done':
            self.state = 'done'
        else:
            raise osv.except_osv(_('Warning!'),
                        _('It is still in the progress state..!!!!!'))



class MaterialAllocationWizard(models.Model):
    _name = 'material.allocation.wizard'

    rec = fields.Many2one('material.request')
    picking_type_id = fields.Many2one('stock.picking.type','Picking Type',required=True)
    material_o2m = fields.One2many('material.request.line','request_ids')

    @api.onchange('rec')
    def onchange_rec(self):
        if self.rec:
            material_request = []
            for rec in self.rec.line_ids:
                material_request.append((0, 0, {'project_id':rec.project_id.id,
                                                'task_id': rec.task_id.id,
                                                'product_id':rec.product_id.id,
                                                'available_qty':rec.available_qty,
                                                'qty':rec.qty,
                                                'price_unit':rec.price_unit,
                                                'product_uom_id':rec.product_uom_id.id,
                                                'inventory_value':rec.inventory_value,
                                                'location_dest_id':rec.location_dest_id.id}))
            self.material_o2m = material_request
            # self._convert_to_write(self.material_o2m)
            # res = self._convert_to_write(res)
            return

    @api.multi
    def confirm_material_allo(self):
        material_alloc = []
        for line in self.material_o2m:
            material_alloc.append((0, 0, {'project_id':line.project_id.id,
                                                'task_id': line.task_id.id,
                                                'product_id':line.product_id.id,
                                                'available_qty':line.available_qty,
                                                'product_uom_qty':line.qty,
                                                'name':line.product_id.name,
                                                'price_unit':line.price_unit,
                                                'product_uom':line.product_uom_id.id,
                                                'inventory_value':line.inventory_value,
                                                'location_id':line.location_id.id,
                                                'location_dest_id':line.location_dest_id.id,
                                                'company_id':1,
                                                'date_expected':fields.Datetime.now(),
                                                'state':'draft'}))
        all_rqst = self.env['stock.picking'].create({'origin':self.rec.name,'min_date':self.rec.scheduled_date,'picking_type_id':self.picking_type_id.id,
                                            'move_lines':material_alloc})
        self.rec.state = 'material_allo'
        self.rec.allocation_name = all_rqst.id
        return


class MaterialRequestLine(models.Model):
    _name = 'material.request.line'


    @api.onchange('product_id')
    def _onchange_product(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id,
            self.name = self.product_id.name
            self.qty = 1
            self.price_unit = self.product_id.standard_price


    @api.onchange('project_id','task_id')
    def _onchange_project(self):
        product_ids = []
        task_ids = []
        domain = {}
        if self.project_id and not self.task_id:
            for estimation in self.env['project.task.estimation'].search([('project_id','=',self.project_id.id)]):
                if estimation.pro_id.id not in product_ids:
                    product_ids.append(estimation.pro_id.id)
            domain['product_id'] = [('id','in',product_ids)]

        if self.project_id.id:
            self.location_dest_id = self.project_id.location_id
            task_ids = [task.id for task in self.env['project.task'].search([('project_id','=',self.project_id.id)])]
            domain['task_id'] = [('id','in',task_ids)]
        return {
            'domain': domain
        }

    @api.onchange('task_id')
    def _onchange_product_selection(self):
        if self.task_id.id != False:
            product_ids = [estimate.pro_id.id for estimate in self.task_id.estimate_ids]

            self.location_dest_id = self.task_id.project_id.location_id

            return {
                'domain': {
                    'product_id': [('id','in',product_ids)]
                },
            }


    # @api.onchange('qty')
    # def _onchange_qty(self):
    #     super(stock_move, self).onchange_quantity(self.product_id.id, self.qty, self.product_uom, self.product_uos)
    #     estimate = [estimate for estimate in self.task_id.estimate_ids if estimate.pro_id == self.product_id]
    #     if not len(estimate):
    #         return
    #     if (estimate[0].qty - self.qty)<0:
    #         stock_move.extra_quantity = (self.qty-estimate[0].qty)
    #         self.qty = estimate[0].qty
    #         self.is_request_more_btn_visible = True
    #         return {
    #             'warning': {
    #                 'title': 'Warning',
    #                 'message': "Quantity cannot be greater than the quantity assigned for the task. Please increase the quantity from the task."
    #             }
    #         }

    @api.multi
    @api.depends('product_id','qty','price_unit')
    def _compute_inventory_value(self):
        for line in self:
            line.inventory_value = line.price_unit * line.qty



    product_id = fields.Many2one('product.product', 'Product')
    product_uom_id = fields.Many2one('product.uom', 'UOM')
    name = fields.Char('Description')
    available_qty = fields.Float(related='product_id.qty_available', store=True, string='Available Qty')
    qty = fields.Float('Qty')
    price_unit = fields.Float('Unit Price')
    inventory_value = fields.Float(compute='_compute_inventory_value', store=True, string='Inventory Value')
    location_dest_id = fields.Many2one('stock.location', 'Destination')
    project_id = fields.Many2one('project.project', 'Related Project')
    task_id = fields.Many2one('project.task', 'Related Task')
    request_id = fields.Many2one('material.request', 'Request')
    request_ids = fields.Many2one('material.allocation.wizard', 'Request')
    state = fields.Selection([
                            ('draft', 'Draft'),
                            ('request', 'Requested'),
                            ('alloted', 'Alloted'),
                            ('cancel', 'Cancel'),
                            ],default='draft')
    location_id = fields.Many2one('stock.location', 'Source Location')
    allocated_qty = fields.Float('Allocated Qty',compute="_compute_allocated_qty")



    @api.multi
    @api.depends('product_id','qty','project_id','task_id')
    def _compute_allocated_qty(self):
        for line in self:
            if line.product_id:
                rec = self.env['stock.picking'].search([('state','=','done')])
                if rec:
                    for vals in rec:
                        for val in vals.move_lines:
                            if val.project_id.id == line.project_id.id:
                                if val.task_id.id == line.task_id.id:
                                    if val.product_id.id == line.product_id.id:
                                        line.allocated_qty += val.product_uom_qty

                     