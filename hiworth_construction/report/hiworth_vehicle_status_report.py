from openerp import fields, models, api
import calendar
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import timedelta,datetime
from openerp.osv import osv

class HiworthVehicleStatusReport(models.TransientModel):
	_name='hiworth.vehicle.status.report'

	from_date=fields.Date(default=lambda self: self.default_time_range('from'))
	to_date=fields.Date(default=lambda self: self.default_time_range('to'))
	rent = fields.Float('Rent')
	state = fields.Float('state')
	dates_btwn = fields.Date('Date:')
	is_machinery = fields.Boolean('Machinery', default=False)
	vehicle_id = fields.Many2one('fleet.vehicle',"Vehicle/Machinery")
	vehicle_categ_id = fields.Many2one('vehicle.category.type', 'Vehicle/Machinery Category')


	# Calculate default time ranges
	@api.model
	def default_time_range(self, type):
		year = datetime.today().year
		month = datetime.today().month
		last_day = calendar.monthrange(datetime.today().year,datetime.today().month)[1]
		first_day = 1
		if type=='from':
			return datetime(year, month, first_day)
		elif type=='to':
			return datetime(year, month, last_day)
	
	@api.multi
	def print_vehicle_status_report(self):
		self.ensure_one()
		# status_report = self.env['driver.daily.statement']
		# vehicle_report = status_report.search([('date','>=',self.from_date),('date','<=',self.to_date)])
		# print 'test=====================', vehicle_report
		# if not vehicle_report:
		# 	raise osv.except_osv(('Error'), ('No vehicle status avaliable in the given dates.'))

		datas = {
			'ids': self._ids,
			'model': self._name,
			'form': self.read(),
			'context':self._context,
		}
		return{
			'type' : 'ir.actions.report.xml',
			'report_name' : 'hiworth_construction.report_vehicle_status_template',
			'datas': datas,
			'report_type': 'qweb-pdf',
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
		}

		
	@api.multi
	def view_vehicle_status_report(self):
		self.ensure_one()
		# status_report = self.env['driver.daily.statement']
		# vehicle_report = status_report.search([('date','>=',self.from_date),('date','<=',self.to_date)])
		# print 'test=====================', vehicle_report
		# if not vehicle_report:
		# 	raise osv.except_osv(('Error'), ('No vehicle status avaliable in the given dates.'))

		datas = {
			'ids': self._ids,
			'model': self._name,
			'form': self.read(),
			'context':self._context,
		}
		return{
			'type' : 'ir.actions.report.xml',
			'report_name' : 'hiworth_construction.report_vehicle_status_template',
			'datas': datas,
			'report_type': 'qweb-html',
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
		}


	@api.multi
	def get_dates(self):
		self.ensure_one()
		date_range_list = []
		d_frm_obj = datetime.strptime(self.from_date, "%Y-%m-%d")
		d_to_obj = datetime.strptime(self.to_date, "%Y-%m-%d")
		temp_date = d_frm_obj
		while(temp_date <= d_to_obj):
			date_range_list.append(temp_date.strftime
								   ("%d-%m-%Y"))
			temp_date = temp_date + timedelta(days=1)

		return date_range_list

	@api.multi
	def get_vehicles(self):
		self.ensure_one()
		dom = []
		dom.append(('vehicle_categ_id', '=', self.vehicle_categ_id.id))
		dom.append(('rent_vehicle', '!=', True))
		if self.vehicle_id:
			dom.append(('id','=',self.vehicle_id.id))
		vehicle_list = [line.id for line in self.env['fleet.vehicle'].search(dom)]
		return vehicle_list

	@api.multi
	def get_driver_statement(self,date,vehicle_list):
		# print 'asdsad===============',date
		details_list = []
		
		details_list = []
		for vehicle in vehicle_list:
			dict = {}
			dict['vehicle'] = self.env['fleet.vehicle'].browse(vehicle)

			date_p = datetime.strptime(date,"%d-%m-%Y").strftime("%Y-%m-%d")

			statements = self.env['driver.daily.statement'].search([('date','=',date_p),('vehicle_no','=',vehicle)])
			operator_statements = self.env['operator.daily.statement'].search([('date','=',date_p),('machinery_id','=',vehicle)])
			if statements:
				driver = ''
				rent = 0
				expense = 0
				km_total = 0
				for statement in statements:
					for lines in statements.diesel_pump_line:
						expense += lines.total_litre_amount
					driver += ' ' + statement.driver_name.name 
					expense += statement.expense + statement.cleaner_bata
					for line in statement.driver_stmt_line:
						rent += line.rent
						km_total += line.total_km
						expense += line.driver_betha

				dict['driver'] = driver
				dict['rent'] = rent
				dict['expense'] = expense
				dict['km_total'] = km_total

			elif operator_statements:
				driver = ''
				rent = 0
				expense = 0
				km_total = 0
				fuel_expense = self.env['machinery.fuel.allocation'].search([('date','=',date_p),('machinery_id','=',vehicle)])
				for fuel in fuel_expense:
					expense += fuel.total_amount
				for statement in operator_statements:
					driver += ' ' + statement.employee_id.name 
					expense += statement.expense +statement.operator_amt
					rent += statement.machinery_rent
					km_total += statement.working_hours
						# expense += line.driver_betha

				dict['driver'] = driver
				dict['rent'] = rent
				dict['expense'] = expense
				dict['km_total'] = km_total

			else:
				dict['km_total'] = 0
				dict['driver'] = False
				dict['expense'] = 0
			if dict != {}:
				details_list.append(dict)

		return details_list
