from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
from openerp.osv import osv
import datetime
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning as UserError

class ItemProduct(models.Model):
	_name = 'item.product'

	name = fields.Char('Name')


class AccountJournal(models.Model):
	_inherit = 'account.move'

	driver_stmt_id = fields.Many2one('driver.daily.statement')
	partner_stmt_id = fields.Many2one('partner.daily.statement')
	rent_vehicle_stmt = fields.Many2one('rent.vehicle.statement')
	fleet_emi = fields.Many2one('fleet.emi')


class CashTransferLimit(models.Model):
	_name = 'cash.transfer.limit'

	name = fields.Many2one('hr.employee','Employee')
	cash_limit = fields.Float('Cash Transfer Limit Per Day',required=True)

class CashConfirmTransfer(models.Model):
	_name = 'cash.confirm.transfer'
	_order = 'id desc'

	@api.multi
	def get_visibility(self):
		for rec in self:
			if rec.user_id:

				if rec.user_id.id == rec.env.user.employee_id.id or rec.env.user.id == 1:
					rec.visibility2 = True
				else:
					rec.visibility2 = False

	@api.multi
	@api.depends('user_id')
	def compute_to_user(self):
		for rec in self:
			rec.transfer_to_user = self.env['res.users'].search([('employee_id','=',rec.user_id.id)], limit=1).id

	@api.multi
	@api.depends('name')
	def compute_from_user(self):
		for rec in self:
			rec.transfer_from_user = self.env['res.users'].search([('employee_id','=',rec.name.id)], limit=1).id
	# rec = fields.Many2one('driver.daily.statement')
	date = fields.Date(default=fields.Date.today, string="Date")
	name = fields.Many2one('hr.employee')
	state = fields.Selection([('pending','Pending'),('accepted','Accepted')],default='pending')
	amount = fields.Float('Amount')
	user_id = fields.Many2one('hr.employee')
	admin = fields.Many2one('res.users')
	driver_stmt_id = fields.Many2one('driver.daily.statement')
	visibility2 = fields.Boolean(default=False,compute='get_visibility')
	transfer_to_user = fields.Many2one('res.users', compute='compute_to_user', store=True, string='Receiver')
	transfer_from_user = fields.Many2one('res.users', compute='compute_from_user', store=True, string='Sender')
	move_id = fields.Many2one('account.move',"Move")


	@api.multi
	def accept_cash(self):
		# if len(self.env['partner.daily.statement'].sudo().search([('date','=',self.date),('employee_id','=',self.user_id.id)])) == 0:
		# 	raise osv.except_osv(_('Error!'),_("Please open a Daily Statement for accepting this transfer."))
		# if len(self.env['partner.daily.statement'].sudo().search([('date','=',self.date)])) == 0:
		# 	raise osv.except_osv(_('Error!'),_("Please open a Daily Statement for accepting this transfer."))
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		journal = self.env['account.journal'].sudo().search([('name','=','Miscellaneous Journal')])
		if not journal:
			pass
			# raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
		if len(journal) > 1:
			raise except_orm(_('Warning'),_('Multiple Journal with same name(Miscellaneous Journal)'))
		
		for rec in self:
			driver_stmt_id = self.env['driver.daily.statement'].sudo().search([('id','=',rec.driver_stmt_id.id)])
			values = {
					'journal_id': journal.id,
					'date': self.date,
					}
			move_id = move.create(values)
			values = {
					'account_id': rec.name.petty_cash_account.id,
					# 'vehicle_id':driver_stmt_id.vehicle_no.id  if driver_stmt_id and rec.name.user_category == 'driver' or rec.name.user_category == 'eicher_driver' else False,
					# 'driver_stmt_id':rec.driver_stmt_id.id if self.driver_stmt_id else False,
					'name': 'narration',
					'debit': 0,
					'credit': rec.amount,
					'move_id': move_id.id,
					}
			line_id = move_line.create(values)
			values2 = {
					'account_id': rec.user_id.petty_cash_account.id,
					'name': 'narration',
					'debit': rec.amount,
					'credit': 0,
					'move_id': move_id.id,
					}
			line_id = move_line.create(values2)
			rec.move_id = move_id.id
			rec.state = 'accepted'

class FuelTransfer(models.TransientModel):
	_name = 'fuel.transfer'

	rec = fields.Many2one('driver.daily.statement')
	date = fields.Date(default=fields.Date.today, string="Date")
	name = fields.Many2one('hr.employee')
	amount = fields.Float('Amount')
	user_id = fields.Many2one('hr.employee')


	@api.multi
	def transfer_fuel(self):
		self.env['fuel.confirm.transfer'].sudo().create({
			'date':self.date,
			'name':self.name.id,
			'amount':self.amount,
			'user_id':self.user_id.id,
			'state':'pending',
			'driver_stmt_id':self.rec.id,
			'admin':1})
		return True


class FuelConfirmTransfer(models.Model):
	_name = 'fuel.confirm.transfer'
	_order = 'id desc'

	@api.multi
	def get_visibility(self):
		for rec in self:
			if rec.user_id:
				if rec.user_id.id == rec.env.user.employee_id.id:
					rec.visibility2 = True
				else:
					rec.visibility2 = False

	@api.multi
	@api.depends('user_id')
	def compute_to_user(self):
		for rec in self:
			rec.transfer_to_user = self.env['res.users'].search([('employee_id','=',rec.user_id.id)], limit=1).id


	@api.multi
	@api.depends('name')
	def compute_from_user(self):
		for rec in self:
			rec.transfer_from_user = self.env['res.users'].search([('employee_id','=',rec.name.id)], limit=1).id
	
	date = fields.Date(default=fields.Date.today, string="Date")
	name = fields.Many2one('hr.employee')
	state = fields.Selection([('pending','Pending'),('accepted','Accepted')],default='pending')
	amount = fields.Float('Amount')
	user_id = fields.Many2one('hr.employee')
	admin = fields.Many2one('res.users')
	driver_stmt_id = fields.Many2one('driver.daily.statement')
	visibility2 = fields.Boolean(default=False,compute='get_visibility')
	transfer_to_user = fields.Many2one('res.users', compute='compute_to_user', store=True, string='Receiver')
	transfer_from_user = fields.Many2one('res.users', compute='compute_from_user', store=True, string='Sender')



class CashTransfer(models.TransientModel):
	_name = 'cash.transfer'

	rec = fields.Many2one('driver.daily.statement')
	date = fields.Date(default=fields.Date.today, string="Date")
	name = fields.Many2one('hr.employee')
	amount = fields.Float('Amount')
	user_id = fields.Many2one('hr.employee')

	@api.multi
	def transfer_amount(self):
		# records = self.env['cash.confirm.transfer'].search([('date','=',self.date),('name','=',self.name.id)])
		# amount = 0
		# limit_amount = 0
		# if records:
		# 	for line in records:
		# 		amount += line.amount
		# limit = self.env['cash.transfer.limit'].search([('name','=',self.name.id)])
		# if limit:
		# 	limit_amount = limit.cash_limit
		# else:
		# 	raise except_orm(_('Warning'),
		# 					 _('Please Set An Amount Transfer Limit'))
		# if limit_amount < amount or (amount + self.amount) > limit_amount:
		# 	raise except_orm(_('Warning'),
		# 					 _('Amount Exceeds Limit..Please Check'))
		# else:
		self.env['cash.confirm.transfer'].sudo().create({
													  'date':self.date,
													  'name':self.name.id,
													  'amount':self.amount,
													  'user_id':self.user_id.id,
													  'state':'pending',
													  'driver_stmt_id':self.rec.id,
													  'admin':1})
													  # 'transfer_from_user':self.env['res.users'].search[('employee_id','=',self.name.id)].id,
													  # 'transfer_to_user':self.env['res.users'].search[('employee_id','=',self.name.id)].id
		return True



class DieselPump(models.Model):
	_name = 'diesel.pump'

	name = fields.Char('Pump Name', required=True)

class DieselPumpLine(models.Model):
	_name = 'diesel.pump.line'

	@api.multi
	def button_demo12345(self):
		diesel_line = self.env['diesel.pump.line'].search([])
		for line in diesel_line:
			records = self.env['driver.daily.statement'].search([('id','=', line.line_id.id)])
			if records:
				line.line_id2 = line.line_id.id

	line_id = fields.Many2one('driver.statement.line')
	line_id2 = fields.Many2one('driver.daily.statement')
	vehicle_id = fields.Many2one('fleet.vehicle', related="line_id2.vehicle_no")
	date = fields.Date("Date")
	diesel_pump = fields.Many2one('res.partner','Diesel Pump')
	litre = fields.Float('Litre')
	per_litre = fields.Float('Per Litre')
	total_litre_amount = fields.Float('Total Litre Amount')
	odometer = fields.Float('Starting Odometer Reading')
	closing_odometer = fields.Float('Closing Odometer Reading')
	total_odometer = fields.Float('Total KM',compute="_compute_total_km",store=True,readonly=True)
	is_full_tank = fields.Boolean('Is Full Tank')
	pump_bill_no = fields.Char('Bill No.')
	fuel_item = fields.Many2one('product.product', 'Fuel Item')

	@api.model
	def default_get(self, vals):
		res = super(DieselPumpLine, self).default_get(vals)
		config = self.env['general.fuel.configuration'].search([], limit=1)

		res.update({
			'fuel_item': config.product_id.id,
		})
		return res

	@api.depends('odometer', 'closing_odometer')
	def _compute_total_km(self):
		for rec in self:
			rec.total_odometer = round(rec.closing_odometer - rec.odometer,2)

	# fuel_tax_ids = fields.Many2many('account.tax',string="Tax")
	# fuel_tax_amount = fields.Float('Tax Amount',compute="_get_subtotal_fuel_report")
	# fuel_sub_total = fields.Float('Sub Total',compute="_get_subtotal_fuel_report")
	# fuel_total = fields.Float('Total',compute="_get_subtotal_fuel_report")
	# fuel_round_off = fields.Float('Round Off')
	# fuel_invoice_value = fields.Float('Invoice Value',compute="_get_subtotal_fuel_report")

	# @api.multi
	# @api.depends('fuel_tax_ids','total_litre_amount','fuel_round_off')
	# def _get_subtotal_fuel_report(self):
	# 	for lines in self:
	# 		taxi = 0
	# 		taxe = 0
	# 		for tax in lines.fuel_tax_ids:
	# 			if tax.price_include == True:
	# 				taxi = tax.amount
	# 			if tax.price_include == False:
	# 				taxe += tax.amount
	# 		lines.fuel_tax_amount = (lines.total_litre_amount)/(1+taxi)*(taxi+taxe)
	# 		lines.fuel_sub_total = (lines.total_litre_amount)/(1+taxi)
	# 		lines.fuel_total = lines.fuel_tax_amount + lines.fuel_sub_total
	# 		lines.fuel_invoice_value = lines.fuel_total + lines.fuel_round_off

	@api.model
	def create(self,vals):
		result = super(DieselPumpLine, self).create(vals)
		fuel_lines = []
		if vals.get('line_id2'):
			rec = self.env['driver.daily.statement'].search([('id','=',vals['line_id2'])])
			self.env['fuel.report'].sudo().create({
									'date':result.date,
									'diesel_pump':result.diesel_pump.id,
									'vehicle_owner':rec.vehicle_no.vehicle_under.id,
									'vehicle_no':rec.vehicle_no.id,
									'item_char':'Diesel',
									'qty':result.litre,
									'rate':result.per_litre,
									'amount':result.total_litre_amount,
									'diesel_pump_id':result.id,

									})

			fuel_lines = [(0, 0, {
				'date': result.date,
				'pump_id': result.diesel_pump.id,
				'vehicle_id': rec.vehicle_no.id,
				'item_char': 'Diesel',
				'litre': result.litre,
				'per_litre': result.per_litre,
				'amount': result.total_litre_amount,
				'odometer': result.odometer,
				'full_tank': result.is_full_tank,
				'opening_reading': result.odometer,
				'closing_reading': result.closing_odometer,
				'total_reading': result.total_odometer,
			})]
			rec.vehicle_no.update({'fuel_lines':fuel_lines})



		return result



	@api.multi
	def write(self,vals):
		result = super(DieselPumpLine, self).write(vals)
		fuel_report = self.env['fuel.report'].search([('diesel_pump_id','=',self.id)])
		if fuel_report:
			if vals.get('date'):
				fuel_report.write({'date':vals['date']})
			if vals.get('diesel_pump'):
				fuel_report.write({'diesel_pump':vals['diesel_pump']})
			if vals.get('litre'):
				fuel_report.write({'qty':vals['litre']})
			if vals.get('per_litre'):
				fuel_report.write({'rate':vals['per_litre']})
			if vals.get('total_litre_amount'):
				fuel_report.write({'amount':vals['total_litre_amount']})

		return result

	# @api.onchange('litre','per_litre')
	# def onchange_odometer1(self):
	# 	if self.litre and self.per_litre:
	# 		self.total_litre_amount = round((float(self.litre) * float(self.per_litre)),2)
	# 	if self.litre == 0 or self.per_litre == 0:
	# 		self.total_litre_amount = 0


	# @api.onchange('total_litre_amount','per_litre')
	# def onchange_odometer2(self):
	# 	if self.total_litre_amount and self.per_litre:
	# 		self.litre = round((float(self.total_litre_amount) / float(self.per_litre)),2)

	# @api.onchange('litre','total_litre_amount')
	# def onchange_odometer3(self):
	# 	if self.litre and self.total_litre_amount:
	# 		self.per_litre = round((float(self.total_litre_amount) / float(self.litre)),2)


	@api.onchange('litre')
	def onchange_litre_rate(self):
		if self.litre == 0:
			self.total_litre_amount = 0
		else:
			if self.total_litre_amount != 0 and self.per_litre != 0 and self.litre != round((self.total_litre_amount / self.per_litre),2):
				self.litre = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Qty field, Rate or Total should be Zero"
						}
					}	
			if self.litre != 0 and self.per_litre != 0:
				if self.per_litre*self.litre != self.total_litre_amount:
					pass
				if self.total_litre_amount == 0.0:
					self.total_litre_amount = round((self.litre * self.per_litre),2)
			if self.total_litre_amount != 0 and self.litre != 0:
				if self.per_litre == 0.0:
					self.per_litre = round((self.total_litre_amount / self.litre),2)	


	@api.onchange('per_litre')
	def onchange_per_litre_total_litre_amount(self):
		if self.per_litre == 0:
			self.total_litre_amount = 0
		else:
			if self.total_litre_amount != 0 and self.litre != 0 and self.per_litre != round((self.total_litre_amount / self.litre),2):
				self.per_litre = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Rate field, Qty or Total should be Zero."
						}
					}
			if self.litre != 0 and self.per_litre != 0:
				if self.per_litre*self.litre != self.total_litre_amount:
					pass
				if self.total_litre_amount == 0.0:
					self.total_litre_amount = round((self.litre * self.per_litre),2)
			if self.total_litre_amount != 0 and self.per_litre != 0:
				if self.litre == 0.0:
					self.litre = round((self.total_litre_amount / self.per_litre),2)		
			


	@api.onchange('total_litre_amount')
	def onchange_qty_total_litre_amount(self):
		if self.total_litre_amount != 0:

			if self.per_litre*self.litre != self.total_litre_amount:
				if not self.per_litre or not self.litre != 0:
					self.total_litre_amount = 0.0
					return {
						'warning': {
							'title': 'Warning',
							'message': "For Entering value to Total field, Qty or Rate should be Zero."
							}
						}
				elif self.per_litre == 0 and self.litre != 0:
					self.per_litre = round((self.total_litre_amount / self.litre),2)
				elif self.litre == 0 and self.per_litre != 0:
					self.litre = round((self.total_litre_amount / self.per_litre),2)				
				else:
					pass





class DriverDailyStatement(models.Model):
	_name = 'driver.daily.statement'
	_order = 'date desc'







	@api.multi
	def test_button(self):
		record = self.env['driver.daily.statement'].search([])
		for rec in record:
			rec._get_user()

	@api.onchange('driver_stmt_line')
	def onchange_stmt_id_line(self):
		amount = 0
		total = 0 
		
		for rec in self:
			amount = rec.driver_name.per_day_eicher_rate
			for lines in rec.driver_stmt_line:
				total += ((lines.end_km - lines.start_km)*rec.vehicle_no.rate_per_km)*rec.vehicle_no.trip_commission/100
			rec.rate_per = amount + total

	@api.multi
	def get_date(self,date):
		date = datetime.datetime.strptime(date, "%Y-%m-%d")
		return str(date.day)+str('/')+str(date.month)+str('/')+str(date.year)

	

	@api.model
	def default_get(self, default_fields):
		vals = super(DriverDailyStatement, self).default_get(default_fields)
		driver_user = self.env['res.users'].search([('id','=',self.env.user.id)])
		if driver_user:
			if driver_user.employee_id:
				# balance = 0
				# for move_lines in driver_user.employee_id.petty_cash_account.move_lines:
				# 	if move_lines.date < rec.date:
				# 		balance += move_lines.debit
				# 		balance -= move_lines.credit
				vals.update({'driver_name' : driver_user.employee_id.id,
							 # 'pre_balance':balance,

							 'rate_per':driver_user.employee_id.per_day_eicher_rate if self.env.context.get('default_eicher') == 1 else 0})
		
		vehicle = self.env['fleet.vehicle'].search([('hr_driver_id','=', self.env.user.employee_id.id)])
		
		if len(vehicle) == 1:
			vals.update({'vehicle_no' : vehicle.id,
						 })
			# self.vehicle_no = vehicle.id
		return vals


	@api.one
	@api.depends('stmt_line')
	def get_expense_line(self):
		if self.stmt_line:
			expense = 0
			for line in self.stmt_line:
				expense += line.payment

			self.expense = expense

	@api.one
	def get_transferred_amount1(self):
		records = self.env['cash.confirm.transfer'].sudo().search([('state','=','pending'),('date','<=',self.date),('name','=',self.driver_name.id)])
		amount = 0
		if records:
			for line in records:
				amount += line.amount
		return amount


	@api.one
	def compute_received_amount1(self):
		rec = self.env['cash.confirm.transfer'].sudo().search([('state','=','pending'),('date','<=',self.date),('user_id','=',self.driver_name.id)])
		received = 0
		if rec:
			for line in rec:
				received += line.amount
		return received

	@api.one
	def get_transferred_amount(self):
		records = self.env['cash.confirm.transfer'].sudo().search([('date','=',self.date),('name','=',self.driver_name.id),('state','=','accepted')])
		amount = 0
		if records:
			for line in records:
				amount += line.amount
		self.transfer_amount = amount


	@api.one
	def compute_received_amount(self):
		rec = self.env['cash.confirm.transfer'].search([('date','=',self.date),('user_id','=',self.driver_name.id),('state','=','accepted')])
		received = 0
		if rec:
			for line in rec:
				received += line.amount
		self.received = received

	@api.multi
	@api.depends('pre_balance','received','expense','transfer_amount','withdrawal_amount')
	def compute_total_amount(self):
		for line in self:
			line.total = line.pre_balance + line.received
			line.actual_balance = line.total - line.expense - line.transfer_amount - line.withdrawal_amount
			line.balance = line.actual_balance - line.get_transferred_amount1()[0] + line.compute_received_amount1()[0]

	# @api.onchange('vehicle_no','theoretical_close_km')
	# def onchange_vehicle_no(self):
	# 	if self.vehicle_no:
	# 		# self.start_km = self.vehicle_no.last_odometer
	# 		driver_record = self.env['driver.daily.statement'].sudo().search([('vehicle_no','=',self.vehicle_no.id)])
	# 		if driver_record:
	# 			for lines in driver_record:
	# 				if lines.state == 'draft' or lines.state == 'confirmed':
	# 					self.vehicle_no = False
	# 					return {
	# 						'warning': {
	# 							'title': 'Warning',
	# 							'message': "There is one record for the same vehicle number which is not in approved state."
	# 						}
	# 					}


			# self.actual_close_km = self.theoretical_close_km

	@api.multi
	@api.depends('driver_stmt_line','start_km')
	def compute_theoretical_close_km(self):
		pass
		# for rec in self:
		# 	if not rec.driver_stmt_line:
		# 		rec.theoretical_close_km = rec.start_km
		# 	else:
		# 		a = rec.start_km
		# 		for lines in rec.driver_stmt_line:
		# 			if lines.end_km > a:
		# 				a = lines.end_km
		# 		rec.theoretical_close_km = a

	# @api.multi
	# @api.onchange('driver_stmt_line','start_km')
	# def onchange_actual_close_km1(self):
	# 	for rec in self:
	# 		if not rec.driver_stmt_line:
	# 			rec.actual_close_km = rec.start_km
	# 			print '==============================start km',rec.start_km
	# 		else:
	# 			a = rec.start_km
	# 			for lines in rec.driver_stmt_line:
	# 				# rec.start_km=lines.start_km
	# 				# a=rec.start_km
	# 				if lines.end_km > a:
	# 					a = lines.end_km
	# 			print '==============================end km',lines.end_km,lines.start_km

	# 			rec.actual_close_km = a


	@api.multi
	@api.depends('actual_close_km','theoretical_close_km')
	def compute_is_difference(self):
		pass
		# for rec in self:
		# 	if rec.actual_close_km != rec.theoretical_close_km:
		# 		rec.is_difference = True
		# 	else:
		# 		rec.is_difference = False

	@api.multi
	@api.depends('start_km','actual_close_km')
	def compute_closing_km(self):
		for rec in self:
			rec.running_km = round(rec.actual_close_km - rec.start_km,2)


	@api.multi
	@api.depends('driver_name','date')
	def compute_name(self):
		for rec in self:
			if rec.driver_name and rec.date:
				date = datetime.datetime.strptime(rec.date, "%Y-%m-%d")
				rec.name = rec.driver_name.name+' '+str(date.day)+ str('-')+str(date.month)+ str('-') + str(date.year)

	READONLY_STATES = {
		'confirmed': [('readonly', True)],
		'approved': [('readonly', True)],
		'cancelled': [('readonly', True)],
	}

	@api.constrains('actual_close_km','vehicle_no')
	def check_actual_close_km(self):
		for rec in self:
			running_km = rec.actual_close_km - rec.vehicle_no.last_odometer

			if running_km <0 or running_km >500:
				pass
				# raise except_orm(_('Warning'), _('Please Check the Closing KM'))



	name = fields.Char(compute='compute_name', string='Name')
	driver_name = fields.Many2one('hr.employee','Name',required=True)
	driver_name2 = fields.Many2one('hr.employee','Driver Name')
	in_charge = fields.Many2one('hr.employee','In Charge')
	vehicle_no = fields.Many2one('fleet.vehicle','Daily Statement Of Vehicle No:')
	rent_amount = fields.Float('Rent Amount',)
	project_id = fields.Many2one('project.project','Project Name')
	# is_a_mach = fields.Boolean(string="Is Rent Machinery",related='vehicle_no.is_a_mach')
	date = fields.Date('Date',default=fields.Date.today, states=READONLY_STATES)
	driver_stmt_line = fields.One2many('driver.daily.statement.line','line_id')
	cleaners_name = fields.Many2one('hr.employee','Cleaner Name')
	stmt_line = fields.One2many('driver.daily.expense','stmt_id', states=READONLY_STATES)
	diesel_pump2 = fields.Many2one('res.partner','Diesel Pump', states=READONLY_STATES)
	# supervisor = fields.Many2one('res.partner')
	litre = fields.Float('Litre', states=READONLY_STATES)
	total_litre_amount = fields.Float('Total Amount', states=READONLY_STATES, compute='onchange_odometer1')
	rent_percent = fields.Float('Rent Percent',required=True, states=READONLY_STATES)

	per_litre = fields.Float('Per Litre Amount', states=READONLY_STATES)
	pre_balance = fields.Float('Pre-Balance',readonly=True)
	received = fields.Float('Received Rs',compute="compute_received_amount")
	total = fields.Float('Total',compute="compute_total_amount")
	expense = fields.Float('Expense',compute="get_expense_line")
	transfer_amount = fields.Float('Transferred Amount',compute="get_transferred_amount")
	withdrawal_amount = fields.Float('Withdrawal Amount', states=READONLY_STATES)
	balance = fields.Float('Balance',compute="compute_total_amount")
	state = fields.Selection([('draft','draft'),('confirmed','Confirmed'),('cancelled','Cancelled'),('approved','Approved')],default='draft')
	driver_status1 = fields.Selection([('sent','Approved By Supervisor'),('reject','Rejected By Supervisor')],string="Material Status", compute="_get_driver_status1", store=True)
	
	start_km = fields.Float('Starting Km')
	theoretical_close_km = fields.Float(compute='compute_theoretical_close_km', store=True, string='Theoretical Closing Km')
	actual_close_km = fields.Float('Closing Km')
	odometer = fields.Float('Meter Reading', states=READONLY_STATES)
	remark = fields.Text('Remarks', states=READONLY_STATES)
	running_km = fields.Float('Running Km',compute="compute_closing_km")
	actual_balance = fields.Float('Actual Balance',compute="compute_total_amount")
	is_difference = fields.Boolean(compute='compute_is_difference', store=True, string='Is Difference')
	request_line = fields.One2many('request.line.driver','line_id')
	approved_by = fields.Many2one('hr.employee','Approved By')
	sign = fields.Binary('Sign')
	reception = fields.Boolean(default=False,compute="get_reception_trenafer")
	transfer = fields.Boolean(default=False,compute="get_reception_trenafer")
	diesel_pump_line = fields.One2many('diesel.pump.line','line_id2')
	eicher = fields.Boolean(default=False)
	taurus = fields.Boolean(default=False)
	pickup = fields.Boolean(default=False)
	shuttle_service = fields.One2many('shuttle.service','shuttle_id')
	rate_per = fields.Float('Rate')
	cleaner_bata = fields.Float('Cleaner Bata')
	is_shuttle = fields.Boolean('Allow Shuttle Service', default=False)
	reference = fields.Char('Reference No:')
	user_id = fields.Many2one('res.users','User', compute="_get_user", store=True)


	@api.multi
	@api.depends('driver_stmt_line')
	def _get_driver_status1(self):
		for record in self:
			# print 'chck77////////////1---------------------'
			reject = 0
			for line in record.driver_stmt_line:
				# print 'line.status------------------', line.status
				if line.status == 'rejected':
					reject = 1
			# print 'reject------------------------------', reject
			if reject == 1:
				record.driver_status1 = 'reject'
			else:
				record.driver_status1 = 'sent'

	@api.multi
	@api.depends('driver_name')
	def _get_user(self):
		for record in self:
			# print 'aaaaaaaaaa----------------------------------', self.env['res.users'].search([('employee_id','=', record.driver_name.id)], limit=1).id
			record.user_id = self.env['res.users'].search([('employee_id','=', record.driver_name.id)], limit=1).id

	@api.onchange('cleaners_name')
	def onchange_cleaners_domain(self):
		employees = self.env['hr.employee'].search([('user_category','=','helpers')])
		# print 'employees------------------------', employees
		ids = []
		for emp_id in employees:
			ids.append(emp_id.id)
		return {'domain': {'cleaners_name': [('id', 'in', ids)]}}


	# @api.onchange('cleaner_bata')
	# def cleaner_bata_onchange(self):
	# 	if self.cleaner_bata != False or self.cleaner_bata != 0:
	# 		count = len(self.driver_stmt_line)
	# 		if count < 2:
	# 			self.cleaner_bata = 0
	# 			return {
	# 					'warning': {
	# 						'title': 'Warning',
	# 						'message': "Minimum 2 Loads must be in statement..!!"
	# 					}
	# 				}



	@api.multi
	@api.depends('state')
	def get_reception_trenafer(self):
		flag = 0
		if self.env.user.id == 1:
			flag = 1
		rec = self.env['cash.confirm.transfer'].search([('date','=',self.date),('state','=','pending'),('user_id','=',self.env.user.employee_id.id if flag == 0 else 1)])
		if rec:
			self.reception = True
		else:
			self.reception = False

		rec_transfer = self.env['cash.confirm.transfer'].search([('date','=',self.date),('state','=','pending'),('name','=',self.env.user.employee_id.id if flag == 0 else 1)])
		if rec_transfer:
			self.transfer = True
		else:
			self.transfer = False



	@api.multi
	def received_rs(self):
		flag = 0
		if self.env.user.id == 1:
			flag = 1
		res = {
		   'name': 'Received',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'cash.confirm.transfer',
			'domain': [('user_id', '=', self.env.user.employee_id.id if flag == 0 else 1),('state','=','pending'),('date','=',self.date)],
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {},

	   }

		return res

	@api.multi
	def transferred_rs(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_construction', 'tree_cash_transfer_view')
		view_id = view_ref[1] if view_ref else False
		flag = 0
		if self.env.user.id == 1:
			flag = 1
		res = {
		   'name': 'Transferred',
			'view_type': 'tree',
			'view_mode': 'tree',
			'res_model': 'cash.confirm.transfer',
			'domain': [('name', '=', self.env.user.employee_id.id if flag == 0 else 1),('date','=',self.date)],
			'target': 'new',
			'view_id': view_id,
			'type': 'ir.actions.act_window',
			'context': {},

	   }

		return res




	
	@api.depends('litre','per_litre')
	def onchange_odometer1(self):
		if self.litre and self.per_litre:
			self.total_litre_amount = self.litre * self.per_litre
		if self.litre == 0 or self.per_litre == 0:
			self.total_litre_amount = 0


	@api.onchange('total_litre_amount','per_litre')
	def onchange_odometer2(self):
		if self.total_litre_amount and self.per_litre:
			self.litre = self.total_litre_amount / self.per_litre

	@api.onchange('litre','total_litre_amount')
	def onchange_odometer3(self):
		if self.litre and self.total_litre_amount:
			self.per_litre = self.total_litre_amount / self.litre






	@api.multi
	def view_reception(self):
		res = {
		   'name': 'Cash Received',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'cash.confirm.transfer',
			'domain': [('user_id', '=', self.driver_name.id),('date','=',self.date)],
			'target': 'current',
			'type': 'ir.actions.act_window',
			'context': {},

	   }

		return res

	@api.multi
	def view_transfer(self):
		res = {
		   'name': 'Cash Transferred',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'cash.confirm.transfer',
			'domain': [('name', '=', self.driver_name.id),('date','=',self.date)],
			'target': 'current',
			'type': 'ir.actions.act_window',
			'context': {},

	   }

		return res


	@api.multi
	def cash_transfer(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_construction', 'view_cash_transfer_amount')
		view_id = view_ref[1] if view_ref else False
		res = {
		   'type': 'ir.actions.act_window',
		   'name': _('Cash Transfer'),
		   'res_model': 'cash.transfer',
		   'view_type': 'form',
		   'view_mode': 'form',
		   'view_id': view_id,
		   'target': 'new',
		   'context': {'default_name':self.driver_name.id,'default_rec':self.id}
	   }

		return res

	@api.model
	def create(self, vals):

		if vals.get('diesel_pump2'):
			if not vals.get('litre'):
				raise except_orm(_('Warning'),_('You have to enter Fuel Quantuty'))
			if not vals.get('per_litre'):
				raise except_orm(_('Warning'),_('You have to enter Fuel Rate'))
			if not vals.get('odometer'):
				raise except_orm(_('Warning'),_('You have to enter Fuel Meter Reading'))
		

		result = super(DriverDailyStatement, self).create(vals)
		if result.reference == False:
			result.reference = self.env['ir.sequence'].next_by_code('driver.daily.statement') or '/'
		balance = 0
		for move_lines in result.driver_name.petty_cash_account.move_lines:
			if move_lines.date < result.date:
				balance += move_lines.debit
				balance -= move_lines.credit


		result.pre_balance = balance
		rec = self.env['cash.confirm.transfer'].search([('date','=',result.date),('state','=','pending'),('name','=',result.driver_name.id)])
		if rec:
			raise except_orm(_('Warning'),
							 _('You Have Some Cash Transfer Amount Which Is In Pending State'))
		result.start_km = result.vehicle_no.last_odometer
		return result

	@api.multi
	def write(self, vals):
		if vals.get('vehicle_no'):
			self.start_km =self.env['fleet.vehicle'].browse(vals.get('vehicle_no')).last_odometer
		if self.diesel_pump2 or vals.get('diesel_pump2'):
			if not vals.get('litre') and not self.litre: 
				raise except_orm(_('Warning'),_('You have to enter Fuel Quantuty'))
			if not vals.get('per_litre') and not self.per_litre: 
				raise except_orm(_('Warning'),_('You have to enter Fuel Rate'))
			if not vals.get('odometer') and not self.odometer:
				raise except_orm(_('Warning'),_('You have to enter Fuel Meter Reading'))
		return super(DriverDailyStatement, self).write(vals)


	@api.multi
	def unlink(self):
		for rec in self:
			for lines in rec.driver_stmt_line:
				reception_temp = self.env['reception.temporary'].search([('driver_stmt_id','=',lines.id)])
				if reception_temp:
					reception_temp.unlink()
				reception = self.env['daily.statement.item.received'].search([('driver_stmt_id','=',lines.id)])
				if reception:
					reception.unlink()
		return super(DriverDailyStatement, self).unlink()




	@api.multi
	def get_warning(self):
		self.state = 'approved'
		# self.approve_entry()
		# lines = self.env['driver.daily.statement.line'].search([('line_id','=', self.id),('status','=','rejected')])
		message = ''
		# if not self.cleaners_name and self.cleaner_bata == 0:
		# 	message = 'Cleaner name and bata is empty. Also some of the records in statement lines are in rejected state. Do you want to proceed it??'
		# 	# if lines and (not self.cleaners_name and self.cleaner_bata == 0):
		# 	# 	message = 'Cleaner name and bata is empty. Also some of the records in statement lines are in rejected state. Do you want to proceed it??'
		#
		# 	# elif not self.cleaners_name and self.cleaner_bata == 0 and not lines:
		# 	# 	message = 'Cleaner name and bata is empty. Do you want to proceed it??'
		# 	# else:
		# 	# 	message = 'Some of the records in statement lines are in rejected state. Do you want to proceed it??'
		# 	# print 'self.message-------------------', message
		# 	# if self.cleaner_bata == False or self.cleaner_bata == 0:
		# 	return {
		# 			'name': 'Warning Message',
		# 			'view_type': 'form',
		# 			'view_mode': 'form',
		# 			'res_model': 'warning.attachment',
		# 			'view_id': self.env.ref('hiworth_construction.view_warning_message_form').id,
		# 			'target': 'new',
		# 			'type': 'ir.actions.act_window',
		# 			'context': {'statement_id': self.id,'default_message':message}
		# 			}
		# else:
		# 	self.approve_entry()
		return True



		

		

	@api.multi
	def approve_entry(self):
		
		rec = self.env['cash.confirm.transfer'].search([('date','=',self.date),('state','=','pending'),('name','=',self.driver_name.id)])
		if rec:
			raise except_orm(_('Warning'),
							 _('You Have Some Cash Transfer Amount Which Is In Pending State'))
		journal = self.env['account.journal'].sudo().search([('name','=','Miscellaneous Journal')])
		if not journal:
			pass
			# raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
		if len(journal) > 1:
			raise except_orm(_('Warning'),_('Multiple Journal with same name(Miscellaneous Journal)'))
		
		move_line = self.env['account.move.line']
		if not self.vehicle_no.related_account:
			raise except_orm(_('Warning'),_('Please Configure Account For Vehicle)'))
		# if self.driver_stmt_line:
		# 	if not self.env.user.company_id.gst_account_id:
		# 		raise osv.except_osv(_('Error!'),_("Please enter companys GST account"))
		expenses = 0
		for expense_line in self.stmt_line:
			expenses += expense_line.payment
		if expenses != 0:
			move_expense = self.env['account.move'].create({'journal_id':journal.id,'ref':self.reference,'driver_stmt_id':self.id,'date':self.date})
			move_line.create({
							'move_id':move_expense.id,
							'state': 'valid',
							'name': str(self.vehicle_no.license_plate)+" Expenses",
							'account_id':self.vehicle_no.related_account.id,
							'journal_id': journal.id,
							'period_id' : move_expense.period_id.id,
							'debit':expenses,
							'credit':0,
							})
			move_line.create({
							'move_id':move_expense.id,
							'state': 'valid',
							'name': 'Expenses',
							'account_id':self.driver_name.petty_cash_account.id,
							# 'vehicle_id':self.vehicle_no.id,
							# 'driver_stmt_id':self.id,
							'journal_id': journal.id,
							'period_id' : move_expense.period_id.id,
							'debit':0,
							'credit':expenses,
							})
			move_expense.state = 'posted'
			expense_book = self.env['expense.book'].search(
				[('date', '=', self.date), ('state', '=', 'open')])
			if expense_book:
				self.env['expense.book.line'].create({
					'expense_book_id': expense_book.id,
					'narration': str(self.vehicle_no.license_plate)+" Expenses",
					'dds_id': self.id,
					'account_id': self.vehicle_no.related_account.id,
					'debit': 0.0,
					'date': self.date,
					# 'location_ids': self.location_ids.id,
					'credit': expenses,
				})
			else:
				raise UserError("Please open today's Expense Book...........!")

		if self.cleaner_bata:
			move_cleaner_bata = self.env['account.move'].create({'journal_id':journal.id, 'ref':self.reference,'driver_stmt_id':self.id,'date':self.date})
			if self.cleaners_name:
				move_line.create({'move_id':move_cleaner_bata.id,
								  'state': 'valid',
								  'name': 'Cleaner Bata',
								  'account_id':self.cleaners_name.payment_account.id,
								  'vehicle_id':self.vehicle_no.id,
								  'driver_stmt_id':self.id,
								  'journal_id': journal.id,
								  'period_id' : move_cleaner_bata.period_id.id,
								  'debit':0,
								  'credit': self.cleaner_bata
							})
			else:
				move_line.create({'move_id':move_cleaner_bata.id,
							  'state': 'valid',
							  'name': 'Cleaner Bata',
							  'account_id':self.driver_name.payment_account.id,
							  'vehicle_id':self.vehicle_no.id,
							  'driver_stmt_id':self.id,
							  'journal_id': journal.id,
							  'period_id' : move_cleaner_bata.period_id.id,
							  'debit':0,
							  'credit': self.cleaner_bata
						})

			move_line.create({'move_id':move_cleaner_bata.id,
							  'state': 'valid',
							  'name': 'Cleaner Bata',
							  'account_id':self.vehicle_no.related_account.id,
							  'journal_id': journal.id,
							  'period_id' : move_cleaner_bata.period_id.id,
							  'debit': self.cleaner_bata,
							  'credit':0,
						})

			move_cleaner_bata.state = 'posted'

		if self.diesel_pump_line:
			for lines in self.diesel_pump_line:
				# fuel_taxes_ids = [i.id for i in lines.fuel_tax_ids]
				move_diesel_pump = self.env['account.move'].create({'journal_id':journal.id, 'ref':self.reference,'driver_stmt_id':self.id,'date':self.date})

				move_line.create({'move_id':move_diesel_pump.id,
									'state': 'valid',
									'name': 'Pump',
									'account_id':lines.diesel_pump.property_account_payable.id,
									'journal_id': journal.id,
									'period_id' : move_diesel_pump.period_id.id,
									'debit':0,
									'credit':float(lines.total_litre_amount),
									'fuel_line': True,
									'vehicle_id': self.vehicle_no.id,
									'partner_id': lines.diesel_pump.id,
									# 'vehicle_owner': lines.vehicle_owner.id,

									# 'location_id':lines.site_id.id,
									'qty':lines.litre,
									'rate':lines.per_litre,
									'amount':lines.total_litre_amount,
									# 'round_off' : lines.fuel_round_off,
									# 'tax_ids': [(6, 0, fuel_taxes_ids)],
									'product_id': lines.fuel_item.id,
									'bill_no':lines.pump_bill_no,
									'diesel_pump_line_id':lines.id,
							})
				move_line.create({'move_id':move_diesel_pump.id,
								  'state': 'valid',
								  'name': 'Pump',
								  'account_id':self.vehicle_no.related_account.id,
								  'journal_id': journal.id,
								  'period_id' : move_diesel_pump.period_id.id,
								  'debit':lines.total_litre_amount,
								  'credit':0,
							})

				move_diesel_pump.state = 'posted'

		driver_betha = 0

		for line in self.driver_stmt_line:
			driver_betha += line.driver_betha
			move_from = self.env['account.move'].create({'journal_id':journal.id, 'ref':self.reference,'driver_stmt_id':self.id,'date':self.date})
			taxes_ids = [i.id for i in line.tax_ids]
			move_line.create({'move_id':move_from.id,
					'state': 'valid',
					'name': 'From',
					'account_id':line.from_id2.property_account_payable.id,
					'product_id':line.item_expense2.id,
					'location_id':line.to_id2.id,
					'vehicle_id':line.line_id.vehicle_no.id,
					'contractor_id':line.contractor_id.id,
					'bill_no':line.voucher_no,
					'qty':line.qty,
					'rate':line.rate,
					'amount':line.total,
					'crusher_line':True,
					'journal_id': journal.id,
					'period_id' : move_from.period_id.id,
					'debit':0,
					'round_off' : line.round_off,
					'tax_ids': [(6, 0, taxes_ids)],
					'driver_stmt_line_id':line.id,
					'credit':line.sub_total_amount,
					})
			if line.tax_ids:
				for tax in  line.tax_ids:
				
					if tax.child_ids:
						for lines in tax.child_ids: 
							if not lines.account_collected_id:
								raise osv.except_osv(_('Warning!'),
										_('There is no account linked to the taxe.'))             
							if lines.account_collected_id: 
								move_line.create({'move_id':move_from.id,
								'state': 'valid',
								'name': 'Tax Amount',
								'account_id':lines.account_collected_id.id,
								'journal_id': journal.id,
								'period_id' : move_from.period_id.id,
								'debit':line.sub_total*lines.amount,
								'credit':0,
								})
					else:  
						if not tax.account_collected_id:
							raise osv.except_osv(_('Warning!'),
									_('There is no account linked to the taxes.'))             
						if tax.account_collected_id:
							
							move_line.create({'move_id':move_from.id,
								'state': 'valid',
								'name': 'Tax Amount',
								'account_id':tax.account_collected_id.id,
								'journal_id': journal.id,
								'period_id' : move_from.period_id.id,
								'debit':line.sub_total*tax.amount,
								'credit':0,
								})

			move_line.create({'move_id':move_from.id,
					'state': 'valid',
					'name': 'From',
					'account_id':line.to_id2.related_account.id,
					'journal_id': journal.id,
					'period_id' : move_from.period_id.id,
					'debit':line.sub_total+line.rent,
					'credit':0,
					})
			move_line.create({'move_id':move_from.id,
					'state': 'valid',
					'name': 'From',
					'account_id':self.vehicle_no.related_account.id,
					'journal_id': journal.id,
					'period_id' : move_from.period_id.id,
					'debit':0,
					'credit':line.rent,
					})
			if line.round_off != 0:
				if not self.env.user.company_id.write_off_account_id:
					raise osv.except_osv(_('Error!'),_("Please enter companys write off account"))
				credit = 0
				debit = 0
				if line.round_off < 0:
					credit = -line.round_off
				else:
					debit = line.round_off
				move_line.create({
					'move_id':move_from.id,
					'state': 'valid',
					'name': 'Round Off',
					'account_id':self.env.user.company_id.write_off_account_id.id,
					'journal_id': journal.id,
					'period_id' : move_from.period_id.id,
					'credit':credit,
					'debit':debit,
					})

			move_from.state = 'posted'
		

		if self.shuttle_service:
			move_rent = self.env['account.move'].create({'journal_id':journal.id, 'ref':self.reference,'driver_stmt_id':self.id,'date':self.date})

			shuttle_driver_amt = 0
			for shuttle in self.shuttle_service:
				if shuttle.rent != 0:
					move_line.create({'move_id':move_rent.id,
								  'state': 'valid',
								  'name': 'Shuttle Rent Percent',
								  'account_id':shuttle.to_location.related_account.id,
								  'journal_id': journal.id,
								  'period_id' : move_rent.period_id.id,
								  'debit':shuttle.rent,
								  'credit':0,
							})
					move_line.create({'move_id': move_rent.id,
									  'state': 'valid',
									  'name': 'Rent Percent',
									  'account_id': self.vehicle_no.related_account.id,
									  'journal_id': journal.id,
									  'period_id': move_rent.period_id.id,
									  'debit': 0,
									  'credit': shuttle.rent,
									  })
				shuttle_driver_amt += shuttle.shuttle_driver_amt
				
			move_line.create({'move_id':move_rent.id,
							  'state': 'valid',
							  'name': 'Rent Percent',
							  'account_id':self.driver_name.payment_account.id,
							  'vehicle_id':self.vehicle_no.id,
							  'driver_stmt_id':self.id,
							  'journal_id': journal.id,
							  'period_id' : move_rent.period_id.id,
							  'debit':0,
							  'credit':shuttle_driver_amt,
						})
			move_line.create({'move_id':move_rent.id,
							  'state': 'valid',
							  'name': 'Rent Percent',
							  'account_id':self.vehicle_no.related_account.id,
							  'journal_id': journal.id,
							  'period_id' : move_rent.period_id.id,
							  'debit':shuttle_driver_amt,
							  'credit':0,
						})

			move_rent.state = 'posted'

		if driver_betha > 0:
			move_driver_bata = self.env['account.move'].create({'journal_id':journal.id, 'ref':self.reference,'driver_stmt_id':self.id,'date':self.date})
			move_line.create({'move_id':move_driver_bata.id,
						  'state': 'valid',
						  'name': 'Driver Bata',
						  'account_id':self.driver_name.payment_account.id,
						  'vehicle_id':self.vehicle_no.id,
						  'driver_stmt_id':self.id,
						  'journal_id': journal.id,
						  'period_id' : move_driver_bata.period_id.id,
						  'debit':0,
						  'credit': driver_betha
					})

			move_line.create({'move_id':move_driver_bata.id,
							  'state': 'valid',
							  'name': 'Driver Bata',
							  'account_id':self.vehicle_no.related_account.id,
							  'journal_id': journal.id,
							  'period_id' : move_driver_bata.period_id.id,
							  'debit': driver_betha,
							  'credit':0,
						})

			move_driver_bata.state = 'posted'

		if self.withdrawal_amount != 0:
			move_withdrawal_amount = self.env['account.move'].create({'journal_id':journal.id, 'ref':self.reference,'driver_stmt_id':self.id,'date':self.date})
			move_line.create({'move_id':move_withdrawal_amount.id,
							  'state': 'valid',
							  'name': 'Withdrawal Amount',
							  'account_id':self.driver_name.petty_cash_account.id,
							  # 'vehicle_id':self.vehicle_no.id,
							  # 'driver_stmt_id':self.id,
							  'journal_id': journal.id,
							  'period_id' : move_withdrawal_amount.period_id.id,
							  'debit':0,
							  'credit':self.withdrawal_amount,
						})
			move_line.create({'move_id':move_withdrawal_amount.id,
							  'state': 'valid',
							  'name': 'Withdrawal Amount',
							  'account_id':self.driver_name.payment_account.id,
							  'vehicle_id':self.vehicle_no.id,
							  'driver_stmt_id':self.id,
							  'journal_id': journal.id,
							  'period_id' : move_withdrawal_amount.period_id.id,
							  'debit':self.withdrawal_amount,
							  'credit':0,
						})
			expense_book = self.env['expense.book'].search(
				[('date', '=', self.date), ('state', '=', 'open')])
			if expense_book:
				self.env['expense.book.line'].create({
					'expense_book_id': expense_book.id,
					'narration': "Driver Withdrawal",
					'dds_id': self.id,
					'account_id': self.driver_name.petty_cash_account.id,
					'debit': 0.0,
					'date': self.date,
					# 'location_ids': self.location_ids.id,
					'credit': self.withdrawal_amount,
				})
			else:
				raise UserError("Please open today's Expense Book...........!")

			move_withdrawal_amount.state = 'posted'
	

		if self.received != 0:
			move_driver_petty = self.env['account.move'].create({'journal_id':journal.id, 'ref':self.reference,'driver_stmt_id':self.id,'date':self.date})
			rec = self.env['cash.confirm.transfer'].search([('date','=',self.date),('name','=',self.driver_name.id)])
			if rec:
				for values in rec:
					move_line.create({'move_id':move_driver_petty.id,
									  'state': 'valid',
									  'name': 'Received',
									  'account_id':values.name.petty_cash_account.id,
									  # 'vehicle_id':self.vehicle_no.id,
									  # 'driver_stmt_id':self.id,
									  'journal_id': journal.id,
									  'period_id' : move_driver_petty.period_id.id,
									  'debit':0,
									  'credit':self.received,
								})
				move_line.create({'move_id':move_driver_petty.id,
								  'state': 'valid',
								  'name': 'Received',
								  'account_id':self.driver_name.petty_cash_account.id,
								  # 'vehicle_id':self.vehicle_no.id,
								  # 'driver_stmt_id':self.id,
								  'journal_id': journal.id,
								  'period_id' : move_driver_petty.period_id.id,
								  'debit':self.received,
								  'credit':0,
							})

				move_driver_petty.state = 'posted'

		


		if self.actual_close_km != False or self.actual_close_km != 0:
			litre = 0
			for litre_lines in self.diesel_pump_line:
				litre += litre_lines.litre
			if (float(self.actual_close_km) - float(self.start_km)) != 0:
				self.env['vehicle.fuel.voucher'].create({'date': self.date,
												  'vehicle_id': self.vehicle_no.id,
												  'opening_reading': self.start_km,
												  'closing_reading': self.actual_close_km,
												})

		if self.diesel_pump_line:
			for lines in self.diesel_pump_line:
				self.env['vehicle.fuel.voucher'].create({'date': self.date,
												  'vehicle_id': self.vehicle_no.id,
												  'pump_id': lines.diesel_pump.property_account_payable.id,
												  'litre': lines.litre,
														 'full_tank':lines.is_full_tank,
												  'per_litre': lines.per_litre,
												  'odometer': lines.odometer,
												  'fuel_value': lines.litre})
		self.state = 'approved'
		if self.env.user.id == 1:
			self.approved_by = self.env['hr.employee'].search([('id','=',1)]).id
			self.sign = self.env['hr.employee'].search([('id','=',1)]).sign
		else:
			self.approved_by = self.env.user.employee_id.id
			self.sign = self.env.user.employee_id.sign


	@api.multi
	def validate_entry(self):
	# 	if self.actual_balance != self.balance:
	# 		raise except_orm(_('Warning'),_('Actual Balance And Theoretical Balance Must Be Same'))
	# 	if float(self.rate_per) < float(self.driver_name.per_day_eicher_rate):
	# 		pass
	# 		# raise except_orm(_('Warning'),_('Rate Must Be Greater Than The Driver Per Day Rate'))
	# 	if self.actual_close_km == False or self.actual_close_km == 0:
	# 		raise except_orm(_('Warning'),_('Must Enter Closing Km'))
	# 	for lines in self.driver_stmt_line:
	# 		supervisor_record = self.env['partner.daily.statement'].sudo().search([('date','=',self.date),('location_ids','=',lines.to_id2.id)])
	# 		if not supervisor_record:
	# 			reception_temp = self.env['reception.temporary'].search([('driver_stmt_id','=',lines.id)])
	# 			if not reception_temp:
	# 				if lines.status == 'new':
	# 					self.env['reception.temporary'].sudo().create({
	# 						'remarks':lines.remarks,
	# 						'driver_stmt_id':lines.id,
	# 						'vehicle_id':lines.line_id.vehicle_no.id,
	# 						'from_id2': lines.from_id2.id,
	# 						'to_id':lines.to_id2.id,
	# 						'date' :self.date,
	# 						'item_expense2' : lines.item_expense2.id,
	# 						'qty':lines.qty,
	# 						'rate':lines.rate,
	# 						'total':lines.total,
	# 						'voucher_no':lines.voucher_no,
	# 						'contractor_id':lines.contractor_id,
	# 						'rent':lines.rent,
	# 						'start_km':lines.start_km,
	# 						'end_km':lines.end_km,
	# 						'total_km':lines.total_km,
	# 						'status':'new'
	# 						})
	# 		if len(supervisor_record) > 1 :
	#
	# 			raise osv.except_osv(_('Error!'),_("Multiple Records In The Same Date with same location"))
	# 		if len(supervisor_record) == 1:
	# 			reception = self.env['daily.statement.item.received'].search([('driver_stmt_id','=',lines.id)])
	# 			if not reception:
	# 				self.env['daily.statement.item.received'].create({
	# 					'received_id':supervisor_record.id,
	# 					'remarks':lines.remarks,
	# 					'driver_stmt_id':lines.id,
	# 					'vehicle_id':lines.line_id.vehicle_no.id,
	# 					'from_id2': lines.from_id2.id,
	# 					'item_expense2' : lines.item_expense2.id,
	# 					'qty':lines.qty,
	# 					'rate':lines.rate,
	# 					'total':lines.total,
	# 					'voucher_no':lines.voucher_no,
	# 					'contractor_id':lines.contractor_id,
	# 					'rent':lines.rent,
	# 					'start_km':lines.start_km,
	# 					'end_km':lines.end_km,
	# 					'total_km':lines.total_km,
	# 					'status':'new'
	# 					})
	# 		lines.sudo().write({'status':'sent'})
	# 	self.vehicle_no.last_odometer = self.actual_close_km
	# 	attendance = self.env['hiworth.hr.attendance'].search([('date', '=', self.date), ('name', '=', self.driver_name.id)])
	# 	if not attendance:
	# 		self.env['hiworth.hr.attendance'].create({'name':self.driver_name.id,
	# 												  'date':self.date,
	# 												  'attendance_category':self.driver_name.attendance_category,
	# 												  'attendance':'full'})
		self.state = 'confirmed' 

	@api.multi
	def set_draft(self):
		self.state = 'draft'

	@api.multi
	def cancel_entry(self):
		# records = self.env['account.move'].search([('driver_stmt_id','=',self.id)])
		# if records:
		# 	for rec in records:
		# 		rec.button_cancel()
		# 		rec.unlink()
		# expenses = self.env['expense.book.line'].search([('dds_id', '=', self.id)])
		# if expenses:
		# 	for exp in expenses:
		# 		exp.unlink()
		# for line in self.driver_stmt_line:
		# 	reception_obj = self.env['reception.temporary'].search([('driver_stmt_id','=',line.id)])
		# 	reception_obj.unlink()
		self.state = 'cancelled'

class ReceptionTemporary(models.Model):
	_name = 'reception.temporary'

	name = fields.Char('Name')
	particulars = fields.Char('Particulars')
	from_id2 = fields.Many2one('res.partner','From')
	to_id = fields.Many2one('stock.location','To')
	item_expense2 = fields.Many2one('product.product','Item')
	qty = fields.Float('Qty',default=1)
	rate = fields.Float('Rate')
	total = fields.Float('Total')
	vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
	start_km = fields.Float('Start KM')
	end_km = fields.Float('End KM')
	
	total_km = fields.Float('Total KM')
	voucher_no = fields.Char('Voucher No')
	contractor_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Contractor')
	rent = fields.Float('Rent')
	remarks  = fields.Char('Remarks')
	date = fields.Date('Date')
	driver_stmt_id = fields.Many2one('driver.daily.statement.line')
	status = fields.Selection([('new','New'),('approved','Approved')],default='new',readonly=True)
	purchase_id = fields.Many2one('purchase.order', 'Purchase')
	invoice_date  = fields.Date('Invoice Date')

class ShuttleService(models.Model):
	_name = 'shuttle.service'

	shuttle_id = fields.Many2one('driver.daily.statement')
	to_location = fields.Many2one('stock.location','To', domain=[('usage','=','internal')])
	qty = fields.Float('Qty')
	rent = fields.Float('Rent')
	remarks = fields.Char('Remarks')
	shuttle_driver_amt = fields.Float('Driver Amount')


class RequestLineDriver(models.Model):
	_name = 'request.line.driver'

	line_id = fields.Many2one('driver.daily.statement')
	date = fields.Datetime('Date',default=fields.Datetime.now())
	item = fields.Many2one('product.product')
	name = fields.Char('Description')
	qty = fields.Float('Qty')


class DriverDailyStatementLine(models.Model):
	_name = 'driver.daily.statement.line'


	@api.multi
	def line_duplicate_button(self):
		dup = self.env['driver.daily.statement.line'].create({
									'line_id': self.line_id.id,
									'from_id2': self.from_id2.id,
									'to_id2': self.to_id2.id,
									'item_expense2': self.item_expense2.id,
									'qty': self.qty,
									'rate': self.rate,
									'total': self.total,
									# 'payment': self.payment,
									# 'voucher_no': self.voucher_no,
									# 'rent': self.rent,
									# 'driver_betha': self.driver_betha,
									# 'status': self.status,
									})
			


 
	# @api.multi
	# def approve_line(self):
	# 	supervisor_record = self.env['partner.daily.statement'].sudo().search([('date','=',self.line_id.date)])
	# 	if not supervisor_record:
	# 		raise except_orm(_('Warning'),_('There is No Supervisor Record For This Day'))
	# 	if len(supervisor_record) >1 :
	# 		raise osv.except_osv(_('Error!'),_("Multiple Records In The Same Date"))
	# 	if len(supervisor_record) == 1:
	# 		self.env['daily.statement.item.received'].create({
	# 			'received_id':supervisor_record.id,
	# 			'remarks':self.remarks,
	# 			'driver_stmt_id':self.id,
	# 			'vehicle_id':self.line_id.vehicle_no.id,
	# 			'from_id2': self.from_id2.id,
	# 			'item_expense2' : self.item_expense2.id,
	# 			'qty':self.qty,
	# 			'rate':self.rate,
	# 			'status':'new'
	# 			})
	# 	self.status = 'sent'





	@api.onchange('qty')
	def onchange_qty_rate(self):
		if self.qty == 0:
			self.total = 0
		else:
			if self.total != 0 and self.rate != 0 and self.qty != round((self.total / self.rate),2):
				self.qty = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Qty field, Rate or Total should be Zero"
						}
					}	
			if self.qty != 0 and self.rate != 0:
				if self.rate*self.qty != self.total:
					pass
				if self.total == 0.0:
					self.total = round((self.qty * self.rate),2)
			if self.total != 0 and self.qty != 0:
				if self.rate == 0.0:
					self.rate = round((self.total / self.qty),2)	


	@api.onchange('rate')
	def onchange_rate_total(self):
		if self.rate == 0:
			self.total = 0
		else:
			if self.total != 0 and self.qty != 0 and self.rate != round((self.total / self.qty),2):
				self.rate = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Rate field, Qty or Total should be Zero."
						}
					}
			if self.qty != 0 and self.rate != 0:
				if self.rate*self.qty != self.total:
					pass
				if self.total == 0.0:
					self.total = round((self.qty * self.rate),2)
			if self.total != 0 and self.rate != 0:
				if self.qty == 0.0:
					self.qty = round((self.total / self.rate),2)		
			
	@api.onchange('total')
	def onchange_qty_total(self):
		if self.total != 0:
			if self.rate*self.qty != self.total:
				if self.rate != 0 and self.qty != 0:
					self.total = 0.0
					return {
						'warning': {
							'title': 'Warning',
							'message': "For Entering value to Total field, Qty or Rate should be Zero."
							}
						}
				elif self.rate == 0 and self.qty != 0:
					self.rate = round((self.total / self.qty),2)
				elif self.qty == 0 and self.rate != 0:
					self.qty = round((self.total / self.rate),2)				
				else:
					pass
		



	# @api.onchange('qty','rate')
	# def onchange_qty_rate(self):
	# 	if self.qty and self.rate:
	# 		self.total = round((self.qty * self.rate),2)
	# 	if self.qty == 0 or self.rate == 0:
	# 		self.total = 0


	# @api.onchange('total','qty')
	# def onchange_qty_total(self):
	# 	if self.total and self.qty:
	# 		self.rate = round((self.total / self.qty),2)

	# @api.onchange('qty')
	# def onchange_rate_total(self):
	# 	if self.rate and self.total:
	# 		self.qty = round((self.total / self.rate),2)


	


	# @api.onchange('start_km','end_km')
	# def _onchange_end_km(self):
	# 	if self.end_km and self.start_km:
	# 		self.rent = self.line_id.vehicle_no.rent_amount

		if self.end_km and self.start_km and self.end_km <= self.start_km:
			self.end_km = 0

			return {
			'warning': {
				'title': 'Warning',
				'message': "End KM Should be greater than starting KM."
				}
			}
	@api.multi
	@api.depends('start_km','end_km')
	def compute_total(self):
		for rec in self:
			rec.total_km = round(rec.end_km-rec.start_km,2)

	@api.onchange('rent')
	def onchange_total_km(self):
		if self.total_km:
			self.driver_betha = self.rent*self.env['fleet.vehicle'].sudo().browse(self.env.context.get('vehicle_no')).trip_commission/100

	@api.onchange('driver_betha')
	def onchange_driver_betha(self):
		if self.driver_betha < self.rent*self.env['fleet.vehicle'].sudo().browse(self.env.context.get('vehicle_no')).trip_commission/100:
			self.driver_betha = self.rent*self.env['fleet.vehicle'].sudo().browse(self.env.context.get('vehicle_no')).trip_commission/100
			return {
			'warning': {
				'title': 'Warning',
				'message': "Driver Betha cannot be less than the minimum value."
				}
			}

	@api.multi
	@api.depends('tax_ids','total','round_off')
	def _get_subtotal_crusher_report(self):
		for lines in self:
			taxi = 0
			taxe = 0
			for tax in lines.tax_ids:
				if tax.price_include == True:
					taxi = tax.amount
				if tax.price_include == False:
					taxe += tax.amount
			lines.tax_amount = (lines.total)/(1+taxi)*(taxi+taxe)
			lines.sub_total = (lines.total)/(1+taxi)
			lines.total_amount = lines.tax_amount + lines.sub_total
			lines.sub_total_amount = lines.total_amount + lines.round_off

	@api.multi
	@api.onchange('purchase_id')
	def onchange_purchase(self):
		if self.purchase_id:
			self.from_id2 = self.purchase_id.partner_id.id
			self.to_id2 = self.purchase_id.location_id.id
			product_ids = [line.product_id.id for line in self.purchase_id.order_line]
			return {'domain': {'item_expense2': [('id', 'in', product_ids)]}}

	
	@api.multi
	@api.onchange('item_expense2','purchase_id')
	def onchange_item_expense2(self):
		if self.item_expense2 and self.purchase_id:
			purcahse_order_line = self.env['purchase.order.line'].search([('product_id','=',self.item_expense2.id),('order_id','=',self.purchase_id.id)], limit=1)
			if purcahse_order_line:
				self.qty = purcahse_order_line.required_qty
				self.rate = purcahse_order_line.expected_rate
		


	line_id = fields.Many2one('driver.daily.statement', delegate=True)
	loc_loc = fields.Boolean('Location to Location ?')
	# stmt_id = fields.Many2one('driver.daily.statement')
	particulars = fields.Char('Particulars')
	from_id2 = fields.Many2one('res.partner','From(Supplier)')
	# from_id2 = fields.Many2one('res.partner','From')
	from_loc= fields.Many2one('stock.location','Source Location')
	to_loc = fields.Many2one('stock.location','Destination Location')
	to_id2 = fields.Many2one('stock.location','To(Location)')
	item = fields.Many2one('account.account','Item')
	item_expense2 = fields.Many2one('product.product','Item')
	qty = fields.Float('Qty')
	rate = fields.Float(string = 'Rate',store=True)
	total = fields.Float(string = 'Total')
	tax_amount = fields.Float('Tax Amount',compute="_get_subtotal_crusher_report")
	sub_total = fields.Float('Sub Total',compute="_get_subtotal_crusher_report")
	total_amount = fields.Float('Total',compute="_get_subtotal_crusher_report")
	payment = fields.Float('Payment')
	voucher_no = fields.Char('Voucher No')
	tax_ids = fields.Many2many('account.tax',string="Tax")
	# trip = fields.Float('Trip/Km')
	rent = fields.Float('Rent')
	remarks  = fields.Char('Remarks')
	start_km = fields.Float('Start KM')
	end_km = fields.Float('End KM')
	driver_betha = fields.Float('Driver Amount')
	contractor_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Contractor')
	round_off = fields.Float('Round Off')
	sub_total_amount = fields.Float('Total Amount',compute="_get_subtotal_crusher_report")
	status = fields.Selection([('new','New'),('sent','Sent'),('accepted','Accepted'),('rejected','Rejected')],default='new',readonly=True)
	total_km = fields.Float(compute='compute_total', store=True, string='Total Km')
	rejection_remarks  = fields.Text('Reason for Rejection')
	purchase_id = fields.Many2one('purchase.order', 'Purchase')
	invoice_date  = fields.Date('Invoice Date')

	@api.onchange('item_expense2')
	def tax_relation(self):
		for rec in self:
			# tax_rel = self.env['product.template'].search([('id','=',rec.item_expense2.id)])
			print '==================================tax',rec.item_expense2.taxes_id
			rec.tax_ids=rec.item_expense2.taxes_id



	@api.model
	def create(self,vals):
		total_km = 0
		rent = 0
		# if not vals.get('start_km'):
		# 	raise osv.except_osv(_('Error!'),_("Start KM should not be Zero"))
		# if not vals.get('end_km'):
		# 	raise osv.except_osv(_('Error!'),_("End KM should not be Zero"))

		# if vals.get('rate') == 0:
		# 	raise except_orm(_('Warning'),_('You have to enter rate in daily statements'))
		# print '(float(vals.get-----------------------------------', vals.get('end_km'), vals.get('start_km')
		if vals.get('total_km') == None and vals.get('end_km') != None and vals.get('start_km') != None:
			total_km = vals['total_km'] = (float(vals.get('end_km')) - float(vals.get('start_km')) )
			print 'chck22----------------------------88888888', total_km, self.env['driver.daily.statement'].search([('id','=',vals.get('line_id'))]).vehicle_no.rate_per_km, self.env['driver.daily.statement'].search([('id','=',vals.get('line_id'))]).vehicle_no.trip_commission

		if vals.get('rent') == None:
			rent = vals['rent'] = total_km * self.env['driver.daily.statement'].search([('id','=',vals.get('line_id'))]).vehicle_no.rate_per_km
		if vals.get('driver_betha') == None:
			vals['driver_betha'] = rent * self.env['driver.daily.statement'].search([('id','=',vals.get('line_id'))]).vehicle_no.trip_commission/100
		# print 'ddd==================='
		result = super(DriverDailyStatementLine, self).create(vals)
		partner_stmt = self.sudo().env['partner.daily.statement'].search([('date','=',result.date),('location_ids','=',result.to_id2.id)], limit=1)
		# print 'test================333', result.to_id2.id,result.date,partner_stmt
		if not partner_stmt:
			values = {
				'date': result.date,
				'from_id2': result.from_id2.id,
				'to_id': result.to_id2.id,
				'item_expense2': result.item_expense2.id,
				'qty': result.qty,
				'rate': result.rate,
				'total': result.total,
				'voucher_no': result.voucher_no,
				'start_km': result.start_km,
				'end_km': result.end_km,
				'total_km': result.total_km,
				'rent': result.rent,
				'driver_betha': result.driver_betha,
				'contractor_id': result.contractor_id.id,
				'remarks': result.remarks,
				'driver_stmt_id': result.id,
				'vehicle_id': result.line_id.vehicle_no.id,
				'purchase_id': result.purchase_id.id,
				'vehicle_id': result.line_id.vehicle_no.id,
				'invoice_date':result.invoice_date
				}
			self.env['reception.temporary'].create(values)
		if partner_stmt:
			values2 = {
				'from_id2': result.from_id2.id,
				'to_id2': result.to_id2.id,
				'item_expense2': result.item_expense2.id,
				'qty': result.qty,
				'rate': result.rate,
				'total': result.total,
				'voucher_no': result.voucher_no,
				'start_km': result.start_km,
				'end_km': result.end_km,
				'total_km': result.total_km,
				'rent': result.rent,
				'driver_betha': result.driver_betha,
				'contractor_id': result.contractor_id.id,
				'remarks': result.remarks,
				'driver_stmt_id': result.id,
				'received_id': partner_stmt.id,
				'purchase_id':result.purchase_id.id,
				'invoice_date':result.invoice_date
				}
			self.env['daily.statement.item.received'].create(values2)
		return result


	@api.multi
	def write(self,vals):
		# print 'self=====================',self
		start_km = 0
		end_km = 0
		total_km = 0
		rent = 0
		if not self.start_km and not vals.get('start_km'):
			raise osv.except_osv(_('Error!'),_("Start KM should not be Zero"))
		if not self.start_km and not vals.get('end_km'):
			raise osv.except_osv(_('Error!'),_("Start KM should not be Zero"))
		if self.rate == 0 and vals.get('rate') == 0:
			raise except_orm(_('Warning'),_('You have to enter rate in daily statements'))
		if vals.get('start_km') or vals.get('end_km'):
			if vals.get('start_km') == None:
				start_km = self.start_km
			else:
				start_km = float(vals.get('start_km'))
			if vals.get('end_km') == None:
				end_km = self.end_km
			else:
				end_km = float(vals.get('end_km'))

			if vals.get('total_km') == None:
				total_km = vals['total_km'] = end_km - start_km
			if vals.get('rent') == None:
				vals['rent'] = rent = total_km * self.line_id.vehicle_no.rate_per_km
			if vals.get('driver_betha') == None:
				vals['driver_betha'] = rent * self.line_id.vehicle_no.trip_commission/100
		
		statement_line = self.env['daily.statement.item.received'].search([('driver_stmt_id','=',self.id)])
		temp_line = self.env['reception.temporary'].search([('driver_stmt_id','=',self.id)])
		print 'statement_line===================',statement_line 
		if statement_line:
			if vals.get('from_id2'):
				statement_line.from_id2 = vals.get('from_id2')
			if vals.get('to_id2'):
				statement_line.to_id2 = vals.get('to_id2')
			if vals.get('item_expense2'):
				statement_line.item_expense2 = vals.get('item_expense2')
			if vals.get('qty'):
				statement_line.qty = vals.get('qty')
			if vals.get('rate'):
				statement_line.rate = vals.get('rate')
			if vals.get('total'):
				statement_line.total = vals.get('total')
			if vals.get('voucher_no'):
				statement_line.voucher_no = vals.get('voucher_no')
			if vals.get('start_km'):
				statement_line.start_km = vals.get('start_km')
			if vals.get('end_km'):
				statement_line.end_km = vals.get('end_km')
			if vals.get('total_km'):
				statement_line.total_km = vals.get('total_km')
			if vals.get('rent'):
				statement_line.rent = vals.get('rent')
			if vals.get('driver_betha'):
				statement_line.driver_betha = vals.get('driver_betha')
			if vals.get('contractor_id'):
				statement_line.contractor_id = vals.get('contractor_id')
			if vals.get('remarks'):
				statement_line.remarks = vals.get('remarks')
			if vals.get('purchase_id'):
				statement_line.purchase_id = vals.get('purchase_id')
			if vals.get('invoice_date'):
				statement_line.invoice_date = vals.get('invoice_date')
		if temp_line:
			if vals.get('from_id2'):
				temp_line.from_id2 = vals.get('from_id2')
			if vals.get('to_id2'):
				temp_line.to_id = vals.get('to_id2')
			if vals.get('item_expense2'):
				temp_line.item_expense2 = vals.get('item_expense2')
			if vals.get('qty'):
				temp_line.qty = vals.get('qty')
			if vals.get('rate'):
				temp_line.rate = vals.get('rate')
			if vals.get('total'):
				temp_line.total = vals.get('total')
			if vals.get('voucher_no'):
				temp_line.voucher_no = vals.get('voucher_no')
			if vals.get('start_km'):
				temp_line.start_km = vals.get('start_km')
			if vals.get('end_km'):
				temp_line.end_km = vals.get('end_km')
			if vals.get('total_km'):
				temp_line.total_km = vals.get('total_km')
			if vals.get('rent'):
				temp_line.rent = vals.get('rent')
			if vals.get('driver_betha'):
				temp_line.driver_betha = vals.get('driver_betha')
			if vals.get('contractor_id'):
				temp_line.contractor_id = vals.get('contractor_id')
			if vals.get('remarks'):
				temp_line.remarks = vals.get('remarks')
			if vals.get('purchase_id'):
				statement_line.purchase_id = vals.get('purchase_id')
			if vals.get('invoice_date'):
				statement_line.invoice_date = vals.get('invoice_date')
		result = super(DriverDailyStatementLine, self).write(vals)
		# crusher_report = self.env['crusher.report'].search([('driver_stmt_id','=',self.id)])
		# if crusher_report:
		# 	if vals.get('to_id2'):
		# 		crusher_report.write({'site_id':vals['to_id2']})
		# 	if vals.get('voucher_no'):
		# 		crusher_report.write({'bill_no':vals['voucher_no']})
		# 	if vals.get('item_expense2'):
		# 		crusher_report.write({'item_id':vals['item_expense2']})
		# 	if vals.get('qty'):
		# 		crusher_report.write({'qty':vals['qty']})
		# 	if vals.get('rate'):
		# 		crusher_report.write({'rate':vals['rate']})
		# 	if vals.get('total'):
		# 		crusher_report.write({'amount':vals['total']})
		# 	if vals.get('from_id2'):
		# 		crusher_report.write({'crusher':vals['from_id2']})
		return result




class DriverDailyExpense(models.Model):
	_name = 'driver.daily.expense'

	# @api.one
	# @api.depends('qty','rate')
	# def _get_total_value(self):
	# 	self.total = self.rate * self.qty


	@api.onchange('qty')
	def onchange_qty_rate(self):
		if self.qty == 0:
			self.total = 0
		else:
			if self.total != 0 and self.rate != 0 and self.qty != round((self.total / self.rate),2):
				self.qty = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Qty field, Rate or Total should be Zero"
						}
					}	
			if self.qty != 0 and self.rate != 0:
				if self.rate*self.qty != self.total:
					pass
				if self.total == 0.0:
					self.total = round((self.qty * self.rate),2)
			if self.total != 0 and self.qty != 0:
				if self.rate == 0.0:
					self.rate = round((self.total / self.qty),2)	


	@api.onchange('rate')
	def onchange_rate_total(self):
		if self.rate == 0:
			self.total = 0
		else:
			if self.total != 0 and self.qty != 0 and self.rate != round((self.total / self.qty),2):
				self.rate = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Rate field, Qty or Total should be Zero."
						}
					}
			if self.qty != 0 and self.rate != 0:
				if self.rate*self.qty != self.total:
					pass
				if self.total == 0.0:
					self.total = round((self.qty * self.rate),2)
			if self.total != 0 and self.rate != 0:
				if self.qty == 0.0:
					self.qty = round((self.total / self.rate),2)		
			


	@api.onchange('total')
	def onchange_qty_total(self):
		if self.total != 0:
			if self.rate*self.qty != self.total:
				if self.rate != 0 and self.qty != 0:
					self.total = 0.0
					return {
						'warning': {
							'title': 'Warning',
							'message': "For Entering value to Total field, Qty or Rate should be Zero."
							}
						}
				elif self.rate == 0 and self.qty != 0:
					self.rate = round((self.total / self.qty),2)
				elif self.qty == 0 and self.rate != 0:
					self.qty = round((self.total / self.rate),2)				
				else:
					pass


	expense_id = fields.Many2one('operator.daily.statement')
	vehicle_id = fields.Many2one('fleet.vehicle',related="stmt_id.vehicle_no")
	stmt_id = fields.Many2one('driver.daily.statement')
	particulars = fields.Char('Particulars')
	item_expense2 = fields.Many2one('item.product','Item')
	qty = fields.Float('Qty')
	rate = fields.Float('Rate')
	total = fields.Float('Total')
	payment = fields.Float('Payment')
	voucher_no = fields.Char('Voucher No')
	remarks  = fields.Char('Remarks')
	date = fields.Date("Date",related="stmt_id.date")

	@api.onchange('rate','qty')
	def onchange_payment(self):
		if self.rate and self.qty:
			self.payment = self.rate * self.qty

	@api.model
	def create(self,vals):
		if vals.get('rate') == 0:
			raise except_orm(_('Warning'),_('You have to enter rate in expense lines'))
		return super(DriverDailyExpense, self).create(vals)

	@api.multi
	def write(self,vals):
		if self.rate == 0 and vals.get('rate') == 0:
			raise except_orm(_('Warning'),_('You have to enter rate in expense lines'))
		return super(DriverDailyExpense, self).create(vals)


class WarningAttachment(models.TransientModel):
	_name = 'warning.attachment'

	message = fields.Text(readonly=True)

	@api.multi
	def warning_ok(self):
		self.env['driver.daily.statement'].browse(self.env.context.get('statement_id')).approve_entry()
		return True




