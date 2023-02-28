from openerp import fields, models, api
from openerp.osv import fields as old_fields, osv, expression
# from openerp.osv import fields, osv
import time
from openerp.osv.orm import browse_record_list, browse_record, browse_null
from datetime import datetime

from openerp.exceptions import except_orm, Warning, RedirectWarning,ValidationError
#from openerp.osv import fields
from openerp import tools
from openerp.tools import float_compare
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

# from pygments.lexer import _default_analyse
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, DATETIME_FORMATS_MAP
# from openerp.osv import osv
from openerp import SUPERUSER_ID

from lxml import etree




class ResCompany(models.Model):
    _inherit = 'res.company'

    write_off_account_id = fields.Many2one('account.account', 'Default Write off Account')
    discount_account_id = fields.Many2one('account.account', 'Default Discount Account')
    gst_account_id = fields.Many2one('account.account', 'Default GST Account')


class mrp_bom_line(models.Model):
    _inherit = 'mrp.bom.line'

    @api.multi
    @api.depends('product_id','product_qty')
    def _compute_total_cost(self):

        for line in self:
            line.total_cost=line.product_id.standard_price*line.product_qty

    total_cost = fields.Float(compute='_compute_total_cost', store=True, string='Total Cost')


class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    @api.multi
    @api.depends('bom_line_ids')
    def _compute_bom_cost(self):

        for line in self:
            for bom_lines in line.bom_line_ids:
                line.bom_cost += bom_lines.product_id.standard_price*bom_lines.product_qty



    bom_cost = fields.Float(compute='_compute_bom_cost', store=True, string='BOM Cost')



    def create(self, cr, uid, vals, context=None):


            product_obj=self.pool.get('product.template').browse( cr, uid, [(vals['product_tmpl_id'])])
            bom_cost = 0.0
            for line in vals['bom_line_ids']:

                product_obj2=self.pool.get('product.product').browse( cr, uid, [(line[2]['product_id'])])
                bom_cost += product_obj2.standard_price*line[2]['product_qty']



            product_obj.write({'standard_price':bom_cost,'list_price':bom_cost})



            result = super(mrp_bom, self).create(cr, uid, vals, context=context)
            return result

class mrp_production(models.Model):
    _inherit = 'mrp.production'


    @api.multi
    @api.depends('bom_id')
    def _compute_estimated_cost(self):

        for line in self:
            for lines in line.bom_id:
                line.estimated_cost=lines.bom_cost


    estimated_cost = fields.Float(compute='_compute_estimated_cost', store=True, string='Estimated Cost')
    real_cost = fields.Float('Actual Host')

# class task_category(models.Model):
#     _name = 'task.category'
#
#
#     @api.multi
#     def name_get(self):
#         def get_names(cat):
#             """ Return the list [cat.name, cat.parent_id.name, ...] """
#             res = []
#             while cat:
#                 res.append(cat.name)
#                 cat = cat.parent_id
#             return res
#
#         return [(cat.id, " / ".join(reversed(get_names(cat)))) for cat in self]
#
#     def name_search(self, cr, uid, name, args=None, operator='ilike', context=None, limit=100):
#         if not args:
#             args = []
#         if not context:
#             context = {}
#         if name:
#             # Be sure name_search is symetric to name_get
#             categories = name.split(' / ')
#             parents = list(categories)
#             child = parents.pop()
#             domain = [('name', operator, child)]
#             if parents:
#                 names_ids = self.name_search(cr, uid, ' / '.join(parents), args=args, operator='ilike', context=context, limit=limit)
#                 category_ids = [name_id[0] for name_id in names_ids]
#                 if operator in expression.NEGATIVE_TERM_OPERATORS:
#                     category_ids = self.search(cr, uid, [('id', 'not in', category_ids)])
#                     domain = expression.OR([[('parent_id', 'in', category_ids)], domain])
#                 else:
#                     domain = expression.AND([[('parent_id', 'in', category_ids)], domain])
#                 for i in range(1, len(categories)):
#                     domain = [[('name', operator, ' / '.join(categories[-1 - i:]))], domain]
#                     if operator in expression.NEGATIVE_TERM_OPERATORS:
#                         domain = expression.AND(domain)
#                     else:
#                         domain = expression.OR(domain)
#             ids = self.search(cr, uid, expression.AND([domain, args]), limit=limit, context=context)
#         else:
#             ids = self.search(cr, uid, args, limit=limit, context=context)
#         return self.name_get(cr, uid, ids, context)
#
#     def _name_get_fnc(self, cr, uid, ids, prop, unknow_none, context=None):
#         res = self.name_get(cr, uid, ids, context=context)
#         return dict(res)
#
#
#     name = fields.Char('name')
#     seq = fields.Integer('sequence')
#     task_ids = fields.One2many('project.task', 'categ_id')
#     parent_id = fields.Many2one('task.category','Parent Category', select=True, ondelete='cascade')
#     child_id = fields.One2many('task.category', 'parent_id', string='Child Categories')

class WorkDes(models.Model):
    _name = "work.descri"

    name = fields.Char('Work Description')
    wid = fields.Many2one('task.details')


# class TaskCategoryWork(models.Model):
#     _name = "task.category.details"
#
#     name=fields.Float()

# class TaskDetails(models.Model):
#     _name = "task.details"
#     # _rec_name = "category_id"
# #
# #     # work_description = fields.Many2one('work.descri','Work Description')
# #     work_description = fields.Char('Work Description')
#     work_loc = fields.Char("Work Location")
#     estimated_hrs = fields.Char('Time Allocated')
# #     comments = fields.Char('Comments')
# #     task_status = fields.Selection([
# # 			('completed', 'Completed'),
# # 			('partial', 'Partially Completed'),
# # 			('inprogress', 'In Progress'),
# # 			('not', 'Not Started')
# # 		], default='not')
# #     work_id = fields.Many2one('project.task')
#     plan_line_id = fields.Many2one('master.plan.line')
#     task_id = fields.Many2one('project.task')
#     # estimation_line_id = fields.Many2one('estimation.line')
#     # estimation_line_id = fields.Many2one('line.estimation')
#     work_id = fields.Many2one('project.work', 'Description Of Work')
#     chainage_from = fields.Float('Chainage From')
#     chainage_to = fields.Float('Chainage To')
#     side = fields.Selection([('lhs','LHS'),
#                             ('rhs','RHS'),
#                             ('bhs','BHS')
#                             ],'Side')
#     length = fields.Float('Length(M)')
#     qty_estimate = fields.Float('Quantity')
#     unit = fields.Many2one('product.uom','Unit')
#     duration = fields.Float('Duration(Days)')
#     start_date = fields.Date('Start Date')
#     finish_date = fields.Date('Finish Date')
#     employee_id = fields.Many2one('hr.employee','Employee')
#     # veh_categ_id = fields.Many2many('vehicle.category.type','task_veh_categ_id','vehicle_categ_id',string='Machinery')
#     veh_categ_id = fields.Many2many('fleet.vehicle',string='Machinery')
#     estimate_cost = fields.Float('Estimate Cost')
#     pre_qty = fields.Float('Previous Qty')
#     upto_date_qty = fields.Float(store=True, string='Balance Qty')
#     quantity = fields.Float(string='Work Order Qty')
#     subcontractor = fields.Many2one('project.task')
#     no_labours = fields.Integer()
#     no_floors = fields.Integer()
#     rate = fields.Float()
#     sqft = fields.Float()
#     category_id = fields.Many2one("task.category.details")
#     stage_id = fields.Many2one('project.stages', 'Project Stage')


# class TaskLine(models.Model):
#     _name = "task.line.custom"
#     _rec_name = "project_task_id"
#
#     partner_statement_id = fields.Many2one('partner.daily.statement')
#     project_task_id = fields.Many2one('project.task')
#     remarks_new = fields.Char('Remarks')
#     work_loc = fields.Char("Work Location")
#     estimated_hrs = fields.Char('Time Allocated')
#     # material = fields.Many2many('product.product', 'material_line','line_product_id', string='Materials')
#     material = fields.Many2many('product.product',string='Materials')
#     # new = fields.Char('Time Allocated')
#     #     comments = fields.Char('Comments')
#     #     task_status = fields.Selection([
#     # 			('completed', 'Completed'),
#     # 			('partial', 'Partially Completed'),
#     # 			('inprogress', 'In Progress'),
#     # 			('not', 'Not Started')
#     # 		], default='not')
#     #     work_id = fields.Many2one('project.task')
#     estimate_plan_line = fields.Many2one('budget.planning.chart.line')
#     plan_line_id = fields.Many2one('master.plan.line')
#     task_id = fields.Many2one('project.task')
#     # estimation_line_id = fields.Many2one('estimation.line')
#     estimation_line_id = fields.Many2one('line.estimation')
#     work_id = fields.Many2one('project.work', 'Description Of Work')
#     chainage_from = fields.Float('Chainage From')
#     chainage_to = fields.Float('Chainage To')
#     side = fields.Selection([('lhs', 'LHS'),
#                              ('rhs', 'RHS'),
#                              ('bhs', 'BHS')
#                              ], 'Side')
#     length = fields.Float('Length(M)')
#     qty_estimate = fields.Float('Quantity')
#     unit = fields.Many2one('product.uom', 'Unit')
#     duration = fields.Float('Duration(Days)')
#     start_date = fields.Date('Start Date')
#     finish_date = fields.Date('Finish Date')
#     employee_id = fields.Many2one('hr.employee', 'Employee')
#     veh_categ_id = fields.Many2many('fleet.vehicle',string='Machineries' )
#     # veh_categ_id = fields.Many2many('vehicle.category.type', 'task_veh_id', 'id_vehicle_categ',
#     #                                 string='Machinery')
#     estimate_cost = fields.Float('Estimate Cost')
#     pre_qty = fields.Float('Previous Qty')
#     upto_date_qty = fields.Float(store=True, string='Balance Qty')
#     quantity = fields.Float(string='Work Order Qty')
#     subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])
#     no_labours = fields.Integer()
#     no_floors = fields.Integer()
#     rate = fields.Float()
#     sqft = fields.Float()
#     category_id = fields.Many2one("task.category.details")
#     stage_id = fields.Many2one('project.stages', 'Project Stage')
#     date_assigned = fields.Date(default=fields.Date.today)



#
# class task(models.Model):
#     _inherit = "project.task"
#
#     @api.multi
#     @api.depends('estimate_ids')
#     def _compute_estimated_cost(self):
#
#
#         for line in self:
#             line.estimated_cost = 0.0
#
#             for lines in line.estimate_ids:
#
#                 line.estimated_cost+=lines.estimated_cost_sum
#
#     def _get_line_numbers(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#         line_num = 1
#
#         if ids:
#             first_line_rec = self.browse(cr, uid, ids[0], context=context)
#             line_num = 1
#             for line_rec in first_line_rec.project_id.task_ids:
#                 line_rec.line_no = line_num
#                 line_num += 1
#             line_num = 1
#             for line_rec in first_line_rec.project_id.extra_task_ids:
#                 line_rec.line_no = line_num
#                 line_num += 1
#             line_num = 1
#             for line_rec in first_line_rec.project_id.temp_tasks:
#                 line_rec.line_no = line_num
#                 line_num += 1
#
#     line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
#     assigned_by = fields.Many2one('hr.employee')
#     partner_statement_id = fields.Many2one('partner.daily.statement')
#     estimated_cost = fields.Float(compute='_compute_estimated_cost', string='Estimated Cost')
#     estimate_ids = fields.One2many('project.task.estimation', 'task_id', 'Estimation')
#     is_extra_work = fields.Boolean('Extra Work', default=False)
#     extra_id = fields.Many2one('project.project')
#     partner_id = fields.Many2one(related='project_id.partner_id', string='Customer')
#     usage_ids1 = fields.One2many('project.task.estimation','task_ids1',string='Items usage')
#     work_list = fields.One2many('task.details','work_id',string='Work List')
#     estimation_line_ids = fields.One2many("task.details", 'task_id')
#     task_line_ids = fields.One2many("task.line.custom", 'project_task_id')
#
#     partner_statement_id = fields.Many2one('partner.daily.statement')
#     work_details = fields.Many2one('project.work', "Work Details")
#
#     # work_items = fields.One2many('task.details','work_id', string="Items")
#
#
#     state = fields.Selection([
#             ('draft', 'Draft'),
#             ('approved', 'Approved'),
#             ('inprogress', 'In Progress'),
#             ('completed', 'Completed')
#         ], default='draft')
#     sub_categ_id = fields.Many2one('task.category', 'Sub Category')
#     categ_id = fields.Many2one('task.category', 'Category')
#     civil_contractor = fields.Many2one('res.partner', 'Civil Contractor', domain = [('contractor','=',True)])
#     labour_report_ids = fields.One2many('project.labour.report', 'task_id')
#     task_id2 = fields.Many2one('project.project', 'Project')
#     assigned_to = fields.Many2one('hr.employee')
#     assigned_by = fields.Many2one('hr.employee')
#     date_end = fields.Date()
#     date_start = fields.Date()
#
#
#     @api.multi
#     def create_supervisor_daily_stmt(self):
#         return{
#                 'name':  _('Supervisor Daily Statement'),
#                 'view_type': 'form',
#                 'view_mode': 'form',
#                 'res_model': 'partner.daily.statement',
#                 'type': 'ir.actions.act_window',
#                 'view_id': self.env.ref('hiworth_construction.form_partner_daily_statement').id,
#                 'target': 'current',
#                 'context': {'default_employee_id': self.reviewer_id.employee_id.id,
#                             'default_project_task_id':self.id,
#                             'default_project_id':self.project_id.id,
#                             # 'location_ids':self.project_id.project_location_ids.id,
#                             }
#
#         }
#
#
#     @api.multi
#     def task_approve(self):
#         self.ensure_one()
#         self.state = 'approved'
#
#     @api.multi
#     def start_task(self):
#         self.ensure_one()
#         self.state = 'inprogress'
#
#     @api.multi
#     def complete_task(self):
#         self.ensure_one()
#
#
#         self.state = 'completed'
#
#
#     @api.multi
#     def reset_task(self):
#         self.ensure_one()
#         self.state = 'draft'

# class project_labour_report(models.Model):
#     _name = 'project.labour.report'
#
#     _order = "date asc"
#
#     @api.multi
#     @api.depends('labour_detail_ids')
#     def _compute_amount(self):
#         for line in self:
#             line.amount = 0.0
#             for lines in line.labour_detail_ids:
#                 line.amount+=lines.amount
#
#     def _get_line_numbers(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#         line_num = 1
#
#         if ids:
#             first_line_rec = self.browse(cr, uid, ids[0], context=context)
#             for line_rec in first_line_rec.project_id.labour_report_ids:
#                 line_rec.line_no = line_num
#                 line_num += 1
#
#     line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
#     name = fields.Text('Description')
#     date = fields.Date('Date')
#     amount = fields.Float(compute='_compute_amount', string='Amount')
#     labour_detail_ids = fields.One2many('labour.details', 'detail_ids')
#     task_id = fields.Many2one('project.task', 'Task')
#     project_id = fields.Many2one('project.project', 'Project')
#
#
#
#
#     _defaults = {
#         'date': fields.Date.today(),
#         }


# class labour_details(models.Model):
#     _name = 'labour.details'
#
#
#     @api.multi
#     @api.depends('product_id','rate','qty')
#     def _compute_amount(self):
#
#         for line in self:
#             line.amount = line.rate * line.qty
#
#     detail_ids = fields.Many2one('project.labour.report', 'Report')
#     product_id = fields.Many2one('product.product', 'Product')
#     rate = fields.Float(related='product_id.standard_price', string='Rate')
#     qty = fields.Float('Nos')
#     amount = fields.Float(compute='_compute_amount', string='Amount')


#
# class category_items_estimation(models.Model):
#     _name = 'category.items.estimation'
#
#     @api.multi
#     @api.depends('product_id','unit_price','qty')
#     def _compute_amount(self):
#
#         for line in self:
#             line.amount = line.unit_price * line.qty
#
#     def _get_line_numbers(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#         line_num = 1
#
#         if ids:
#             first_line_rec = self.browse(cr, uid, ids[0], context=context)
#             for line_rec in first_line_rec.project_id.categ_estimation_ids:
#                 line_rec.line_no = line_num
#                 line_num += 1
#
#     line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
#     name = fields.Char('Name')
#     product_id = fields.Many2one('product.product', 'Product')
#     unit_price = fields.Float(related='product_id.standard_price', string="Unit Price")
#     uom = fields.Many2one(related='product_id.uom_id', string="Uom")
#     qty = fields.Float('Qty')
#     amount = fields.Float(compute='_compute_amount', string='Amount')
#     project_id = fields.Many2one('project.project', 'Project')
#
#
# class MasterPlanLine(models.Model):
#     _name = 'project.master.plan.line'
#     _rec_name = "work_id"
#
#     master_plan_line_id = fields.Many2one('master.plan.line')
#     work_id = fields.Many2one('project.work', 'Description Of Work')
#     qty_estimate = fields.Float('Qty As Per Estimate')
#     unit = fields.Many2one('product.uom', 'Unit')
#     duration = fields.Float('Duration(Days)')
#     no_labours = fields.Integer()
#     start_date = fields.Date('Start Date')
#     finish_date = fields.Date('Finish Date')
#     employee_id = fields.Many2one('hr.employee', 'Site Engineer')
#     # veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
#     veh_categ_id = fields.Many2many('fleet.vehicle', string='Machineries')
#     products_id = fields.Many2many('product.product', string='Products')
#     estimate_cost = fields.Float('Estimate Cost')
#     sqft = fields.Float('Area')
#     pre_qty = fields.Float('Previous Qty')
#     remarks = fields.Text()
#     upto_date_qty = fields.Float(store=True, string='Balance Qty')
#     quantity = fields.Float(string='Work Order Qty')
#     subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])
#     project_id = fields.Many2one('project.project')
#
#
# class BudgetPlanningChartLine(models.Model):
#     _name = 'budget.planning.chart.line'
#     _rec_name = 'master_plan_line_id'
#
#     project_id = fields.Many2one('project.project')
#     mep = fields.Selection([('mechanical', 'Mechanical'), ('electricel', 'Electrical'), ('plumbing', 'Plumbing')])
#     master_plan_id = fields.Many2one('master.plan')
#     master_plan_line_id = fields.Many2one('master.plan.line', required=True)
#     line_id = fields.Many2one('planning.chart')
#     date = fields.Date('Date')
#     work_id = fields.Char('Work Description')
#     labour = fields.Float('No of Labours')
#     # veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
#     veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
#     qty = fields.Float('Qty')
#     target_qty = fields.Float('Target Qty')
#     material_qty = fields.Float('Material Qty')
#     material = fields.Many2many('product.product', string='Materials')
#     uom_id = fields.Many2one('product.uom', string="Units")
#     working_hours = fields.Float('Working Hours')
#     remarks = fields.Char('Remarks')
#     sqft = fields.Float('Square Feet')
#     estimated_cost = fields.Float(string='Material Cost')
#     work_status = fields.Selection([('started', 'Started'),
#                                     ('on_progressing', 'On Progressing'),
#                                     ('partially_completed', 'Partially Completed'),
#                                     ('completed', 'Completed')])
#     plan_id = fields.Many2one('planning.chart.line')
#     labour_charge = fields.Float('Labour Cost')
#     machinery_charge = fields.Float('Machinery Cost')
#     total_charge = fields.Float('Total Cost')
#     test = fields.Float('test')
#
#     @api.multi
#     def open_view_wizard(self):
#         for rec in self:
#             res = {
#                 'name': 'Tasks',
#                 'view_type': 'form',
#                 'view_mode': 'form',
#                 'res_model': 'project.task',
#                 'target': 'new',
#                 'type': 'ir.actions.act_window',
#                 'context': {'default_name': rec.master_plan_line_id.work_id.name,
#                             'default_project_id': rec.project_id.id,
#                             'default_task_line_ids': [(0, 0, {'estimate_plan_line': rec.id,
#                                                              'sqft': rec.sqft,
#                                                               'no_labours':rec.labour,
#                                                               'work_id':rec.work_id,
#                                                               'veh_categ_id':rec.veh_categ_id.ids,
#                                                               'material':rec.material.ids,
#                                                               'start_date':rec.date,
#                                                               'finish_date':rec.date,
#                                                               # 'subcontractor':rec.subcontractor,
#                                                               'remarks_new':rec.remarks})]
#                             }
#             }
#
#         return res
#
#
# class AccountStatmentsProject(models.Model):
#     _name = 'account.statement.view'
#
#     date = fields.Date()
#     work_description = fields.Many2one('budget.planning.chart.line')
#     remarks = fields.Char()
#     work_status = fields.Selection([('started', 'Started'),
#                                     ('on_progressing', 'On Progressing'),
#                                     ('partially_completed', 'Partially Completed'),
#                                     ('completed', 'Completed')])
#
#
# class ActualEstimation(models.Model):
#     _name = 'actual.estimation.line'
#
#     project_id = fields.Many2one('project.project')
#     remark = fields.Char()
#     estimated_cost = fields.Float()
#     actual_estimated_cost = fields.Float()
#     actual_working_hours = fields.Float()
#     estimated_hours = fields.Float()
#     work_description = fields.Char()
#     work_done= fields.Char()
#     reason_for_delay= fields.Char(string="Reason for Delay")
#     work_plan = fields.Many2one('master.plan.line')
#     sub_contractor = fields.Many2one('res.partner')
#
#
#     # @api.onchange('work_plan')
#     # def onchange_work_plan(self):
#     #     for record in self:
#     #         task_lines = self.env['task.line'].search([('estimate_plan_line', '=', record.work_plan.id)])
#     #         output_summary_lines = self.env['partner.daily.statement.line'].search([('estimation_line_id', 'in', task_lines)])
#     #         # subcontactor_summary_lines =
#
#
#
#
#
#
class project(models.Model):
    _inherit = "project.project"
#
#     @api.multi
#     def set_open_project(self):
#         self.state = 'open'
#
#     @api.multi
#     @api.depends('task_ids')
#     def _compute_estimated_cost(self):
#
#         for line in self:
#             for lines in line.task_ids:
#                 line.estimated_cost+=lines.estimated_cost
#     @api.multi
#     @api.depends('extra_task_ids')
#     def _compute_estimated_cost_extra(self):
#
#         for line in self:
#             for lines in line.extra_task_ids:
#                 line.estimated_cost_extra+=lines.estimated_cost
#
#     @api.multi
#     @api.depends('estimated_cost','estimated_cost_extra')
#     def _compute_estimated_cost_total(self):
#
#         for line in self:
#             line.total_estimated_cost = line.estimated_cost + line.estimated_cost_extra
#
#     @api.onchange('schedule_id')
#     @api.multi
#     def _compute_stage_total(self):
#         if (not self.schedule_id):
#             return
#
#         amount = 0.0
#         for line in self.schedule_id:
#             amount+= line.amount
#         line['stage_total'] =  amount
#
#
#     @api.multi
#     @api.onchange('categ_id')
#     def onchange_task_ids(self):
#         return {
#             'domain': {
#                 'task_ids':[('categ_id','=', self.categ_id.id)]
#             }
#         }
#
    @api.model
    def _default_company_id(self):
        return self.env.user.company_id.partner_id
#
    project_number = fields.Char()
#     project_value = fields.Float()
#     company_id = fields.Many2one('res.company', 'Company', required=True,)
#     estimated_cost = fields.Float(compute='_compute_estimated_cost', store=True, string='Estimated Cost')
#     estimated_cost_extra = fields.Float(compute='_compute_estimated_cost_extra', store=True, string='Estimated Cost for Extra Work')
#     total_estimated_cost = fields.Float(compute='_compute_estimated_cost_total', store=True, string='Total Estimated Cost')
#     date_end = fields.Date('End Date')
#     start_date = fields.Date('Start Date')
#
#     expected_start = fields.Date('Expected Start Date')
#     expected_end = fields.Date('Expected End Date')
#     tender_id = fields.Many2one('hiworth.tender','Tender')
#
#     task_ids = fields.One2many('project.task', 'project_id',
#                                     domain=[('is_extra_work', '=', False)])
#     extra_task_ids = fields.One2many('project.task', 'project_id', domain=[('is_extra_work','=', True)])
#
#     stage_id = fields.One2many('project.stages', 'project_id', 'Project Status')
#     stages_generated = fields.Boolean('Stages Generated', default=False)
#
#     location_id = fields.Many2one('stock.location', 'Location', domain=[('usage','=','internal')])
#     cent = fields.Float('Cent')
#     building_sqf = fields.Float('Building in Sq. Ft')
#     rate = fields.Float('Rate')
#     total_value = fields.Float('Total Value')
#     schedule_id = fields.One2many('project.schedule', 'project_id', 'Schedule')
#     schedule_note = fields.Text('Note')
#     remark1 = fields.Char('Remarks')
#     acc_statement = fields.One2many('account.move.line','project_id', string='Account Statement',compute="_onchange_acc_statement")
#     acc_balance = fields.Float(string='Balance',compute="_onchange_acc_statement")
#     civil_contractor = fields.Many2one('res.partner', 'Civil Contractor')
#     project_product_ids = fields.One2many('project.product', 'project_id')
#     labour_report_ids = fields.One2many('project.labour.report', 'project_id')
#     categ_id = fields.Many2one('task.category', 'Category')
#     view_categ_estimation = fields.Boolean('View Category Wise Estimation', default=False)
#     hide_tasks = fields.Boolean('Hide Tasks', default=False)
#     temp_tasks = fields.One2many('project.task', 'task_id2', 'Tasks')
#     categ_estimation_ids = fields.One2many('category.items.estimation', 'project_id', 'Category Estimation')
#     directory_ids = fields.One2many('project.directory', 'project_id', 'Directory')
#     project_location_ids = fields.Many2many('stock.location','stock_location_project_rel','stock_location_id','project_id',"Locations")
#     # partner_id.property_account_receivable.balance
    company_contractor_id = fields.Many2one('res.partner', string="Company", default=_default_company_id)
#     # company_contractor_id = fields.Many2one('res.partner', domain=[('company_contractor', '=', True)], string="Company")
#     agreement_no = fields.Char("Agreement No")
#     agreement_date = fields.Date("Agreement Date")
#     district_id = fields.Many2one('location.district',"District")
#     contract_awarder_id = fields.Many2one('contract.awarder',"Contract Awarder")
#     tender_attachment_ids = fields.One2many('tender.attachments','project_id',"Attachments")
#     estimation_id = fields.One2many('estimation.estimation', 'project_id')
#     estimation_line_ids = fields.One2many('estimation.line', 'project_id')
#     plan_line_ids = fields.One2many('line.estimation', 'project_id')
#     plan_id = fields.Many2one('master.plan')
#     planning_chart_line_ids = fields.One2many('budget.planning.chart.line', 'project_id')
#     project_master_line_ids = fields.One2many('project.master.plan.line', 'project_id')
#     actual_estimation_line_ids = fields.One2many('actual.estimation.line', 'project_id')
#
    # @api.model
    # def create(self, vals):
    #     if not vals.get('project_number'):
    #         vals['project_number'] = self.env['ir.sequence'].next_by_code('project.project')
    #     # seq = self.env['ir.sequence'].next_by_code('project.project')
    #     # result['name'] = str('PBA/')+str(self.project_category)+str('/')+seq[:3]+str('/1/')+seq[-4:]
    #     return super(project, self).create(vals)
#
#     @api.depends('partner_id')
#     def _onchange_acc_statement(self):
#         debit = 0.0
#         credit = 0.0
#         record = self.env['account.move.line'].search([('project_id','=',self.id),('account_id','=',self.partner_id.property_account_receivable.id)])
#         self.acc_statement = record
#         for rec in record:
#             debit += rec.debit
#             credit += rec.credit
#         self.acc_balance = debit - credit
#
#
#
#     _defaults = {
#         'schedule_note': 'KVAT AND SERVICE TAX AS PER GOVT. RULES SHOULD BE PAID IN ADDITION TO THE ABOVE AMOUNT ALONG WITH EACH INSTALLMENT. ALL INSTALLMENTS SHOULD BE PAID IN ADVANCE BEFORE STARTING EACH WORK',
#         'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
#         }
#
#
#
#     @api.multi
#     def compute_estimated_cost(self):
#         temp=0.0
#         for line in self:
#             for lines in line.task_ids:
#
#                 temp+=lines.estimated_cost
#             line.estimated_cost=temp
#             temp2=0.0
#             for lines in line.extra_task_ids:
#
#                 temp2 += lines.estimated_cost
#             line.estimated_cost_extra=temp2
#
#
#     @api.multi
#     def display_project_status(self):
#         stage_lines = self.env['project.stages.line'].search([('id','!=',False)])
#         stage = self.env['project.stages']
#
#         for line in self:
#             if line.stages_generated == False:
#                 for stage_line in stage_lines:
#                     values = {'stage_line_id': stage_line.id,
#                               'state': 'no',
#                               'project_id': line.id}
#                     stage_id = stage.create(values)
#
#
#
#             if line.stages_generated == True:
#
#
#                 for stage_line in stage_lines:
#                     generated = False
#                     for stages in stage_line.stage_id:
#                         if stages.project_id.id == line.id:
#                             generated = True
#                     if generated ==  False:
#                         values = {'stage_line_id': stage_line.id,
#                                   'state': 'no',
#                                   'project_id': line.id}
#                         stage_id = stage.create(values)
#
#                         line.stages_generated = True
#
#
#             line.stages_generated = True
#
#
#     @api.multi
#     def visible_category(self):
#         for line in self:
#             line.view_categ_estimation=True
#
#     @api.multi
#     def hide_category(self):
#         for line in self:
#
#             line.view_categ_estimation = False
#             line.hide_tasks = False
#
#     @api.multi
#     def refresh_category(self):
#         for line in self:
#             if line.categ_id.id == False:
#                 raise osv.except_osv(('Warning!'), ('Please Select A Category'))
#             if line.categ_id.id != False:
#                 line.hide_tasks = True
#                 categ_estimation_obj = self.env['category.items.estimation']
#                 categ_estimations = categ_estimation_obj.search([('id','!=',False)])
#
#                 for items in categ_estimations:
#                     items.unlink()
#
#
#                 temp_task_ids = self.env['project.task'].search([('task_id2','=',line.id)])
#                 for tasks2 in temp_task_ids:
#                     tasks2.task_id2 = False
#
#                 child_ids = []
#                 childs=self.env['task.category'].search([('parent_id','=',line.categ_id.id)])
#                 for child in childs:
#                     child_ids.append(child.id)
#                 if child_ids == []:
#                     child_ids.append(line.categ_id.id)
#
#
#                 task_ids = self.env['project.task'].search([('project_id','=',line.id),('categ_id','in',child_ids)])
#                 for lines in task_ids:
#                     lines.task_id2 = line.id
#
#                     for esimations in lines.estimate_ids:
#
#                         if categ_estimation_obj.search([('product_id','=',esimations.pro_id.id)]).id != False:
#                             categ_obj = categ_estimation_obj.search([('product_id','=',esimations.pro_id.id)])
#
#                             categ_obj.qty+=esimations.qty
#                         if categ_estimation_obj.search([('product_id','=',esimations.pro_id.id)]).id == False:
#                             values = {'product_id':esimations.pro_id.id,
#                                     'qty':esimations.qty,
#                                     'project_id':line.id}
#                             categ_estimation_obj.create(values)
#
#     @api.model
#     def get_records(self, project_id):
#
#         res = self.env['project.labour.report'].search([('project_id','=',project_id)])
#         recordset = res.sorted(key=lambda r: r.date)
#         return recordset
#
#     def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
#         res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
#         if view_type == 'form':
#             doc = etree.XML(res['arch'])
#             for sheet in doc.xpath("//sheet"):
#                 parent = sheet.getparent()
#                 index = parent.index(sheet)
#                 for child in sheet:
#                     parent.insert(index, child)
#                     index += 1
#                 parent.remove(sheet)
#             res['arch'] = etree.tostring(doc)
#
#         return res
#
#
# class EstimationEstimation(models.Model):
#     _name = "estimation.estimation"
#
#     name = fields.Char("Work name")
#     project_id = fields.Many2one('project.project')
#     assigned_to = fields.Many2one('hr.employee')
#     start_date = fields.Date()
#     end_date = fields.Date()
#     estimated_cost = fields.Float()
#     no_of_floors = fields.Integer()
#     sqft = fields.Float()
#     rate = fields.Float()
#     machine_ids = fields.One2many('operator.daily.statement', 'estimation_id')
#     item_usage_ids = fields.One2many('item.usage', 'estimation_id')
#     estimation_line_ids = fields.One2many('estimation.line', 'estimation_id')
#
#
# class EstimationLine(models.Model):
#     _name = "estimation.line"
#     _rec_name = "plan_line_id"
#
#     mep = fields.Selection([('mechanical', 'Mechanical'), ('electricel', 'Electrical'), ('plumbing', 'Plumbing')])
#     plan_line_id = fields.Many2one('master.plan.line')
#     chart_plan_line_id = fields.Many2one('planning.chart.line')
#     no_of_floors = fields.Integer()
#     sqft = fields.Float()
#     estimation_id = fields.Many2one('estimation.estimation')
#     project_id = fields.Many2one('project.project')
#     category_id = fields.Many2one("task.category.details")
#     work_id = fields.Many2one('project.work', 'Description Of Work')
#     qty_estimate = fields.Float('Quantity')
#     unit = fields.Many2one('product.uom', 'Unit')
#     duration = fields.Float('Duration(Days)')
#     start_date = fields.Date('Start Date')
#     finish_date = fields.Date('Finish Date')
#     employee_id = fields.Many2one('hr.employee', 'Employee')
#     # veh_categ_id = fields.Many2many('vehicle.category.type', 'veh_categ_id_lines','estimation_line_vehicle_id', string='Machinery')
#     veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
#     material = fields.Many2many('product.product', 'material_ids_line','line_estimation_product_id', string='Materials')
#     estimate_cost = fields.Float('Estimate Cost')
#     pre_qty = fields.Float('Previous Qty')
#     upto_date_qty = fields.Float(store=True, string='Balance Qty')
#     quantity = fields.Float(string='Work Order Qty')
#     subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])
#     no_labours = fields.Integer()
#     rate = fields.Float()
#
#
# class LineEstimation(models.Model):
#     _name = "line.estimation"
#     # _inherits = {'planning.chart.line': "chart_plan_line_id"}
#
#     chart_plan_line_id = fields.Many2one('planning.chart.line')
#     no_of_floors = fields.Integer()
#     sqft = fields.Float()
#     estimation_id = fields.Many2one('estimation.estimation')
#     project_id = fields.Many2one('project.project')
#     category_id = fields.Many2one("task.category.details")
#     work_id = fields.Many2one('project.work', 'Description Of Work')
#     qty_estimate = fields.Float('Quantity')
#     unit = fields.Many2one('product.uom', 'Unit')
#     duration = fields.Float('Duration(Days)')
#     start_date = fields.Date('Start Date')
#     finish_date = fields.Date('Finish Date')
#     employee_id = fields.Many2one('hr.employee', 'Employee')
#     # veh_categ_id = fields.Many2many('vehicle.category.type', 'veh_categ_mlines','estimation_line_vehicle', string='Machinery')
#     veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
#     material = fields.Many2many('product.product', 'material_line','line_product_id', string='Materials')
#     estimate_cost = fields.Float('Estimate Cost')
#     pre_qty = fields.Float('Previous Qty')
#     upto_date_qty = fields.Float(store=True, string='Balance Qty')
#     quantity = fields.Float(string='Work Order Qty')
#     subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])
#     no_labours = fields.Integer()
#     rate = fields.Float()
#
#
#
#
#
# class document_file(models.Model):
#     _inherit = 'ir.attachment'
#
#     ref_name = fields.Char('Description', size=100)
#     stage_id = fields.Many2one('project.stages', 'Project Stage')
#
#
# class project_attachment(models.Model):
#     _name = 'project.attachment'
#     _description = "Project Attachment"
#
#
#     name = fields.Char('Name')
#     binary_field = fields.Binary('File')
#     filename = fields.Char('Filename')
#     parent_id = fields.Many2one('document.directory', 'Directory')
#     stage_id = fields.Many2one('project.stages', 'Project Stage')
#     project_id = fields.Many2one(related='stage_id.project_id', string="Project")
#
#
# class project_directory(models.Model):
#     _name = 'project.directory'
#
#     name = fields.Char('Document No')
#     project_id = fields.Many2one('project.project', 'Project')
#     directory_id = fields.Many2one('document.directory', 'Directories')
#     date = fields.Date(string="Date")
#     document_id = fields.Many2one('document.document',string="Document")
#     status_id = fields.Many2one('document.status',string="Status")
#
#
#     remark = fields.Char(string="Remark")
#
#
#     @api.multi
#     def open_selected_directory(self):
#         self.ensure_one()
#         # Search for record belonging to the current staff
#         record =  self.env['document.directory'].search([('id','=',self.directory_id.id)])
#
#         context = self._context.copy()
#
#         if record:
#             res_id = record[0].id
#         else:
#             res_id = False
#         # Return action to open the form view
#         return {
#             'name':'Directory Form view',
#             'view_type': 'form',
#             'view_mode':'form',
#             'views' : [(False,'form')],
#             'res_model':'document.directory',
#             'view_id':'view_document_directory_form',
#             'type':'ir.actions.act_window',
#             'res_id':res_id,
#             'context':context,
#         }
#
# class DocumentDocument(models.Model):
#     _name = 'document.document'
#
#     name = fields.Char("Name")
#
# class DocumentStatus(models.Model):
#     _name = 'document.status'
#
#     name = fields.Char("Name")
#
# class document_directory(models.Model):
#     _inherit = 'document.directory'
#
#     @api.multi
#     @api.depends('parent_id')
#     def _compute_is_parent(self):
#         for line in self:
#             if line.parent_id.id == False:
#                 line.is_parent = True
#             if line.parent_id.id != False:
#                 line.is_parent = False
#
#     pro_attachment_ids = fields.One2many('project.attachment', 'parent_id', 'Attachments')
#     is_parent = fields.Boolean(compute='_compute_is_parent', store=True, readonly=False, string="Parent")
#
#
# class project_stages(models.Model):
#     _name = 'project.stages'
#     _order = "sequence, id"
#
#     name = fields.Char('Name')
#     sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
#     project_id = fields.Many2one('project.project', 'Project')
#     stage_line_id = fields.Many2one('project.stages.line', 'Stage')
#     attachment_id = fields.One2many('project.attachment', 'stage_id', 'Attachments')
#     state = fields.Selection([('no', 'No'),('yes', 'Yes')], 'Status',
#                                     select=True, copy=False)
#     seq = fields.Integer(related='stage_line_id.seq', store=True, string='Sequence')
#
#     _defaults = {
#         'state': 'no'}
#
# class project_schedule(models.Model):
#     _name = 'project.schedule'
#     _order = "seq asc"
#
#
#     name = fields.Char('Name')
#     sequence = fields.Integer('Sequence', help="Gives the sequence order when displaying a list of Projects.")
#     seq = fields.Integer('Seq')
#     amount = fields.Float('Inst Amount')
#     due_on = fields.Char('Due on')
#     stage_total = fields.Float(compute='_compute_stage_total',  store=True, string='Stage Total')
#
#     project_id = fields.Many2one('project.project', 'Project')
#
#
#     @api.multi
#     @api.depends('amount')
#     def _compute_stage_total(self):
#         for line in self:
#             for lines in line.project_id.schedule_id:
#                 if lines.seq <= line.seq:
#                     line.stage_total += lines.amount
#
#
#
# class project_stages_line(models.Model):
#     _name = 'project.stages.line'
#
#     _order = "seq asc"
#
#
#     name = fields.Char('Status')
#     seq = fields.Integer('Sequence')
#     stage_id = fields.One2many('project.stages', 'stage_line_id', 'Stages')
#
# class project_task_estimation(models.Model):
#     _name = 'project.task.estimation'
#
#     @api.multi
#     @api.depends('pro_id','qty','unit_price')
#     def _compute_estimated_cost_sum(self):
#
#         for line in self:
#             line.estimated_cost_sum = line.qty * line.unit_price
#
#
#     @api.onchange('pro_id')
#     def onchange_product_id(self):
#         for line in self:
#             for estimate in line.task_ids1.estimate_ids:
#                 if estimate.pro_id.id==line.pro_id.id:
#                     line.qty = estimate.qty
#
#     def _get_line_numbers(self, cr, uid, ids, context=None):
#         if context is None:
#             context = {}
#         line_num = 1
#
#         if ids:
#             first_line_rec = self.browse(cr, uid, ids[0], context=context)
#             for line_rec in first_line_rec.task_id.estimate_ids:
#                 line_rec.line_no = line_num
#                 line_num += 1
#
#     line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
#     name = fields.Char('Description')
#     task_id = fields.Many2one('project.task', 'Task')
#     task_ids1 = fields.Many2one('project.task', 'Task')
#     project_id = fields.Many2one(related='task_id.project_id', string="Project")
#     pro_id =  fields.Many2one('product.product', 'Resource')
#     qty = fields.Float('Qty', default=1)
#
#     unit_price = fields.Float(related='pro_id.standard_price', string='Unit Price')
#     uom = fields.Many2one(related='pro_id.uom_id',string='Uom')
#     estimated_cost_sum =  fields.Float(compute='_compute_estimated_cost_sum', string='Estimated Cost')
#     qty_used = fields.Float('Consumed Qty', default=0)
#     qty_assigned = fields.Float(string='Assigned quantity')
#     trigger_project_estimation_calc = fields.Integer(compute='_trigger_project_estimation_calc')
#     invoiced_qty = fields.Float('Invoiced Qty', default=0.0)
#
#
#     @api.multi
#     @api.depends('qty')
#     def _trigger_project_estimation_calc(self):
#         # Retrive all product ids related to current project and delete from project_product table
#         project_product_recs_ids = self.env['project.product'].search([('project_id','=',self[0].task_id.project_id.id)])._ids
#         if project_product_recs_ids:
#             sql = ('DELETE FROM project_product '
#                 'WHERE id in {}').format('('+', '.join(str(t) for t in project_product_recs_ids)+')')
#             self.env.cr.execute(sql)
#
#         project = self.env['project.project'].browse(self[0].task_id.project_id.id)
#
#         project_product_list = []
#         prod_dict = {}
#
#         for task in project.task_ids:
#
#             for estimate in task.estimate_ids:
#                 if estimate.pro_id not in prod_dict:
#                     prod_dict[estimate.pro_id] = estimate.qty
#                 else:
#                     prod_dict[estimate.pro_id] = prod_dict[estimate.pro_id]+estimate.qty
#
#         for key, value in prod_dict.items():
#             project_product_dict = {}
#             project_product_dict['name'] = key.id
#             project_product_dict['quantity'] = value
#             project_product_dict['unit_price'] = key.standard_price
#             project_product_dict['estimated_price'] = value*key.standard_price
#             project_product_dict['project_id'] = project.id
#             project_product_list.append(project_product_dict)
#         for rec in project_product_list:
#             self.env['project.product'].create(rec)
#
#
#     @api.onchange('qty_used')
#     @api.multi
#     def _restrict_qty_used(self):
#         if self.qty_used>self.qty_assigned:
#             return {
#                 'warning': {
#                     'title': 'Warning',
#                     'message': "Used qunatity cannot be greater than assigned quantity."
#                 }
#             }
#
# class AccountMoveLine(models.Model):
#     _inherit = 'account.move.line'
#
#
#     @api.model
#     def hide_reconcile_entries(self):
#         if self.env.ref('account.action_account_move_line_reconcile_prompt_values'):
#             self.env.ref('account.action_account_move_line_reconcile_prompt_values').unlink()
#         if self.env.ref('account.account_unreconcile_values'):
#             self.env.ref('account.account_unreconcile_values').unlink()
#         if self.env.ref('account.action_partner_reconcile_actino'):
#             self.env.ref('account.action_partner_reconcile_actino').unlink()
#         if self.env.ref('account.validate_account_move_line_values'):
#             self.env.ref('account.validate_account_move_line_values').unlink()
#
#
#
#
#
#
#
#
#
#
#     @api.multi
#     def reconcile_entry(self):
#         for line in self:
#             line.reconcile_bool = True
#
#     @api.multi
#     def apply_reconcile_entry(self):
#         for line in self:
#             line.reconcile_bool = False
#
#     @api.multi
#     @api.depends('name')
#     def _get_opposite_accounts_cash_bank(self):
#         for temp in self:
#             temp.opp_acc_cash_bank = ""
#             for line in temp.move_id:
#                 for lines in line.line_id:
#                     if lines.id != temp.id:
#                         if lines.account_id.is_cash_bank == True:
#                             temp.opp_acc_cash_bank = lines.account_id.name + "," + temp.opp_acc_cash_bank
#
#
#     @api.multi
#     @api.depends('debit','credit')
#     def get_balance(self):
#         rec = self.env['account.move.line'].search([])
#         for lines in self:
#             balance = 0
#             if lines.crusher_line == True:
#                 move_lines = rec.search([('crusher_line','=',True),('date','<=',lines.date),('id','<',lines.id)])
#                 for move in move_lines:
#                     if move.id != lines.id:
#                         balance += move.debit - move.credit
#                 lines.balance = balance + lines.debit - lines.credit
#
#             if lines.fuel_line == True:
#                 move_lines = rec.search([('fuel_line','=',True),('date','<=',lines.date),('id','<',lines.id)])
#                 for move in move_lines:
#                     if move.id != lines.id:
#                         balance += move.debit - move.credit
#                 lines.balance = balance + lines.debit - lines.credit
#
#     @api.multi
#     @api.depends('tax_ids','amount')
#     def _get_subtotal_crusher_report(self):
#         for lines in self:
#             taxi = 0
#             taxe = 0
#             for tax in lines.tax_ids:
#                 if tax.price_include == True:
#                     taxi = tax.amount
#                 if tax.price_include == False:
#                     taxe += tax.amount
#             lines.tax_amount = (lines.amount)/(1+taxi)*(taxi+taxe)
#             lines.sub_total = (lines.amount)/(1+taxi)
#
#
#     description2 =  fields.Char('Description')
#     project_id = fields.Many2one('project.project', 'Project')
#     opp_acc_cash_bank = fields.Char(compute='_get_opposite_accounts_cash_bank', store=True, string='Account Opposite')
#     vehicle_id = fields.Many2one('fleet.vehicle','Vehicle')
#     driver_stmt_id = fields.Many2one('driver.daily.statement','Vehicle')
#     is_crusher = fields.Boolean(related='account_id.is_crusher', store=True, string='Is Crusher')
#     is_fuel_pump = fields.Boolean(related='account_id.is_fuel_pump', store=True, string='Is Fuel Pump')
#     bill_no = fields.Char('Bill No')
#     contractor_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Contractor')
#     vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
#     location_id = fields.Many2one('stock.location', 'Site Name')
#     product_id = fields.Many2one('product.product', 'Material')
#     qty = fields.Float('Qty')
#     rate = fields.Float('Rate')
#     amount = fields.Float('Amount')
#     tax_ids = fields.Many2many('account.tax', string="GST")
#     balance = fields.Float(compute="get_balance",string='Balance')
#     driver_stmt_line_id = fields.Many2one('driver.daily.statement.line')
#     partner_stmt_line_id = fields.Many2one('partner.daily.statement.line')
#     rent_stmt_id = fields.Many2one('rent.vehicle.statement')
#     diesel_pump_line_id = fields.Many2one('diesel.pump.line')
#     mach_fuel_collection_id = fields.Many2one('machinery.fuel.collection')
#     round_off = fields.Float('Round Off')
#     sub_total = fields.Float('Sub Total',compute="_get_subtotal_crusher_report")
#     tax_amount = fields.Float('Tax Amount',compute="_get_subtotal_crusher_report")
#
#
#
#
#
# class account_voucher(models.Model):
#     _inherit = 'account.voucher'
#
#
#     description =  fields.Char('Description')
#
#     def first_move_line_get(self, cr, uid, voucher_id, move_id, company_currency, current_currency, context=None):
#         '''
#         Return a dict to be use to create the first account move line of given voucher.
#
#         :param voucher_id: Id of voucher what we are creating account_move.
#         :param move_id: Id of account move where this line will be added.
#         :param company_currency: id of currency of the company to which the voucher belong
#         :param current_currency: id of currency of the voucher
#         :return: mapping between fieldname and value of account move line to create
#         :rtype: dict
#         '''
#         voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
#         debit = credit = 0.0
#         # TODO: is there any other alternative then the voucher type ??
#         # ANSWER: We can have payment and receipt "In Advance".
#         # TODO: Make this logic available.
#         # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
#         if voucher.type in ('purchase', 'payment'):
#             credit = voucher.paid_amount_in_company_currency
#         elif voucher.type in ('sale', 'receipt'):
#             debit = voucher.paid_amount_in_company_currency
#         if debit < 0: credit = -debit; debit = 0.0
#         if credit < 0: debit = -credit; credit = 0.0
#         sign = debit - credit < 0 and -1 or 1
#         #set the first line of the voucher
#
#         move_line = {
#                 'name': voucher.name or '/',
#                 'debit': debit,
#                 'credit': credit,
#                 'account_id': voucher.account_id.id,
#                 'move_id': move_id,
#                 'journal_id': voucher.journal_id.id,
#                 'period_id': voucher.period_id.id,
#                 'partner_id': voucher.partner_id.id,
#                 'currency_id': company_currency != current_currency and  current_currency or False,
#                 'amount_currency': (sign * abs(voucher.amount) # amount < 0 for refunds
#                     if company_currency != current_currency else 0.0),
#                 'date': voucher.date,
#                 'date_maturity': voucher.date_due,
#                 'description2': voucher.description
#             }
#         return move_line
#
#
#     def writeoff_move_line_get(self, cr, uid, voucher_id, line_total, move_id, name, company_currency, current_currency, context=None):
#         '''
#         Set a dict to be use to create the writeoff move line.
#
#         :param voucher_id: Id of voucher what we are creating account_move.
#         :param line_total: Amount remaining to be allocated on lines.
#         :param move_id: Id of account move where this line will be added.
#         :param name: Description of account move line.
#         :param company_currency: id of currency of the company to which the voucher belong
#         :param current_currency: id of currency of the voucher
#         :return: mapping between fieldname and value of account move line to create
#         :rtype: dict
#         '''
#         currency_obj = self.pool.get('res.currency')
#         move_line = {}
#
#         voucher = self.pool.get('account.voucher').browse(cr,uid,voucher_id,context)
#         current_currency_obj = voucher.currency_id or voucher.journal_id.company_id.currency_id
#
#         if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
#             diff = line_total
#             account_id = False
#             write_off_name = ''
#             if voucher.payment_option == 'with_writeoff':
#                 account_id = voucher.writeoff_acc_id.id
#                 write_off_name = voucher.comment
#             elif voucher.partner_id:
#                 if voucher.type in ('sale', 'receipt'):
#                     account_id = voucher.partner_id.property_account_receivable.id
#                 else:
#                     account_id = voucher.partner_id.property_account_payable.id
#             else:
#                 # fallback on account of voucher
#                 account_id = voucher.account_id.id
#             sign = voucher.type == 'payment' and -1 or 1
#             move_line = {
#                 'name': write_off_name or name,
#                 'account_id': account_id,
#                 'move_id': move_id,
#                 'partner_id': voucher.partner_id.id,
#                 'date': voucher.date,
#                 'credit': diff > 0 and diff or 0.0,
#                 'debit': diff < 0 and -diff or 0.0,
#                 'amount_currency': company_currency <> current_currency and (sign * -1 * voucher.writeoff_amount) or 0.0,
#                 'currency_id': company_currency <> current_currency and current_currency or False,
#                 'analytic_account_id': voucher.analytic_id and voucher.analytic_id.id or False,
#                 'description2': voucher.description
#             }
#
#         return move_line
#
#
#     def action_move_line_create(self, cr, uid, ids, context=None):
#         '''
#         Confirm the vouchers given in ids and create the journal entries for each of them
#         '''
#         if context is None:
#             context = {}
#         move_pool = self.pool.get('account.move')
#         move_line_pool = self.pool.get('account.move.line')
#         for voucher in self.browse(cr, uid, ids, context=context):
#             local_context = dict(context, force_company=voucher.journal_id.company_id.id)
#             if voucher.move_id:
#                 continue
#             company_currency = self._get_company_currency(cr, uid, voucher.id, context)
#             current_currency = self._get_current_currency(cr, uid, voucher.id, context)
#             # we select the context to use accordingly if it's a multicurrency case or not
#             context = self._sel_context(cr, uid, voucher.id, context)
#             # But for the operations made by _convert_amount, we always need to give the date in the context
#             ctx = context.copy()
#             ctx.update({'date': voucher.date})
#             # Create the account move record.
#             move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, voucher.id, context=context), context=context)
#             # Get the name of the account_move just created
#             name = move_pool.browse(cr, uid, move_id, context=context).name
#             # Create the first line of the voucher
#
#             move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,voucher.id, move_id, company_currency, current_currency, local_context), local_context)
#             move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
#             line_total = move_line_brw.debit - move_line_brw.credit
#             rec_list_ids = []
#             if voucher.type == 'sale':
#                 line_total = line_total - self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
#             elif voucher.type == 'purchase':
#                 line_total = line_total + self._convert_amount(cr, uid, voucher.tax_amount, voucher.id, context=ctx)
#             # Create one move line per voucher line where amount is not 0.0
#             line_total, rec_list_ids = self.voucher_move_line_create(cr, uid, voucher.id, line_total, move_id, company_currency, current_currency, context)
#
#             # Create the writeoff line if needed
#             ml_writeoff = self.writeoff_move_line_get(cr, uid, voucher.id, line_total, move_id, name, company_currency, current_currency, local_context)
#
#             if ml_writeoff:
#                 move_line_pool.create(cr, uid, ml_writeoff, local_context)
#             # We post the voucher.
#             self.write(cr, uid, [voucher.id], {
#                 'move_id': move_id,
#                 'state': 'posted',
#                 'number': name,
#             })
#             if voucher.journal_id.entry_posted:
#                 move_pool.post(cr, uid, [move_id], context={})
#             # We automatically reconcile the account move lines.
#             reconcile = False
#             for rec_ids in rec_list_ids:
#                 if len(rec_ids) >= 2:
#                     reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=voucher.writeoff_acc_id.id, writeoff_period_id=voucher.period_id.id, writeoff_journal_id=voucher.journal_id.id)
#         return True
#
#
#     def voucher_move_line_create(self, cr, uid, voucher_id, line_total, move_id, company_currency, current_currency, context=None):
#         '''
#         Create one account move line, on the given account move, per voucher line where amount is not 0.0.
#         It returns Tuple with tot_line what is total of difference between debit and credit and
#         a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).
#
#         :param voucher_id: Voucher id what we are working with
#         :param line_total: Amount of the first line, which correspond to the amount we should totally split among all voucher lines.
#         :param move_id: Account move wher those lines will be joined.
#         :param company_currency: id of currency of the company to which the voucher belong
#         :param current_currency: id of currency of the voucher
#         :return: Tuple build as (remaining amount not allocated on voucher lines, list of account_move_line created in this method)
#         :rtype: tuple(float, list of int)
#         '''
#         if context is None:
#             context = {}
#         move_line_obj = self.pool.get('account.move.line')
#         currency_obj = self.pool.get('res.currency')
#         tax_obj = self.pool.get('account.tax')
#         tot_line = line_total
#         rec_lst_ids = []
#
#         date = self.read(cr, uid, [voucher_id], ['date'], context=context)[0]['date']
#         ctx = context.copy()
#         ctx.update({'date': date})
#         voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=ctx)
#         voucher_currency = voucher.journal_id.currency or voucher.company_id.currency_id
#         ctx.update({
#             'voucher_special_currency_rate': voucher_currency.rate * voucher.payment_rate ,
#             'voucher_special_currency': voucher.payment_rate_currency_id and voucher.payment_rate_currency_id.id or False,})
#         prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
#         for line in voucher.line_ids:
#             #create one move line per voucher line where amount is not 0.0
#             # AND (second part of the clause) only if the original move line was not having debit = credit = 0 (which is a legal value)
#             if not line.amount and not (line.move_line_id and not float_compare(line.move_line_id.debit, line.move_line_id.credit, precision_digits=prec) and not float_compare(line.move_line_id.debit, 0.0, precision_digits=prec)):
#                 continue
#             # convert the amount set on the voucher line into the currency of the voucher's company
#             # this calls res_curreny.compute() with the right context, so that it will take either the rate on the voucher if it is relevant or will use the default behaviour
#             amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, voucher.id, context=ctx)
#             # if the amount encoded in voucher is equal to the amount unreconciled, we need to compute the
#             # currency rate difference
#             if line.amount == line.amount_unreconciled:
#                 if not line.move_line_id:
#                     raise osv.except_osv(_('Wrong voucher line'),_("The invoice you are willing to pay is not valid anymore."))
#                 sign = line.type =='dr' and -1 or 1
#                 currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
#             else:
#                 currency_rate_difference = 0.0
#             move_line = {
#                 'journal_id': voucher.journal_id.id,
#                 'period_id': voucher.period_id.id,
#                 'name': line.name or '/',
#                 'account_id': line.account_id.id,
#                 'move_id': move_id,
#                 'partner_id': voucher.partner_id.id,
#                 'currency_id': line.move_line_id and (company_currency != line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
#                 'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
#                 'quantity': 1,
#                 'credit': 0.0,
#                 'debit': 0.0,
#                 'date': voucher.date,
#                 'description2': voucher.description
#             }
#             if amount < 0:
#                 amount = -amount
#                 if line.type == 'dr':
#                     line.type = 'cr'
#                 else:
#                     line.type = 'dr'
#
#             if (line.type=='dr'):
#                 tot_line += amount
#                 move_line['debit'] = amount
#             else:
#                 tot_line -= amount
#                 move_line['credit'] = amount
#
#             if voucher.tax_id and voucher.type in ('sale', 'purchase'):
#                 move_line.update({
#                     'account_tax_id': voucher.tax_id.id,
#                 })
#
#             # compute the amount in foreign currency
#             foreign_currency_diff = 0.0
#             amount_currency = False
#             if line.move_line_id:
#                 # We want to set it on the account move line as soon as the original line had a foreign currency
#                 if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
#                     # we compute the amount in that foreign currency.
#                     if line.move_line_id.currency_id.id == current_currency:
#                         # if the voucher and the voucher line share the same currency, there is no computation to do
#                         sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
#                         amount_currency = sign * (line.amount)
#                     else:
#                         # if the rate is specified on the voucher, it will be used thanks to the special keys in the context
#                         # otherwise we use the rates of the system
#                         amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
#                 if line.amount == line.amount_unreconciled:
#                     foreign_currency_diff = line.move_line_id.amount_residual_currency - abs(amount_currency)
#
#             move_line['amount_currency'] = amount_currency
#             voucher_line = move_line_obj.create(cr, uid, move_line)
#             rec_ids = [voucher_line, line.move_line_id.id]
#
#             if not currency_obj.is_zero(cr, uid, voucher.company_id.currency_id, currency_rate_difference):
#                 # Change difference entry in company currency
#                 exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
#                 new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
#                 move_line_obj.create(cr, uid, exch_lines[1], context)
#                 rec_ids.append(new_id)
#
#             if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
#                 # Change difference entry in voucher currency
#                 move_line_foreign_currency = {
#                     'journal_id': line.voucher_id.journal_id.id,
#                     'period_id': line.voucher_id.period_id.id,
#                     'name': _('change')+': '+(line.name or '/'),
#                     'account_id': line.account_id.id,
#                     'move_id': move_id,
#                     'partner_id': line.voucher_id.partner_id.id,
#                     'currency_id': line.move_line_id.currency_id.id,
#                     'amount_currency': (-1 if line.type == 'cr' else 1) * foreign_currency_diff,
#                     'quantity': 1,
#                     'credit': 0.0,
#                     'debit': 0.0,
#                     'date': line.voucher_id.date,
#
#                 }
#                 new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
#                 rec_ids.append(new_id)
#             if line.move_line_id.id:
#                 rec_lst_ids.append(rec_ids)
#         return (tot_line, rec_lst_ids)


class purchase_item_category(models.Model):
    _name = 'purchase.item.category'

    name = fields.Char('Name')
    account_id = fields.Many2one('account.account','Related Account')

class purchase_order(models.Model):
    _inherit = 'purchase.order'
    _order = 'name desc'

    READONLY_STATES = {
        'confirmed': [('readonly', True)],
        'approved': [('readonly', True)],
        'done': [('readonly', True)]
    }

    # @api.onchange('project_id')
    # def _onchange_task_selection(self):
    # @api.one
    # @api.onchange('partner_id')
    # def _onchange_partner_id(self):
    #     if self.partner_id:
    #         self.account_id = self.partner_id.property_account_payable.id
    def do_merge(self, cr, uid, ids, context=None):
        """
        To merge similar type of purchase orders.
        Orders will only be merged if:
        * Purchase Orders are in draft
        * Purchase Orders belong to the same partner
        * Purchase Orders are have same stock location, same pricelist, same currency
        Lines will only be merged if:
        * Order lines are exactly the same except for the quantity and unit

         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: the ID or list of IDs
         @param context: A standard dictionary

         @return: new purchase order id

        """

        # TOFIX: merged order line should be unlink
        def make_key(br, fields):
            list_key = []
            for field in fields:
                field_val = getattr(br, field)
                if field in ('product_id', 'account_analytic_id'):
                    if not field_val:
                        field_val = False
                if isinstance(field_val, browse_record):
                    field_val = field_val.id
                elif isinstance(field_val, browse_null):
                    field_val = False
                elif isinstance(field_val, browse_record_list):
                    field_val = ((6, 0, tuple([v.id for v in field_val])),)
                list_key.append((field, field_val))
            list_key.sort()
            return tuple(list_key)

        context = dict(context or {})

        # Compute what the new orders should contain
        new_orders = {}

        order_lines_to_move = {}
        purchase_request_list = []
        for porder in [order for order in self.browse(cr, uid, ids, context=context) if order.state == 'approved']:
            order_key = make_key(porder, ('partner_id', 'location_id', 'pricelist_id', 'currency_id'))
            new_order = new_orders.setdefault(order_key, ({}, []))

            new_order[1].append(porder.id)
            order_infos = new_order[0]
            purchase_request_list.append(porder.site_purchase_id.id)
            order_lines_to_move.setdefault(order_key, [])
            minimum_plann_date = datetime.strptime(porder.date_order,"%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
            if not order_infos:


                order_infos.update({
                    'origin': porder.origin,
                    'date_order': porder.date_order,
                    'minimum_plann_date':minimum_plann_date,
                    'partner_id': porder.partner_id.id,
                    'dest_address_id': porder.dest_address_id.id,
                    'picking_type_id': porder.picking_type_id.id,
                    'location_id': porder.location_id.id,
                    'pricelist_id': porder.pricelist_id.id,
                    'currency_id': porder.currency_id.id,
                    'state': 'approved',
                    'packing_charge':porder.packing_charge,
                    'packing_tax_id':porder.packing_tax_id.id,
                    'loading_tax':porder.loading_tax,
                    'loading_tax_id':porder.loading_tax_id.id,
                    'transport_cost':porder.transport_cost,
                    'transport_cost_tax_id':porder.transport_cost_tax_id,
                    'order_line': {},
                    'merged_po':True,
                    'project_id':porder.project_id.id,
                    'company_contractor_id':porder.project_id.company_contractor_id.id,
                    'notes': '%s' % (porder.notes or '',),
                    'minimum_plann_date':minimum_plann_date,
                    'maximum_planned_date':minimum_plann_date,
                    'vehicle_id':porder.vehicle_id.id,
                    'vehicle_agent_id':porder.vehicle_agent_id.id,
                    'fiscal_position': porder.fiscal_position and porder.fiscal_position.id or False,
                })
            else:
                if porder.partner_id.id != order_infos['partner_id']:
                    raise ValidationError(_(
                        "Supplier is not equal"))
                if porder.date_order < order_infos['date_order']:
                    order_infos['date_order'] = porder.date_order
                if porder.notes:
                    order_infos['notes'] = (order_infos['notes'] or '') + ('\n%s' % (porder.notes,))
                if porder.origin:
                    order_infos['origin'] = (order_infos['origin'] or '') + ' ' + porder.origin
                if porder.packing_charge:
                    order_infos['packing_charge'] = order_infos['packing_charge'] + porder.packing_charge
                if porder.loading_tax:
                    order_infos['loading_tax'] = order_infos['loading_tax'] + porder.loading_tax
                if porder.packing_charge:
                    order_infos['transport_cost'] = order_infos['transport_cost'] + porder.transport_cost



            order_lines_to_move[order_key] += [order_line.id for order_line in porder.order_line
                                               if order_line.state != 'cancel']

        allorders = []
        orders_info = {}
        for order_key, (order_data, old_ids) in new_orders.iteritems():
            # skip merges with only one order
            if len(old_ids) < 2:
                allorders += (old_ids or [])
                continue

            # cleanup order line data
            for key, value in order_data['order_line'].iteritems():
                del value['uom_factor']
                value.update(dict(key))


            order_list = []
            order_line = {}
            for line in order_lines_to_move[order_key]:
                order_line_obj = self.pool.get('purchase.order.line').browse(cr, uid, line, context=context)
                if not order_line_obj.product_id.id in order_line.keys():
                    order_line.update({order_line_obj.product_id.id:{'product_id':order_line_obj.product_id.id,
                                                                 'rate':order_line_obj.expected_rate,
                                                                     'name':order_line_obj.product_id.name,
                                                                     'unit':order_line_obj.product_id.uom_id.id,
                                                                     'qty':order_line_obj.required_qty,
                                                                 'taxes_id':[(6,0,order_line_obj.taxes_id.ids)]}})
                else:

                    if order_line_obj.expected_rate != order_line[order_line_obj.product_id.id]['rate'] or order_line_obj.taxes_id.ids != order_line[order_line_obj.product_id.id]['taxes_id'][0][2]:
                        raise ValidationError(_(
                            "Rate or taxes is not equal"))
                    else:
                        order_line[order_line_obj.product_id.id]['qty'] = order_line[order_line_obj.product_id.id]['qty'] +order_line_obj.required_qty

                # c[2244444444444444]
            line_list = []
            line_values={}
            print "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu",order_line
            for key,item in order_line.items():
                print "ooooooooooooooooooooooooooooooooo",order_line[key]['product_id']
                line_values ={'product_id':order_line[key]['product_id'],
                                    'expected_rate':order_line[key]['rate'],
                                    'required_qty':order_line[key]['qty'],
                                    'name':order_line[key]['name'],
                                    'product_uom':order_line[key]['unit'],
                                    'taxes_id':order_line[key]['taxes_id']}
                line_list.append((0,0,line_values))


            order_data['order_line'] = line_list
            order_data['state'] = 'approved'

            order_data['site_purchase_ids']=[(6,0,purchase_request_list)]

            # create the new order
            context.update({'mail_create_nolog': True})
            neworder_id = self.create(cr, uid, order_data)
            self.message_post(cr, uid, [neworder_id], body=_("RFQ created"), context=context)
            orders_info.update({neworder_id: old_ids})
            allorders.append(neworder_id)
            # neworder_id.write({'state':'approved'})
            # make triggers pointing to the old orders point to the new order
            for old_id in old_ids:

                self.signal_workflow(cr, uid, [old_id], 'purchase_cancel')
        if not orders_info:
            raise ValidationError(_(
                "Supplier or Location is not equal"))
        return orders_info

    @api.multi
    @api.depends('name')
    def _count_invoices(self):
        for line in self:
            line.invoice_count = 0
            invoice_ids = self.env['hiworth.invoice'].search([('origin','=',line.name)])
            line.invoice_count = len(invoice_ids)


    @api.model
    def _default_currency(self):
        journal = self._default_journal()
        return journal.currency or journal.company_id.currency_id or self.env.user.company_id.currency_id

    @api.model
    def _default_journal(self):
        inv_type = ['purchase']
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', 'in', inv_type),
            ('company_id', '=', company_id),
        ]
        return self.env['account.journal'].search(domain, limit=1)


    @api.onchange('minimum_plann_date')
    def onchage_minimum_plann_date(self):
        if self.date_order:
            self.minimum_planned_date = datetime.strptime(self.date_order,"%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")

    @api.model
    def create(self,vals):
        if vals.get('supplier_ids'):
            vals['name'] =self.env['ir.sequence'].next_by_code('rfq.code')

        if vals.get('partner_id'):
            vals.update({'state':'confirmed'})
        if vals.get('merged_po',False):
            vals.update({'state': 'approved'})
        res = super(purchase_order, self).create(vals)
        return res

    @api.multi
    def purchase_confirm(self):

        self.minimum_planned_date = self.minimum_plann_date
        if self.amount_total > 1000:
            if not self.env.user.has_group('base.group_erp_manager') and not self.comparison_id:
                raise Warning(_('You have not access to approve this Purchase Order.'))
            else:
                self.state = 'approved1'
        else:
            self.state = 'approved'
        return True

    @api.multi
    def purchase_approve(self):
        for rec in self:
            self.state = 'approved'
        return True

    @api.multi
    @api.depends('order_line','packing_tax_id','loading_tax_id','transport_cost_tax_id','packing_charge','loading_tax','transport_cost')
    def compute_new_gross_total(self):
        for rec in self:
            additonal_charge = 0
            other_charge = 0
            if rec.packing_tax_id:
                if rec.packing_tax_id.price_include:

                    additonal_charge += rec.packing_charge / (1+rec.packing_tax_id.amount)
                else:
                    additonal_charge += rec.packing_charge
            else:
                other_charge += rec.packing_charge

            if rec.loading_tax_id:
                if rec.loading_tax_id.price_include:
                    additonal_charge += rec.loading_tax / (1+rec.loading_tax_id.amount)
                else:
                    additonal_charge += rec.loading_tax
            else:
                other_charge += rec.loading_tax

            if rec.transport_cost_tax_id:
                if rec.transport_cost_tax_id.price_include:
                    additonal_charge += rec.transport_cost / (1+rec.transport_cost_tax_id.amount)
                else:
                    additonal_charge += rec.transport_cost
            else:
                other_charge += rec.transport_cost

            amount_untaxed = 0

            non_taxabale = 0
            for line in rec.order_line:

                if line.non_taxable_amount == 0:
                    amount_untaxed += line.new_sub_total

                else:
                    non_taxabale +=line.non_taxable_amount
            rec.tax_amount = sum(rec.order_line.mapped('tax_amount'))
            rec.other_charge = other_charge
            if amount_untaxed >0:
                rec.new_gross_total = amount_untaxed
            else:
                rec.new_gross_total = sum(rec.order_line.mapped('new_sub_total'))
            rec.non_taxable_amount =non_taxabale
    @api.multi
    @api.depends('packing_tax_id','loading_tax_id','transport_cost_tax_id','order_line','packing_charge','loading_tax','transport_cost')
    def compute_new_gst(self):
        for line in self:
            sgst_tax = 0
            cgst_tax= 0
            igst_tax=0
            if line.packing_tax_id:
                if line.packing_tax_id.price_include:
                    if line.packing_tax_id.tax_type == 'gst':
                        cgst_tax += ((line.packing_charge / (
                                    1 + line.packing_tax_id.amount)) * line.packing_tax_id.amount) / 2
                        sgst_tax += ((line.packing_charge / (1 + line.packing_tax_id.amount)) * line.packing_tax_id.amount)/2
                    else:
                        igst_tax += ((line.packing_charge / (
                                1 + line.packing_tax_id.amount)) * line.packing_tax_id.amount)

                else:
                    if line.packing_tax_id.tax_type == 'gst':
                        cgst_tax += (line.packing_charge * line.packing_tax_id.amount) / 2
                        sgst_tax += (line.packing_charge * line.packing_tax_id.amount) / 2
                    else:
                        igst_tax += (line.packing_charge * line.packing_tax_id.amount)

            if line.loading_tax_id:
                if line.loading_tax_id.price_include:
                    if line.loading_tax_id.tax_type == 'gst':
                        cgst_tax += ((line.loading_tax / (
                                    1 + line.loading_tax_id.amount)) * line.loading_tax_id.amount) / 2
                        sgst_tax += ((line.loading_tax / (1 + line.loading_tax_id.amount)) * line.loading_tax_id.amount)/2
                    else:
                        igst_tax += ((line.loading_tax / (
                                1 + line.loading_tax_id.amount)) * line.loading_tax_id.amount)


                else:
                    if line.loading_tax_id.tax_type == 'gst':
                        cgst_tax += (line.loading_tax  * line.loading_tax_id.amount) / 2
                        sgst_tax += (line.loading_tax  * line.loading_tax_id.amount) / 2

                    else:
                        igst_tax += (line.loading_tax  * line.loading_tax_id.amount)

            if line.transport_cost_tax_id:
                if line.transport_cost_tax_id.price_include:
                    if line.transport_cost_tax_id.tax_type == 'gst':
                        cgst_tax += ((line.transport_cost / (
                                1 + line.transport_cost_tax_id.amount)) * line.transport_cost_tax_id.amount) / 2
                        sgst_tax += ((line.transport_cost / (
                                    1 + line.transport_cost_tax_id.amount)) * line.transport_cost_tax_id.amount) / 2
                    else:
                        igst_tax += ((line.transport_cost / (
                                1 + line.transport_cost_tax_id.amount)) * line.transport_cost_tax_id.amount)


                else:
                    if line.transport_cost_tax_id.tax_type == 'gst':
                        cgst_tax += (line.transport_cost * line.transport_cost_tax_id.amount) / 2
                        sgst_tax += (line.transport_cost * line.transport_cost_tax_id.amount) / 2
                    else:
                        igst_tax += (line.transport_cost * line.transport_cost_tax_id.amount)


            for order in line.order_line:

                if order.non_taxable_amount == 0:
                    sgst_tax += order.gst_tax /2
                    cgst_tax += order.gst_tax / 2
                    igst_tax += order.igst_tax




            line.new_sgst_tax =  sgst_tax
            line.new_cgst_tax =cgst_tax
            line.new_igst_tax =igst_tax
    @api.multi
    @api.depends('order_line','round_off_amount','discount_amount','packing_charge','loading_tax','transport_cost')
    def compute_gst(self):
        for rec in self:
            rec.sgst_tax = 0.0
            rec.cgst_tax = 0.0
            rec.igst_tax = 0.0
            if rec.order_line:
                for line in rec.order_line:
                    rec.sgst_tax += line.gst_tax/2
                    rec.cgst_tax += line.gst_tax/2
                    rec.igst_tax += line.igst_tax

            rec.amount_total = round(rec.new_sgst_tax + rec.new_cgst_tax +rec.new_igst_tax+rec.new_gross_total +rec.non_taxable_amount + rec.other_charge+  rec.round_off_amount - rec.discount_amount, 2)
            if rec.amount_total2 == 0.0:
                rec.amount_total2 =rec.amount_total

    @api.model
    def _default_write_off_account(self):
        return self.env['res.company'].browse(self.env['res.company']._company_default_get('hiworth.invoice')).write_off_account_id

    @api.model
    def _default_discount_account(self):
        return self.env['res.company'].browse(self.env['res.company']._company_default_get('hiworth.invoice')).discount_account_id

    @api.onchange('account_id')
    def onchange_account(self):
        account_ids = []
        account_ids = [account.id for account in self.env['account.account'].search([('company_id','=',self.company_id.id)])]
        return {
                'domain': {
                    'account_id': [('id','in',account_ids)]
                }
            }

    @api.constrains('bid_validity')
    def constrain_bid_validity(self):
        for rec in self:
            if rec.bid_validity:
                date = datetime.strptime(rec.date_order, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                if date > rec.bid_validity:
                    raise ValidationError(
                        _("Qutotation Valid Date must be equal or greater than Order Date"))



    @api.constrains('maximum_planned_date')
    def constrain_maximum_planned_date(self):
        for rec in self:
            if rec.maximum_planned_date:
                date = datetime.strptime(rec.date_order, "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d")
                if date > rec.maximum_planned_date:
                    raise ValidationError(
                        _("Maximum Expected Date must be equal or greater than Order Date"))


    STATE_SELECTION = [
        ('draft', 'Waiting'),
        ('sent', 'RFQ'),
        ('bid', 'Bid Received'),
        ('confirmed', 'First Approval'),
    ('approved1', 'Second  Approval'),
        ('approved', 'Order Placed'),
        ('except_picking', 'Shipping Exception'),
        ('except_invoice', 'Invoice Exception'),
        ('done', 'Received'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
    ]

    READONLY_STATES = {

    }

    state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
                                  help="The status of the purchase order or the quotation request. "
                                       "A request for quotation is a purchase order in a 'Draft' status. "
                                       "Then the order has to be confirmed by the user, the status switch "
                                       "to 'Confirmed'. Then the supplier must confirm the order to change "
                                       "the status to 'Approved'. When the purchase order is paid and "
                                       "received, the status becomes 'Done'. If a cancel action occurs in "
                                       "the invoice or in the receipt of goods, the status becomes "
                                       "in exception.",
                                  select=True, copy=False)
    journal_id2 = fields.Many2one('account.journal', string='Journal',
        default=_default_journal, states=READONLY_STATES,
        domain="[('type', '=', 'purchase')]")
    partner_id = fields.Many2one('res.partner', 'Supplier', required=False,
            change_default=True, track_visibility='always',states=READONLY_STATES,)
    invoice_created = fields.Boolean('Invoice Created', default=False)
    invoice_count = fields.Integer(compute='_count_invoices', string='Invoice Nos')
    order_line = fields.One2many('purchase.order.line', 'order_id', 'Order Lines',
                                      states=READONLY_STATES,
                                      copy=True)
    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, states={'draft': [('readonly', False)]},
        default=_default_currency, track_visibility='always')
    is_requisition = fields.Boolean('Is Requisition', default = True)
    requisition_id = fields.Many2one('purchase.order', 'Purchase Requisition')
    account_id = fields.Many2one('account.account', 'Account', states=READONLY_STATES)
    sgst_tax = fields.Float(compute="compute_gst", store=True, string="SGST Amount")
    cgst_tax = fields.Float(compute="compute_gst", store=True, string="CGST Amount")
    igst_tax = fields.Float(compute="compute_gst", store=True, string="IGST Amount")
    new_sgst_tax = fields.Float(compute='compute_new_gst',store=True,string="SGST Amount")
    new_cgst_tax = fields.Float(compute='compute_new_gst', store=True, string="CGST Amount")
    new_igst_tax = fields.Float(compute='compute_new_gst', store=True, string="IGST Amount")
    other_tax_charge = fields.Float("Other Tax")
    additional_charge = fields.Float("Additonal charge")
    other_igst_tax = fields.Float("Other Tax IGST")
    non_taxable_amount = fields.Float(compute='compute_new_gross_total',store=True,string="Non-Taxable Amount")
    new_gross_total = fields.Float(compute='compute_new_gross_total',store=True,string="Gross Total")
    tax_amount = fields.Float(compute='compute_new_gross_total',store=True,string="Tax")
    amount_total2 = fields.Float(compute="compute_gst", string='Total', store=True, help="The total amount")
    amount_total = fields.Float(compute="compute_gst", string='Total', store=True, help="The total amount")
    invoice_date = fields.Date('Invoice Date')
    round_off_amount = fields.Float('Round off Amount (+/-)', )
    round_off_account = fields.Many2one('account.account', 'Round off Account', states=READONLY_STATES,
     default=_default_write_off_account)

    discount_amount = fields.Float('Discount Amount',)
    discount_account = fields.Many2one('account.account', 'Discount Account', states=READONLY_STATES,
     default=_default_discount_account)
    order_line = fields.One2many('purchase.order.line', 'order_id', 'Order Lines',
                        readonly=False, copy=True)
    maximum_planned_date = fields.Date('Maximum Expected Date')
    project_id = fields.Many2one('project.project',"Project")
    location_id = fields.Many2one('stock.location', domain=[('usage','=','internal')])
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist', required=False, states=READONLY_STATES, help="The pricelist sets the currency used for this purchase order. It also computes the supplier price for the selected products/quantities.")
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")
    site_purchase_id = fields.Many2one('site.purchase',"Site Purchase")
    other_charge = fields.Float(String="Other Charge")
    deliver_to = fields.Text("Deliver To")
    company_contractor_id = fields.Many2one('res.partner',string="Company")
    supplier_ids = fields.Many2many('res.partner','purchase_order_res_partner_rel','order_id','partner_id',domain="[('supplier','=',True)]",string="Suppliers")
    minimum_plann_date = fields.Date(string='Minimum Expected Date')
    comparison_id = fields.Many2one('purchase.comparison',"Comparison No")
    quotation_id = fields.Many2one('purchase.order',"RFQ No")
    packing_charge = fields.Float("Packing Charge")
    packing_tax_id = fields.Many2one('account.tax',"Tax",domain="[('parent_id','=',False)]")
    loading_tax = fields.Float("Loading Charge")
    loading_tax_id = fields.Many2one('account.tax',"Tax",domain="[('parent_id','=',False)]")
    transport_cost = fields.Float("Transport Cost")
    transport_cost_tax_id = fields.Many2one('account.tax',"Tax",domain="[('parent_id','=',False)]")
    vehicle_agent_id = fields.Many2one('res.partner', 'Vehicle Agent')
    merged_po = fields.Boolean("Merged PO",default=False)
    site_purchase_ids = fields.Many2many('site.purchase','purase_order_site_purchase_rel','order_id','site_purchase_id',"Purchase Request No/s")
    additional_terms = fields.Text()


    @api.multi
    def write(self,vals):
        if not self.quotation_id and not self.comparison_id:
            if vals.get('order_line',False):
                for li in vals.get('order_line',False):
                    if li[0]==1:
                        line_id = self.env['purchase.order.line'].browse(li[1])
                        if li[2].get('required_qty') >= 0:
                            for req_list in self.site_purchase_id.site_purchase_item_line_ids:
                                if req_list.item_id.id == line_id.product_id.id:
                                    req_list.quantity = li[2].get('required_qty')
                    if li[0]==0:
                        values = {'item_id':li[2].get('product_id'),
                                  'brand_name':li[2].get('brand_name'),
                                  'desc':li[2].get('name'),
                                  'unit':li[2].get('product_uom'),
                                  'quantity':li[2].get('required_qty'),
                                  'site_purchase_id':self.site_purchase_id.id}
                        req_line = self.env['site.purchase.item.line'].create(values)
                    if li[0] == 2:
                        line_id = self.env['purchase.order.line'].browse(li[1])
                        for req_list in self.site_purchase_id.site_purchase_item_line_ids:
                            if req_list.item_id.id == line_id.product_id.id:
                                req_list.unlink()
        else:
            if vals.get('order_line',False) :
                for li in vals.get('order_line',False):
                    if li[0]==0 and self.state =='approved':

                        raise ValidationError(
                            _("Only Purchase Order created through Direct PO can add item"))


        res = super(purchase_order, self).write(vals)

        return res

    @api.multi
    def force_po_close(self):
        return {
            'name': 'Foreclosure',
            'view_type': 'form',
            'view_mode': 'form',

            'res_model': 'force.po.close',

            'type': 'ir.actions.act_window',
            'target':'new',


        }

    @api.multi
    def button_view_invoice(self):
        value_list = []
        prev_list = []
        for line in self.order_line:

            value_list.append((0, 0, {'item_id': line.product_id.id,
                                  'desc': line.name,
                                      'brand_name':line.brand_name.id,
                                  'tax_ids': [(6, 0, line.taxes_id.ids)],
                                  'po_quantity': line.required_qty - line.received_qty,
                                  'rate': line.expected_rate,
                                  'unit_id': line.product_uom.id

                                  }))
            prev_list.append((0, 0, {'item_id': line.product_id.id,
                                     'desc': line.name,
                                     'brand_name': line.brand_name.id,
                                     'tax_ids': [(6, 0, line.taxes_id.ids)],
                                     'po_quantity': line.required_qty,
                                     'quantity_accept': line.received_qty,
                                     'quantity_reject': line.closed_qty,
                                     'rate': line.expected_rate,
                                     'unit_id': line.product_uom.id

                                     }))
        merged_po = False
        for site_pur in self.site_purchase_ids:
            merged_po = True
        context = {'default_mpr_id':self.site_purchase_id.id,
                  'default_supplier_id' : self.partner_id.id,
                'default_purchase_id':self.id,
                   'default_company_contractor_id':self.company_contractor_id.id,
                   'default_site':self.site_purchase_id.site.id,
                  'default_project_id' : self.project_id.id,
                  'default_goods_recieve_report_line_ids':value_list,
                  'default_previous_goods_receipt_entries_ids':prev_list,
                   'default_vehicle_id':self.site_purchase_id.vehicle_id.id,
                   'default_vehicle_agent_id':self.vehicle_agent_id.id,
                   'default_site':self.location_id.id,
                   'default_merged_po':merged_po,
                   'default_site_purchase_ids':[(6,0,self.site_purchase_ids.ids)]
                  }
        print "iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii",self.company_contractor_id,self.project_id
        # daily_stmt_supervisor = self.env['partner.daily.statement'].search([('project_id','=',self.project_id.id)])
        res = {
            'type': 'ir.actions.act_window',
            'name': 'Goods Receipt & Invoice Entry',
            'res_model': 'goods.recieve.report',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'context':context
            # 'res_id': goods_receipt.id,

        }

        return res



    @api.multi
    def button_create_comparison(self):
        self.state = 'bid'
        value_list = []
        for line in self.order_line:
            value_list.append((0,0,{'product_id':line.product_id.id,
                                    'brand_name':line.brand_name.id,
                                    'qty':line.product_qty,
                                    'uom':line.product_uom.id}))
        values = {'mpr_id':self.site_purchase_id.id,
                  'quotation_id':self.id,
                  'vehicle_id':self.vehicle_id.id,
                  'project_id':self.site_purchase_id.project_id.id,
                  'location_id':self.location_id.id,
                  'comparison_line':value_list,
                  'remark':self.notes,
                  }

        comparison = self.env['purchase.comparison'].create(values)

        self.comparison_id = comparison.id

        res = {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Comparison',
            'res_model': 'purchase.comparison',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id':self.comparison_id.id,
            'context': {'default_supplier_ids': self.supplier_ids.ids}
        }

        return res

    @api.multi
    def view_comparison(self):
        res = {
            'type': 'ir.actions.act_window',
            'name': 'Purchase Comparison',
            'res_model': 'purchase.comparison',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'current',
            'res_id':self.comparison_id.id,
            # 'domain': [('id', '=', self.comparison_id.id)],
            'context': {'default_supplier_ids': self.supplier_ids.ids,
                        'current_id': self.comparison_id.id}
        }

        return res


    @api.onchange('site_purchase_id')
    def onchange_mpr_id(self):
        for rec in self:
            if rec.site_purchase_id:
                values = []
                rec.project_id = rec.site_purchase_id.project_id.id
                for mpr_line in rec.site_purchase_id.site_purchase_item_line_ids:
                    values.append((0, 0, {'product_id': mpr_line.item_id.id,
                                          'name':mpr_line.item_id.name,
                                          'product_qty': mpr_line.quantity,
                                          'product_uom': mpr_line.unit.id,
                                          'brand_name': mpr_line.brand_name.id,
                                          'state':'draft'}))
                rec.order_line = values



    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            user_obj = self.pool.get('res.users')

            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:

                    parent.insert(index, child)
                    index += 1
                    for she_root in child.xpath("//notebook"):

                        for line in she_root.xpath("//field[@name='order_line']"):


                            if self.pool['res.users'].has_group(cr, uid, 'base.group_erp_manager'):

                                line.set('modifiers','{}')



                parent.remove(sheet)
            order_line_tree = etree.XML(res['fields']['order_line']['views']['tree']['arch'])
            if self.pool['res.users'].has_group(cr, uid, 'base.group_erp_manager'):

                order_line_tree.set('create', 'true')
                order_line_tree.set('delete', 'true')
            res['fields']['order_line']['views']['tree']['arch'] = etree.tostring(order_line_tree)


            res['arch'] = etree.tostring(doc)
        return res


    def wkf_send_rfq(self, cr, uid, ids, context=None):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        if not context:
            context= {}
        ir_model_data = self.pool.get('ir.model.data')
        try:
            if context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference(cr, uid, 'hiworth_construction', 'email_template_edi_purchase15')[1]
            else:
                template_id = ir_model_data.get_object_reference(cr, uid, 'hiworth_construction', 'email_template_edi_purchase_done2')[1]
        except ValueError:
            template_id = False
        try:
#
            compose_form_id = ir_model_data.get_object_reference(cr, uid, 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(context)
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }



    def picking_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'shipped':1,'state':'done'}, context=context)
        # Do check on related procurements:
        proc_obj = self.pool.get("procurement.order")
        po_lines = []
        for po in self.browse(cr, uid, ids, context=context):
            po_lines += [x.id for x in po.order_line if x.state != 'cancel']
        if po_lines:
            procs = proc_obj.search(cr, uid, [('purchase_line_id', 'in', po_lines)], context=context)
            if procs:
                proc_obj.check(cr, uid, procs, context=context)
        self.message_post(cr, uid, ids, body=_("Products received"), context=context)
        return True

    @api.multi
    def create_invoice(self):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        if not self.partner_ref:
            raise osv.except_osv(_('Warning!'),
                        _('You must enter a Invoice Number'))

        invoice_line = self.env['hiworth.invoice.line2']
        invoice = self.env['hiworth.invoice']
        now = datetime.datetime.now()
        for line in self:
            values1 = {
                        'is_purchase_bill': True,
                        'partner_id': line.partner_id.id,
                        'purchase_order_date':line.date_order,
                        'origin': line.name,
                        'name': self.partner_ref,
                        'journal_id': line.journal_id2.id,
                        'account_id': line.account_id.id,
                        'date_invoice': line.invoice_date,
                        'round_off_amount': line.round_off_amount,
                        'round_off_account': line.round_off_account.id,
                        'discount_amount': line.discount_amount,
                        'discount_account': line.discount_account.id,
                        'purchase_order_id': line.id,
#                         'grand_total': line.amount_total
                        }
            invoice_id = invoice.create(values1)
            for lines in line.order_line:
                taxes_ids = []
                taxes_ids = [tax.id for tax in lines.taxes_id]
                values2={
                        'product_id': lines.product_id.id,
                        'name': lines.product_id.name,
                        'price_unit': lines.price_unit,
                        'uos_id': lines.product_uom.id,
                        'quantity': lines.product_qty,
                        'price_subtotal':lines.price_subtotal,
                        'task_id': lines.task_id.id,
                        'location_id': lines.location_id.id,
                        'invoice_id': invoice_id.id,
                        'account_id': lines.account_id.id,
                        'tax_ids':  [(6, 0, taxes_ids)]
                        }
                invoice_line_id = invoice_line.create(values2)
            invoice_id.action_for_approval()
            # invoice_id.action_approve()
            line.invoice_created = True

    # @api.multi
    # def action_sanction(self):
    # 	for line in self:
    # 		line.state = 'sanction'



    @api.multi
    def invoice_open(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['hiworth.invoice'].search([('origin','=',self.name)])

        context = self._context.copy()
        context['type2'] = 'out'
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Invoice view',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'hiworth.invoice',
            'view_id':'hiworth_invoice_form',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':context,
        }


    def view_invoice(self, cr, uid, ids, context=None):
        '''
        This function returns an action that display existing invoices of given sales order ids. It can either be a in a list or in a form view, if there is only one invoice to show.
        '''
        context = dict(context or {})
        mod_obj = self.pool.get('ir.model.data')
        wizard_obj = self.pool.get('purchase.order.line_invoice')
        #compute the number of invoices to display
        inv_ids = []
        for po in self.browse(cr, uid, ids, context=context):
            if po.invoice_method == 'manual':
                if not po.invoice_ids:
                    context.update({'active_ids' :  [line.id for line in po.order_line if line.state != 'cancel']})
                    wizard_obj.makeInvoices(cr, uid, [], context=context)

        for po in self.browse(cr, uid, ids, context=context):
            inv_ids+= [invoice.id for invoice in po.invoice_ids]
            invoice = self.pool.get('account.invoice').search(cr, uid, [('purchase_id','=',po.id)])
            if self.pool.get('account.invoice').browse(cr, uid, invoice).not_visible == True:
                for line in self.pool.get('account.invoice').browse(cr, uid, invoice).invoice_line:
                    line.quantity = line.purchase_line_id.product_qty
                    line.price_unit = line.purchase_line_id.price_unit

                self.pool.get('account.invoice').browse(cr, uid, invoice).not_visible = False
                self.pool.get('account.invoice').browse(cr, uid, invoice).number = po.partner_ref
                self.pool.get('account.invoice').browse(cr, uid, invoice).date_invoice = po.invoice_date
            self.pool.get('account.invoice').browse(cr, uid, invoice).other_charge = po.other_charge
            self.pool.get('account.invoice').browse(cr, uid, invoice).amount_total = po.amount_total
        res = mod_obj.get_object_reference(cr, uid, 'account', 'invoice_supplier_form')
        res_id = res and res[1] or False

        return {
            'name': _('Supplier Invoices'),
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res_id],
            'res_model': 'account.invoice',
            'context': "{'type':'in_invoice', 'journal_type': 'purchase'}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': inv_ids and inv_ids[0] or False,
        }






# class invoice_attachment(models.Model):
#     _name = "invoice.attachment"
#
#     @api.onchange('parent_id')
#     def _onchange_attachment_selection(self):
#         res={}
#
#         attachment_ids = []
# #         product_ids = [estimate.pro_id.id for estimate in self.env['project.task'].search([('id','=',task_id)]).estimate_ids]
#         if self.parent_id.id != False and self.invoice_id.project_id.id != False:
#             attachment_ids = [attachment.id for attachment in self.env['project.attachment'].search([('parent_id','=',self.parent_id.id),('project_id','=',self.invoice_id.project_id.id)])]
#             return {
#                 'domain': {
#                     'attachment_id': [('id','in',attachment_ids)]
#                 }
#             }
#         if self.parent_id.id != False and self.invoice_id.project_id.id == False:
#             attachment_ids = [attachment.id for attachment in self.env['project.attachment'].search([('parent_id','=',self.parent_id.id)])]
#             return {
#                 'domain': {
#                     'attachment_id': [('id','in',attachment_ids)]
#                 }
#             }
#         else:
#             return res
#
#     name = fields.Char('Name')
#     attachment_id = fields.Many2one('project.attachment', 'Attachments')
#     filename = fields.Char(related='attachment_id.filename', string='Filename')
#     binary_field = fields.Binary(related='attachment_id.binary_field', string="File")
#     invoice_id = fields.Many2one('account.invoice', 'Invoice')
#     parent_id = fields.Many2one('document.directory', 'Directory')

# class account_invoice(models.Model):
#     _inherit = "account.invoice"
#     _rec_name = 'prime_invoice'
#
#
#     @api.onchange('project_id')
#     def _onchange_task_selection(self):
#
#         if self.is_contractor_bill == True:
#             return {
#                 'domain': {
#                     'task_id': [('project_id','=',self.project_id.id)]
#                 }
#             }
#
#
#     @api.onchange('is_contractor_bill')
#     def _onchange_contractor_selection(self):
#         if self.is_contractor_bill == True:
#
# #             taks_ids = [project.task_id.id for project in self.picking_id.task_id.estimate_ids]
#             return {
#                 'domain': {
#                     'partner_id': [('contractor','=',True)]
#                 }
#             }
#
#     @api.multi
#     @api.depends('task_id')
#     def _visible_prevoius_bills(self):
#
#         for line in self:
#
#             if line.task_id.id != False:
#                 line.visible_previous_bill = True
#
#     @api.multi
#     @api.depends('amount_total','residual')
#     def _compute_balance(self):
#         for line in self:
#
#             if line.state == 'draft':
#                 line.balance2 = line.amount_total
#             if line.state != 'draft':
#                 line.balance2 = line.residual
#
#     @api.multi
#     @api.depends('prevous_bills')
#     def _compute_prevoius_balance(self):
#         for line in self:
#             for lines in line.prevous_bills:
#                 line.previous_balance+=lines.balance2
#
#     @api.one
#     @api.depends('invoice_line.price_subtotal', 'tax_line.amount','other_charge')
#     def _compute_amount(self):
#         res = super(account_invoice, self)._compute_amount()
#         for rec in self:
#             rec.amount_total += rec.amount_total + rec.other_charge
#         return res
#     @api.multi
#     @api.depends('previous_balance','amount_total','residual')
#     def _compute_net_total(self):
#         for line in self:
#             if line.residual == 0.0:
#                 line.net_total = line.previous_balance + line.amount_total
#             else:
#                 line.net_total = line.previous_balance + line.residual
#
#     state = fields.Selection([
#             ('draft','Draft'),
#             ('proforma','Pro-forma'),
#             ('proforma2','Pro-forma'),
#             ('open','Waiting for Approval'),
#             ('approve','Approved'),
#             ('paid','Paid'),
#             ('cancel','Cancelled'),
#         ], string='Status', index=True, readonly=True, default='draft',
#         track_visibility='onchange', copy=False,
#         help=" * The 'Draft' status is used when a user is encoding a new and unconfirmed Invoice.\n"
#              " * The 'Pro-forma' when invoice is in Pro-forma status,invoice does not have an invoice number.\n"
#              " * The 'Open' status is used when user create invoice,a invoice number is generated.Its in open status till user does not pay invoice.\n"
#              " * The 'Approved' status is used when the Invoice approved for Payment.\n"
#              " * The 'Paid' status is set automatically when the invoice is paid. Its related journal entries may or may not be reconciled.\n"
#              " * The 'Cancelled' status is used when user cancel invoice.")
#     project_id = fields.Many2one('project.project', 'Project')
#     customer_id = fields.Many2one(related='project_id.partner_id', string="Client")
#     is_contractor_bill = fields.Boolean('Contractor Bill', default=False)
#     task_id = fields.Many2one('project.task', 'Task')
#     prevous_bills = fields.One2many('account.invoice', 'invoice_id5', 'Previous Invoices')
#     invoice_id5 = fields.Many2one('account.invoice', 'Invoices')
#     visible_previous_bill = fields.Boolean(compute='_visible_prevoius_bills', store=True, string="Visible Prevoius Bill", default=False)
#     visible_bills = fields.Boolean('Visible', default=False)
#     balance2 = fields.Float(compute='_compute_balance', string="Balance Of Not Validated")
#     previous_balance = fields.Float(compute='_compute_prevoius_balance', string="Previous Balance")
#     net_total = fields.Float(compute='_compute_net_total', string="Net Total")
#     attachment_ids = fields.One2many('invoice.attachment', 'invoice_id', 'Attachments')
#     task_related = fields.Boolean('Related To Task')
#     agreed_amount = fields.Float(related='task_id.estimated_cost', string="Agreement Amount")
#     type_id = fields.Selection([('Arch','Architectural'),('Struc','Structural'),('Super','Supervision')],string="Type")
#     prime_invoice = fields.Char('Prime Invoice')
#
#     account_invoice_ids = fields.Many2one('account.invoice','Invoice no')
#     district = fields.Char('District')
#     person = fields.Char('Person Incharge',compute='select_person')
#     total_tender_amount = fields.Float('Tender Amount',compute='compute_tender_amount')
#     balance_amount = fields.Float('Balance Amount',readonly=True)
#     contractor_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Contractor')
#     statusline_ids = fields.One2many('customer.invoice.follow.up','account_invoice_ids', 'Status')
#     purchase_id = fields.Many2one('purchase.order', 'Purchase Order')
#     not_visible =  fields.Boolean('Visible', default=False)
#     location_id = fields.Many2one('stock.location',string="Location",domain="[('usage','=','internal')]")
#     vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")
#     other_charge = fields.Float('Other charges')
#
#
#     def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
#         res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
#         if view_type == 'form':
#             doc = etree.XML(res['arch'])
#             for sheet in doc.xpath("//sheet"):
#                 parent = sheet.getparent()
#                 index = parent.index(sheet)
#                 for child in sheet:
#                     parent.insert(index, child)
#                     index += 1
#                 parent.remove(sheet)
#             res['arch'] = etree.tostring(doc)
#         return res
#
#
#     @api.onchange('project_id')
#     def onchange_datas(self):
#         if self.project_id:
#             self.district = self.project_id.district
#             self.contractor_id = self.project_id.contractor_id.id
#
#
# #     attachment_ids = fields.Many2one('project.attachment', 'Attachments')
#     @api.multi
#     @api.depends('account_invoice_ids')
#     def select_person(self):
#         for person in self:
#             person.person = self.env['customer.invoice.follow.up'].search([('account_invoice_ids', '=',person.account_invoice_ids.id)]).person
#             person.balance_amount=self.env['customer.invoice.follow.up'].search([('account_invoice_ids', '=',person.account_invoice_ids.id)]).balance_amount
#
#
#
#     @api.multi
#     @api.depends('project_id')
#     def compute_tender_amount(self):
#         for tender in self:
#             tender.total_tender_amount = self.env['hiworth.tender'].search([('id', '=',tender.project_id.tender_id.id)]).apac
#
#     @api.multi
#     def refresh_prevoius_bills(self):
#         for line in self:
#
#             invoice_objs = self.env['account.invoice'].search([('task_id','=',line.task_id.id)])
#
#             for invoice in invoice_objs:
#                 invoice.invoice_id5 = False
#
#             for invoices in invoice_objs:
#                 if invoices.id != line.id:
#                     invoices.invoice_id5 = line.id
#
#             line.visible_bills = True
#
#     @api.multi
#     def hide_prevoius_bills(self):
#         for line in self:
#             line.visible_bills = False
#
#     @api.multi
#     def invoice_approve(self):
#         for line in self:
#             line.state = 'approve'
#
#
#     @api.multi
#     def action_invoice_sent(self):
#         """ Open a window to compose an email, with the edi invoice template
#             message loaded by default
#         """
#         assert len(self) == 1, 'This option should only be used for a single id at a time.'
#         template = self.env.ref('hiworth_construction.email_template_edi_invoice23', False)
#         compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
#
#         ctx = dict(
#             default_model='account.invoice',
#             default_res_id=self.id,
#             default_use_template=bool(template),
#             default_template_id=template.id,
#             default_composition_mode='comment',
#             mark_invoice_as_sent=True,
#         )
#
#         return {
#             'name': _('Compose Email'),
#             'type': 'ir.actions.act_window',
#             'view_type': 'form',
#             'view_mode': 'form',
#             'res_model': 'mail.compose.message',
#             'views': [(compose_form.id, 'form')],
#             'view_id': compose_form.id,
#             'target': 'new',
#             'context': ctx,
#         }
#
#     def group_lines(self, iml, line):
#         res = super(account_invoice, self).group_lines(iml, line)
#         for rec in self:
#             if rec.location_id and  not rec.vehicle_id:
#                 res.append((0, 0, {'name': rec.location_id.name,
#                                    'account_id': rec.location_id.related_account.id,
#                                    'debit': rec.amount_total,
#                                    'credit': 0}))
#             if rec.vehicle_id:
#                 res.append((0, 0, {'name': rec.vehicle_id.name,
#                                    'account_id': rec.vehicle_id.related_account.id,
#                                    'debit': rec.amount_total,
#                                    'credit': 0}))
#
#             for line in rec.invoice_line:
#
#                     res.append((0, 0, {'name': line.name,
#                                       'account_id': line.account_id.id,
#                                       'debit': 0,
#                                       'credit': line.price_subtotal,
#                                       }))
#
#
#
#
#
#         return res



# class StatusUpdateLine(models.Model):
# 	_name = 'status.update.line2'

# 	invoice_id = fields.Many2one('account.invoice', 'Invoice')
# 	date = fields.Date('Date',compute='date_status_record')
# 	bill_status = fields.Text('Bill Status')

    # @api.multi
    # def date_status_record(self):
    # 	for tender in self:
        # 		tender.date = self.env['customer.invoice.follow.up'].search([('id', '=',tender.invoice_id.account_invoice_ids.id)]).date
    # 		tender.bill_status = self.env['customer.invoice.follow.up'].search([('id', '=',tender.invoice_id.account_invoice_ids.id)]).bill_status





# class account_invoice_line(models.Model):
#     _inherit = 'account.invoice.line'
#
# # 	@api.onchange('quantity')
# # 	def _onchange_qty(self):
# # 		if self.product_id.id != False and self.quantity != 0:
# # 			task_id = self.invoice_id.task_id
#
#
# # 			estimation = self.env['project.task.estimation'].search([('task_id','=',task_id.id),('pro_id','=',self.product_id.id)])
# # 			if estimation.invoiced_qty == 0.0:
# # 				if estimation.qty == 0.0:
# # 					self.quantity = 0.0
# # 					return {
# # 						'warning': {
# # 								'title': 'Warning',
# # 								'message': "Please enter some Qty in the Estimation."
# # 									}
# # 								}
# # 				if estimation.qty < self.quantity:
# # 					self.quantity = estimation.qty
# # #                     estimation.write({'invoiced_qty': self.quantity})
# # 					return {
# # 						'warning': {
# # 								'title': 'Warning',
# # 								'message': "Entered qty is greater than the qty to invoice."
# # 									}
# # 								}
# # 				if estimation.qty > self.quantity:
#
# # #                     estimation.write({'invoiced_qty': self.quantity})
#
# # 			if estimation.invoiced_qty != 0.0:
# # 				if self.quantity > estimation.qty - estimation.invoiced_qty:
# # 					self.quantity = estimation.qty - estimation.invoiced_qty
#
# # 					return {
# # 						'warning': {
# # 								'title': 'Warning',
# # 								'message': "Entered qty is greater than the qty to invoice."
# # 									}
# # 								}
#
#
#
# #     task_id = fields.Many2one('project.task', string='task',
# #         related='invoice_id.task_id', store=True, readonly=True)
# #     task_related = fields.Boolean(related='invoice_id.task_related', store=True, string='Related To Task')
#     total_assigned_qty = fields.Float('Assigned Qty')
#     discount_amt = fields.Float('Cash Discount')
#     net_total = fields.Float('Net Total')
#
#     @api.multi
#     def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
#             partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
#             company_id=None, task_related=False,task_id=False):
#         context = self._context
#         company_id = company_id if company_id is not None else context.get('company_id', False)
#         self = self.with_context(company_id=company_id, force_company=company_id)
#
#         if not partner_id:
#             raise except_orm(_('No Partner Defined!'), _("You must first select a partner!"))
#
#         values = {}
#
#         part = self.env['res.partner'].browse(partner_id)
#         fpos = self.env['account.fiscal.position'].browse(fposition_id)
#
#         if part.lang:
#             self = self.with_context(lang=part.lang)
#         product = self.env['product.product'].browse(product)
#
#         values['name'] = product.partner_ref
#         if type in ('out_invoice', 'out_refund'):
#             account = product.property_account_income or product.categ_id.property_account_income_categ
#         else:
#             account = product.property_account_expense or product.categ_id.property_account_expense_categ
#         account = fpos.map_account(account)
#         if account:
#             values['account_id'] = account.id
#
#         if type in ('out_invoice', 'out_refund'):
#             taxes = product.taxes_id or account.tax_ids
#             if product.description_sale:
#                 values['name'] += '\n' + product.description_sale
#         else:
#             taxes = product.supplier_taxes_id or account.tax_ids
#             if product.description_purchase:
#                 values['name'] += '\n' + product.description_purchase
#
#         fp_taxes = fpos.map_tax(taxes)
#         values['invoice_line_tax_id'] = fp_taxes.ids
#
#         if type in ('in_invoice', 'in_refund'):
#             if price_unit and price_unit != product.standard_price:
#                 values['price_unit'] = price_unit
#             else:
#                 values['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.standard_price, taxes, fp_taxes.ids)
#         else:
#             values['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.lst_price, taxes, fp_taxes.ids)
#
#         values['uos_id'] = product.uom_id.id
#         if uom_id:
#             uom = self.env['product.uom'].browse(uom_id)
#             if product.uom_id.category_id.id == uom.category_id.id:
#                 values['uos_id'] = uom_id
#
#         domain = {'uos_id': [('category_id', '=', product.uom_id.category_id.id)]}
#
#         company = self.env['res.company'].browse(company_id)
#         currency = self.env['res.currency'].browse(currency_id)
#
#         if company and currency:
#             if company.currency_id != currency:
#                 values['price_unit'] = values['price_unit'] * currency.rate
#
#             if values['uos_id'] and values['uos_id'] != product.uom_id.id:
#                 values['price_unit'] = self.env['product.uom']._compute_price(
#                     product.uom_id.id, values['price_unit'], values['uos_id'])
#
# #         print 'parpartner_ident ========================', partner_id,task_related,task_id,product
#         product_ids = []
#         if task_related == True:
#             estimation = self.env['project.task.estimation'].search([('task_id','=',task_id),('pro_id','=',product.id)])
#             values['total_assigned_qty']=estimation.qty
#             values['quantity']=0.0
#             if task_id == False:
#                 raise osv.except_osv(_('Warning!'),
#                         _('Please enter a task or uncheck "Related to task Field"'))
#             if task_id != False:
# #                 print 'task=============================', self.env['project.task'].search([('id','=',task_id)])
#                 product_ids = [estimate.pro_id.id for estimate in self.env['project.task'].search([('id','=',task_id)]).estimate_ids]
#                 return {'value': values, 'domain': {'product_id': [('id','in',product_ids)]}}
#
#         if not product:
#             if type in ('in_invoice', 'in_refund'):
#                 return {'value': {}, 'domain': {'uos_id': []}}
#             else:
#                 return {'value': {'price_unit': 0.0}, 'domain': {'uos_id': []}}
#
#         return {'value': values, 'domain': domain,}
#
#
#     @api.model
#     def create(self,vals):
# #         task_id = self.invoice_id.task_id
# #         print 'vals======================', vals
#         if 'invoice_id' in vals:
#             task_id = self.env['account.invoice'].browse(vals['invoice_id']).task_id
#             product_id = self.env['product.product'].browse(vals['product_id'])
#             estimation = self.env['project.task.estimation'].search([('task_id','=',task_id.id),('pro_id','=',product_id.id)],limit=1)
#             print 'estimation==================',task_id ,estimation
#
#             if vals['quantity'] != 0.0:
#                 estimation.write({'invoiced_qty': estimation.invoiced_qty+vals['quantity']})
#             vals['total_assigned_qty']=estimation.qty
#             return super(account_invoice_line, self).create(vals)
#         return super(account_invoice_line, self).create(vals)

#     @api.model
#     def write(self,vals):
#
#         if vals['quantity']:
#             task_id = self.env['account.invoice'].browse(vals['invoice_id']).task_id
#             product_id = self.env['product.product'].browse(vals['product_id'])
#             estimation = self.env['project.task.estimation'].search([('task_id','=',task_id.id),('pro_id','=',product_id.id)])
#
#
#
#         super(account_invoice_line, self).write(vals)
#         return True


class product_cost_table(models.Model):
    _name = "product.cost.table"

    _order = "date desc"

    name = fields.Char('name')
    product_id = fields.Many2one('product.template', 'Product')
    date = fields.Date('Date')
    standard_price = fields.Float('Cost')
    purchase_id = fields.Char('Reference')
    remarks = fields.Char('Remarks' ,size=200)
    qty = fields.Float('Quantity')
    location_id = fields.Many2one('stock.location','Location')
 #   template_id = fields.Many2one('product.template', 'Product Tempate')

#
# class product_product(models.Model):
#     _inherit = "product.product"
#
#     @maulti
#     @depends('name')
#     def _total_product_in(self, cr, uid, ids, field_names=None, arg=False, context=None):
#         context = context or {}
#         field_names = field_names or []
#
# #         domain_products = [('product_id', 'in', ids)]
# #         domain_quant, domain_move_in, domain_move_out = [], [], []
#         domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations(cr, uid, ids, context=context)
#         print 'qqqqqqqqqqqqqqqqqqq=================',domain_move_in_loc,asdasd
# #         domain_move_in += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
# #         domain_move_out += self._get_domain_dates(cr, uid, ids, context=context) + [('state', 'not in', ('done', 'cancel', 'draft'))] + domain_products
# #         domain_quant += domain_products
#     total_qty_received = fields.Float(compute='__total_product_in', string="Total Qty In")




class product_template(models.Model):
    _inherit = "product.template"


#     @api.multi
#     @api.depends('standard_price','cost_table_id')
#     def _compute_old_price(self):
#
#         for line in self:
#             cost_table = []
#             cost_table = [table.id for table in line.cost_table_id]
#             if len(cost_table) == 0:
#                 print 'test==========================21221'
#                 line.old_price = line.standard_price
#
#             print 'iefsdf===============================', len(cost_table)
#             if len(cost_table) > 1:
#                 tables = self.env['product.cost.table'].search([('id','in',cost_table)])
#                 recordset = tables.sorted(key=lambda r: r.date, reverse=True)
#                 line.old_price = recordset[1].standard_price
#                 line.standard_price = recordset[0].standard_price
#                 print 'test==========================21221',tables,recordset,recordset[1],recordset[0],recordset[0]
# #             for costs in line.cost_table_id:
# #                 print 'cost_tables============================',line.cost_table_id,line.id,len(line.cost_table_id.search([('product_id','=',line.id)]))
# #                 if len(line.cost_table_id.search([('product_id','=',line.id)])) > 1:
# #                     pre_id = line.cost_table_id.search([('product_id','=',line.id)])[len(line.cost_table_id.search([('product_id','=',line.id)]))-1].standard_price
# #                     print 'pre_id==========================', pre_id
# #                     line.old_price = pre_id
# # #                 line.old_price = line.standard_price
# #             if cost_table == []:


    @api.multi
    @api.depends('standard_price','qty_available')
    def _compute_inventory_value(self):

        for line in self:
            line.inventory_value = line.standard_price * line.qty_available

    @api.multi
    @api.depends('name')
    def _compute_total_in_qty(self):
        cr = self._cr
        uid = self._uid
        context = self._context
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        warehouse = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', user.company_id.id)], limit=1, context=context)
        if warehouse:
            loc_id = self.env['stock.warehouse'].search([('id','=',warehouse[0])]).lot_stock_id
            for line in self:
                line.qty_in = 0.0
                moves = self.env['stock.move'].search([('location_dest_id','=',loc_id.id),('product_id','=',line.id),('state','=','done')])
                for move in moves:
                    line.qty_in += move.product_uom_qty

    brand_name = fields.Many2one('material.brand')
    model_name = fields.Many2one('material.model')
    show_cost_variation = fields.Boolean('Show Cost Variations', default=False)
    cost_table_id = fields.One2many('product.cost.table','product_id', 'Cost Variations')
    old_price = fields.Float('Old Price')
#     compute='_compute_old_price', string="
    inventory_value = fields.Float(compute='_compute_inventory_value', string="Inventory Value")
    temp_remain = fields.Float('Qty')
    process_ok = fields.Boolean('Process')
    qty_in = fields.Float(compute='_compute_total_in_qty', string="Qty IN")
    allocation_no = fields.Char('Allocation No')
    battery = fields.Boolean("Battery", default=False)
    tyre = fields.Boolean("Tyre", default=False)
    tyre_retread = fields.Boolean("Retread", default=False)
    gps = fields.Boolean("GPS",default=False)




    @api.multi
    def show_cost_variation2(self):
        for line in self:
            line.show_cost_variation = True

    @api.multi
    def hide_cost_variation(self):
        for line in self:
            line.show_cost_variation = False


    @api.multi
    def unlink(self):
        for product in self:
#             if invoice.state not in ('draft', 'cancel'):
#                 raise Warning(_('You cannot delete an invoice which is not draft or cancelled. You should refund it instead.'))
#             elif invoice.internal_number:
#                 raise Warning(_('You cannot delete an invoice after it has been validated (and received a number).  You can set it back to "Draft" state and modify its content, then re-confirm it.'))
            print('aaaaaaaaaaaaaaaaaaaaaaaaaa')
        return super(product_template, self).unlink()



class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'

    # @api.onchange('task_id')
    # def onchange_task_id(self):
    #     if self.task_id:
    #         product_ids = []
    #         product_ids = [estimation.pro_id.id for estimation in self.task_id.estimate_ids]
    #         return {
    #             'domain': {
    #                 'product_id':[('id','in', product_ids)]
    #             }
    #         }

    # @api.onchange('product_qty')
    # def _onchange_product_qty(self):
    # 	print 'test order line================='
    # 	super(purchase_order_line, self).onchange_product_id(self.order_id.pricelist_id.id,self.product_id.id,self.product_qty,self.product_uom.id,self.order_id.partner_id.id,self.order_id.date_order,self.order_id.fiscal_position.id,self.date_planned,self.name,False,self.order_id.state)
# 		estimate = [estimate for estimate in self.task_id.estimate_ids if estimate.pro_id == self.product_id]
# 		if not len(estimate):
# 			return
# 		if ((estimate[0].qty - estimate[0].qty_assigned) - self.product_qty)<0:
# #             print 'estimate[0].qty===========================', estimate[0].qty,self.product_qty
# 			# stock_move.extra_quantity = (self.product_qty-estimate[0].qty)
# #             print
# 			self.product_qty = estimate[0].qty
# 			# self.is_request_more_btn_visible = True

# #             if self.picking_id.change_help == True:
# #                 self.picking_id.change_help = False
# #             if self.picking_id.change_help == False:
# #                 self.picking_id.change_help = True
# 			return {
# 				'warning': {
# 					'title': 'Warning',
# 					'message': "Quantity cannot be greater than the quantity assigned for the task. Please increase the quantity from the task."
# 				}
# 			}


    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom_id,
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name=False, price_unit=False, state='draft', context=None):
        """
        onchange handler of product_id.
        """
        if context is None:
            context = {}

        res = {'value': {'expected_rate': price_unit or 0.0, 'name': name or '', 'product_uom' : uom_id or False}}
        if not product_id:
            if not uom_id:
                uom_id = self.default_get(cr, uid, ['product_uom'], context=context).get('product_uom', False)
                res['value']['product_uom'] = uom_id
            return res

        product_product = self.pool.get('product.product')
        product_uom = self.pool.get('product.uom')
        res_partner = self.pool.get('res.partner')
        product_pricelist = self.pool.get('product.pricelist')
        account_fiscal_position = self.pool.get('account.fiscal.position')
        account_tax = self.pool.get('account.tax')

        # - check for the presence of partner_id and pricelist_id
        #if not partner_id:
        #    raise osv.except_osv(_('No Partner!'), _('Select a partner in purchase order to choose a product.'))
        #if not pricelist_id:
        #    raise osv.except_osv(_('No Pricelist !'), _('Select a price list in the purchase order form before choosing a product.'))

        # - determine name and notes based on product in partner lang.
        context_partner = context.copy()
        if partner_id:
            lang = res_partner.browse(cr, uid, partner_id).lang
            context_partner.update( {'lang': lang, 'partner_id': partner_id} )
        product = product_product.browse(cr, uid, product_id, context=context_partner)
        #call name_get() with partner in the context to eventually match name and description in the seller_ids field
        if not name or not uom_id:
            # The 'or not uom_id' part of the above condition can be removed in master. See commit message of the rev. introducing this line.
            dummy, name = product_product.name_get(cr, uid, product_id, context=context_partner)[0]
            if product.description_purchase:
                name += '\n' + product.description_purchase
            res['value'].update({'name': name})

        # - set a domain on product_uom
        res['domain'] = {'product_uom': [('category_id','=',product.uom_id.category_id.id)]}

        # - check that uom and product uom belong to the same category
        product_uom_po_id = product.uom_po_id.id
        if not uom_id:
            uom_id = product_uom_po_id

        if product.uom_id.category_id.id != product_uom.browse(cr, uid, uom_id, context=context).category_id.id:
            if context.get('purchase_uom_check') and self._check_product_uom_group(cr, uid, context=context):
                res['warning'] = {'title': _('Warning!'), 'message': _('Selected Unit of Measure does not belong to the same category as the product Unit of Measure.')}
            uom_id = product_uom_po_id

        res['value'].update({'product_uom': uom_id})

        # - determine product_qty and date_planned based on seller info
        if not date_order:
            date_order = fields.datetime.now()


        supplierinfo = False
        precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
        for supplier in product.seller_ids:
            if partner_id and (supplier.name.id == partner_id):
                supplierinfo = supplier
                if supplierinfo.product_uom.id != uom_id:
                    res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier only sells this product by %s') % supplierinfo.product_uom.name }
                min_qty = product_uom._compute_qty(cr, uid, supplierinfo.product_uom.id, supplierinfo.min_qty, to_uom_id=uom_id)
                if float_compare(min_qty , qty, precision_digits=precision) == 1: # If the supplier quantity is greater than entered from user, set minimal.
                    if qty:
                        res['warning'] = {'title': _('Warning!'), 'message': _('The selected supplier has a minimal quantity set to %s %s, you should not purchase less.') % (supplierinfo.min_qty, supplierinfo.product_uom.name)}
                    qty = min_qty
        dt = self._get_date_planned(cr, uid, supplierinfo, date_order, context=context).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        qty = qty or False
        res['value'].update({'date_planned': date_planned or dt})
        if qty:
            res['value'].update({'product_qty': qty})

        price = price_unit
        if price_unit is False or price_unit is None:
            # - determine price_unit and taxes_id
            if pricelist_id:
                date_order_str = datetime.strptime(date_order, DEFAULT_SERVER_DATETIME_FORMAT).strftime(DEFAULT_SERVER_DATE_FORMAT)
                price = product_pricelist.price_get(cr, uid, [pricelist_id],
                        product.id, qty or False, partner_id or False, {'uom': uom_id, 'date': date_order_str})[pricelist_id]
            else:
                price = product.standard_price

        if uid == SUPERUSER_ID:
            company_id = self.pool['res.users'].browse(cr, uid, [uid]).company_id.id
            taxes = product.supplier_taxes_id.filtered(lambda r: r.company_id.id == company_id)
        else:
            taxes = product.supplier_taxes_id
        fpos = fiscal_position_id and account_fiscal_position.browse(cr, uid, fiscal_position_id, context=context) or False
        taxes_ids = account_fiscal_position.map_tax(cr, uid, fpos, taxes, context=context)
        price = self.pool['account.tax']._fix_tax_included_price(cr, uid, price, product.supplier_taxes_id, taxes_ids)
        res['value'].update({'expected_rate': price, 'taxes_id': taxes_ids})
        return res


    @api.multi
    @api.depends('expected_rate','required_qty','taxes_id')
    def compute_new_subtotal(self):
        for line in self:
            tax_amount = 0
            non_tax_amount = 0
            sub_total = 0
            if line.taxes_id:
                for tax in line.taxes_id:
                    if tax.price_include:
                        tax_amount += tax.amount
            else:
                non_tax_amount = line.expected_rate * line.required_qty
            line.tax_amount = tax_amount
            line.non_taxable_amount = non_tax_amount

            line.new_sub_total = (line.expected_rate / (1+tax_amount)) * line.required_qty



    @api.multi
    @api.depends('new_sub_total','taxes_id','product_id','required_qty','expected_rate')
    def compute_gst_tax(self):
        for line in self:
            line.gst_tax=0.0
            line.igst_tax=0.0
            tax_amt = 0
            gst = 0
            igst = 0
            non_taxable= 0
            if line.taxes_id:
                for tax in line.taxes_id:

                        if tax.tax_type == 'gst':
                            gst += tax.amount
                        if tax.tax_type == 'igst':
                            igst += tax.amount

            else:
                non_taxable = line.new_sub_total
            line.gst_tax = line.new_sub_total*(gst)
            line.igst_tax = line.new_sub_total*(igst)
            line.tax_amount = line.gst_tax + line.igst_tax
            line.total = line.new_sub_total + line.gst_tax + line.igst_tax



    brand_name = fields.Many2one('material.brand')
    pro_old_price = fields.Float(related='product_id.standard_price', store=True, string='Previous Unit Price')
    task_id = fields.Many2one('project.task', 'Task')
    location_id = fields.Many2one(related='task_id.project_id.location_id', store=True, string='Location')
    # item_category_id = fields.Many2one('purchase.item.category', 'Category')
    account_id = fields.Many2one('account.account', 'Account', domain=[('type', 'not in', ['view', 'closed', 'consolidation'])])
    # other_charge = fields.Float('Loading and trasportation charge')
    # unit_price = fields.Float('Unit Price')
    # price_unit = fields.Float(compute='compute_unit_price', store=True, string="Unit Price")
    date_planned = fields.Date('Scheduled Date', required=False, select=True)
    checked_qty = fields.Boolean('Is Checked Arrived Qty', default=False)
    new_sub_total = fields.Float("Subtotal",compute='compute_new_subtotal',store=True)
    gst_tax = fields.Float(compute='compute_gst_tax', string="GST Tax")
    igst_tax = fields.Float(compute='compute_gst_tax', string="IGST Tax")
    site_purchase_id = fields.Many2one('site.purchase')
    required_qty = fields.Float('Qty')
    expected_rate = fields.Float('Rate')
    tax_amount = fields.Float(compute='compute_gst_tax', string='Tax Amount')
    total = fields.Float(compute='compute_gst_tax', string='Total')
    price_unit = fields.Float('Unit Price', required=False, digits_compute= dp.get_precision('Product Price'))
    product_qty = fields.Float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=False)
    received_qty = fields.Float("Received Qty")
    received_rate = fields.Float("Received Rate")
    closed_qty = fields.Float("Foreclosure Qty")
    returned_qty = fields.Float("Returned Qty")
    non_taxable_amount = fields.Float("Non-Taxable Amount",compute='compute_gst_tax',store=True)


class stock_history(models.Model):
    _inherit = 'stock.history'

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'stock_history')
        cr.execute("""
            CREATE OR REPLACE VIEW stock_history AS (
              SELECT MIN(id) as id,
                move_id,
                location_id,
                company_id,
                product_id,
                product_categ_id,
                SUM(quantity) as quantity,
                date,
                COALESCE(SUM(price_unit_on_quant * quantity) / NULLIF(SUM(quantity), 0), 0) as price_unit_on_quant,
                source
                FROM
                ((SELECT
                    stock_move.id AS id,
                    stock_move.id AS move_id,
                    dest_location.id AS location_id,
                    dest_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_quant_move_rel on stock_quant_move_rel.move_id = stock_move.id
                JOIN
                    stock_quant as quant on stock_quant_move_rel.quant_id = quant.id
                JOIN
                   stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND dest_location.usage in ('internal', 'transit')
                  AND (
                    not (source_location.company_id is null and dest_location.company_id is null) or
                    source_location.company_id != dest_location.company_id or
                    source_location.usage not in ('internal', 'transit'))
                ) UNION ALL
                (SELECT
                    (-1) * stock_move.id AS id,
                    stock_move.id AS move_id,
                    source_location.id AS location_id,
                    source_location.company_id AS company_id,
                    stock_move.product_id AS product_id,
                    product_template.categ_id AS product_categ_id,
                    - quant.qty AS quantity,
                    stock_move.date AS date,
                    quant.cost as price_unit_on_quant,
                    stock_move.origin AS source
                FROM
                    stock_move
                JOIN
                    stock_quant_move_rel on stock_quant_move_rel.move_id = stock_move.id
                JOIN
                    stock_quant as quant on stock_quant_move_rel.quant_id = quant.id
                JOIN
                    stock_location source_location ON stock_move.location_id = source_location.id
                JOIN
                    stock_location dest_location ON stock_move.location_dest_id = dest_location.id
                JOIN
                    product_product ON product_product.id = stock_move.product_id
                JOIN
                    product_template ON product_template.id = product_product.product_tmpl_id
                WHERE quant.qty>0 AND stock_move.state = 'done' AND source_location.usage in ('internal', 'transit')
                 AND (
                    not (dest_location.company_id is null and source_location.company_id is null) or
                    dest_location.company_id != source_location.company_id or
                    dest_location.usage not in ('internal', 'transit'))
                ))
                AS foo
                GROUP BY move_id, location_id, company_id, product_id, product_categ_id, date, source
            )""")


    uom_id = fields.Many2one(related='product_id.uom_id', string="Unit")
#     inventory_value_with_tax = fields.Float(compute='_compute_inventory_value_with_tax', store="True", string="Inventory Value With Tax")
#


class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    @api.depends('project_ids')
    def _count_projects(self):

        for line in self:
            line.project_count = 0
            for lines in line.project_ids:
                line.project_count+=1


    tin_no = fields.Char('GST NO', size=20)
    diesel_pump_bool = fields.Boolean(default=False)
    crusher_bool = fields.Boolean(default=False)
    cleaners_bool = fields.Boolean(default=False)
    sp_code = fields.Char('Supplier Code', size=20)
    attachment_id = fields.One2many('ir.attachment', 'partner_id', 'Attachments')
#     state = fields.Selection(STATE_SELECTION, 'Status', readonly=True,
#                                    select=True, copy=False)
    guardian = fields.Char('guardian')
    kara = fields.Char('Kara')
    desam = fields.Char('Desam')
    village = fields.Char('Village')
    Municipality = fields.Char('Name of Municipality')
    taluk = fields.Char('Taluk')
    dist = fields.Char('District')
    age = fields.Integer('Age')
    post = fields.Char('Post')
    stage_id = fields.Many2one('project.stages', 'Customer Status')
    project_ids = fields.One2many('project.project', 'partner_id', 'Projects')
    project_count = fields.Integer(compute='_count_projects', store=True, string='No of Projects')
    contractor = fields.Boolean('Contractor')
    account_receivable = fields.Many2one(related='property_account_receivable', string='Account Receivable', store=True)
    account_payable = fields.Many2one(related='property_account_receivable', string='Account Payable', store=True)
    tds_applicable = fields.Boolean(default=False,string='TDS Applicable')
    pan_no = fields.Char("PAN No")
    tender_contractor = fields.Boolean("Tender Contractor")

#     power_of_attorny = fields.Text('Power of Attorny')

#     @api.multi
#     def action_sanction(self):
#         for line in self:
#             line.state = 'sanction'



class stock_picking(models.Model):
    _inherit="stock.picking"

    _order = 'date desc'


    @api.multi
    def unlink(self):
        #on picking deletion, cancel its move then unlink them too
        move_obj = self.env['stock.move']
#         context = context or {}
        for pick in self:
            move_ids = [move.id for move in pick.move_lines]
            move_obj.action_cancel()
            move_obj.unlink()
            packs = self.env['stock.pack.operation'].search([('picking_id','=',pick.id)])
            for pack in packs:
                pack.unlink()
        return super(stock_picking, self).unlink()



    @api.onchange('picking_type_id')
    def onchange_picking_type(self):
        if self.picking_type_id:
            self.source_location_id = self.picking_type_id.default_location_dest_id.id

    @api.multi
    @api.depends('move_lines')
    def _compute_is_stock_receipts(self):
        cr = self._cr
        uid = self._uid
        context = self._context
        user = self.pool.get('res.users').browse(cr, uid, uid, context)
        warehouse = self.pool.get('stock.warehouse').search(cr, uid, [('company_id', '=', user.company_id.id)], limit=1, context=context)
        loc_id = self.env['stock.warehouse'].search([('id','=',warehouse[0])]).lot_stock_id

        for line in self:
            is_stock_reciept = False
            for move in line.move_lines:
                is_stock_reciept = False
                if move.location_dest_id.id == loc_id.id:
                    is_stock_reciept = True
            line.is_stock_reciept = is_stock_reciept



    @api.multi
    @api.depends('move_lines')
    def _compute_inventory_value(self):

        for line in self:
            for lines in line.move_lines:
                line.inventory_value+=lines.inventory_value

    def _state_get(self, cr, uid, ids, field_name, arg, context=None):
        '''The state of a picking depends on the state of its related stock.move
            draft: the picking has no line or any one of the lines is draft
            done, draft, cancel: all lines are done / draft / cancel
            confirmed, waiting, assigned, partially_available depends on move_type (all at once or partial)
        '''
        res = {}
        for pick in self.browse(cr, uid, ids, context=context):
            if (not pick.move_lines) or any([x.state == 'draft' for x in pick.move_lines]):
                res[pick.id] = 'draft'
                continue
            if all([x.state == 'cancel' for x in pick.move_lines]):
                res[pick.id] = 'cancel'
                continue
            if all([x.state in ('cancel', 'done') for x in pick.move_lines]):
                res[pick.id] = 'done'
                continue

            order = {'confirmed': 0, 'waiting': 1, 'assigned': 2}
            order_inv = {0: 'confirmed', 1: 'waiting', 2: 'assigned'}
            lst = [order[x.state] for x in pick.move_lines if x.state not in ('cancel', 'done')]
            if pick.move_type == 'one':
                res[pick.id] = order_inv[min(lst)]
            else:
                #we are in the case of partial delivery, so if all move are assigned, picking
                #should be assign too, else if one of the move is assigned, or partially available, picking should be
                #in partially available state, otherwise, picking is in waiting or confirmed state
                res[pick.id] = order_inv[max(lst)]
                if not all(x == 2 for x in lst):
                    if any(x == 2 for x in lst):
                        res[pick.id] = 'partially_available'
                    else:
                        #if all moves aren't assigned, check if we have one product partially available
                        for move in pick.move_lines:
                            if move.partially_available:
                                res[pick.id] = 'partially_available'
                                break

        if 'assigned' in res.values():
            res[ids[0]] = 'approve'
        return res

    def _get_pickings(self, cr, uid, ids, context=None):
        res = set()
        for move in self.browse(cr, uid, ids, context=context):
            if move.picking_id:
                res.add(move.picking_id.id)
        return list(res)


    @api.model
    def _default_journal(self):
        return self.env['account.journal'].search([('name','=','Stock Journal')], limit=1)
    @api.model
    def _default_source(self):
        return self.env['stock.location'].search([('name','=','Stock')], limit=1)



    @api.onchange('source_location_id')
    def onchange_source(self):
        if self.source_location_id:
            self.account_id = self.source_location_id.related_account.id




    source_location_id = fields.Many2one('stock.location', 'Source Location',default=_default_source)
    # account_id = fields.Many2one('account.account',string='Account')
    journal_id = fields.Many2one('account.journal',string='Journal', default=_default_journal)
    account_id = fields.Many2one('account.account', 'Account')
    min_date = fields.Datetime(default=lambda self: fields.datetime.now(), states={'done': [('readonly', True)], 'cancel': [('readonly', True)]}, string='Scheduled Date', select=1, help="Scheduled time for the first part of the shipment to be processed. Setting manually a value here would set it as expected date for all the stock moves.", track_visibility='onchange')

    task_id = fields.Many2one('project.task', string="Related task")
    is_task_related = fields.Boolean('Related to task')
    is_other_move = fields.Boolean('Other Move')
    is_eng_request = fields.Boolean('Engineer Request')
    is_stock_reciept = fields.Boolean(compute='_compute_is_stock_receipts', store=True, string='Stock Receipt', default=False)
    inventory_value = fields.Float(compute='_compute_inventory_value', string='Inventory Value')
    changed_to_allocation = fields.Boolean('Changed To Allocation', default=False)

    request_user = fields.Many2one('res.users', 'Requested By')
    is_purchase = fields.Boolean('Is From Purchase', default=False)
    purchase_id = fields.Many2one('purchase.order', 'Purchase Order')
    picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type', required=False)
#     allow_to_request = fields.Boolean(compute='_compute_allow_request' , store=True, string='Allow To Request', default=True)
#     change_help = fields.Boolean('Change', default=False)
    partner_id = fields.Many2one('res.partner', 'Partner', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},)

    returned_move_ids = fields.One2many('stock.move','returned_id', string="Returned Products")
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")

    _columns = {
        'state': old_fields.function(_state_get, type="selection", copy=False,
            store={
                    'stock.picking': (lambda self, cr, uid, ids, ctx: ids, ['move_type'], 20),
                    'stock.move': (_get_pickings, ['state', 'picking_id', 'partially_available'], 20)},
            selection=[
                ('draft', 'Draft'),
                ('cancel', 'Cancelled'),
                ('waiting', 'Waiting Another Operation'),
                ('confirmed', 'Waiting Availability'),
                ('partially_available', 'Partially Available'),
                ('approve', 'Waiting for approval'),
                ('assigned', 'Ready to Transfer'),
                ('done', 'Transferred'),
                ('partial_returned', 'Partially Returned'),
                ('returned', 'Returned'),
                ], string='Status', readonly=True, select=True, track_visibility='onchange',
            help="""
                * Draft: not confirmed yet and will not be scheduled until confirmed\n
                * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n
                * Waiting Availability: still waiting for the availability of products\n
                * Partially Available: some products are available and reserved\n
                * Ready to Transfer: products reserved, simply waiting for confirmation.\n
                * Transferred: has been processed, can't be modified or cancelled anymore\n
                * Cancelled: has been cancelled, can't be confirmed anymore"""
        ),
    }

    _defaults = {
        'request_user': lambda self, cr, uid, ctx=None: uid,
        }

    @api.multi
    def approve_picking(self):

        sql = ('UPDATE stock_picking '
                'SET state={} '
                'WHERE id={}').format('\'assigned\'', self[0].id)
        self.env.cr.execute(sql)

    @api.multi
    def set_to_draft(self):

        sql = ('UPDATE stock_picking '
                'SET state={} '
                'WHERE id={}').format('\'draft\'', self[0].id)
        self.env.cr.execute(sql)

        sql = ('UPDATE stock_move '
                'SET state={} '
                'WHERE picking_id={}').format('\'draft\'', self[0].id)
        self.env.cr.execute(sql)

    def action_confirm(self, cr, uid, ids, context=None):
        todo = []
        todo_force_assign = []
        for picking in self.browse(cr, uid, ids, context=context):
            if picking.location_id.usage in ('supplier', 'inventory', 'production'):
                todo_force_assign.append(picking.id)
            for r in picking.move_lines:
                if r.state == 'draft':
                    todo.append(r.id)
            if picking.is_eng_request == True:
                picking.changed_to_allocation = True
        if len(todo):
            self.pool.get('stock.move').action_confirm(cr, uid, todo, context=context)

        if todo_force_assign:
            self.force_assign(cr, uid, todo_force_assign, context=context)


        allow = True
        for line in self.browse(cr, uid, ids[0], context=context).move_lines:
            if line.allow_to_request == False:
                allow = False
        if allow == False:
            raise osv.except_osv(_('Warning!'),
                        _('You cannot request until the extra demand for products are approved.'))

        return True

    @api.model
    def get_move_line(self, picking_id):
        return self.env['stock.picking'].browse(picking_id).move_lines

#     from lxml import etree
#     @api.model
    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = models.Model.fields_view_get(self, cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            for sheet in doc.xpath("//sheet"):
                parent = sheet.getparent()
                index = parent.index(sheet)
                for child in sheet:
                    parent.insert(index, child)
                    index += 1
                parent.remove(sheet)
            res['arch'] = etree.tostring(doc)
#         if view_type != 'form' and uid != SUPERUSER_ID:
#             # Check if user is in group that allow creation
#             has_my_group = self.env.user.has_group('group_warehouse_user')
#             if not has_my_group:
#                 root = etree.fromstring(res['arch'])
#                 root.set('create', 'false')
#                 res['arch'] = etree.tostring(root)
        return res


    @api.multi
    def open_purchase_order(self):
        self.ensure_one()
        # Search for record belonging to the current staff
        record =  self.env['purchase.order'].search([('name','=',self.origin)])

        context = self._context.copy()
        #context['default_name'] = self.id
        if record:
            res_id = record[0].id
        else:
            res_id = False
        # Return action to open the form view
        return {
            'name':'Purchase Order view',
            'view_type': 'form',
            'view_mode':'form',
            'views' : [(False,'form')],
            'res_model':'purchase.order',
            'view_id':'purchase_order_form_changed',
            'type':'ir.actions.act_window',
            'res_id':res_id,
            'context':context,
        }


    @api.multi
    def action_account_move_create(self):
        move = self.env['account.move']
        move_line = self.env['account.move.line']
        for line in self:
            values = {
                'journal_id': self.journal_id.id,
                'date': self.min_date,
                }
            move_id = move.create(values)
            inventory_value = 0
            name = ""

            move_list = []

            for lines in line.move_lines:
                entry_list = filter(lambda x: x['account_id'] == lines.account_id.id, move_list)

                if len(entry_list) == 0:
                    move_list.append({'account_id':lines.account_id.id, 'debit': lines.inventory_value, 'credit': 0, 'move_id': move_id.id, 'name': 'Stock Movement ' + lines.product_id.categ_id.name,})

                if len(entry_list) != 0:
                                    a = move_list.index(entry_list[0])
                                    move_list[a]['debit'] += lines.inventory_value
                                    move_list[a]['credit'] += 0
                                    if lines.product_id.categ_id.name not in move_list[a]['name']:
                                        move_list[a]['name'] += ', ' + lines.product_id.categ_id.name


                entry_list = filter(lambda x: x['account_id'] == line.account_id.id, move_list)

                if len(entry_list) == 0:
                    move_list.append({'account_id':line.account_id.id, 'debit': 0, 'credit': lines.inventory_value, 'move_id': move_id.id, 'name': 'Stock Movement ' + lines.product_id.categ_id.name,})

                if len(entry_list) != 0:
                                    a = move_list.index(entry_list[0])
                                    move_list[a]['debit'] += 0
                                    move_list[a]['credit'] += lines.inventory_value
                                    if lines.product_id.categ_id.name not in move_list[a]['name']:
                                        move_list[a]['name'] += ', ' + lines.product_id.categ_id.name


            for entry_line in move_list:
                line_id = move_line.create(entry_line)

            move_id.button_validate()



    @api.cr_uid_ids_context
    def do_enter_transfer_details(self, cr, uid, picking, context=None):
        for line in self.pool.get('stock.picking').browse(cr, uid, picking):
            if not line.date_done:
                raise osv.except_osv(('Warning!'), ('Please Enter Date of Transfer'))
        if not context:
            context = {}
        else:
            context = context.copy()
        context.update({
            'active_model': self._name,
            'active_ids': picking,
            'active_id': len(picking) and picking[0] or False
        })

        created_id = self.pool['stock.transfer_details'].create(cr, uid, {'picking_id': len(picking) and picking[0] or False}, context)
        return self.pool['stock.transfer_details'].wizard_view(cr, uid, created_id, context)

    def action_invoice_create(self, cr, uid, ids, journal_id, group=False, type='in_invoice', context=None):
        res = super(stock_picking, self).action_invoice_create(cr, uid, ids, journal_id, group=False, type='in_invoice', context=None)

        return res

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        res =  super(stock_picking, self)._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=None)
        location_dest = False
        vehicle = False

        for rec in move:
            vehicle = rec.picking_id.vehicle_id.id
            location_dest = rec.location_dest_id.id
        res.update({'location_id':location_dest,
                    'vehicle':vehicle,
                    'purchase_id':rec.picking_id.purchase_id.id})
        return res

class stock_move(models.Model):
    _inherit="stock.move"
    extra_quantity = 0


    @api.onchange('product_id','location_id','product_uom_qty')
    def onchange_pro_id(self):
        if self.product_id:
            self.location_id = self.picking_id.source_location_id.id
            self.product_uom = self.product_id.uom_id.id
            self.name = self.product_id.name
            product = self.env['product.product'].search([('id','=',self.product_id.id)])
            self.available_qty = product.with_context({'location' : self.picking_id.source_location_id.id}).qty_available

            if self.product_id.product_tmpl_id.track_product == True:

                if self.product_uom_qty > self.available_qty and self.picking_id.picking_type_id.code != 'incoming':
                    self.product_uom_qty = self.available_qty
                    return {
                                'warning': {
                                    'title': 'Warning',
                                    'message': "Not Much Available Qty For This Product"
                                }
                            }
                qty = 0
                price_unit = 0
                if self.product_id and self.location_id and self.product_uom_qty:
                    qty = self.product_uom_qty
                    rec = self.env['product.price.data'].search([('site_id','=',self.location_id.id),('product_id','=',self.product_id.id)], order='date asc')
                    for val in rec:
                        if qty != 0:
                            if qty <= val.qty:
                                price_unit += qty * val.rate
                                qty = 0
                            else:
                                price_unit += val.qty * val.rate
                                qty = qty - val.qty
                    self.price_unit = price_unit/self.product_uom_qty
            else:
                self.price_unit = self.product_id.standard_price




    def _default_location_destination(self, cr, uid, context=None):
        pass




    def _default_destination_address(self, cr, uid, context=None):
        return False

    def _default_group_id(self, cr, uid, context=None):
        context = context or {}
        if context.get('default_picking_id', False):
            picking = self.pool.get('stock.picking').browse(cr, uid, context['default_picking_id'], context=context)
            return picking.group_id.id
        return False

    _defaults = {
        # 'location_id': _default_location_source,
        'location_dest_id': _default_location_destination,
        'partner_id': _default_destination_address,
        'state': 'draft',
        'priority': '1',
        'product_uom_qty': 1.0,
        'scrapped': False,

        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'stock.move', context=c),

        'procure_method': 'make_to_stock',
        'propagate': True,
        'partially_available': False,
        'group_id': _default_group_id,
    }

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
#         result = super(stock_move, self).onchange_product_id(self.product_id.id,self.location_id,self.location_dest_id, False)
#         if self.product_id.id:
#             result = result['value']
#             self.name = result['name']
#             self.product_uom = result['product_uom']
#             self.product_uos_qty = result['product_uos_qty']
#             self.product_uom_qty = result['product_uom_qty']
#             self.location_dest_id = result.get('location_dest_id', False)
#             self.product_uos = result['product_uos']
#             self.location_id = result.get('location_id', False)
        if self.task_id.id != False:
            product_ids = [estimate.pro_id.id for estimate in self.task_id.estimate_ids]

            self.location_dest_id = self.task_id.project_id.location_id

            return {
                'domain': {
                    'product_id': [('id','in',product_ids)]
                },

            }


    @api.onchange('product_uom_qty')
    def _onchange_product_uom_qty(self):

        super(stock_move, self).onchange_quantity(self.product_id.id, self.product_uom_qty, self.product_uom, self.product_uos)
        estimate = [estimate for estimate in self.task_id.estimate_ids if estimate.pro_id == self.product_id]

        if not len(estimate):
            return
        if (estimate[0].qty - self.product_uom_qty)<0:

            stock_move.extra_quantity = (self.product_uom_qty-estimate[0].qty)

            self.product_uom_qty = estimate[0].qty
            self.is_request_more_btn_visible = True


            return {
                'warning': {
                    'title': 'Warning',
                    'message': "Quantity cannot be greater than the quantity assigned for the task. Please increase the quantity from the task."
                }
            }

    @api.onchange('location_dest_id')
    def onchange_location_dest_id(self):
        if self.location_dest_id:
            self.account_id = self.location_dest_id.related_account



    @api.multi
    @api.depends('product_id','product_uom_qty','price_unit')
    def _compute_inventory_value(self):

        for line in self:
            line.inventory_value = line.price_unit * line.product_uom_qty

    def _get_line_numbers(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        line_num = 1

        if ids:
            first_line_rec = self.browse(cr, uid, ids[0], context=context)
            for line_rec in first_line_rec.picking_id.move_lines:
                line_rec.line_no = line_num
                line_num += 1

    line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
    is_request_more_btn_visible = fields.Boolean(default=False)
    is_task_related = fields.Boolean(related='picking_id.is_task_related', string='Related to task')
#     task_id = fields.Many2one(related='picking_id.task_id', string="Related task")
    task_id = fields.Many2one('project.task', string="Related Task")
    inventory_value = fields.Float(compute='_compute_inventory_value', string='Inventory Value',store=True)
#     price_unit = fields.Float(related='product_id.standard_price', string="Unit Price")
    available_qty = fields.Float(string='Available Qty')
    # related='product_id.qty_available',
    allow_to_request = fields.Boolean('Allow To Request', default=True)
    project_id = fields.Many2one('project.project', string="Related Project")
    asset_account_id = fields.Many2one('account.account', string='Asset Account')
    account_id = fields.Many2one('account.account', string='Account')
    # location_id = fields.Many2one(d', string='Source Location', required=False)
    is_purchase = fields.Boolean(related='picking_id.is_purchase', store=True)

    partner_stmt_id = fields.Many2one('partner.daily.statement')
    mach_collection_id = fields.Many2one('machinery.fuel.collection')
    mach_allocation_id = fields.Many2one('machinery.fuel.allocation')
    fuel_transfer_id = fields.Many2one('partner.fuel.transfer')
    returned_id = fields.Many2one('stock.picking','Returned Product')
    returned_qty = fields.Float(string="Returned Qty")
    category_id = fields.Many2one('product.category',"Category")
    select_qty = fields.Float("Select Quantity")
    # journal_id = fields.Many2one('account.journal', string= 'Journal')

    # @api.onchange('account_id','location_id')
    # def onchange_source_details(self):
    #     if self.picking_id:
    #         self.account_id = self.picking_id.account_id.id
    #         self.location_id = self.picking_id.source_location_id.id
    #         self.journal_id = self.picking_id.journal_id.id



#     date = fields.Date('Date', required=True, select=True, help="Move date: scheduled date until move is done, then date of actual move processing", states={'done': [('readonly', True)]})


# 	def unlink(self, cr, uid, ids, context=None):
# 		context = context or {}
# 		for move in self.browse(cr, uid, ids, context=context):
# 			if move.state not in ('draft', 'cancel'):
# #                 raise osv.except_osv(_('User Error!'), _('You can only delete draft moves.'))
# 		return super(stock_move, self).unlink(cr, uid, ids, context=context)


    @api.multi
    def unlink(self):
        for move in self:
            quants = self.env['stock.quant'].search([('reservation_id','=', move.id)])
            for quant in move.quant_ids:
                quant.qty = 0.0
            move.state = 'draft'
            move.product_id.product_tmpl_id.qty_available = move.product_id.product_tmpl_id.qty_available - move.product_uom_qty
#             if move.state not in ('draft', 'cancel'):
#                 raise osv.except_osv(_('User Error!'), _('You can only delete draft moves.'))
            if move.picking_id:
                packs = self.env['stock.pack.operation'].search([('picking_id','=',move.picking_id.id)])
                for pack in packs:
                    pack.unlink()
            return  super(stock_move, move).unlink()


    # def onchange_product_id(self, cr, uid, ids, prod_id=False, loc_id=False, loc_dest_id=False, partner_id=False):
    #     """ On change of product id, if finds UoM, UoS, quantity and UoS quantity.
    #     @param prod_id: Changed Product id
    #     @param loc_id: Source location id
    #     @param loc_dest_id: Destination location id
    #     @param partner_id: Address id of partner
    #     @return: Dictionary of values
    #     """
    #     if not prod_id:
    #         return {}
    #     user = self.pool.get('res.users').browse(cr, uid, uid)
    #     lang = user and user.lang or False
    #     if partner_id:
    #         addr_rec = self.pool.get('res.partner').browse(cr, uid, partner_id)
    #         if addr_rec:
    #             lang = addr_rec and addr_rec.lang or False
    #     ctx = {'lang': lang}

    #     product = self.pool.get('product.product').browse(cr, uid, [prod_id], context=ctx)[0]
    #     uos_id = product.uos_id and product.uos_id.id or False
    #     result = {
    #         'name': product.partner_ref,
    #         'product_uom': product.uom_id.id,
    #         'price_unit': product.standard_price,
    #         'asset_account_id': product.categ_id.stock_account_id.id,
    #         'product_uos': uos_id,
    #         'product_uom_qty': 0.00,
    #         'product_uos_qty': self.pool.get('stock.move').onchange_quantity(cr, uid, ids, prod_id, 1.00, product.uom_id.id, uos_id)['value']['product_uos_qty'],
    #     }
    #     # if loc_id:
    #     #     result['location_id'] = loc_id
    #     # if loc_dest_id:
    #     #     result['location_dest_id'] = loc_dest_id
    #     return {'value': result}



    @api.multi
    def generate_prchase_order(self):
        self.ensure_one()
        view_id = self.env.ref('hiworth_construction.purchase_order_form_changed').id

        context = self._context.copy()

        order_obj = self.env['purchase.order']
        order_line_obj = self.env['purchase.order.line']
        price_list = self.env['product.pricelist'].search([('name','=','Default Purchase Pricelist')])

        order_values = {'origin': self.picking_id.name,
                        'date_order': self.date,
                         'location_id': self.location_id.id,
                        'state': 'draft',
                        'minimum_planned_date': self.picking_id.min_date,
                        'pricelist_id': price_list.id,

                   }

        order_id = order_obj.create(order_values)
        order_line_values = {'product_id': self.product_id.id,
                             'name': self.product_id.name,
                              'price_unit': self.product_id.standard_price,
                              'product_qty': self.product_uom_qty,
                              'date_planned': self.picking_id.min_date,
                              'order_id': order_id.id }
        line_id = order_line_obj.create(order_line_values)

        context = {'related_usage': False,
                   }
        return {
            'name':'Purchase Requisition',
            'view_type':'form',
            'view_mode':'tree',
            'views' : [(view_id, 'form')],
            'res_model':'purchase.order',
            'view_id':view_id,
            'type':'ir.actions.act_window',
            'res_id':order_id.id,

            'context':context,
            }

    @api.multi
    def request_more_task_qty(self):
        return {
            'type': 'ir.actions.act_window',
            'id': 'test_id_act',
            'res_model': 'estimate.quantity.extra.request',
            'views': [[self.env.ref("hiworth_construction.estimate_quantity_extra_request_popup").id, "form"]],
            'target': 'new',
            'name': 'Send extra request',
            'context': {
                'default_task_id': self.picking_id.task_id.id,
                'default_product_id': self.product_id.id,
                'default_materialrequest_id': self.picking_id.id,
                'default_quantity': stock_move.extra_quantity,
                'default_date': fields.Datetime.now(),
                'default_move_id': self.id
            }
        }

class EstimateQuantityExtraRequest(models.Model):
    _name='estimate.quantity.extra.request'

    task_id = fields.Many2one('project.task', 'Task')
    product_id = fields.Many2one('product.product', 'Product')
    materialrequest_id  = fields.Many2one('stock.picking')
    quantity = fields.Float(string="Quantity")
    date = fields.Date()
    move_id = fields.Many2one('stock.move', 'Stock Move')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),
        ],default='draft')

    @api.multi
    def extra_request_approve(self):
        self.ensure_one()
        estimate = [estimate for estimate in self.task_id.estimate_ids if estimate.pro_id == self.product_id]
        if estimate:
            estimate[0].qty = estimate[0].qty+self.quantity
        self.state = 'approved'
        self.move_id.allow_to_request = True

    @api.multi
    def extra_request_reject(self):
        self.ensure_one()
        self.state = 'rejected'

    @api.multi
    def write(self,vals):
        if self.move_id.id != False:

            self.move_id.is_request_more_btn_visible = False
            self.move_id.allow_to_request = False

        super(EstimateQuantityExtraRequest, self).write(vals)
        return True


class res_groups(models.Model):
    _inherit = 'res.groups'

    company_group = fields.Boolean('Company Group')


class product_category(models.Model):
    _inherit = 'product.category'

    stock_account_id = fields.Many2one('account.account', 'Asset Account', domain=[('type','not in', ['view','consolidation', 'closed'])])




class stock_return_picking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self, cr, uid, ids, context=None):
        res,res1 = super(stock_return_picking, self)._create_returns(cr, uid, ids, context=None)




        return res,res1

class stock_quant(osv.osv):
    _inherit = 'stock.quant'
    _order = 'in_date asc'



class stock_inventory(osv.osv):
    _inherit = "stock.inventory"

    category_id = fields.Many2one('product.category',"Category")

    def _get_inventory_lines(self, cr, uid, inventory, context=None):
        location_obj = self.pool.get('stock.location')
        product_obj = self.pool.get('product.product')
        location_ids = location_obj.search(cr, uid, [('id', 'child_of', [inventory.location_id.id])], context=context)
        domain = ' location_id in %s'
        args = (tuple(location_ids),)
        if inventory.partner_id:
            domain += ' and owner_id = %s'
            args += (inventory.partner_id.id,)
        if inventory.lot_id:
            domain += ' and lot_id = %s'
            args += (inventory.lot_id.id,)
        if inventory.product_id:

            domain += ' and product_id = %s'
            args += (inventory.product_id.id,)
        if inventory.package_id:
            domain += ' and package_id = %s'
            args += (inventory.package_id.id,)


        cr.execute('''
           SELECT product_id, sum(qty) as product_qty, location_id, lot_id as prod_lot_id, package_id, owner_id as partner_id
           FROM stock_quant WHERE''' + domain + '''
           GROUP BY product_id, location_id, lot_id, package_id, partner_id
        ''', args)
        vals = []
        for product_line in cr.dictfetchall():
            # replace the None the dictionary by False, because falsy values are tested later on
            for key, value in product_line.items():
                if not value:
                    product_line[key] = False
            if inventory.category_id:
                if product_line['product_id']:
                    product = product_obj.browse(cr, uid, product_line['product_id'], context=context)
                    product_line['product_uom_id'] = product.uom_id.id
                if inventory.category_id.id == product_obj.browse(cr, uid, product_line['product_id'], context=context).categ_id.id:

                    product_line['inventory_id'] = inventory.id
                    product_line['theoretical_qty'] = product_line['product_qty']
                    if product_line['product_id']:
                        product = product_obj.browse(cr, uid, product_line['product_id'], context=context)
                        product_line['product_uom_id'] = product.uom_id.id
                    vals.append(product_line)
            else:
                product_line['inventory_id'] = inventory.id
                product_line['theoretical_qty'] = product_line['product_qty']
                if product_line['product_id']:
                    product = product_obj.browse(cr, uid, product_line['product_id'], context=context)
                    product_line['product_uom_id'] = product.uom_id.id
                vals.append(product_line)
        return vals

class stock_inventory_line(osv.osv):
    _inherit = "stock.inventory.line"

    _defaults = {
        'product_qty': 0,
        'product_uom_id': False
    }

    # Should be left out in next version
    def on_change_product_id(self, cr, uid, ids, product, uom, theoretical_qty, context=None):
        """ Changes UoM
        @param location_id: Location id
        @param product: Changed product_id
        @param uom: UoM product
        @return:  Dictionary of changed values
        """
        product_ids = []
        obj_product = self.pool.get('product.product').browse(cr, uid, product, context=context)

        return {'value': {'product_uom_id': uom or obj_product.uom_id.id},
                }

    def onchange_createline(self, cr, uid, ids, location_id=False, product_id=False, uom_id=False, package_id=False,
                            prod_lot_id=False, partner_id=False, company_id=False, context=None):
        quant_obj = self.pool["stock.quant"]
        uom_obj = self.pool["product.uom"]
        res = {'value': {}}

        # If no UoM already put the default UoM of the product
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            uom = self.pool['product.uom'].browse(cr, uid, uom_id, context=context)
            if product.uom_id.category_id.id != uom.category_id.id:
                res['value']['product_uom_id'] = product.uom_id.id
                res['domain'] = {'product_uom_id': [('category_id', '=', product.uom_id.category_id.id)],
                                 'product_id': [('categ_id', '=', context.get('default_category_id'))]}
                uom_id = product.uom_id.id
        # Calculate theoretical quantity by searching the quants as in quants_get
        if product_id and location_id:
            product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
            if not company_id:
                company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
            dom = [('company_id', '=', company_id), ('location_id', '=', location_id), ('lot_id', '=', prod_lot_id),
                   ('product_id', '=', product_id), ('owner_id', '=', partner_id), ('package_id', '=', package_id)]
            quants = quant_obj.search(cr, uid, dom, context=context)
            th_qty = sum([x.qty for x in quant_obj.browse(cr, uid, quants, context=context)])
            if product_id and uom_id and product.uom_id.id != uom_id:
                th_qty = uom_obj._compute_qty(cr, uid, product.uom_id.id, th_qty, uom_id)
            res['value']['theoretical_qty'] = th_qty
            res['value']['product_qty'] = th_qty


        return res

    def _get_move_values(self, cr, uid, inventory_line, qty, location_id, location_dest_id):
        return {
            'name': _('INV:') + (inventory_line.inventory_id.name or ''),
            'product_id': inventory_line.product_id.id,
            'product_uom': inventory_line.product_uom_id.id,
            'product_uom_qty': qty,
            'date': inventory_line.inventory_id.date,
            'date_expected': inventory_line.inventory_id.date,
            'company_id': inventory_line.inventory_id.company_id.id,
            'inventory_id': inventory_line.inventory_id.id,
            'state': 'confirmed',
            'price_unit':inventory_line.product_id.standard_price,
            'restrict_lot_id': inventory_line.prod_lot_id.id,
            'restrict_partner_id': inventory_line.partner_id.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
        }


class ResPartner(models.Model):
    _inherit = "res.partner"

    responsible_name = fields.Char()
    responsible_mobile = fields.Char()
    responsible_email = fields.Char()
    owner_name = fields.Char()
    vat_no = fields.Char()
    trn_no = fields.Char()

