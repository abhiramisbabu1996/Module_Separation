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

class TaskLine(models.Model):
    _name = "task.line.custom"

    estimate_plan_line = fields.Many2one('budget.planning.chart.line')
    work_id = fields.Many2one('project.work', 'Description Of Work')
    sqft = fields.Float()
    no_labours = fields.Integer()

    veh_categ_id = fields.Many2many('fleet.vehicle',string='Machinery')
    material = fields.Many2many('product.product', string='Materials')
    start_date = fields.Date('Start Date')
    finish_date = fields.Date('Finish Date')
    subcontractor = fields.Many2one('res.partner')
    remarks_new = fields.Char('Remarks')
    project_task_id = fields.Many2one('project.task')




    # partner_statement_id = fields.Many2one('partner.daily.statement')

    # work_loc = fields.Char("Work Location")
    # estimated_hrs = fields.Char('Time Allocated')
    # # material = fields.Many2many('product.product', 'material_line','line_product_id', string='Materials')
    # plan_line_id = fields.Many2one('master.plan.line')
    # task_id = fields.Many2one('project.task')
    # # estimation_line_id = fields.Many2one('estimation.line')
    # estimation_line_id = fields.Many2one('line.estimation')
    # chainage_from = fields.Float('Chainage From')
    # chainage_to = fields.Float('Chainage To')
    # side = fields.Selection([('lhs', 'LHS'),
    #                          ('rhs', 'RHS'),
    #                          ('bhs', 'BHS')
    #                          ], 'Side')
    # length = fields.Float('Length(M)')
    # qty_estimate = fields.Float('Quantity')
    # unit = fields.Many2one('product.uom', 'Unit')
    # duration = fields.Float('Duration(Days)')
    # employee_id = fields.Many2one('hr.employee', 'Employee')
    estimate_cost = fields.Float('Estimate Cost')
    # pre_qty = fields.Float('Previous Qty')
    # upto_date_qty = fields.Float(store=True, string='Balance Qty')
    # quantity = fields.Float(string='Work Order Qty')
    # no_floors = fields.Integer()
    # rate = fields.Float()
    # category_id = fields.Many2one("task.category.details")
    # stage_id = fields.Many2one('project.stages', 'Project Stage')

class task(models.Model):
    _inherit = "project.task"

    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_num = 1

        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context)
            line_num = 1
            for line_rec in first_line_rec.project_id.task_ids:
                line_rec.line_no = line_num
                line_num += 1
            line_num = 1
            for line_rec in first_line_rec.project_id.extra_task_ids:
                line_rec.line_no = line_num
                line_num += 1
            line_num = 1
            for line_rec in first_line_rec.project_id.temp_tasks:
                line_rec.line_no = line_num
                line_num += 1

    # @api.multi
    # def create_supervisor_daily_stmt(self):
    #     return {
    #         'name': _('Supervisor Daily Statement'),
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'partner.daily.statement',
    #         'type': 'ir.actions.act_window',
    #         'view_id': self.env.ref('hiworth_construction.form_partner_daily_statement').id,
    #         'target': 'current',
    #         'context': {'default_employee_id': self.reviewer_id.employee_id.id,
    #                     'default_project_task_id': self.id,
    #                     'default_project_id': self.project_id.id,
    #                     # 'location_ids':self.project_id.project_location_ids.id,
    #                     }
    #
    #     }

    @api.multi
    def task_approve(self):
        self.ensure_one()
        self.state = 'approved'

    @api.multi
    def start_task(self):
        self.ensure_one()
        self.state = 'inprogress'

    @api.multi
    def complete_task(self):
        self.ensure_one()

        self.state = 'completed'

    @api.multi
    def reset_task(self):
        self.ensure_one()
        self.state = 'draft'

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No', readonly=False, default=False)
    is_extra_work = fields.Boolean('Extra Work', default=False)
    extra_id = fields.Many2one('project.project')
    task_line_ids = fields.One2many("task.line.custom", 'project_task_id')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('inprogress', 'In Progress'),
        ('completed', 'Completed')
    ], default='draft')
    task_id2 = fields.Many2one('project.project', 'Project')
    assigned_to = fields.Many2one('hr.employee')
    assigned_by = fields.Many2one('hr.employee')
    date_end = fields.Date()
    date_start = fields.Date()
    civil_contractor = fields.Many2one('res.partner', 'Civil Contractor')
    estimated_cost = fields.Float(string='Estimated Cost')




