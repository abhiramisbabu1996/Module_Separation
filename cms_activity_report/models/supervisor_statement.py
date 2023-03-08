from openerp import fields, models, api
import datetime
from openerp.exceptions import Warning as UserError
from openerp.osv import osv
from openerp.tools.translate import _
from dateutil import relativedelta
from openerp.exceptions import except_orm, ValidationError
import math
# from datetime import date
# from datetime import datetime
import dateutil.parser

# class ReceivedItems(models.Model):
#     _name = 'received.items'
#
#     item_id = fields.Many2one('daily.statement.item', 'Item')
#     brand_name = fields.Many2one('material.brand')
#     quantity_accept = fields.Float('Quantity Accepted')
#     taxable_amount = fields.Float("Taxable amount")
#     sup_daily_statements_id = fields.Many2one('partner.daily.statement',string="Supervisor Daily Statement")
#     received_items_id = fields.Many2one('goods.recieve.report.line',string="Supervisor Daily Statement")
#     rate= fields.Float('Rate')
#     desc = fields.Char('Item Name')

class LabourEmployeeDetails(models.Model):
    _name = 'labour.employee.details.custom'

    supervisor_id = fields.Many2one('hr.employee')
    # item_id = fields.Many2one('daily.statement.item', 'Item')
    remarks = fields.Text('Remarks')
    details_ids = fields.One2many('labours.details.custom', 'labour_id')
    supervisor_statement_id = fields.Many2one('partner.daily.statement')
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    # mep = fields.Selection([('mechanical', 'Mechanical'), ('electricel', 'Electrical'), ('plumbing', 'Plumbing')],
    #                        string="Work Category")
    site_id = fields.Many2one('stock.location', string='Site', related='supervisor_statement_id.location_ids')
    project_id = fields.Many2one('project.project', related='supervisor_statement_id.project_id')

    @api.model
    def create(self, vals):
        res = super(LabourEmployeeDetails, self).create(vals)
        if res.supervisor_id:
            lines = {'labour_name': res.supervisor_id.id,
                     'labour_id': res.id,
                     'site_id': res.site_id.id,
                     'project': res.project_id.id,
                     'end_time': res.end_time,
                     'start_time': res.start_time, }
            res.details_ids.create(lines)
        return res


class LaboursDetails(models.Model):
    _name = 'labours.details.custom'

    labour_id = fields.Many2one('labour.employee.details.custom')
    labour_name = fields.Many2one('hr.employee')
    # labour_name = fields.Many2one('hr.employee', domain=[('attendance_category', '!=', 'office_staff')])
    remarks = fields.Text('Remarks')
    start_time = fields.Datetime()
    end_time = fields.Datetime()
    # position = fields.Selection(related='labour_name.user_category')
    # mep = fields.Selection([('mechanical', 'Mechanical'), ('electricel', 'Electrical'), ('plumbing', 'Plumbing')],
    #                        string="Work Category")
    site_id = fields.Many2one('stock.location', string='Site')
    # site_id = fields.Many2one('stock.location', string='Site', related='labour_id.site_id')
    project = fields.Many2one('project.project', related='labour_id.project_id', store=True)
    date = fields.Date(default=fields.Date.today())


class PartnerDailyStatement(models.Model):
    _name = 'partner.daily.statement'
    _order = 'date desc'




    @api.multi
    def load_recieved_items(self):
        list =[]
        stmt_date = self.date
        print("hiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",stmt_date)

        project_id = self.project_id
        location = self.location_ids
        grr_ids = self.env['goods.recieve.report'].search([('site','=',location.id),('project_id','=',project_id.id)])
        print(grr_ids)
        for item in grr_ids:
            print("date from grr is",item.Date)
            t_date = datetime.datetime.strptime(item.Date, "%Y-%m-%d %H:%M:%S").date()
            print("date extracted is",t_date.strftime("%Y-%m-%d"))
            date_grr = t_date.strftime("%Y-%m-%d")
            if date_grr == stmt_date:
                print("hiyayyayayyaa")
                self.recieved_items_line_ids = item.goods_recieve_report_line_ids.ids


    @api.onchange('project_id')
    def onchange_project(self):
        self.project_task_id = False
        self.location_ids = False
        if self.project_id:
            return {
                'domain': {
                    'project_task_id': [('project_id', '=', self.project_id.id)],
                    'location_ids': [('id', 'in', self.project_id.project_location.ids)],
                    # 'location_ids': [('id', 'in', self.project_id.project_location_ids.ids)],
                },
            }

    @api.onchange('project_id', 'location_ids')
    def onchange_partner_line_ids(self):
        self.partner_line_ids = False
        partner_line_ids = []
        for rec in self:
            if rec.project_id and rec.location_ids:
                statements_ids = self.search(
                    [('project_id', '=', rec.project_id.id), ('location_ids', '=', rec.location_ids.id)])
                for statement in statements_ids:
                    new_partner_line_ids = statement.partner_line_ids.copy()
                    partner_line_ids += new_partner_line_ids.ids
                rec.partner_line_ids = partner_line_ids

    @api.onchange('project_task_id')
    def onchange_project_task_id(self):
        self.project_task_ids = False
        self.project_task_line_ids = False
        project_task_ids = []
        project_task_line_ids = []
        if self.project_task_id:
            statements_ids = self.project_task_id.task_line_ids
            for statement in statements_ids:
                values_dict = statement.read()
                if 'project_task_id' in values_dict[0]:
                    values_dict[0]['project_task_id'] = False
                    project_task_line_ids.append((0, 0, values_dict[0]))
                # self.write({'project_task_line_ids': [(0,0,values_dict[0])]})
                if statement.subcontractor:
                    project_task_ids.append((0, 0, values_dict[0]))
        self.update({'project_task_line_ids': project_task_line_ids})
        self.update({'project_task_ids': project_task_ids})
        self.update({'partner_line_ids': project_task_line_ids})
        return

    @api.depends('employee_id')
    def compute_employee_id(self):
        for rec in self:
            if rec.employee_id:
                balance = 0
                for move_lines in rec.employee_id.petty_cash_account.move_lines:
                    if move_lines.date < rec.date:
                        balance += move_lines.debit
                        balance -= move_lines.credit

                rec.pre_balance = balance
                rec.account_id = rec.employee_id.petty_cash_account.id

    name = fields.Char('Name')
    date = fields.Date('Date', default=datetime.date.today())
    employee_id = fields.Many2one('hr.employee', 'Supervisor')
    account_id = fields.Many2one('account.account', 'Account', compute='compute_employee_id')
    location_ids = fields.Many2one('stock.location', 'Site', domain=[('usage', '=', 'internal')])
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('approved', 'Approved'), ('checked', 'Checked'),
         ('cancelled', 'Cancelled')], default='draft')

    line_ids = fields.One2many('partner.daily.statement.line', 'report_id', 'Lines', domain=[('expense', '!=', True)])
    partner_line_ids = fields.One2many('partner.daily.statement.line', 'report_id')
    labour_details_ids = fields.One2many('labour.employee.details.custom', 'supervisor_statement_id')
    # expense_line_ids = fields.One2many('partner.daily.statement.expense', 'report_id', 'Lines')
    # mou_expense_line_ids = fields.One2many('partner.daily.statement.mou.line', 'report_id', 'Lines')
    # pre_balance = fields.Float('Pre. Balance', compute='compute_employee_id')
    # receipts = fields.Float('Receipts', compute='compute_received_amount')
    # total = fields.Float(compute='compute_total', string='Total')
    # expense = fields.Float(compute='compute_expense', string='Expense')
    # transfer_amount = fields.Float('Transferred Amount', compute="get_transferred_amount")
    # balance = fields.Float(compute='compute_balance', string='Actual Balance')
    # item_usage_lines = fields.One2many('item.usage', 'report_id', string='Materials Used')
    # work_details = fields.Text('Details Of Work Done At Site', required=False)
    # tmrw_work_arrangement = fields.Text(required=False)
    details_rqrd_item = fields.One2many('site.purchase', 'site_id')
    # details_received_item_ids = fields.One2many('goods.recieve.report', 'partner_daily_statement_id')
    details_received_item_ids = fields.Many2many('goods.recieve.report', string='Recieved Items')
    recieved_items_line_ids = fields.Many2many('goods.recieve.report.line', string='Recieved Items')
    # recieved_materials_line_ids = fields.Many2many('received.items', string='Recieved Items')

    # received_ids = fields.One2many('daily.statement.item.received', 'received_id', 'Receptions')
    # next_approver = fields.Many2one('res.users', 'Next Approver', readonly=True)
    # approvers = fields.One2many('supervisor.statement.approvers', 'approver_id', readonly=True)
    # theoretical_balance = fields.Float('Theoretical Balance', compute="compute_balance")
    # reception = fields.Boolean(default=False, compute="get_reception_trenafer")
    # transfer = fields.Boolean(default=False, compute="get_reception_trenafer")
    # rent_vehicle = fields.Float('Rent Vehicle', compute="get_rent_vehicle_amount")
    # approved_by = fields.Many2one('res.users', 'Approved By')
    # approved_sign = fields.Binary('Sign')
    # checked_by = fields.Many2one('res.users', 'Checked By')
    # checked_sign = fields.Binary('Sign')
    # rent_vehicle_stmts = fields.One2many('rent.vehicle.statement', 'rent_id')
    # operator_daily_stmts = fields.One2many('operator.daily.statement', 'operator_id')
    # operator_daily_stmts_rent = fields.One2many('operator.daily.statement.rent', 'operator_id')
    # machinery_fuel_collection = fields.One2many('machinery.fuel.collection', 'collection_id')
    # machinery_fuel_allocation = fields.One2many('machinery.fuel.allocation', 'allocation_id')
    # rent_machinery_fuel_allocation = fields.One2many('machinery.fuel.allocation', 'rent_allocation_id')
    # payment_line = fields.One2many('pay.labour', 'labour_id')
    # product_ids = fields.One2many('partner.statement.products', 'line_id', compute="_get_product_ids", store=True)
    # fuel_transfer_ids = fields.One2many('partner.fuel.transfer', 'daily_statement_id')
    # rent_fuel_transfer_ids = fields.One2many('partner.fuel.transfer', 'rent_daily_statement_id')
    project_id = fields.Many2one('project.project', string="Project")
    # item_received_lines = fields.One2many('items.received', 'product_id', 'Materials Used')
    # products_received_lines = fields.One2many('partner.received.products', 'partner_id')
    products_used_lines = fields.One2many('partner.used.products', 'partner_id')
    # products_consumed_id = fields.Many2one('partner.used.products', string='products consumed')
    subcontractor_products_used_lines = fields.One2many('partner.used.products', 'partner_id')
    # project_task_ids = fields.One2many('project.task', 'partner_statement_id')
    project_task_ids = fields.One2many('task.line.custom', 'partner_statement_id')
    project_task_id = fields.Many2one('project.task')
    project_task_line_ids = fields.One2many('task.line.custom', 'partner_statement_id')
    # recieved_items_ids = fields.One2many('site.purchase.item.line', string="reieved items")


class PartnerDailyStatementLine(models.Model):
    _name = 'partner.daily.statement.line'

    estimation_line_id = fields.Many2one('task.line.custom')
    # task_category_id = fields.Many2one("task.category.details")
    # # estimation_line_id = fields.Many2one('estimation.line')
    # # estimation_line_id = fields.Many2one('line.estimation')
    no_labours = fields.Integer('No of Labours')
    work_id = fields.Many2one('project.work', 'Description Of Work')
    # qty_estimate = fields.Float('Quantity')
    sqft = fields.Float('Square Feet')
    # unit = fields.Many2one('product.uom', 'Unit')
    # duration = fields.Float('Duration(Days)')
    # start_date = fields.Date('Start Date')
    # finish_date = fields.Date('Finish Date')
    # employee_id = fields.Many2one('hr.employee', 'Employee')
    # # veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
    veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
    product_id = fields.Many2many('product.product', string='Products')
    estimate_cost = fields.Float('Estimate Cost')
    # pre_qty = fields.Float('Previous Qty')
    # upto_date_qty = fields.Float(store=True, string='Balance Qty')
    quantity = fields.Float(string='Work Order Qty')
    # subcontractor = fields.Many2one('project.task')
    estimated_hrs = fields.Char('Time Allocated')
    #
    # qty_no = fields.Float('Total Qty', compute='compute_qty_char')
    # rep = fields.Integer('Rep')
    # account_id = fields.Many2one('account.account', 'Account')
    # total = fields.Float('Total', compute='compute_total')
    # # category_id = fields.Many2one('labour.category', 'Category')
    # category_id = fields.Many2one('labour.category', compute='compute_category', store=True, string='Category')
    # line_bool = fields.Boolean(default=True)
    # is_labour = fields.Boolean(default=False)
    # item_id = fields.Many2one('daily.statement.item', 'Item')
    # qty_entered = fields.Float('Qty')
    # qty = fields.Float(compute='compute_qty', store=True, string='Qty')
    # qty_char = fields.Char(compute='compute_qty_char', string="Qty")
    # # rate_char = fields.Char(compute='compute_amount_char', store=True, string="Rate")
    # rate = fields.Float('Rate')
    # rate_char = fields.Char('Rate', compute="compute_rate_char")
    # expense_payment = fields.Float("Payment")
    # expense_total = fields.Float("Total")
    # payment = fields.Float('Payment')
    # payment_total = fields.Float('Payment', compute="get_total_payment")
    # vr_no = fields.Char('VR No.')
    remarks = fields.Text('Remarks')
    report_id = fields.Many2one('partner.daily.statement', 'Report')
    # particular_ids = fields.One2many('statement.particular', 'line_id', 'Particulars')
    account_type = fields.Selection([
        ('ie', 'Income/Expense'),
        ('al', 'Asset/Liability')], 'Account Type')
    mason_bool = fields.Boolean(default=False)
    # mason_lines = fields.One2many('mason.line', 'line_ids')
    expense = fields.Boolean(default=False)
    expense_other = fields.Boolean(String="other expense")
    expense_char = fields.Char("Expense")
    exp_account_id = fields.Many2one('account.account', "Account")
    date = fields.Date()
    #
    sqft_completed = fields.Float(string="Sqft Completed")
    sqft_pending = fields.Float(string="Sqft Pending")
    total_attendance = fields.Integer(string="Total Attendance")
    total_absence = fields.Integer(string="Absentee")
    machines_used = fields.Many2many('fleet.vehicle', string="Machinery Used")


class UsedProducts(models.Model):
    _name = 'partner.used.products'

    @api.model
    def create(self, vals):
        res = super(UsedProducts, self).create(vals)
        if res.partner_id.location_ids:
            destination_loc = self.env['stock.location'].search([('name', '=', 'HwsLocation')])
            print("hiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii location", destination_loc)

            move = self.env['stock.move'].create({
                'name': 'Use on HwsLocation',
                'location_id': res.partner_id.location_ids.id,
                'location_dest_id': destination_loc.id,
                'product_id': res.product_id.id,
                'product_uom': 1,
                'product_uom_qty': res.used_qty,
                'date':res.date,
            })
            move.action_confirm()
            move.action_assign()
            res.write({'move_id': move.id, 'state': 'done'})
            # move.move_line_ids.write(
            #     {
            #       'qty_done': res.used_qty})  # This creates a stock.move.line record. You could also do it manually
            #
            move.action_done()

        return res

    product_id = fields.Many2one('product.product')
    stock_qty = fields.Float(readonly=True, compute="compute_quantity", store=True)
    used_qty = fields.Float()
    balance_qty = fields.Float(readonly=True, compute="compute_quantity", store=True)
    unit = fields.Many2one('product.uom', readonly=True,store=True)
    partner_id = fields.Many2one('partner.daily.statement')

    @api.onchange('product_id', 'used_qty')
    def onchange_product_id(self):
        for record in self:
            if record.product_id:
                record.unit = record.product_id.uom_id.id
            if record.product_id and record.partner_id.location_ids:
                current_qty = sum(self.env['stock.quant'].search([('product_id', '=', record.product_id.id),
                                                                  ('location_id', '=',
                                                                   record.partner_id.location_ids.id)]).mapped('qty'))
                record.stock_qty = current_qty
                # record.stock_qty = record.product_id.qty_available
                if record.used_qty:
                    if record.stock_qty < record.used_qty:
                        raise osv.except_osv(('Warning!'),
                                             ('%s stock quantity is less than used quantity' % record.product_id.name))
                    record.balance_qty = record.stock_qty - record.used_qty

    @api.depends('product_id', 'used_qty')
    def compute_quantity(self):
        for record in self:
            if record.product_id and record.partner_id.location_ids:
                current_qty = sum(self.env['stock.quant'].search([('product_id', '=', record.product_id.id),
                                                                  ('location_id', '=',
                                                                   record.partner_id.location_ids.id)]).mapped('qty'))
                record.stock_qty = current_qty
                if record.used_qty:
                    if record.stock_qty < record.used_qty:
                        raise osv.except_osv(('Warning!'),
                                             ('%s stock quantity is less than used quantity' % record.product_id.name))
                    record.balance_qty = record.stock_qty - record.used_qty


    @api.multi
    def unlink(self, cr, uid, ids, context=None):
        for rec in self:
            if rec.partner_id.state != 'draft':
                raise osv.except_osv(('Warning!'), ('Records in the %s state cannot be deleted' % rec.partner_id.state))
            super(UsedProducts, self).unlink(cr, uid, ids, context)
