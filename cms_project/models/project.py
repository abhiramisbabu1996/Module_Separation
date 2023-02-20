from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
# from openerp.osv import fields, osv
import time
from openerp.osv.orm import browse_record_list, browse_record, browse_null
from datetime import datetime

from openerp.exceptions import except_orm, Warning, RedirectWarning, ValidationError
# from openerp.osv import fields
from openerp import tools
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

# from pygments.lexer import _default_analyse
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
# from openerp.osv import osv
from openerp import SUPERUSER_ID

from lxml import etree

class InheritRespartner(models.Model):
    _inherit = 'res.partner'

    is_a_sub_contractor = fields.Boolean(string='Sub Contractor?')
    is_a_company = fields.Boolean(string='Company?')

class ActualEstimation(models.Model):
    _name = 'actual.estimation.line'

    project_id = fields.Many2one('project.project')
    remark = fields.Char()
    estimated_cost = fields.Float()
    actual_estimated_cost = fields.Float()
    actual_working_hours = fields.Float()
    estimated_hours = fields.Float()
    work_description = fields.Char()
    work_done = fields.Char()
    reason_for_delay = fields.Char(string="Reason for Delay")
    work_plan = fields.Many2one('master.plan.line')
    sub_contractor = fields.Many2one('res.partner')


class MasterPlanLine(models.Model):
    _name = 'project.master.plan.line1'
    _rec_name = "work_id"

    master_plan_line_id1 = fields.Many2one('master.plan.line')
    work_id = fields.Many2one('project.work', 'Description Of Work')
    qty_estimate = fields.Float('Qty As Per Estimate')
    unit = fields.Many2one('product.uom', 'Unit')
    duration = fields.Float('Duration(Days)')
    no_labours = fields.Integer()
    start_date = fields.Date('Start Date')
    finish_date = fields.Date('Finish Date')
    employee_id = fields.Many2one('hr.employee', 'Site Engineer')
    veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
    products_id = fields.Many2many('product.product', string='Products')
    estimate_cost = fields.Float('Estimate Cost')
    sqft = fields.Float('Area')
    pre_qty = fields.Float('Previous Qty')
    remarks = fields.Text()
    upto_date_qty = fields.Float(store=True, string='Balance Qty')
    quantity = fields.Float(string='Work Order Qty')
    subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])
    project_id = fields.Many2one('project.project')
    material = fields.Many2many('product.product', string='Materials')


class ProjectFormInherit(models.Model):
    _inherit = 'project.project'
    _order = 'id desc'

    @api.multi
    def set_open_project(self):
        self.state = 'open'

    @api.multi
    def reopen_project(self):
        self.state = 'open'
        self.status_pro = 'ongoing'
        number = self.name[-6]
        if number:
            if number.isdigit():
                number = int(number)
                number = number + 1
        self.name = self.name[:-6] + str(number) + self.name[-5:]

    project_location = fields.Many2one('stock.location', "Locations")
    company_contractor_id = fields.Many2one('res.partner', string="Company")
    date_end = fields.Date('End Date')
    start_date = fields.Date('Start Date')
    expected_start = fields.Date('Expected Start Date')
    expected_end = fields.Date('Expected End Date')
    contractor_id1 = fields.Many2one('res.partner', string='Sub Contractor 1')
    contractor_id2 = fields.Many2one('res.partner', string='Sub Contractor 2')
    contractor_id3 = fields.Many2one('res.partner', string='Sub Contractor 3')
    description = fields.Text('Description')
    village = fields.Char('Name Of Village')
    taluk = fields.Char('Name Of Taluk')
    district = fields.Char('Name Of District')
    user_id = fields.Many2one('res.users')
    site_engineer1 = fields.Many2one('hr.employee', 'Site Engineer 1')
    site_engineer2 = fields.Many2one('hr.employee', 'Site Engineer 2')
    site_engineer3 = fields.Many2one('hr.employee', 'Site Engineer 3')
    description = fields.Text('Description')
    project_value = fields.Float()
    task_ids = fields.One2many('project.task', 'project_id')
    project_master_line_ids1 = fields.One2many('project.master.plan.line1', 'project_id')
    planning_chart_line_ids = fields.One2many('budget.planning.chart.line', 'project_id')
    actual_estimation_line_ids = fields.One2many('actual.estimation.line', 'project_id')
    temp_tasks = fields.One2many('project.task', 'task_id2', 'Tasks')

