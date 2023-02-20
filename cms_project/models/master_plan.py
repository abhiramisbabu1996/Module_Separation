from openerp import models, fields, api, _
from openerp.osv import osv, expression
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class VehicleCategoryTypes(models.Model):
    _name = 'vehicle.category.types'

    name = fields.Char(string="Vehicle Type")


class ProjectWork1(models.Model):
    _name = 'project.work'

    name = fields.Char('Work Name')


class MasterPlanForm(models.Model):
    _name = 'master.plan'

    name = fields.Char(string="Planning/Programme")
    site_id = fields.Many2one('stock.location', string="Location")
    no_floors = fields.Integer()
    sqft = fields.Float('Square Feet')
    completion_date = fields.Date('Completion Date')
    target_date = fields.Date('Target Date')
    master_plan_line = fields.One2many('master.plan.line', 'line_id')
    # planning_chart_line = fields.One2many('planning.chart.line','master_plan_id')
    agreement_date = fields.Date('Agreement Date')
    work_start_date = fields.Date('Work Start Date')
    project_name = fields.Many2one('project.project', 'Project')
    contractor_id = fields.Many2one('res.partner', string="Contractor")

    @api.onchange('project_name')
    def onchange_project_name(self):
        for rec in self:
            rec.site_id = rec.project_name.project_location.id


class MasterPlanLine(models.Model):
    _name = 'master.plan.line'
    _rec_name = "work_id"

    @api.model
    def create(self, vals):
        # print("helooo master plan..................")
        res = super(MasterPlanLine, self).create(vals)
        project_id = res.line_id.project_name
        if project_id:
            lines = vals
            # vals.pop('line_id')
            # vals.pop('veh_categ_id')
            lines.update({'master_plan_line_id1': res.id,
                          'project_id': project_id.id})
            project_id.project_master_line_ids1.create(lines)
        return res

    line_id = fields.Many2one('master.plan')
    work_id = fields.Many2one('project.work', 'Description Of Work')
    qty_estimate = fields.Float('Qty As Per Estimate')
    unit = fields.Many2one('product.uom', 'Unit')
    duration = fields.Float('Duration(Days)')
    no_labours = fields.Integer()
    start_date = fields.Date('Start Date')
    finish_date = fields.Date('Finish Date')
    employee_id = fields.Many2one('hr.employee', 'Site Engineer')
    veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
    material = fields.Many2many('product.product',string="Materials")
    products_id = fields.Many2many('product.product', string='Products')
    estimate_cost = fields.Float('Estimate Cost')
    sqft = fields.Float('Area')
    pre_qty = fields.Float('Previous Qty')
    remarks = fields.Text()
    upto_date_qty = fields.Float(store=True, string='Balance Qty')
    quantity = fields.Float(string='Work Order Qty')
    subcontractor = fields.Many2one('res.partner', )

    @api.one
    @api.onchange('start_date', 'finish_date')
    def onchange_start_date(self):
        for rec in self:
            if rec.start_date and rec.finish_date:
                rec.duration = (datetime.strptime(rec.finish_date, "%Y-%m-%d") - datetime.strptime(rec.start_date,
                                                                                                   "%Y-%m-%d")).days

    @api.onchange('subcontractor', 'line_id.project_name')
    def onchange_project_id_subcontractor(self):
        subcontractor_ids = []
        for rec in self:
            if rec.line_id.project_name:
                if rec.line_id.project_name.contractor_id1:
                    subcontractor_ids.append(rec.line_id.project_name.contractor_id1.id)
                if rec.line_id.project_name.contractor_id2:
                    subcontractor_ids.append(rec.line_id.project_name.contractor_id2.id)
                if rec.line_id.project_name.contractor_id3:
                    subcontractor_ids.append(rec.line_id.project_name.contractor_id3.id)
                return {'domain': {
                    'subcontractor': [('id', 'in', subcontractor_ids)]
                }}

    @api.onchange('employee_id', 'line_id.project_name')
    def onchange_project_id(self):
        for rec in self:
            employee_ids = []
            if rec.line_id:
                if rec.line_id.project_name:
                    if rec.line_id.project_name.site_engineer1:
                        employee_ids.append(rec.line_id.project_name.site_engineer1.id)
                    if rec.line_id.project_name.site_engineer2:
                        employee_ids.append(rec.line_id.project_name.site_engineer2.id)
                    if rec.line_id.project_name.site_engineer3:
                        employee_ids.append(rec.line_id.project_name.site_engineer3.id)

                return {'domain': {
                    'employee_id': [('id', 'in', employee_ids)]
                }}


