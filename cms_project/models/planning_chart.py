from openerp import models, fields, api, _
from openerp.osv import osv, expression
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta



class PlanningChart(models.Model):
    _name = 'planning.chart'
    _rec_name = 'date'

    supervisor_id = fields.Many2one('hr.employee','Name Of Supervisor/Captain')
    project_id = fields.Many2one('project.project')
    site_id = fields.Many2one('master.plan', string="Planning/Programme")
    work_plan_id = fields.Many2one('master.plan.line', string="Work Plan")
    date = fields.Date('Creation Date', default=datetime.today())
    planning_chart_line = fields.One2many('planning.chart.line','line_id')
    duration_from = fields.Date("Duration From")
    duration_to = fields.Date("Duration To")
    master_plan_line = fields.One2many('master.plan.chart.line', 'chart_id')
    master_plan_line_new = fields.One2many('master.plan.chart.line1', 'chart_id')

    @api.onchange('site_id')
    def onchange_site_id(self):
        list = []
        for rec in self:
            if rec.site_id:
                rec.project_id = rec.site_id.project_name.id
                rec.duration_to = rec.site_id.work_start_date
                rec.duration_from = rec.site_id.completion_date
                rec.master_plan_line = False
                for line in rec.site_id.master_plan_line:
                    list.append([0, 0, {'subcontractor': line.subcontractor.id,
                                        'quantity': line.quantity,
                                        'upto_date_qty': line.upto_date_qty,
                                        'remarks': line.remarks,
                                        'pre_qty': line.pre_qty,
                                        'sqft': line.sqft,
                                        'estimate_cost': line.estimate_cost,
                                        'products_id': line.products_id.ids,
                                        'veh_categ_id': line.veh_categ_id.ids,
                                        'material': line.material.ids,
                                        'employee_id': line.employee_id.id,
                                        'finish_date': line.finish_date,
                                        'start_date': line.start_date,
                                        'no_labours': line.no_labours,
                                        'duration': line.duration,
                                        'unit': line.unit.id,
                                        'qty_estimate': line.qty_estimate,
                                        'work_id': line.work_id.id,
                                        'line_id': line.line_id.id,
                                        }])
            rec.update({'master_plan_line_new' :list})




class PlanningChartLine(models.Model):
    _name = 'planning.chart.line'
    _rec_name = 'master_plan_line_id'

    project_id = fields.Many2one('project.project')
    mep = fields.Selection([('mechanical', 'Mechanical'), ('electricel', 'Electrical'), ('plumbing', 'Plumbing')])
    master_plan_id = fields.Many2one('master.plan')
    master_plan_line_id = fields.Many2one('master.plan.line', required=True)
    line_id = fields.Many2one('planning.chart')
    date = fields.Date('Date')
    work_id = fields.Char('Work Description')
    labour = fields.Float('No of Labours')
    labour_charge = fields.Float('Labour Cost')
    # veh_categ_id = fields.Many2many('vehicle.category.types', string='Machinery')
    veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
    machinery_charge = fields.Float('Machinery Cost')
    qty = fields.Float('Qty')
    target_qty = fields.Float('Target Qty')
    material_qty = fields.Float('Material Qty')
    material = fields.Many2many('product.product', string='Materials')
    uom_id = fields.Many2one('product.uom', string="Units")
    working_hours = fields.Float('Working Hours')
    remarks = fields.Char('Remarks')
    sqft = fields.Float('Square Feet')
    estimated_cost = fields.Float(string='Material Cost')
    work_status = fields.Selection([('started', 'Started'),
                                    ('on_progressing', 'On Progressing'),
                                    ('partially_completed', 'Partially Completed'),
                                    ('completed', 'Completed')])
    total_charge = fields.Float('Total Cost')
    test = fields.Float('test', compute="_compute_lines_total")

    @api.multi
    @api.onchange('labour_charge', 'machinery_charge', 'estimated_cost', 'total_charge', 'test')
    def _compute_lines_total(self):
        total = 0.0
        for rec in self:
            total = rec.labour_charge + rec.machinery_charge + rec.estimated_cost
            rec.total_charge = total

    # @api.model
    # def create(self, vals):
    #     res = super(PlanningChartLine, self).create(vals)
    #     project_id = res.line_id.project_id or res.master_plan_line_id.line_id.project_name
    #     # lines = []
    #     if project_id:
    #         lines = vals
    #         lines.update({'plan_id': res.id,
    #                       'project_id': project_id.id})
    #         project_id.planning_chart_line_ids.create(lines)
    #
    #     return res

    @api.onchange('master_plan_line_id')
    def _onchage_master_plan_line_id(self):
        for rec in self:
            if rec.master_plan_id:
                return {'domain': {'master_plan_line_id': [('id', '=', rec.master_plan_id.master_plan_line.ids)]}}


    @api.model
    def create(self, vals):
        res = super(PlanningChartLine, self).create(vals)
        project_id = res.line_id.project_id or res.master_plan_line_id.line_id.project_name
        if project_id:
            print("planning chart",vals)
            lines = vals
            # vals.pop('line_id')
            # vals.pop('veh_categ_id')
            # vals.pop('material')
            lines.update({'plan_id': res.id,
                         'project_id': project_id.id})
            project_id.planning_chart_line_ids.create(lines)


        return res

    @api.multi
    def write(self, vals):
        res = super(PlanningChartLine, self).write()
        res.line_id.project_name.update(vals)
        return res


class MasterPlanChartLine(models.Model):
    _name = 'master.plan.chart.line'
    _rec_name = "work_id"

    chart_id = fields.Many2one('planning.chart')
    line_id = fields.Many2one('master.plan')
    work_id = fields.Many2one('project.work', 'Description Of Work')
    qty_estimate = fields.Float('Qty As Per Estimate')
    unit = fields.Many2one('product.uom','Unit')
    duration = fields.Float('Duration(Days)')
    no_labours = fields.Integer()
    start_date = fields.Date('Start Date')
    finish_date = fields.Date('Finish Date')
    employee_id = fields.Many2one('hr.employee', 'Site Engineer')
    # veh_categ_id = fields.Many2many('vehicle.category.types',string='Machinery')
    veh_categ_id = fields.Many2many('fleet.vehicle',string='Machinery')
    products_id = fields.Many2many('product.product', string='Products')
    estimate_cost = fields.Float('Estimate Cost')
    sqft = fields.Float('Square Feet')
    pre_qty = fields.Float('Previous Qty')
    remarks = fields.Text()
    upto_date_qty = fields.Float(store=True, string='Balance Qty')
    quantity = fields.Float(string='Work Order Qty')
    subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])

class MasterPlanChartLineNew(models.Model):
    _name = 'master.plan.chart.line1'
    _rec_name = "work_id"

    chart_id = fields.Many2one('planning.chart')
    line_id = fields.Many2one('master.plan')
    work_id = fields.Many2one('project.work', 'Description Of Work')
    qty_estimate = fields.Float('Qty As Per Estimate')
    unit = fields.Many2one('product.uom','Unit')
    duration = fields.Float('Duration(Days)')
    no_labours = fields.Integer()
    start_date = fields.Date('Start Date')
    finish_date = fields.Date('Finish Date')
    employee_id = fields.Many2one('hr.employee', 'Site Engineer')
    veh_categ_id = fields.Many2many('fleet.vehicle',string='Machinery')
    # veh_categ_id = fields.Many2many('vehicle.category.types',string='Machinery')
    products_id = fields.Many2many('product.product', string='Products')
    estimate_cost = fields.Float('Estimate Cost')
    sqft = fields.Float('Square Feet')
    pre_qty = fields.Float('Previous Qty')
    remarks = fields.Text()
    upto_date_qty = fields.Float(store=True, string='Balance Qty')
    quantity = fields.Float(string='Work Order Qty')
    subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])
    material = fields.Many2many('product.product', string='Materials')

