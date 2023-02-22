from openerp import fields, models, api
import datetime
from openerp.exceptions import Warning as UserError
from openerp.osv import osv
from openerp.tools.translate import _
from dateutil import relativedelta
from openerp.exceptions import except_orm, ValidationError
import math


class PartnerDailyStatement(models.Model):
    _name = 'partner.daily.statement'
    _order = 'date desc'

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
        # self.update({'project_task_ids': project_task_ids})
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
    # details_rqrd_item = fields.One2many('site.purchase', 'site_id')
    # details_received_item_ids = fields.One2many('goods.recieve.report', 'partner_daily_statement_id')

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
    # labour_details_ids = fields.One2many('labour.employee.details.custom', 'supervisor_statement_id')
    # products_received_lines = fields.One2many('partner.received.products', 'partner_id')
    # products_used_lines = fields.One2many('partner.used.products', 'partner_id')
    # subcontractor_products_used_lines = fields.One2many('partner.used.products', 'partner_id')
    # # project_task_ids = fields.One2many('project.task', 'partner_statement_id')
    # project_task_ids = fields.One2many('task.line.custom', 'partner_statement_id')
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
