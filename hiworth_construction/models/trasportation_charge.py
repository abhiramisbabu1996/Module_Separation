from openerp import fields, models, api, _
import datetime, calendar
from openerp.osv import osv
from decimal import Decimal

class ViewAccount(models.Model):
	_name = 'view.account'

	rec = fields.Many2one('payment.vouchers')
	account_id = fields.Many2one('account.account','Account')
	date_from = fields.Date('From')
	date_to = fields.Date('To')

	@api.multi
	def view_data(self):
		res = {
		   'name': 'Move Lines',
			'view_type': 'form',
			'view_mode': 'tree,form',
			'res_model': 'account.move.line',
			'domain': [('date','>=',self.date_from),('date','<=',self.date_to),('account_id','=',self.account_id.id)],
			'target': 'current',
			'type': 'ir.actions.act_window',
			'context': {},

	   }

		return res


class PaymentVouchers(models.Model):
	_inherit = 'payment.vouchers'

	opp_account_balance = fields.Float(compute='compute_opp_balance', store=True, string='Balance')

	@api.multi
	def view_account_data(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_construction', 'view_account_datas')
		view_id = view_ref[1] if view_ref else False
		res = {
		   'type': 'ir.actions.act_window',
		   'name': _('View'),
		   'res_model': 'view.account',
		   'view_type': 'form',
		   'view_mode': 'form',
		   'view_id': view_id,
		   'target': 'new',
		   'context': {'default_rec':self.id,'default_account_id':self.opp_account_id.id}
	   }

		return res



	@api.onchange('receiver_id')
	def _onchange_receiver_id(self):
		if self.receiver_id:
			user = self.env['res.users'].search([('partner_id','=',self.receiver_id.id)])
			if user:
				if user.employee_id:
					self.opp_account_id = user.employee_id.payment_account.id
	@api.multi	
	@api.depends('opp_account_id')
	def compute_opp_balance(self):
		for rec in self:
			if rec.opp_account_id:
				rec.opp_account_balance = rec.opp_account_id.balance1



	@api.onchange('invoice_id')
	def _onchange_invoice_no(self):
		invoice_ids = []
		invoice_obj = self.env['hiworth.invoice'].search([('state','in',['approve','partial'])])
		invoice_ids = [invoice.id for invoice in invoice_obj]

		return {'domain': {'invoice_id': [('id','in',invoice_ids)]}}

	READONLY_STATES = {
		'post': [('readonly', True)],
		'confirm': [('readonly', True)],
		'cancel': [('readonly', True)],
	}

	invoice_id = fields.Many2one('hiworth.invoice', 'Invoice No', states=READONLY_STATES)



	@api.multi
	def action_post(self):
		if self.invoice_id:
			qty = 0
			for lines in self.env['hiworth.invoice'].search([('id','=',self.invoice_id.id)]).invoice_lines2:
				qty += lines.quantity 
			for lines in self.env['hiworth.invoice'].search([('id','=',self.invoice_id.id)]).invoice_lines2:
				transport = self.env['product.location.transport'].search([('expense_account_id','=',self.opp_account_id.id),('product_id','=',lines.product_id.id)])
				# print 'test=================1', transport
				if len(transport) == 0:
					values = {'expense_account_id': self.opp_account_id.id,
							  'product_id': lines.product_id.id,
							  'avg_trasport': lines.quantity*(self.cash_amt/qty),
							  'product_qty': lines.quantity}
					transport.create(values)
				else:
					transport.avg_trasport += lines.quantity*(self.cash_amt/qty)
					if self.invoice_id.trasport_cost_entered == False:
						transport.product_qty += lines.quantity
			self.invoice_id.trasport_cost_entered = True
		res = super(PaymentVouchers,self).action_post()
		return res

	@api.multi
	def action_cancel(self):
		if self.invoice_id:
			qty = 0
			for lines in self.env['hiworth.invoice'].browse(self.invoice_id.id).invoice_lines2:
				qty += lines.quantity
			for lines in self.env['hiworth.invoice'].browse(self.invoice_id.id).invoice_lines2:
				transport = self.env['product.location.transport'].search([('expense_account_id','=',self.opp_account_id.id),('product_id','=',lines.product_id.id)])
				# print 'test=================1', transport
				if len(transport) != 0:
					transport.avg_trasport -= lines.quantity*(self.cash_amt/qty)
					if self.invoice_id.trasport_cost_entered == True:
						transport.product_qty -= lines.quantity
			self.invoice_id.trasport_cost_entered = False

		self.move_id.button_cancel()
		self.move_id.unlink()

		for line in self.payment_invoice_ids:
			if line.bill_no.balance == line.bill_no.amount_to_be_paid:
				line.bill_no.state = 'approve'
				for invoice_line in line.bill_no.invoice_line:
					invoice_line.state = 'draft'
			if line.bill_no.balance > 0 and line.bill_no.balance < line.bill_no.amount_to_be_paid:
				line.bill_no.state = 'partial'
				for invoice_line in line.bill_no.invoice_line:
					invoice_line.state = 'partial'
		if self.payment_invoice_ids:
			for line in self.payment_invoice_ids:
				if line.tds_amount != 0.0:
					if line.bill_no.move_id:
						line.bill_no.move_id.button_cancel()
						move_line = self.env['account.move.line'].search([('move_id','=',line.bill_no.move_id.id),('account_id','=',line.bill_no.account_id.id)], limit=1)
						old_credit = move_line.credit
						move_line.credit = old_credit+line.tds_amount

						move_line = self.env['account.move.line'].search([('move_id','=',line.bill_no.move_id.id),('account_id','=',self.tds_account_id.id)], limit=1)
						move_line.unlink()
						line.bill_no.move_id.button_validate()
					if not line.bill_no.move_id:
						move_id10 = self.env['account.move'].search([('tds_id','=',line.id)])
						move_id10.button_cancel()
						move_id10.unlink()
		self.state = 'cancel'


class ProductLocationTransport(models.Model):
	_name = 'product.location.transport'

	expense_account_id = fields.Many2one('account.account', 'Expense Acc')
	product_id = fields.Many2one('product.product', 'Product')
	avg_trasport = fields.Float('Avg Unloading Cost')    
	product_qty = fields.Float('Product Qty')    
	 # = fields.Float('Avg ')

# class ProductLocationUnloading(models.Model):
#     _name = 'product.location.unloading'

#     expense_account_id = fields.Many2one('account.account', 'Expense Acc')
#     product_id = fields.Many2one('product.product', 'Product')
#     avg_trasport = fields.Float('Avg Trasportation Cost')    
#     product_qty = fields.Float('Product Qty')




class SupervisorPaymentVoucher(models.Model):
	_name = 'supervisor.payment.voucher'
	_order = "date desc"

	date = fields.Date('Date',default=fields.Date.today, required=True)
	employee_id = fields.Many2one('hr.employee', string="Cashier Name", required=True, domain="[('user_category','=','cashier')]")
	payment_ids = fields.One2many('supervisor.payment.line.approved','line_id')
	approve_ids = fields.One2many('supervisor.payment.line.approved','line_id')
	approve_ids2 = fields.One2many('supervisor.payment.line.approved','line_id')
	state = fields.Selection([('draft','Draft'),
							('send_approval','Send for approval'),
							('approved','Approved'),
							('process','Processing'),
							('partially_paid','Partially Paid'),
							('paid','Paid')
							], default="draft", string="Status")
	approve_person_id = fields.Many2one('hr.employee', string="Approved Person")
	# company_id = fields.Many2one('res.company.new', string="Company Name")

	@api.model
	def default_get(self, default_fields):
		vals = super(SupervisorPaymentVoucher, self).default_get(default_fields)
		user = self.env['res.users'].search([('id','=',self.env.user.id)])
		
		# statement = self.env['partner.daily.statement'].search([('state','=','draft'),('employee_id','=',user.employee_id.id)])
		# if statement:
		# 	raise osv.except_osv(_('Error!'),_("You have old statement to confirm."))
			
		if user:
			if user.employee_id:
				vals.update({'employee_id' : user.employee_id.id,
							 })
			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'),_("User and Employee is not linked."))

		return vals

	@api.multi
	def button_send_approval(self):
		print 'state1------', self.state
		self.state = 'send_approval'
		print 'state2------', self.approve_ids
		# for line in self.payment_ids:
		# 	self.env['supervisor.payment.line.approved'].create({
		# 							'date':self.date,
		# 							'line_id':line.line_id.id,
		# 							'supervisor_id':line.supervisor_id.id,
		# 							'requested_amount':line.requested_amount,
		# 							'approved_amount':line.requested_amount,
		# 							})
		# print 'self.payment_ids------', self.payment_ids

	@api.multi
	def button_set_to_draft(self):
		self.state = 'draft'

	@api.multi
	def approve_button(self):
		self.state = 'approved'
		user = self.env['res.users'].search([('id','=',self.env.user.id)])
		print 'user.employee_id-----------------', self.env.user.id, user.employee_id.id, user.employee_id.name
		
		if user:
			if user.employee_id:
				self.approve_person_id = user.employee_id.id
				# self.update({'approve_person_id' : user.employee_id.id,
				# 			 })
			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'),_("User and Employee is not linked."))

		
	@api.multi
	def create_payment_records(self):
		self.state = 'process'

		print 'self.approve_ids2-----------------', self.approve_ids2
		for line in self.approve_ids2:
			print 'line---------------------------------', line.payment_mode, line.is_approve
			if line.is_approve == True:
				if line.payment_mode == 'cash':
					cash = self.env['supervisor.payment.cash'].search([('line_id','=', self.id)])
					if len(cash) == 0:
						cash = self.env['supervisor.payment.cash'].create({
											'date':self.date,
											'employee_id':self.employee_id.id,
											# 'company_id':self.company_id.id,
											'line_id':self.id,
											})
					self.env['supervisor.payment.cash.line'].create({
										'cash_id':cash.id,
										'supervisor_id':line.supervisor_id.id,
										'approved_amount':line.approved_amount,
										'appr_id':line.id,
										})
				if line.payment_mode == 'bank':
					bank = self.env['supervisor.payment.bank'].search([('line_id','=', self.id)])
					if len(bank) == 0:
						bank = self.env['supervisor.payment.bank'].create({
										'date':self.date,
										'employee_id':self.employee_id.id,
										# 'company_id':self.company_id.id,
										'line_id':self.id,
										})
					print 'bank----------', bank
					self.env['supervisor.payment.bank.line'].create({
										'bank_id':bank.id,
										'supervisor_id':line.supervisor_id.id,
										'approved_amount':line.approved_amount,
										'appr_id':line.id,
										})
		# print gvhgihgijg


	@api.multi
	def view_supervisor_cash_transfer(self):
		record =  self.env['supervisor.payment.cash'].search([('line_id','=',self.id)])

		if record:
			res_id = record[0].id
		else:
			res_id = False
		res = {
			'name': 'Cash Transfer',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'supervisor.payment.cash',
			'domain': [('line_id', '=', self.id),('date','=',self.date)],
			'res_id': res_id,
			'target': 'current',
			'type': 'ir.actions.act_window',
			'context': {},

		}

		return res


	@api.multi
	def view_supervisor_bank_transfer(self):
		record =  self.env['supervisor.payment.bank'].search([('line_id','=',self.id)])

		if record:
			res_id = record[0].id
		else:
			res_id = False

		res = {
		   'name': 'Cash Transfer',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'supervisor.payment.bank',
			'domain': [('line_id', '=', self.id),('date','=',self.date)],
			'res_id': res_id,
			'target': 'current',
			'type': 'ir.actions.act_window',
			'context': {},

		}

		return res


	# @api.multi
	# def view_supervisor_request(self):
	# 	record =  self.env['supervisor.payment.voucher'].search([('id','=',self.id)])

	# 	if record:
	# 		res_id = record[0].id
	# 	else:
	# 		res_id = False
	# 	view_id = self.env.ref('hiworth_construction.view_supervisors_payment_voucher_req_form').id

	# 	res = {
	# 	   'name': 'Cash Transfer',
	# 		'view_type': 'form',
	# 		'view_mode': 'form',
	# 		'res_model': 'supervisor.payment.voucher',
	# 		'domain': [('id', '=', self.id),('date','=',self.date)],
	# 		'res_id': res_id,
	# 		'view_id': view_id,
	# 		'target': 'current',
	# 		'type': 'ir.actions.act_window',
	# 		'context': {},

	# 	}

	# 	return res



class SupervisorPaymentVoucherLine1(models.Model):
	_name = 'supervisor.payment.line.approved'
	_order = "date desc"

	date = fields.Date('Date',default=fields.Date.today)
	line_id = fields.Many2one('supervisor.payment.voucher')
	supervisor_id = fields.Many2one('hr.employee', string="Supervisor")
	requested_amount = fields.Float('Requested Amount')
	approved_amount = fields.Float('Approved Amount')
	payment_mode = fields.Selection([('cash','Cash'),
									('bank','Bank')
									], string="Mode of Payment")
	
	is_approve = fields.Boolean('Is Aproved', default=False)
	state = fields.Selection(related="line_id.state")
	payment_state = fields.Selection([('draft','Unpaid'),
							('done','Done')
							], default="draft", string="Status")


	@api.onchange('requested_amount')
	def onchange_approved_amount(self):
		print '11--------------------------------------', self.approved_amount,self.requested_amount
		self.approved_amount = self.requested_amount
		print '22--------------------------------------', self.approved_amount,self.requested_amount


class SupervisorPaymentCash(models.Model):
	_name = 'supervisor.payment.cash'
	_order = "date desc"

	@api.model
	def _default_journal(self):
		return self.env['account.journal'].search([('name','=','Cash')], limit=1)

	@api.model
	def _default_account(self):
		return self.env['account.account'].search([('name','=','Cash')], limit=1)

	date = fields.Date('Date')
	line_id = fields.Many2one('supervisor.payment.voucher')
	cash_ids = fields.One2many('supervisor.payment.cash.line','cash_id')
	employee_id = fields.Many2one('hr.employee', string="Cashier Name", domain="[('user_category','=','cashier')]")
	state = fields.Selection([('draft','Draft'),
							('partially_done','Partially Done'),
							('done','Done')
							], default="draft", string="Status")
	account_id = fields.Many2one('account.account',string='Account', default=_default_account)
	journal_id = fields.Many2one('account.journal',string='Journal', domain="[('type','in',['cash','bank'])]", default=_default_journal)
	done_person_id = fields.Many2one('hr.employee', string="Done By")
	# company_id = fields.Many2one('res.company.new', string="Company Name")
	move_id = fields.Many2one('account.move',"Move")

	@api.multi
	def view_payment_voucher(self):
		record =  self.env['supervisor.payment.voucher'].search([('id','=',self.line_id.id)])

		if record:
			res_id = record[0].id
		else:
			res_id = False
		view_id = self.env.ref('hiworth_construction.view_supervisors_payment_voucher_appr_form').id

		res = {
		   'name': 'Cash Transfer',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'supervisor.payment.voucher',
			'domain': [('id', '=', self.id),('date','=',self.date)],
			'res_id': res_id,
			'view_id': view_id,
			'target': 'current',
			'type': 'ir.actions.act_window',
			'context': {},

		}

		return res


	@api.multi
	def button_done(self):
		# self.state = 'done'
				

		amount = 0
		move = self.env['account.move']
		move_line = self.env['account.move.line']	

		for rec in self.cash_ids:
			# if rec.is_payment != True:
			# 	raise osv.except_osv(_('Error!'),_("Possible only after the payment done of all supervisors"))
			# print 'rec.is', rec.is_payment == True and rec.state
			if rec.is_payment == True and rec.state1 != 'paid':
				values = {
				'journal_id': self.journal_id.id,
				'date': self.date,
				}
				move_id = move.create(values)
				
				rec.appr_id.payment_state = 'done'	
				rec.state1 = 'paid'	
				self.state = 'partially_done'	
				if rec.supervisor_id.petty_cash_account.id == False:
					raise osv.except_osv(_('Error!'),_("There is no petty cash account for supervisor") + ' ' + rec.supervisor_id.name)

				# if len(self.env['partner.daily.statement'].sudo().search([('employee_id','=',rec.supervisor_id.id),('date','=',self.date)])) == 0:
				# 	raise osv.except_osv(_('Error!'),_("Please open a Daily Statement for accepting this transfer."))


				values2 = {
						'account_id': rec.supervisor_id.petty_cash_account.id,
						'name': 'Paid To' + ' ' + rec.supervisor_id.name,
						'debit': rec.approved_amount,
						'credit': 0,
						'move_id': move_id.id,
						}

				line_id = move_line.create(values2)
				amount += rec.approved_amount

				values = {
					'account_id': self.account_id.id,
					'name': 'Supervisor Payment',
					'debit': 0,
					'credit': rec.approved_amount,
					'move_id': move_id.id,
					}
				line_id = move_line.create(values)
				if move_id.line_id:
					move_id.button_validate()
				else:
					move_id.unlink()
				self.env['cash.confirm.transfer'].create({
					'user_id': rec.supervisor_id.id,
					'date': self.date,
					'name': self.employee_id.id,
					'amount': rec.approved_amount,
					'state': 'accepted',
					'move_id':move_id.id
				})
				self.move_id = move_id.id

		record = self.env['supervisor.payment.line.approved'].search([('line_id','=',self.line_id.id),('is_approve','=',True),('state','!=','done')])
		record1 = self.env['supervisor.payment.line.approved'].search([('line_id','=',self.line_id.id),('is_approve','=',True),('state','=','done')])
		if len(record) == 0:
			self.line_id.state = 'paid'
		if len(record) != 0 and len(record1) != 0:
			self.line_id.state = 'partially_paid'

		user = self.env['res.users'].search([('id','=',self.env.user.id)])
		
		if user:
			if user.employee_id:
				self.update({'done_person_id' : user.employee_id.id,
							 })
			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'),_("User and Employee is not linked."))

		record2 = self.env['supervisor.payment.cash.line'].search([('cash_id','=',self.id),('state1','=','draft')])
		if len(record2) == 0:
			self.state = 'done'
			self.line_id.state = 'paid'






class SupervisorPaymentCashLine(models.Model):
	_name = 'supervisor.payment.cash.line'

	cash_id = fields.Many2one('supervisor.payment.cash')
	supervisor_id = fields.Many2one('hr.employee', string="Supervisor", domain="[('user_category','=','supervisor')]")
	approved_amount = fields.Float('Approved Amount')
	is_payment = fields.Boolean('Done')
	state = fields.Selection(related="cash_id.state")
	appr_id = fields.Many2one('supervisor.payment.line.approved')
	state1 = fields.Selection([('draft','Draft'),('paid','Paid')], default="draft")


class SupervisorPaymentBank(models.Model):
	_name = 'supervisor.payment.bank'
	_order = "date desc"

	date = fields.Date('Date')
	line_id = fields.Many2one('supervisor.payment.voucher')
	bank_ids = fields.One2many('supervisor.payment.bank.line','bank_id')
	employee_id = fields.Many2one('hr.employee', string="Cashier Name", domain="[('user_category','=','cashier')]")
	state = fields.Selection([('draft','Draft'),
							('approved','Approved'),
							('partially_done','Partially Done'),
							('done','Done')
							], default="draft", string="Status")
	approve_person_id = fields.Many2one('hr.employee', string="Approved Person")
	done_person_id = fields.Many2one('hr.employee', string="Done By")
	# company_id = fields.Many2one('res.company.new', string="Company Name")
	move_id = fields.Many2one('account.move', "Move")


	@api.multi
	def button_approve(self):
		self.state = 'approved'
		user = self.env['res.users'].search([('id','=',self.env.user.id)])
		
		if user:
			if user.employee_id:
				self.update({'approve_person_id' : user.employee_id.id,
							 })
			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'),_("User and Employee is not linked."))

	@api.multi
	def button_done(self):
		
		# self.state = 'done'
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		list = []
		for rec in self.bank_ids:
			if rec.is_payment == True and not rec.bank:
				raise osv.except_osv(_('Error!'),_("There is no bank selected corresponding to") + ' ' + rec.supervisor_id.name)
			if rec.bank.id not in list:
				if rec.bank.id:
					list.append(rec.bank.id)

		for bank in list:
			amount = 0
			values =[]
			record = self.env['supervisor.payment.bank.line'].search([('bank_id','=', self.id),('bank','=',bank),('state1','!=','paid'),('is_payment','=',True)])
			for rec in record:

				rec.appr_id.payment_state = 'done'	
				rec.state1 = 'paid'	
				self.state = 'partially_done'	
				if rec.supervisor_id.petty_cash_account.id == False:
					raise osv.except_osv(_('Error!'),_("There is no petty cash account for supervisor") + ' ' + rec.supervisor_id.name)
				account_ids = [line.account_id.id for line in self.env.user.company_id.account_ids]
				cash_book = self.env['cash.book'].search(
					[('date', '=', rec.bank_id.date), ('account_id', '=', account_ids[0]),
					 ('state', '=', 'open')])
				if rec.approved_amount > 0.0:
					self.env['cash.book.line'].create({
						'cash_book_id': cash_book.id,
						'narration': 'A1-Ezy Card' + ' ' + rec.supervisor_id.name,
						'account_id': self.env['res.partner.bank'].search([('id','=',bank)]).journal_id.default_credit_account_id.id,
						# 'move_id': result.move_id.id,
						'debit': rec.approved_amount,
						'credit': rec.approved_amount,
					})

				amount += rec.approved_amount

				values.append((0,0, {
					'account_id': rec.supervisor_id.petty_cash_account.id,
					'name': 'A1-Ezy Card' + ' ' + rec.supervisor_id.name,
					'debit': rec.approved_amount,
					'credit': 0,
					}))
			if amount != 0:
				values.append((0,0,{
					'account_id': self.env['res.partner.bank'].search(
						[('id', '=', bank)]).journal_id.default_credit_account_id.id,
					'name': 'A1-From Ezy Card To Supervisor',
					'debit': 0,
					'credit': amount,
				}))
				move = self.env['account.move'].create({
					'journal_id': self.env['res.partner.bank'].search([('id','=',bank)]).journal_id.id,
					'date': self.date,
					'line_id': values,
				})
				self.env['cash.confirm.transfer'].create({
					'user_id': rec.supervisor_id.id,
					'date': self.date,
					'name': self.employee_id.id,
					'amount': rec.approved_amount,
					'state': 'accepted',
					'move_id':move.id
				})
				self.move_id = move.id
				self.env['supervisor.payment.line.approved'].search([('line_id','=',self.line_id.id),('is_approve','=',True),('payment_state','!=','done')])
			record1 = self.env['supervisor.payment.line.approved'].search([('line_id','=',self.line_id.id),('is_approve','=',True),('state','=','done')])
			if len(record) == 0:
				self.line_id.state = 'paid'
			if len(record) != 0 and len(record1) != 0:
				self.line_id.state = 'partially_paid'
		user = self.env['res.users'].search([('id','=',self.env.user.id)])
		if user:
			if user.employee_id:
				self.update({'done_person_id' : user.employee_id.id,
							 })
			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'),_("User and Employee is not linked."))

		record2 = self.env['supervisor.payment.bank.line'].search([('bank_id','=',self.id),('state1','=','draft')])
		if len(record2) == 0:
			self.state = 'done'
			self.line_id.state = 'paid'



	@api.multi
	def view_payment_voucher(self):
		record =  self.env['supervisor.payment.voucher'].search([('id','=',self.line_id.id)])

		if record:
			res_id = record[0].id
		else:
			res_id = False
		view_id = self.env.ref('hiworth_construction.view_supervisors_payment_voucher_appr_form').id

		res = {
		   'name': 'Cash Transfer',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'supervisor.payment.voucher',
			'domain': [('id', '=', self.id),('date','=',self.date)],
			'res_id': res_id,
			'view_id': view_id,
			'target': 'current',
			'type': 'ir.actions.act_window',
			'context': {},

		}

		return res


	@api.multi
	def button_add_bank(self):

		res = {
			'name': 'Add Bank',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'supervisor.payment.bank.wizard',
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_payment_id': self.id},

		}

		return res

class SupervisorPaymentwizard(models.Model):
	_name = 'supervisor.payment.bank.wizard'

	payment_id = fields.Many2one('supervisor.payment.bank') 
	bank_id = fields.Many2one('res.partner.bank', string="Bank")

	@api.multi
	def button_bank_confirm(self):
		for record in self.payment_id.bank_ids:
			if record.check_box == True:
				record.bank = self.bank_id.id
				record.check_box = False


class SupervisorPaymentLine(models.Model):
	_name = 'supervisor.payment.bank.line'


	check_box = fields.Boolean(string=".")
	bank_id = fields.Many2one('supervisor.payment.bank')
	supervisor_id = fields.Many2one('hr.employee', string="Supervisor", domain="[('user_category','=','supervisor')]")
	approved_amount = fields.Float('Approved Amount')
	bank = fields.Many2one('res.partner.bank', string='Bank')
	state = fields.Selection(related="bank_id.state")
	is_payment = fields.Boolean('Done')
	appr_id = fields.Many2one('supervisor.payment.line.approved')
	state = fields.Selection([('draft','Draft'),('paid','Paid')], default="draft")
	state1 = fields.Selection([('draft','Draft'),('paid','Paid')], default="draft")

	
