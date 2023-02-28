from openerp import models, fields, api, _
from openerp.osv import osv, expression
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# class MasterPlan(models.Model):
# 	_name = 'master.plan'
# 	_rec_name = 'site_id'
#
# 	site_id = fields.Many2one('hiworth.tender',string="Planning/Programme", domain=[('state','!=','rejected'),('state','!=','cancel')])
# 	package_no = fields.Char(related='site_id.package_no', string='Package No:')
# 	length_km = fields.Float('Length In KM:')
# 	completion_date = fields.Date('Completion Date')
# 	target_date = fields.Date('Target Date')
# 	master_plan_line = fields.One2many('master.plan.line','line_id')
# 	agreement_date = fields.Date('Agreement Date')
# 	work_start_date = fields.Date('Work Start Date')


# class MasterPlanLine(models.Model):
# 	_name = 'master.plan.line'
#
# 	line_id = fields.Many2one('master.plan')
# 	work_id = fields.Many2one('project.work','Description Of Work')
# 	chainage_from = fields.Float('Chainage From')
# 	chainage_to = fields.Float('Chainage To')
# 	side = fields.Selection([('lhs','LHS'),
# 							('rhs','RHS'),
# 							('bhs','BHS')
# 							],'Side')
# 	length = fields.Float('Length(M)')
# 	qty_estimate = fields.Float('Qty As Per Estimate')
# 	unit = fields.Many2one('product.uom','Unit')
# 	duration = fields.Float('Duration(Days)')
# 	start_date = fields.Date('Start Date')
# 	finish_date = fields.Date('Finish Date')
# 	employee_id = fields.Many2one('hr.employee','Employee')
# 	veh_categ_id = fields.Many2many('vehicle.category.type',string='Machinery')
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


class PlanningChart(models.Model):
	_name = 'survey.planning.chart'
	_rec_name = 'date'

	supervisor_id = fields.Many2one('hr.employee','Name Of Supervisor/Captain')
	site_id = fields.Many2one('stock.location',string="Planning/Programme", domain=[('state','!=','rejected')])
	date = fields.Date('Date')
	planning_chart_line = fields.One2many('survey.planning.chart.line','line_id')

class PlanningChartLine(models.Model):
	_name = 'survey.planning.chart.line'

	line_id = fields.Many2one('planning.chart')
	date = fields.Date('Date')
	work_id = fields.Char('Description')
	labour = fields.Float('Labour')
	veh_categ_id = fields.Many2many('fleet.vehicle',string='Machinery')
	# veh_categ_id = fields.Many2many('vehicle.category.type',string='Machinery')
	chainage = fields.Char('Working Location/Chainage')
	qty = fields.Float('Qty')
	target_qty = fields.Float('Target Qty')
	material = fields.Many2one('product.product', 'Material')
	uom_id = fields.Many2one('product.uom', string="Units")
	material_qty = fields.Float('Requirement Qty')
	remarks = fields.Char('Remarks')

class DprStatus(models.Model):
	_name = 'survey.dpr.status'
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
	dpr_status_line = fields.One2many('survey.dpr.status.line','line_id')

class DprStatusLine(models.Model):
	_name = 'survey.dpr.status.line'

	line_id = fields.Many2one('survey.dpr.status')
	site_id = fields.Many2one('stock.location','Site')
	supervisor_id = fields.Many2one('hr.employee','Supervisor')
	planned_work = fields.Char('Planned Work')
	todays_work = fields.Char('Todays Work Done')
	next_day_plan = fields.Char('Next Days Plan')
	target_status = fields.Char('Target Status')
#
#
# class GradingAbstract(models.Model):
# 	_name = 'grading.abstract'
#
#
# 	date = fields.Date('Date')
# 	employee_id = fields.Many2one('hr.employee','Project Manager')
# 	grading_line = fields.One2many('grading.abstract.line','line_id')
#
#
#
# 	@api.onchange('employee_id','date')
# 	def onchange_grading(self):
# 		result = []
# 		grading = self.env['grading.measure'].search([('grading_type','=','photo')])
# 		for ids in grading:
# 			grading_point = 0
# 			gallery = self.env['image.gallery'].search([('employee_id','=',self.employee_id.id),('measure_id','=',ids.id),('state','=','confirm')])
# 			for gal in gallery:
# 				start_dt = datetime.strptime(gal.confirmed_date, "%Y-%m-%d %H:%M:%S")+ timedelta(hours=5,minutes=30)
# 				print 'start_dt----------------------------', start_dt
# 				hr = datetime.strftime(start_dt, "%H")
# 				mint = datetime.strftime(start_dt, "%M")
# 				hr = int(hr)
# 				mint = int(mint)
# 				if int(ids.fixed_time) != 0:
# 					fixed_mint = (ids.fixed_time % int(ids.fixed_time)) * 60
# 				# fixed_mint = ids.fixed_time * 60
# 				fixed_hr = int(ids.fixed_time)
#
#
# 				if (hr == int(fixed_hr) and mint <= int(fixed_mint)) or hr < int(fixed_hr):
# 					print 'gal---------------------', fixed_mint,fixed_hr,hr,mint
# 					if len(gal.image_ids) >= ids.no_photos:
# 						grading_point = ids.maximum_mark
# 					else:
# 						pass
# 						grading_point = self.env['grading.measure.line'].search([('line_id','=', ids.id)], order="time_lag asc", limit=1).mark
# 				else:
# 					hr_diff = int(hr) - int(fixed_hr)
# 					min_diff = int(mint) - int(fixed_mint)
# 					grading_lines = self.env['grading.measure.line'].search([('line_id','=', ids.id)], order="time_lag asc")
# 					variable = False
# 					for line in grading_lines:
# 						time_lag = 0
# 						if line.time_lag != 0:
# 							# gal_mint = line.time_lag * 60
# 							if int(time_lag) != 0:
# 								gal_mint = (time_lag % int(time_lag)) * 60
# 							gal_hr = int(line.time_lag)
# 							print 'line---------------------------------------', hr_diff,min_diff,gal_hr,gal_mint
# 							if variable == False:
# 								print 'zxy-------------'
# 								if (int(gal_hr) == int(hr_diff) and int(gal_mint) >= int(min_diff)) or int(gal_hr) < int(hr_diff):
# 									if len(gal.image_ids) == line.line_id.no_photos:
# 										grading_point = line.mark
# 										variable = True
#
#
#
#
#
# 			result.append((0, 0, {'name' : ids.id, 'grading_point':grading_point}))
# 		print 'result-----------------------------', result
# 		self.grading_line = result
#
#
# class GradingAbstractLine(models.Model):
# 	_name = 'grading.abstract.line'
#
# 	def get_total(self):
# 		for s in self:
# 			s.total_score = s.morning_meeting+s.work_start_photo+s.attendance_updation+s.wip_photos+s.after_lunch_photos+s.dpr_next_day+s.site_measurement+s.target_achievement+s.daily_statement
#
# 	line_id = fields.Many2one('grading.abstract')
# 	employee_id = fields.Many2one('hr.employee', 'Employee')
# 	designation = fields.Many2many('hr.employee.category',string='Designation')
# 	site_id = fields.Many2one('stock.location', 'Site')
# 	morning_meeting = fields.Float('Morning Meeting')
# 	work_start_photo = fields.Float('Work Start Photo')
# 	attendance_updation = fields.Float('Attendance Update')
# 	wip_photos = fields.Float('WIP Photos')
# 	after_lunch_photos = fields.Float('After Lunch Photos')
# 	dpr_next_day = fields.Float('DPR & Next Day')
# 	site_measurement = fields.Float('Site Measurement')
# 	target_achievement = fields.Float('Target Achievement')
# 	daily_statement = fields.Float('Daily Statement')
# 	total_score = fields.Float('Total', compute="get_total")
# 	remarks = fields.Char('Remarks')
#
#
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
#
#
#
#
#
# class ImageGallery(models.Model):
# 	_name = 'image.gallery'
#
# 	name = fields.Char('Name')
# 	date = fields.Date('Date')
# 	confirmed_date = fields.Datetime('Confirmed Date')
# 	employee_id = fields.Many2one('hr.employee', string='Employee')
# 	measure_id = fields.Many2one('grading.measure', domain=[('grading_type','=','photo')], string='Process')
# 	# old_image_field = fields.Binary(related="image_main", store=False)
# 	image_ids = fields.Many2many('ir.attachment','gallery_img_rel1', 'gallery_id','attachment_id', 'Images')
# 	state = fields.Selection([('draft','Draft'),
# 							('confirm','Confirmed')
# 							], default='draft')
#
# 	@api.multi
# 	def add_image(self):
# 		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_construction', 'view_ir_attachment_form_view_image_new')
# 		view_id = view_ref[1] if view_ref else False
# 		res = {
# 		   'type': 'ir.actions.act_window',
# 		   'name': _('Add Image'),
# 		   'res_model': 'ir.attachment',
# 		   'view_type': 'form',
# 		   'view_mode': 'form',
# 		   'view_id': view_id,
# 		   'target': 'new',
# 		   'context': {'default_gallery_id':self.id}
# 	   }
#
# 		return res
#
# 	@api.multi
# 	def button_confirm(self):
# 		self.state = 'confirm'
# 		self.confirmed_date = datetime.now()
#
#
#
# # class ImageGalleryLine(models.Model):
# # 	_name = 'image.gallery.line'
#
# # 	gallery_id = fields.Many2one('image.gallery', 'Gallery')
#
#
# class IrAttachment(models.Model):
# 	_inherit = 'ir.attachment'
#
# 	@api.onchange('datas','datas_fname')
# 	def onchange_datas(self):
# 		if self.datas or self.datas_fname:
# 			self.name = self.datas_fname
#
#
# 	@api.multi
# 	def action_create(self):
# 		if self.datas:
# 			record = []
# 			att_id = self.env['ir.attachment'].create({'datas':self.datas,'name':self.name})
# 			record.append(att_id.id)
# 			for att in self.gallery_id.image_ids:
# 				record.append(att.id)
# 			self.gallery_id.write({'image_ids' : [(6, 0, record)]})
#
# 	gallery_id = fields.Many2one('image.gallery')
#
