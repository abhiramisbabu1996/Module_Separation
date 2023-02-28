from openerp import models, fields, api, _
from openerp.osv import osv, expression
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class MasterPlan(models.Model):
    _name = 'master.plan'

    name = fields.Char(string="Planning/Programme")
    site_id = fields.Many2one('stock.location', string="Location")
    no_floors = fields.Integer()
    sqft = fields.Float('Square Feet')
    completion_date = fields.Date('Completion Date')
    target_date = fields.Date('Target Date')
    master_plan_line = fields.One2many('master.plan.line','line_id')
    planning_chart_line = fields.One2many('planning.chart.line','master_plan_id')
    agreement_date = fields.Date('Agreement Date')
    work_start_date = fields.Date('Work Start Date')
    project_name = fields.Many2one('project.project', 'Project')
    contractor_id = fields.Many2one('res.partner', string="Contractor")

    @api.onchange('project_name')
    def onchange_project_name(self):
        for rec in self:
            rec.site_id = rec.project_name.project_location_ids.id


class MasterPlanLine(models.Model):
    _name = 'master.plan.line'
    _rec_name = "work_id"

    line_id = fields.Many2one('master.plan')
    work_id = fields.Many2one('project.work', 'Description Of Work')
    qty_estimate = fields.Float('Qty As Per Estimate')
    unit = fields.Many2one('product.uom','Unit')
    duration = fields.Float('Duration(Days)')
    no_labours = fields.Integer()
    start_date = fields.Date('Start Date')
    finish_date = fields.Date('Finish Date')
    employee_id = fields.Many2one('hr.employee', 'Site Engineer')
    # veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
    veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
    products_id = fields.Many2many('product.product', string='Products')
    estimate_cost = fields.Float('Estimate Cost')
    sqft = fields.Float('Area')
    pre_qty = fields.Float('Previous Qty')
    remarks = fields.Text()
    upto_date_qty = fields.Float(store=True, string='Balance Qty')
    quantity = fields.Float(string='Work Order Qty')
    subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])\

    @api.one
    @api.onchange('start_date', 'finish_date')
    def onchange_start_date(self):
        for rec in self:
            if rec.start_date and rec.finish_date:
                rec.duration = (datetime.strptime(rec.finish_date, "%Y-%m-%d") - datetime.strptime(rec.start_date, "%Y-%m-%d")).days

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
                return {'domain':{
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

    @api.one
    @api.onchange('chainage_from', 'chainage_to')
    def onchange_chainage_from(self):
        if self.chainage_to:
            self.length = self.chainage_to - self.chainage_from



    @api.model
    def create(self, vals):
        res = super(MasterPlanLine, self).create(vals)
        project_id = res.line_id.project_name
        # lines = []
        if project_id:
            # line = res.copy()
            # line.project_id = project_id
            lines = vals
            lines.update({'master_plan_line_id': res.id,
                         'project_id': project_id.id})
            project_id.project_master_line_ids.create(lines)
        return res


class ProjectWork1(models.Model):
    _name = 'project.work'

    name = fields.Char('Work Name')


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
    master_plan_line_demo = fields.One2many('master.plan.chart.line1', 'chart_id')

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
            rec.update({'master_plan_line' :list})
            rec.update({'master_plan_line_demo' :list})




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
    # veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
    veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
    qty = fields.Float('Qty')
    target_qty = fields.Float('Target Qty')
    material_qty = fields.Float('Material Qty')
    material = fields.Many2many('product.product', string='Materials')
    uom_id = fields.Many2one('product.uom', string="Units")
    working_hours = fields.Float('Working Hours')
    remarks = fields.Char('Remarks')
    sqft = fields.Float('Square Feet')
    estimated_cost = fields.Float('Material Cost')
    work_status = fields.Selection([('started', 'Started'),
                                    ('on_progressing', 'On Progressing'),
                                    ('partially_completed', 'Partially Completed'),
                                    ('completed', 'Completed')])
    labour_charge = fields.Float('Labour Cost')
    machinery_charge = fields.Float('Machinery Cost')
    total_charge = fields.Float('Total Cost')
    test = fields.Float('test',compute="_compute_lines_total")

    @api.multi
    @api.onchange('labour_charge','machinery_charge','estimated_cost','total_charge','test')
    def _compute_lines_total(self):
        total=0.0
        for rec in self:
            total = rec.labour_charge+rec.machinery_charge+rec.estimated_cost
            rec.total_charge = total




    @api.onchange('master_plan_line_id')
    def _onchage_master_plan_line_id(self):
        for rec in self:
            if rec.master_plan_id:
                return {'domain': {'master_plan_line_id': [('id', '=', rec.master_plan_id.master_plan_line.ids)]}}


    @api.model
    def create(self, vals):
        res = super(PlanningChartLine, self).create(vals)
        project_id = res.line_id.project_id or res.master_plan_line_id.line_id.project_name
        # lines = []
        if project_id:
            # line = res.copy()
            # line.project_id = project_id
            lines = vals
            # if 'master_plan_id' in lines:
            #     del lines['master_plan_id']
            lines.update({'plan_id': res.id,
                         'project_id': project_id.id})
            # new_lines = [(0, 0, lines)]
            # # project_id.update({'estimation_line_ids': lines})
            # # project_id.update({'planning_chart_line_ids': [(0, 0, lines)]})
            # lines[] = pr
            project_id.planning_chart_line_ids.create(lines)


        return res
            # lines = [(0, 0, {
            #     'subcontractor': res.master_plan_line_id.subcontractor.id,
            #     'quantity': res.qty,
            #     'upto_date_qty': res.master_plan_line_id.upto_date_qty,
            #     'sqft': res.sqft,
            #     'estimate_cost': res.estimated_cost,
            #     'employee_id': res.master_plan_line_id.employee_id.id,
            #     'finish_date': res.master_plan_line_id.finish_date,
            #     'start_date': res.master_plan_line_id.start_date,
            #     'no_labours': res.labour,
            #     'duration': res.working_hours,
            #     'unit': res.uom_id.id,
            #     'qty_estimate': res.material_qty,
            #     'material': res.material.ids,
            #     'veh_categ_id': res.master_plan_line_id.veh_categ_id.ids,
            #     'mep': res.mep,
            #     'chart_plan_line_id': res.id,
            #     'plan_line_id': res.master_plan_line_id.id,
            #     'project_id': project_id.id,
            # })]
            # project_id.update({'estimation_line_ids': lines})
        # return res
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
    labour_charge = fields.Float('Labour Cost')
    start_date = fields.Date('Start Date')
    finish_date = fields.Date('Finish Date')
    employee_id = fields.Many2one('hr.employee', 'Site Engineer')
    # veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
    veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
    machinery_charge = fields.Float('Machinery Cost')
    products_id = fields.Many2many('product.product', string='Products')
    estimate_cost = fields.Float('Estimate Cost')
    sqft = fields.Float('Square Feet')
    pre_qty = fields.Float('Previous Qty')
    remarks = fields.Text()
    upto_date_qty = fields.Float(store=True, string='Balance Qty')
    quantity = fields.Float(string='Work Order Qty')
    subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])
    total_charge = fields.Float('Total Cost')
class MasterPlanChartLineDemo(models.Model):
    _name = 'master.plan.chart.line1'
    _rec_name = "work_id"

    chart_id = fields.Many2one('planning.chart')
    line_id = fields.Many2one('master.plan')
    work_id = fields.Many2one('project.work', 'Description Of Work')
    qty_estimate = fields.Float('Qty As Per Estimate')
    unit = fields.Many2one('product.uom','Unit')
    duration = fields.Float('Duration(Days)')
    no_labours = fields.Integer()
    labour_charge = fields.Float('Labour Cost')
    start_date = fields.Date('Start Date')
    finish_date = fields.Date('Finish Date')
    employee_id = fields.Many2one('hr.employee', 'Site Engineer')
    # veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
    veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
    machinery_charge = fields.Float('Machinery Cost')
    products_id = fields.Many2many('product.product', string='Products')
    estimate_cost = fields.Float('Estimate Cost')
    sqft = fields.Float('Square Feet')
    pre_qty = fields.Float('Previous Qty')
    remarks = fields.Text()
    upto_date_qty = fields.Float(store=True, string='Balance Qty')
    quantity = fields.Float(string='Work Order Qty')
    subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])
    total_charge = fields.Float('Total Cost')




# class MasterPlan(models.Model):
# 	_name = 'master.plan'
#
# 	name = fields.Char(string="Planning/Programme")
# 	site_id = fields.Many2one('stock.location', string="Location")
# 	no_floors = fields.Integer()
# 	sqft = fields.Float('Square Feet')
# 	completion_date = fields.Date('Completion Date')
# 	target_date = fields.Date('Target Date')
# 	master_plan_line = fields.One2many('master.plan.line','line_id')
# 	planning_chart_line = fields.One2many('planning.chart.line','master_plan_id')
# 	agreement_date = fields.Date('Agreement Date')
# 	work_start_date = fields.Date('Work Start Date')
# 	project_name = fields.Many2one('project.project', 'Project')
# 	contractor_id = fields.Many2one('res.partner', string="Contractor")
#
#
# class MasterPlanLine(models.Model):
# 	_name = 'master.plan.line'
# 	_rec_name = "work_id"
#
# 	line_id = fields.Many2one('master.plan')
# 	work_id = fields.Many2one('project.work', 'Description Of Work')
# 	qty_estimate = fields.Float('Qty As Per Estimate')
# 	unit = fields.Many2one('product.uom','Unit')
# 	duration = fields.Float('Duration(Days)')
# 	no_labours = fields.Integer()
# 	start_date = fields.Date('Start Date')
# 	finish_date = fields.Date('Finish Date')
# 	employee_id = fields.Many2one('hr.employee', 'Site Engineer')
# 	veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
# 	products_id = fields.Many2many('product.product', string='Products')
# 	estimate_cost = fields.Float('Estimate Cost')
# 	sqft = fields.Float('Square Feet')
# 	pre_qty = fields.Float('Previous Qty')
# 	remarks = fields.Text()
# 	upto_date_qty = fields.Float(store=True, string='Balance Qty')
# 	quantity = fields.Float(string='Work Order Qty')
# 	subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])
#
# 	@api.one
# 	@api.onchange('start_date','duration')
# 	def onchange_start_date(self):
# 		if self.start_date and self.duration:
# 			self.finish_date = datetime.strptime(self.start_date, "%Y-%m-%d") + timedelta(days=self.duration-1)
#
# 	@api.one
# 	@api.onchange('chainage_from','chainage_to')
# 	def onchange_chainage_from(self):
# 		if self.chainage_to:
# 			self.length = self.chainage_to - self.chainage_from
#
#
# class ProjectWork1(models.Model):
# 	_name = 'project.work'
#
# 	name = fields.Char('Work Name')
#
#
# class PlanningChart(models.Model):
# 	_name = 'planning.chart'
# 	_rec_name = 'date'
#
# 	supervisor_id = fields.Many2one('hr.employee','Name Of Supervisor/Captain')
# 	site_id = fields.Many2one('master.plan', string="Planning/Programme")
# 	work_plan_id = fields.Many2one('master.plan.line', string="Work Plan")
# 	date = fields.Date('Creation Date')
# 	planning_chart_line = fields.One2many('planning.chart.line','line_id')
# 	duration_from = fields.Date("Duration From")
# 	duration_to = fields.Date("Duration To")
# 	master_plan_line = fields.One2many('master.plan.chart.line', 'chart_id')
#
# 	@api.onchange('site_id')
# 	def onchange_site_id(self):
# 		list = []
# 		for rec in self:
# 			if rec.site_id:
# 				for line in rec.site_id.master_plan_line:
# 					list.append([0, 0, {'subcontractor': line.subcontractor.id,
# 										'quantity': line.quantity,
# 										'upto_date_qty': line.upto_date_qty,
# 										'remarks': line.remarks,
# 										'pre_qty': line.pre_qty,
# 										'sqft': line.sqft,
# 										'estimate_cost': line.estimate_cost,
# 										'products_id': line.products_id.ids,
# 										'veh_categ_id': line.veh_categ_id.ids,
# 										'employee_id': line.employee_id.id,
# 										'finish_date': line.finish_date,
# 										'start_date': line.start_date,
# 										'no_labours': line.no_labours,
# 										'duration': line.duration,
# 										'unit': line.unit.id,
# 										'qty_estimate': line.qty_estimate,
# 										'work_id': line.work_id.id,
# 										'line_id': line.line_id.id,
# 										}])
# 			rec.master_plan_line = list
#
#
# class PlanningChartLine(models.Model):
# 	_name = 'planning.chart.line'
#
# 	master_plan_id = fields.Many2one('master.plan')
# 	master_plan_line_id = fields.Many2one('master.plan.line')
# 	line_id = fields.Many2one('planning.chart')
# 	date = fields.Date('Date')
# 	work_id = fields.Char('Work Description')
# 	labour = fields.Float('No of Labours')
# 	veh_categ_id = fields.Many2many('vehicle.category.type',string='Machinery')
# 	qty = fields.Float('Qty')
# 	target_qty = fields.Float('Target Qty')
# 	material_qty = fields.Float('Material Qty')
# 	material = fields.Many2many('product.product', string='Materials')
# 	uom_id = fields.Many2one('product.uom',string="Units")
# 	working_hours = fields.Float('Working Hours')
# 	remarks = fields.Char('Remarks')
# 	sqft = fields.Float('Square Feet')
# 	estimated_cost = fields.Float('')
#
#
# class MasterPlanChartLine(models.Model):
# 	_name = 'master.plan.chart.line'
# 	_rec_name = "work_id"
#
# 	chart_id = fields.Many2one('planning.chart')
# 	line_id = fields.Many2one('master.plan')
# 	work_id = fields.Many2one('project.work', 'Description Of Work')
# 	qty_estimate = fields.Float('Qty As Per Estimate')
# 	unit = fields.Many2one('product.uom','Unit')
# 	duration = fields.Float('Duration(Days)')
# 	no_labours = fields.Integer()
# 	start_date = fields.Date('Start Date')
# 	finish_date = fields.Date('Finish Date')
# 	employee_id = fields.Many2one('hr.employee', 'Site Engineer')
# 	veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
# 	products_id = fields.Many2many('product.product', string='Products')
# 	estimate_cost = fields.Float('Estimate Cost')
# 	sqft = fields.Float('Square Feet')
# 	pre_qty = fields.Float('Previous Qty')
# 	remarks = fields.Text()
# 	upto_date_qty = fields.Float(store=True, string='Balance Qty')
# 	quantity = fields.Float(string='Work Order Qty')
# 	subcontractor = fields.Many2one('res.partner', domain=[('contractor', '=', True)])


class DprStatus(models.Model):
    _name = 'dpr.status'
    _rec_name = 'date'

    @api.onchange('date')
    def onchange_date(self):
        if self.date:
            list = []
            date = fields.Datetime.from_string(self.date)
            record = self.search([('date', '=',str(date + relativedelta(days=-1)).split(' ')[0])])
            for i in record.dpr_status_line:
                list.append((0,0,{
                    'site_id': i.site_id.id,
                    'supervisor_id': i.supervisor_id.id,
                    'planned_work': i.next_day_plan,
                }))
            self.dpr_status_line = list

    date = fields.Date('Date')
    dpr_status_line = fields.One2many('dpr.status.line','line_id')

class DprStatusLine(models.Model):
    _name = 'dpr.status.line'

    line_id = fields.Many2one('dpr.status')
    site_id = fields.Many2one('stock.location','Site')
    supervisor_id = fields.Many2one('hr.employee','Supervisor')
    planned_work = fields.Char('Planned Work')
    todays_work = fields.Char('Todays Work Done')
    next_day_plan = fields.Char('Next Days Plan')
    target_status = fields.Char('Target Status')
    remarks = fields.Text('Remarks')

class DprStatusSupervisor(models.Model):
    _name = 'dpr.supervisor.line'

    site_id = fields.Many2one('stock.location','Site')
    supervisor_id = fields.Many2one('hr.employee','Supervisor')
    planned_work = fields.Char('Planned Work')
    todays_work = fields.Char('Todays Work Done')
    next_day_plan = fields.Char('Next Days Plan')
    target_status = fields.Char('Target Status')
    remarks = fields.Text('Remarks')
    date = fields.Date('Date')


class GradingAbstract(models.Model):
    _name = 'grading.abstract'


    date = fields.Date('Date')
    employee_id = fields.Many2one('hr.employee','Project Manager')
    grading_line = fields.One2many('grading.abstract.line','line_id')


    # @api.onchange('employee_id','date')
    # def onchange_grading(self):
    # 	result = []
    # 	grading = self.env['grading.measure'].search([('grading_type','=','photo')])
    # 	for ids in grading:
    # 		grading_point = 0
    # 		gallery = self.env['image.gallery'].search([('employee_id','=',self.employee_id.id),('measure_id','=',ids.id),('state','=','confirm')])
    # 		for gal in gallery:
    # 			start_dt = datetime.strptime(gal.confirmed_date, "%Y-%m-%d %H:%M:%S")+ timedelta(hours=5,minutes=30)
    # 			print 'start_dt----------------------------', start_dt
    # 			hr = datetime.strftime(start_dt, "%H")
    # 			mint = datetime.strftime(start_dt, "%M")
    # 			hr = int(hr)
    # 			mint = int(mint)
    # 			if int(ids.fixed_time) != 0:
    # 				fixed_mint = (ids.fixed_time % int(ids.fixed_time)) * 60
    # 			# fixed_mint = ids.fixed_time * 60
    # 			fixed_hr = int(ids.fixed_time)


    # 			if (hr == int(fixed_hr) and mint <= int(fixed_mint)) or hr < int(fixed_hr):
    # 				print 'gal---------------------', fixed_mint,fixed_hr,hr,mint
    # 				if len(gal.image_ids) >= ids.no_photos:
    # 					grading_point = ids.maximum_mark
    # 				else:
    # 					pass
    # 					grading_point = self.env['grading.measure.line'].search([('line_id','=', ids.id)], order="time_lag asc", limit=1).mark
    # 			else:
    # 				hr_diff = int(hr) - int(fixed_hr)
    # 				min_diff = int(mint) - int(fixed_mint)
    # 				grading_lines = self.env['grading.measure.line'].search([('line_id','=', ids.id)], order="time_lag asc")
    # 				variable = False
    # 				for line in grading_lines:
    # 					time_lag = 0
    # 					if line.time_lag != 0:
    # 						# gal_mint = line.time_lag * 60
    # 						if int(time_lag) != 0:
    # 							gal_mint = (time_lag % int(time_lag)) * 60
    # 						gal_hr = int(line.time_lag)
    # 						print 'line---------------------------------------', hr_diff,min_diff,gal_hr,gal_mint
    # 						if variable == False:
    # 							print 'zxy-------------'
    # 							if (int(gal_hr) == int(hr_diff) and int(gal_mint) >= int(min_diff)) or int(gal_hr) < int(hr_diff):
    # 								if len(gal.image_ids) == line.line_id.no_photos:
    # 									grading_point = line.mark
    # 									variable = True





    # 		result.append((0, 0, {'name' : ids.id, 'grading_point':grading_point}))
    # 	print 'result-----------------------------', result
    # 	self.grading_line = result


class GradingAbstractLine(models.Model):
    _name = 'grading.abstract.line'

    def get_total(self):
        for s in self:
            s.total_score = s.morning_meeting+s.work_start_photo+s.attendance_updation+s.wip_photos+s.after_lunch_photos+s.dpr_next_day+s.site_measurement+s.target_achievement+s.daily_statement

    line_id = fields.Many2one('grading.abstract')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    designation = fields.Many2many('hr.employee.category',string='Designation')
    site_id = fields.Many2one('stock.location', 'Site')
    morning_meeting = fields.Float('Morning Meeting')
    work_start_photo = fields.Float('Work Start Photo')
    attendance_updation = fields.Float('Attendance Update')
    wip_photos = fields.Float('WIP Photos')
    after_lunch_photos = fields.Float('After Lunch Photos')
    dpr_next_day = fields.Float('DPR & Next Day')
    site_measurement = fields.Float('Site Measurement')
    target_achievement = fields.Float('Target Achievement')
    daily_statement = fields.Float('Daily Statement')
    total_score = fields.Float('Total', compute="get_total")
    remarks = fields.Char('Remarks')

class GradingWeeklyAbstract(models.Model):
    _name = 'grading.weekly.abstract'


    date = fields.Date('Date')
    employee_id = fields.Many2one('hr.employee','Project Manager')
    grading_weekly_line = fields.One2many('grading.weekly.abstract.line','line_id')



    # @api.onchange('employee_id','date')
    # def onchange_grading(self):
    # 	result = []
    # 	grading = self.env['grading.measure'].search([('grading_type','=','photo')])
    # 	for ids in grading:
    # 		grading_point = 0
    # 		gallery = self.env['image.gallery'].search([('employee_id','=',self.employee_id.id),('measure_id','=',ids.id),('state','=','confirm')])
    # 		for gal in gallery:
    # 			start_dt = datetime.strptime(gal.confirmed_date, "%Y-%m-%d %H:%M:%S")+ timedelta(hours=5,minutes=30)
    # 			print 'start_dt----------------------------', start_dt
    # 			hr = datetime.strftime(start_dt, "%H")
    # 			mint = datetime.strftime(start_dt, "%M")
    # 			hr = int(hr)
    # 			mint = int(mint)
    # 			if int(ids.fixed_time) != 0:
    # 				fixed_mint = (ids.fixed_time % int(ids.fixed_time)) * 60
    # 			# fixed_mint = ids.fixed_time * 60
    # 			fixed_hr = int(ids.fixed_time)
    #
    #
    # 			if (hr == int(fixed_hr) and mint <= int(fixed_mint)) or hr < int(fixed_hr):
    # 				print 'gal---------------------', fixed_mint,fixed_hr,hr,mint
    # 				if len(gal.image_ids) >= ids.no_photos:
    # 					grading_point = ids.maximum_mark
    # 				else:
    # 					pass
    # 					grading_point = self.env['grading.measure.line'].search([('line_id','=', ids.id)], order="time_lag asc", limit=1).mark
    # 			else:
    # 				hr_diff = int(hr) - int(fixed_hr)
    # 				min_diff = int(mint) - int(fixed_mint)
    # 				grading_lines = self.env['grading.measure.line'].search([('line_id','=', ids.id)], order="time_lag asc")
    # 				variable = False
    # 				for line in grading_lines:
    # 					time_lag = 0
    # 					if line.time_lag != 0:
    # 						# gal_mint = line.time_lag * 60
    # 						if int(time_lag) != 0:
    # 							gal_mint = (time_lag % int(time_lag)) * 60
    # 						gal_hr = int(line.time_lag)
    # 						print 'line---------------------------------------', hr_diff,min_diff,gal_hr,gal_mint
    # 						if variable == False:
    # 							print 'zxy-------------'
    # 							if (int(gal_hr) == int(hr_diff) and int(gal_mint) >= int(min_diff)) or int(gal_hr) < int(hr_diff):
    # 								if len(gal.image_ids) == line.line_id.no_photos:
    # 									grading_point = line.mark
    # 									variable = True
    #
    #
    #
    #
    #
    # 		result.append((0, 0, {'name' : ids.id, 'grading_point':grading_point}))
    # 	print 'result-----------------------------', result
    # 	self.grading_line = result


class GradingAbstractLine(models.Model):
    _name = 'grading.weekly.abstract.line'

    def get_total(self):
        for s in self:
            s.total = s.first_week+s.second_week+s.third_week+s.fourth_week+s.fourth_week+s.sunday

    line_id = fields.Many2one('grading.abstract')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    designation = fields.Many2many('hr.employee.category',string='Designation')
    site_id = fields.Many2one('stock.location', 'Site')
    activity = fields.Char('Activity')
    first_week = fields.Float('First Week')
    second_week = fields.Float('Second Week')
    third_week = fields.Float('Third Week')
    fourth_week = fields.Float('Fourth Week')
    sunday = fields.Float('Sunday')
    total = fields.Float('Total', compute="get_total")


# class GradingMeasure(models.Model):
# 	_name = 'grading.measure'
#
# 	name = fields.Char('Name')
# 	fixed_time = fields.Float('Submission Time')
# 	grading_type = fields.Selection([('photo','Photo')
# 									], string="Type")
# 	line_ids = fields.One2many('grading.measure.line', 'line_id')
# 	maximum_mark = fields.Float('Maximum Mark')
# 	no_photos = fields.Integer('No. of Photos')
#
#
# 	@api.model
# 	def create(self, vals):
# 		res = super(GradingMeasure, self).create(vals)
# 		total = 0
# 		for line in res.line_ids:
# 			total += line.mark
# 			if line.mark > res.maximum_mark:
# 				raise osv.except_osv(('Warning!'), ('Marks cannot be greater than the maximum mark'))
# 		return res
#
#
# 	@api.multi
# 	def write(self,vals):
# 		total = 0
# 		maximum_mark = 0
# 		if vals.get('line_ids'):
# 			for lines in vals.get('line_ids'):
# 				print
# 				if lines[2] == False:
# 					total += self.line_ids.browse(lines[1]).mark
# 				elif 'mark' in lines[2]:
# 					total += lines[2]['mark']
# 		else:
# 			for lines in self.line_ids:
# 				total += lines.mark
# 				if float(lines.mark) > float(self.maximum_mark):
# 						raise osv.except_osv(('Warning!'), ('Marks cannot be greater than the maximum mark'))
# 		if vals.get('maximum_mark'):
# 			maximum_mark = vals.get('maximum_mark')
# 		else:
# 			maximum_mark = self.maximum_mark
# 		return super(GradingMeasure, self).write(vals)
#
# class GradingMeasureLine(models.Model):
# 	_name = 'grading.measure.line'
#
#
# 	line_id = fields.Many2one('grading.measure')
# 	no_photos = fields.Integer('No. of Photos')
# 	time_lag_unit = fields.Selection([('minutes', 'Minutes'),('hours', 'Hours')], 'Time Lag Unit')
# 	time_lag = fields.Float('Allowed Time Lag')
# 	mark = fields.Float('Mark')





class ImageGallery(models.Model):
    _name = 'image.gallery'

    name = fields.Char('Name')
    date = fields.Date('Date')
    confirmed_date = fields.Datetime('Confirmed Date')
    employee_id = fields.Many2one('hr.employee', string='Employee')
    measure_id = fields.Selection([('m_m_p', 'Morning Meeting Photo'),('wsp', 'Work Start Photo'),('wip', 'Work In Progress Photo'),('aftl', 'Work After Lunch Photo')],'Types')
    image_ids = fields.Many2many('ir.attachment','gallery_img_rel1', 'gallery_id','attachment_id', 'Images')
    state = fields.Selection([('draft','Draft'),
                            ('confirm','Confirmed')
                            ], default='draft')

    @api.multi
    def add_image(self):
        view_ref = self.env['ir.model.data'].get_object_reference('hiworth_construction', 'view_ir_attachment_form_view_image_new')
        view_id = view_ref[1] if view_ref else False
        res = {
           'type': 'ir.actions.act_window',
           'name': _('Add Image'),
           'res_model': 'ir.attachment',
           'view_type': 'form',
           'view_mode': 'form',
           'view_id': view_id,
           'target': 'new',
           'context': {'default_gallery_id':self.id}
       }

        return res

    @api.multi
    def button_confirm(self):
        self.state = 'confirm'
        self.confirmed_date = datetime.now()



# class ImageGalleryLine(models.Model):
# 	_name = 'image.gallery.line'

# 	gallery_id = fields.Many2one('image.gallery', 'Gallery')


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.onchange('datas','datas_fname')
    def onchange_datas(self):
        if self.datas or self.datas_fname:
            self.name = self.datas_fname


    @api.multi
    def action_create(self):
        if self.datas:
            record = []
            att_id = self.env['ir.attachment'].create({'datas':self.datas,'name':self.name})
            record.append(att_id.id)
            for att in self.gallery_id.image_ids:
                record.append(att.id)
            self.gallery_id.write({'image_ids' : [(6, 0, record)]})

    gallery_id = fields.Many2one('image.gallery')

