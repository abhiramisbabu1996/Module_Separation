from openerp import fields, models, api, _
# from datetime import datetime
from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta
from datetime import date
from dateutil import relativedelta
from openerp.osv import osv



class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	account_balance = fields.Float('Account Balance', related="journal_id.default_credit_account_id.balance")
	usable_balance = fields.Float('Usable Balance', compute='_get_usable_balance')
	common_usage = fields.Boolean('Default Banks Used')


	@api.multi
	def _get_usable_balance(self):
		for record in self:
			if record.bank_acc_type_id.name == 'OD Account':
				record.usable_balance = record.limit+record.account_balance
			else:
				record.usable_balance = record.account_balance

	@api.multi
	def unlink(self):
		for record in self:
			if record.id == self.env.ref('bank_account_type_od').id:
				raise Warning(_('You cannot delete OD Bank Account Type'))
			elif record.id == self.env.ref('bank_account_type_current').id:
				raise Warning(_('You cannot delete Current Bank Account Type'))
			else:
				pass
		return super(ResPartnerBank, self).unlink()


class CustomerInvoiceFollowUp(models.Model):
	_name = 'customer.invoice.follow.up'

	project_id = fields.Many2one('project.project','Name Of Work',related="account_invoice_ids.project_id",store=True)
	bill_amount = fields.Float('Bill Amount(Before Deducion)',compute='compute_bill_amount')
	district = fields.Char('District',store=True)
	department = fields.Char('Department')
	contractor_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Contractor',store=True)
	type_of_bill = fields.Many2one('type.of.bill','Type of Bill')
	person = fields.Char('Person Incharge')
	account_invoice_ids = fields.Many2one('account.invoice','Invoice no')
	# status_line = fields.One2many('status.update.line','line_id')
	balance_amount = fields.Float('Balance Amount',compute='compute_balance_amount',store=True)
	total_tender_amount = fields.Float('Tender Amount',compute='compute_tender_amount')
	previous_balance_amount = fields.Float('Previous Balance Amount',readonly = True)
	date = fields.Date('Date',required=True)
	bill_status = fields.Text('Bill Status',required=True)
	it_amount = fields.Float('IT')
	welfare_amount = fields.Float('Welfare')
	tds_gst = fields.Float('TDS-GST')
	retention_security = fields.Float('Retention/Security')
	other_recovery = fields.Float('Other Recovery')
	advance_mobile = fields.Float('Advance Mobile')
	e_payment = fields.Float('E-Payment')
	check_amount = fields.Float('Check Amount')
	hr_agency = fields.Float('HR/Agency')
	total_deduction = fields.Float('Total Deduction',compute='compute_total_deduction',readonly=True)
	bill_amount_after = fields.Float('Bill Amount(After Deduction)',compute='compute_final_bill_amount')
	mode_of_payment = fields.Many2one('account.journal','Mode of Payment')
	bill_date = fields.Date('Bill Date')
	state = fields.Selection([
			('draft', 'Draft'),
			('approved', 'Approved')],
			default='draft')



	@api.depends('it_amount','welfare_amount','tds_gst','retention_security','other_recovery','advance_mobile','e_payment','check_amount','hr_agency')
	def compute_total_deduction(self):
		for rec in self:
			rec.total_deduction = rec.it_amount+rec.welfare_amount+rec.tds_gst+rec.retention_security+rec.other_recovery+rec.advance_mobile+rec.e_payment+rec.check_amount+rec.hr_agency

	@api.depends('bill_amount','total_deduction')
	def compute_final_bill_amount(self):
		for rec in self:
			rec.bill_amount_after = rec.bill_amount - rec.total_deduction

	@api.multi
	def approved_progressbar(self):
		self.write({
					'state': 'approved'
					})


	@api.multi
	@api.depends('project_id')
	def compute_bill_amount(self):
		for bal in self:
			bal.bill_amount=bal.account_invoice_ids.amount_total

	@api.multi
	@api.depends('project_id')
	def compute_tender_amount(self):
		for tender in self:
			tender.total_tender_amount = self.env['hiworth.tender'].search([('id', '=',tender.project_id.tender_id.id)]).apac
	@api.multi
	@api.depends('bill_amount','balance_amount')
	def compute_balance_amount(self):
		for record in self:
			bill_amount = 0
			update_balance = self.env['customer.invoice.follow.up'].search([('project_id','=',record.project_id.id)])
			for bal in update_balance:
				bill_amount += bal.bill_amount
			if bill_amount >= record.total_tender_amount:
				record.balance_amount=0
			else:
				record.balance_amount = record.total_tender_amount - bill_amount


	@api.model
	def create(self, vals):

		cnt = vals.get('project_id')
		update_balance = self.env['customer.invoice.follow.up'].search([('project_id','=',cnt)],order='id desc', limit=1)
		vals['previous_balance_amount']=update_balance.balance_amount


		return super(CustomerInvoiceFollowUp,self).create(vals)


class StatusUpdateLine(models.Model):
	_name = 'status.update.line'


	# line_id = fields.Many2one('customer.invoice.follow.up','line_ids' )
	# date = fields.Date('Date',required=True)
	# bill_status = fields.Text('Bill Status',required=True)
	


	


class StatusUpdate(models.Model):
	_name = 'status.update'

	project_id = fields.Many2one('project.project','Name Of Work')
	person = fields.Char('Person')
	date = fields.Date('Date')
	bill_status = fields.Text('Bill Status')



class AccountJournal(models.Model):
	_inherit = 'account.journal'

	@api.onchange('default_credit_account_id')
	def onchange_debit_account(self):
		self.default_debit_account_id = self.default_credit_account_id.id



class CreditorsPayment(models.Model):
	_name = 'creditor.payment'

	supervisor_id = fields.Many2one('hr.employee', string="Supervisor", domain="[('user_category','=','supervisor')]")
	site_id = fields.Many2one('stock.location','Site', domain=[('usage','=','internal')])
	partner_id = fields.Many2one('res.partner', domain=[('supplier','=',True)], string="Party Name")
	account_id = fields.Many2one('account.account','Debit Account')

	tds_id = fields.Many2one('tds.configuration','TDS')
	is_condition = fields.Boolean('Need Condition', related="tds_id.is_condition")
	tds_condition_id = fields.Many2one('tds.condition', 'Condition')
	payable_amount = fields.Float('Amount Payable')
	tds_percent = fields.Float('TDS Percent')
	tds_amount = fields.Float('TDS Amount', compute="_compute_amount", store=True)
	amount_after_tds = fields.Float('Amount After TDS', compute="_compute_amount", store=True)

	date = fields.Date('Date of Request')
	journal_id = fields.Many2one('account.journal','Bank Account')
	remarks = fields.Text('Remarks')
	prepared_by = fields.Many2one('res.users', 'Prepared By')
	verified_by = fields.Many2one('res.users', 'Verified By')
	approved_by = fields.Many2one('res.users', 'Approved By')
	state = fields.Selection([('draft','Draft'),
								('verified','Verified'),
								('approved','Approved')
								], default="draft")

	mode_o_pay = fields.Selection([('cash','CASH'),
									('bank','BANK')],string ='Mode of payment',default="cash")


	@api.onchange('tds_id','tds_condition_id')
	def onchange_tds(self):
		if self.is_condition == True:
			self.tds_percent = self.env['tds.configuration.line'].search([('line_id','=', self.tds_id.id),('tds_condition_id','=', self.tds_condition_id.id)], limit=1).tds_percent
		else:
			self.tds_percent = self.tds_id.tds_percent

	@api.multi
	@api.depends('payable_amount','tds_percent')
	def _compute_amount(self):
		for record in self:
			record.tds_amount = (self.payable_amount * self.tds_percent)/100
			record.amount_after_tds = self.payable_amount - ((self.payable_amount * self.tds_percent)/100)



	@api.onchange('account_id')
	def onchange_account(self):
		ids = []
		record = self.env['account.account.type'].search([('report_type','=','liability')])
		for rec in record:
			accounts = self.env['account.account'].search([('user_type','=',rec.id)])
			for acc in accounts:
				ids.append(acc.id)
		return {'domain': {'account_id': [('id', 'in', ids)]}}


	@api.multi
	def button_verify(self):
		self.verified_by = self.env.user.id
		self.state = 'verified'

	@api.multi
	def button_approve(self):
		self.approved_by = self.env.user.id
		self.state = 'approved'
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		# Creditor Payment
		if self.payable_amount != 0:
			move_id = move.create({
								'journal_id': self.journal_id.id,
								'date': self.date,
								})
			
			print 'test11-----------------------------'
			line_id = move_line.create({
									'account_id': self.account_id.id,
									'name': 'Creditor Payment without TDS',
									'credit': self.amount_after_tds,
									'debit': 0,
									'move_id': move_id.id,
									'status': 'draft'
									})

			line_id = move_line.create({
									'account_id': self.tds_id.tds_related_account_id.id,
									'name': 'TDS Amount',
									'credit': self.tds_amount,
									'debit': 0,
									'move_id': move_id.id,
									'status': 'draft'
									})
			print 'test22-----------------------------'
				
			line_id = move_line.create({
									'account_id': self.journal_id.default_credit_account_id.id,
									'name': 'Creditor Payment',
									'credit': 0,
									'debit': self.payable_amount,
									'move_id': move_id.id,
									'status': 'draft'
									})
			print 'test33-----------------------------'
			move_id.button_validate()

	@api.model
	def create(self,vals):
		print 'self.env.user.id------------------', self.env.user.id
		vals['prepared_by'] = self.env.user.id

		return super(CreditorsPayment, self).create(vals)

class TypeOfBill(models.Model):

	_name = "type.of.bill"

	name = fields.Char('Type')


class FleetEMI(models.Model):
	_name ='fleet.emi'


	name = fields.Char('Loan No')
	category_id = fields.Many2one('vehicle.category.type','Particulars', related="vehicle_id.vehicle_categ_id")
	vehicle_id = fields.Many2one('fleet.vehicle','Reg.No')
	model_id = fields.Many2one('fleet.vehicle.model','Model', related="vehicle_id.model_id")
	owner_id = fields.Many2one('res.partner',string='Owner',domain=[('res_company_new','=',True)])
	cost = fields.Float('Asset Cost')
	loan_amount = fields.Float('Amount Financed')
	emi_amount = fields.Float('EMI Amount')
	start_date = fields.Date('Beginning Date')
	end_date = fields.Date('Last Date')
	period = fields.Integer('Tenure (In Months)',compute="_compute_period1", store=True)
	loan_bank_id = fields.Many2one('res.partner.bank','Financier')
	loan_account_id = fields.Many2one('account.account','Account')
	bank_id = fields.Many2one('res.partner.bank','EMI-Bank')
	payment_ids = fields.One2many('fleet.emi.payment', 'loan_id')
	state = fields.Selection([('draft','Draft'),
								('approved','Approved'),
								('closed','Closed'),
								('noc','NOC Received'),
							  ('documents','Documents Received'),
								('hypothecation','Hypothecation')
								], default="draft")



	@api.multi
	def generate_payment_entries(self):
		print 'self.period--------------------', self.period
		for record in range(0, self.period):
			print 'record------------------', record + 1
			date_start_dt = fields.Datetime.from_string(self.start_date)
			dt = date_start_dt + relativedelta.relativedelta(months=record)
			self.payment_ids.create({'installment_no': record + 1,
									'loan_id': self.id,
									'date': dt,
									'amount': self.emi_amount,
									'bank_id': self.bank_id.id,
									'state': 'draft'
									})




	@api.model
	def _cron_payment_pop_up(self):
		prev_popups = self.env['popup.notifications'].search([('emi','=',True)])
		for popup in prev_popups:
			popup.unlink()

		amount4 = 0
		amount3 = 0
		amount2 = 0
		amount1 = 0
		amount0 = 0
		emi_no4 = 0
		emi_no3 = 0
		emi_no2 = 0
		emi_no1 = 0
		emi_no0 = 0
		print 'chcl=-------------------------------------------------', self.env['fleet.emi'].search([('state','=','approved')])
		for day in self.env['fleet.emi'].search([('state','=','approved')]):
			print 'day--------------------------------', day
			today = date.today()
			today_month = today.month
			beg_month =  datetime.strptime(day.start_date, "%Y-%m-%d").month
			payment_day =  datetime.strptime(day.start_date, "%Y-%m-%d").day
			payment_date = date(today.year, today.month, payment_day)
			print 'zzzzzzzz1111----------------------', today_month, beg_month, payment_day
			if day.period != 0 and today_month >= beg_month:
				print 'zzzzzzzz----------------------', abs((payment_date - today).days)

				if abs((payment_date - today).days) == 4:
					date4 = payment_date
					amount4 += day.emi_amount
					emi_no4 += 1
				elif abs((payment_date - today).days) == 3:
					date3 = payment_date
					amount3 += day.emi_amount
					emi_no3 += 1

				elif abs((payment_date - today).days) == 2:
					date2 = payment_date
					amount2 += day.emi_amount
					emi_no2 += 1

				elif abs((payment_date - today).days) == 1:
					date1 = payment_date
					amount1 += day.emi_amount
					emi_no1 += 1

				elif abs((payment_date - today).days) == 0:
					date0 = payment_date
					amount0 += day.emi_amount
					emi_no0 += 1
				else:
					pass

		message = ''
		if emi_no0 != 0:
			message = message + 'You have'+ ' ' + str(emi_no0) +' ' +  'EMI payments on' +' ' +  str(date0) +' ' +  'for Rs.' +' ' +  str(amount0)
		if emi_no1 != 0:
			message = message + 'You have'+ ' ' + str(emi_no1) +' ' +  'EMI payments on' +' ' +  str(date1) +' ' +  'for Rs.' +' ' +  str(amount1)
		if emi_no2 != 0:
			message = message + 'You have'+ ' ' + str(emi_no2) +' ' +  'EMI payments on' +' ' +  str(date2) +' ' +  'for Rs.' +' ' +  str(amount2)
		if emi_no3 != 0:
			message = message + 'You have'+ ' ' + str(emi_no3) +' ' +  'EMI payments on' +' ' +  str(date3) +' ' +  'for Rs.' +' ' +  str(amount3)
		if emi_no4 != 0:
			message = message + 'You have'+ ' ' + str(emi_no4) +' ' +  'EMI payments on' +' ' +  str(date4) +' ' +  'for Rs.' +' ' +  str(amount4)

		if message != '':
			self.env['popup.notifications'].sudo().create({
													'name':day.env.user.id,
													'status':'draft',
													'message':message,
													'emi':True,
													})

		
		for day in self.env['fleet.emi'].search([('state','=','closed')]):
			self.env['popup.notifications'].sudo().create({
														'name':day.env.user.id,
														'status':'draft',
														'emi':True,
														'message':"You have to receive NOC for loan-" + day.name,
														})

		for day in self.env['fleet.emi'].search([('state','=','noc')]):
			self.env['popup.notifications'].sudo().create({
														'name':day.env.user.id,
														'status':'draft',
														'emi':True,
														'message':"You have to clear hypothecation for loan-" + day.name,
														})


	@api.multi
	@api.depends('start_date','end_date')
	def _compute_period1(self):
		for record in self:
			if record.start_date and record.end_date:
				d1 = datetime.strptime(record.start_date, "%Y-%m-%d")
				d2 = datetime.strptime(record.end_date, "%Y-%m-%d")
				r = relativedelta.relativedelta(d2, d1)
				print 'rrrrrrrrrrrrrrrrrrrrrrrrrrrr',r
				date_f = (d2 - d1).days 
				if date_f % 30 == 0:
					print 'ddddddddddddddddd',date_f
				else:
					print 'vvvvvvvvvvvvvvvvvvvv',date_f + 1
				#print 'dddddddddddddddddddddddd',date_f
				record.period = r.months + (12*(int(d2.year)-int(d1.year)))

	@api.multi
	def button_set_to_draft(self):
		self.state = 'draft'
		moves = self.env['account.move'].search([('fleet_emi','=', self.id)])
		if moves:
			for rec in moves:
				rec.button_cancel()
				rec.unlink()

		self.state = 'draft'


	@api.multi
	def button_approve(self):
		self.state = 'approved'
		self.vehicle_id.emi_no = self.name
		self.vehicle_id.emi_start_date = self.start_date
		self.vehicle_id.emi_amt = self.emi_amount
		self.vehicle_id.last_paid_date = self.end_date
		self.vehicle_id.total_due = self.emi_amount
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		move_id = move.create({
							'journal_id': self.bank_id.journal_id.id,
							'date': datetime.now(),
							'fleet_emi': self.id
							})
		
		line_id = move_line.create({
								'account_id': self.loan_account_id.id,
								'name': 'Loan Amount',
								'credit': self.loan_amount,
								'debit': 0,
								'move_id': move_id.id,
								})

		if not self.vehicle_id.asset_account_id.id:
				raise osv.except_osv(_('Error!'),_("Please configure an asset account for this vehicle."))
			
		line_id = move_line.create({
								'account_id': self.vehicle_id.asset_account_id.id,
								'name': 'Loan Amount',
								'credit': 0,
								'debit': self.loan_amount,
								'move_id': move_id.id,
								})
		move_id.button_validate()


	@api.multi
	def button_noc_receive(self):
		self.state = 'noc'

	@api.multi
	def button_documents(self):
		self.state = 'documents'

	@api.multi
	def button_hypothecation(self):
		self.state = 'hypothecation'

	@api.multi
	def button_close(self):
		self.state = 'closed'



class FleetEMIPayment(models.Model):
	_name ='fleet.emi.payment'


	loan_id = fields.Many2one('fleet.emi','Loan No')
	category_id = fields.Many2one('vehicle.category.type','Particulars', related="loan_id.category_id")
	vehicle_id = fields.Many2one('fleet.vehicle','Reg.No',related="loan_id.vehicle_id")
	model_id = fields.Many2one('fleet.vehicle.model','Model', related="loan_id.model_id")
	installment_no = fields.Integer('Installment No.')
	# date = fields.Integer('Date')
	date = fields.Date('Date')
	amount = fields.Float('EMI Amount')
	principal = fields.Float('Principal')
	interest = fields.Float('Interest')
	opening_principal = fields.Float('Opening Principal', compute="_compute_principal", store=True)
	closing_principal = fields.Float('Closing Principal', compute="_compute_principal", store=True)
	bank_id = fields.Many2one('res.partner.bank','EMI-Bank')
	state = fields.Selection([('draft','Draft'),
								('paid','Paid'),
								], default="draft")
	expense_account_id = fields.Many2one('account.account', 'Account for EMI Interest')

	@api.multi
	@api.depends('principal')
	def _compute_principal(self):
		for record in self:
			opening_principal = 0
			closing_principal = 0
			# opening_principal += line1.pricipal for line1 in self.env['fleet.emi.payment'].search([('date','<', record.date)])
			# closing_principal += line2.pricipal for line2 in self.env['fleet.emi.payment'].search([('date','<=', record.date)])
			for line1 in self.env['fleet.emi.payment'].search([('date','<', record.date)]):
				opening_principal += line1.principal 
			for line2 in self.env['fleet.emi.payment'].search([('date','<=', record.date)]):
				closing_principal += line2.principal 
			record.opening_principal = record.loan_id.loan_amount - opening_principal
			record.closing_principal = record.loan_id.loan_amount - closing_principal


	@api.multi
	def button_payment(self):
		self.state = 'paid'

		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		move_id = move.create({
							'journal_id': self.bank_id.journal_id.id,
							'date': datetime.now(),
							})
		
		line_id = move_line.create({
								'account_id': self.loan_id.loan_bank_id.journal_id.default_debit_account_id.id,
								'name': 'Vehicle EMI Principal Amount',
								'credit': 0,
								'debit': self.principal,
								'move_id': move_id.id,
								})

		line_id = move_line.create({
								'account_id': self.expense_account_id.id,
								'name': 'Vehicle EMI Interest',
								'credit': 0,
								'debit': self.interest,
								'move_id': move_id.id,
								})
			
		line_id = move_line.create({
								'account_id': self.bank_id.journal_id.default_credit_account_id.id,
								'name': 'Vehicle EMI Amount',
								'debit': 0,
								'credit': self.amount,
								'move_id': move_id.id,
								})
		move_id.button_validate()


class FleetEMIWizard(models.Model):
	_name ='fleet.emi.wizard'


	date = fields.Date('Date')



class HiworthBankPaymentHead(models.Model):
	_name = 'hiworth.bank.payment.head'

	date = fields.Date('Date',default=fields.Date.today, required=True)
	employee_id = fields.Many2one('hr.employee', string="User", required=True, domain="[('user_category','=','cashier')]")
	bank_payment_ids = fields.One2many('hiworth.bank.payment','pay_id')
	state = fields.Selection([('draft','Draft'),
							('send_approval','Send for approval'),
							('approved','Approved'),
							('paid','Paid')
							], default="draft", string="Status")
	approve_person_id = fields.Many2one('hr.employee', string="Approved Person")
	emergency_payment = fields.Boolean('Emergency Payment')

	@api.model
	def default_get(self, default_fields):
		vals = super(HiworthBankPaymentHead, self).default_get(default_fields)
		user = self.env['res.users'].search([('id','=',self.env.user.id)])
			
		if user:
			if user.employee_id:
				vals.update({'employee_id' : user.employee_id.id,
							 })
			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'),_("User and Employee is not linked."))

		return vals

	@api.multi
	def button_send_approval(self):
		self.state = 'send_approval'


	@api.multi
	def approve_button(self):
		self.state = 'approved'
		user = self.env['res.users'].search([('id','=',self.env.user.id)])
		if user:
			if user.employee_id:
				self.approve_person_id = user.employee_id.id

			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'),_("User and Employee is not linked."))


	@api.multi
	def button_payment(self):
		self.state = 'paid'

		for record in self.bank_payment_ids:

			values = {
				'journal_id': record.bank_id.journal_id.id,
				'date': self.date,
				}
			move_id = self.env['account.move'].create(values)
			amount = 0
			for rec in record.approve_ids2:

				if rec.is_approve == True:


					move_line = self.env['account.move.line']


					amount += rec.approved_amount

					values2 = {
						'account_id': rec.account_id.id,
						'name': 'Paid To' + ' ' + rec.account_id.name,
						'debit': rec.approved_amount,
						'credit': 0,
						'move_id': move_id.id,
						}

					line_id = move_line.create(values2)

			if amount != 0:
				values = {
					'account_id': record.bank_id.journal_id.default_credit_account_id.id,
					'name': 'Bank Payment',
					'debit': 0,
					'credit': amount,
					'move_id': move_id.id,
					}
				line_id = move_line.create(values)
			move_id.button_validate()


class HiworthBankPayment(models.Model):
	_name = 'hiworth.bank.payment'

	payment_ids = fields.One2many('hiworth.bank.payment.line','line_id')
	approve_ids = fields.One2many('hiworth.bank.payment.line','line_id')
	approve_ids2 = fields.One2many('hiworth.bank.payment.line','line_id')
	pay_id = fields.Many2one('hiworth.bank.payment.head')
	
	bank_id = fields.Many2one('res.partner.bank', string="Bank")
	state = fields.Selection(related="pay_id.state")



class HiworthBankPaymentLine(models.Model):
	_name = 'hiworth.bank.payment.line'

	date = fields.Date('Date',default=fields.Date.today)
	line_id = fields.Many2one('hiworth.bank.payment')
	account_id = fields.Many2one('account.account', string="Account")
	requested_amount = fields.Float('Requested Amount')
	approved_amount = fields.Float('Approved Amount')
	
	is_approve = fields.Boolean('Is Aproved', default=False)
	state = fields.Selection(related="line_id.state")

	narration = fields.Text('Narration')

	# @api.onchange('account_id')
	# def onchange_account(self):
	# 	ids = []
	# 	record = self.env['account.account.type'].search([('report_type','=','liability')])
	# 	for rec in record:
	# 		accounts = self.env['account.account'].search([('user_type','=',rec.id)])
	# 		for acc in accounts:
	# 			ids.append(acc.id)
	# 	return {'domain': {'account_id': [('id', 'in', ids)]}}


	@api.onchange('requested_amount')
	def onchange_approved_amount(self):
		self.approved_amount = self.requested_amount




class TdsConfiguration(models.Model):
	_name = 'tds.configuration'

	name = fields.Char('Section')
	is_condition = fields.Boolean('Need Condition', default=False)
	tds_percent = fields.Float('TDS Percent')
	threshold_limit = fields.Float('Threshold Limit')
	one_time_limit = fields.Float('One Time Limit')
	tds_related_account_id = fields.Many2one('account.account', 'Related Account')
	tds_ids = fields.One2many('tds.configuration.line', 'line_id')


class TdsConfigurationLine(models.Model):
	_name = 'tds.configuration.line'

	line_id = fields.Many2one('tds.configuration')
	tds_condition_id = fields.Many2one('tds.condition', 'Condition')
	tds_percent = fields.Float('TDS Percent')

class TdsCondition(models.Model):
	_name = 'tds.condition'

	name = fields.Char('Name')


class HREmployee1(models.Model):
	_inherit ='hr.employee'


	@api.model
	def _cron_esi_pf_payment_pop_up13(self):
		prev_popups = self.env['popup.notifications'].search([('pf_esi','=',True)])
		for popup in prev_popups:
		  popup.unlink()

		esi_payment_date = False
		pf_payment_date = False

		config = self.env['general.hr.configuration'].search([],limit=1)
		today = date.today()

		print 'date----------------------', today.year, today.month, config.esi_payment_date, config.pf_payment_date
		esi_date = config.esi_payment_date
		if esi_date:
			esi_payment_date = date(today.year, today.month, esi_date)

		pf_date = config.pf_payment_date
		if pf_date:
			pf_payment_date = date(today.year, today.month, pf_date)
		print 'esi_payment_date----------------------', esi_payment_date, pf_payment_date

		if today.month == 1:
			month = 'January'
		elif today.month == 2:
			month = 'February'
		elif today.month == 3:
			month = 'March'
		elif today.month == 4:
			month = 'April'
		elif today.month == 5:
			month = 'May'
		elif today.month == 6:
			month = 'June'
		elif today.month == 7:
			month = 'July'
		elif today.month == 8:
			month = 'August'
		elif today.month == 9:
			month = 'September'
		elif today.month == 10:
			month = 'October'
		elif today.month == 11:
			month = 'November'
		elif today.month == 12:
			month = 'December'
		else:
			pass

		if esi_payment_date:
			print 'abs((esi_payment_date - today).days)----------------', abs((esi_payment_date - today).days)
			esi = self.env['hr.esi.payment'].search([('month','=',month),('year','=',today.year),('state','=', 'paid')])
			# if esi_payment_date and abs((esi_payment_date - today).days) <= 15 and not esi:
			# 	self.env['popup.notifications'].sudo().create({
			# 										  'name':self.env.user.id,
			# 										  'status':'draft',
			# 										  'pf_esi':True,
			# 										  'message':'Last date of ESI payment is on' + ' ' + str(esi_payment_date),
			# 										  })
			#

			

		if pf_payment_date:
			pf = self.env['pf.payment'].search([('month','=',month),('year','=',today.year),('state','=', 'paid')])
			# if pf_payment_date and abs((pf_payment_date - today).days) <= 15 and not pf:
			# 	self.env['popup.notifications'].sudo().create({
			# 										  'name':self.env.user.id,
			# 										  'status':'draft',
			# 										  'pf_esi':True,
			# 										  'message':'Last date of PF payment is on' + ' ' + str(pf_payment_date),
			# 										  })
			#


class FleetDocuments1(models.Model):
	_inherit ='fleet.vehicle.documents'


	@api.model
	def _cron_veh_document_renewal_pop_up(self):
		prev_popups = self.env['popup.notifications'].search([('veh_doc','=',True)])
		for popup in prev_popups:
			popup.unlink()

		today = date.today()

		vehicles = self.env['fleet.vehicle'].search([('rent_vehicle','!=',True)])
		for veh_id in vehicles:

			pollution = self.env['fleet.vehicle.documents'].search([('vehicle_id','=',veh_id.id),('document_type','=','pollution')], limit=1)
			if pollution:
				pollution_date = datetime.strptime(pollution.renewal_date,'%Y-%m-%d').date()
				print 'chkkkk--------------------------', abs((pollution_date - today).days)

				# if pollution.renewal_date and abs((pollution_date - today).days) <= 15:
				# 	self.env['popup.notifications'].sudo().create({
				# 										  'name':self.env.user.id,
				# 										  'status':'draft',
				# 										  'veh_doc':True,
				# 										  'message':'Pollution renewal date of' + ' ' + str(veh_id.name) + ' ' + 'is on' + ' ' + str(pollution_date),
				# 										  })

			road_tax = self.env['fleet.vehicle.documents'].search([('vehicle_id','=',veh_id.id),('document_type','=','road_tax')], limit=1)
			if road_tax:
				road_tax_date = datetime.strptime(road_tax.renewal_date,'%Y-%m-%d').date()
				print 'chkkkk--------------------------', abs((road_tax_date - today).days)

				if road_tax.renewal_date and abs((road_tax_date - today).days) <= 15:
					self.env['popup.notifications'].sudo().create({
														  'name':self.env.user.id,
														  'status':'draft',
														  'veh_doc':True,
														  'message':'Road tax renewal date of' + ' ' + str(veh_id.name) + ' ' + 'is on' + ' ' + str(road_tax_date),
														  })


			fitness = self.env['fleet.vehicle.documents'].search([('vehicle_id','=',veh_id.id),('document_type','=','fitness')], limit=1)
			if fitness:
				if fitness.renewal_date:
					fitness_date = datetime.strptime(fitness.renewal_date,'%Y-%m-%d').date()
				print 'chkkkk--------------------------', abs((fitness_date - today).days)

				# if fitness.renewal_date and abs((fitness_date - today).days) <= 15:
				# 	self.env['popup.notifications'].sudo().create({
				# 										  'name':self.env.user.id,
				# 										  'status':'draft',
				# 										  'veh_doc':True,
				# 										  'message':'Fitness renewal date of' + ' ' + str(veh_id.name) + ' ' + 'is on' + ' ' + str(fitness_date),
				# 										  })

			insurance = self.env['fleet.vehicle.documents'].search([('vehicle_id','=',veh_id.id),('document_type','=','insurance')], limit=1)
			if insurance:
				insurance_date = datetime.strptime(insurance.renewal_date,'%Y-%m-%d').date()
				print 'chkkkk--------------------------', abs((insurance_date - today).days)

				# if insurance.renewal_date and abs((insurance_date - today).days) <= 15:
				# 	self.env['popup.notifications'].sudo().create({
				# 										  'name':self.env.user.id,
				# 										  'status':'draft',
				# 										  'veh_doc':True,
				# 										  'message':'Insurance renewal date of' + ' ' + str(veh_id.name) + ' ' + 'is on' + ' ' + str(insurance_date),
				# 										  })


class PostalForm(models.Model):


	_name = 'postal.form'

	purpose = fields.Char('Purpose')
	submitted_to = fields.Text("Submitted To")
	date_from = fields.Date('Date From', default=False)
	date_to = fields.Date('Date To')
	maturity_date = fields.Date('Maturity Date')
	closing_date = fields.Date('Closing Date')
	# product_id = fields.Many2one('product.product',string = 'Name of Product')
	work_name = fields.Char('Work Name')
	fd_percent = fields.Float('FD Percent')
	fd_amount_wo_roundoff = fields.Float('FD Amount w/o round-off')
	fd_round_off = fields.Float('Round-Off')
	fd_amount = fields.Float('FD Amount', )
	fd_payment_mode = fields.Many2one('res.partner.bank', string='FD Payment Mode')
	fd_account = fields.Many2one('account.account', 'FD Account')
	fd_issue_date = fields.Date('Date of Issue FD')
	fd_number = fields.Char('FD Number')
	fd_no_of_days = fields.Float('FD No. of Days')
	fd_holder = fields.Char('FD Holder Name')
	fd_mature_value = fields.Float('FD Mature Value')
	fd_interest = fields.Float('FD Interest')
	fd_period = fields.Char('BG Duration')
	expected_bg_release_date = fields.Date('Maturity Date')
	remarks = fields.Text('Remarks')
	type_of_bond = fields.Selection([('kisan','Kisan Patra'),
									  ('national','National Service')])
	

		


		


