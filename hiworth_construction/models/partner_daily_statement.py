from openerp import fields, models, api
import datetime
from openerp.exceptions import Warning as UserError
from openerp.osv import osv
from openerp.tools.translate import _
from dateutil import relativedelta
from openerp.exceptions import except_orm, ValidationError
import math


class FuelTransfer1(models.Model):
	_name = 'partner.fuel.transfer'

	product_id = fields.Many2one('product.product', 'Fuel', domain=[('fuel_ok', '=', True)])
	uom_id = fields.Many2one('product.uom', 'Unit', related="product_id.uom_id")
	available_quantity = fields.Float('Available Quantity', compute="_get_available_qty", store=True)
	current_quantity = fields.Float('Current Quantity', compute="_get_current_qty", store=True)
	transfer_quantity = fields.Float('Transfer Quantity')
	site_id = fields.Many2one('stock.location', string="From Location", domain=[('usage', '=', 'internal')])
	supervisor_id = fields.Many2one('hr.employee')
	to_location_id = fields.Many2one('stock.location', string="To Location", domain=[('usage', '=', 'internal')])
	amount_per_unit = fields.Float('Amount Per Unit', )
	total_amount = fields.Float('Total Amount', compute="get_amount", store=True)
	stock_move_id = fields.Many2one('stock.move')
	account_move_id = fields.Many2one('account.move')
	machinery_id = fields.Many2one('fleet.vehicle', "Machinery")
	#state = fields.Selection([('draft', 'Draft'), ('confirm', 'Approved')], default='draft')
	daily_statement_id = fields.Many2one('partner.daily.statement')
	rent_daily_statement_id = fields.Many2one('partner.daily.statement')

	@api.multi
	def unlink(self):
		res = super(FuelTransfer1, self).unlink()
		for record in self:
			location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)

			stock_move = self.env['stock.move'].create({'name': record.product_id.name,
														'product_id': record.product_id.id,
														'product_uom_qty': record.transfer_quantity,
														'product_uom': record.uom_id.id,
														'location_id': record.site_id.id,
														'location_dest_id': location.id,
														'price_unit': record.amount_per_unit,
														'partner_stmt_id': record.daily_statement_id.id,
														# 'mach_allocation_id': record.id
														})
			stock_move.action_done()
		return res

	@api.multi
	@api.depends('product_id', 'transfer_quantity')
	def _get_current_qty(self):
		for record in self:
			if record.available_quantity > 0:
				record.current_quantity = record.available_quantity - record.transfer_quantity


	@api.multi
	def button_approve(self):
		for record in self:
			location = self.env['stock.location'].search([('usage', '=', 'inventory')], limit=1)

			stock_move = self.env['stock.move'].create({'name': record.product_id.name,
														'product_id': record.product_id.id,
														'product_uom_qty': record.transfer_quantity,
														'product_uom': record.uom_id.id,
														'location_id': record.site_id.id,
														'location_dest_id': location.id,
														'price_unit': record.amount_per_unit,
														# 'partner_stmt_id': record.transfer_id.id,
														# 'mach_allocation_id': record.id
														})
			stock_move.action_done()
			record.state = 'confirm'

	@api.multi
	@api.depends('product_id', 'site_id')
	def _get_available_qty(self):
		for record in self:
			if record.site_id:
				product = self.env['product.product'].search([('id', '=', record.product_id.id)])
				stock_history = self.env['stock.history'].search(
					[('product_id', '=', product.id), ('location_id', '=', record.site_id.id)])
				qty = 0
				for hist in stock_history:
					qty += hist.quantity
				record.available_quantity = qty

	@api.multi
	@api.depends('transfer_quantity')
	def get_amount(self):
		for record in self:
			amt = 0
			transfer_quantity = record.transfer_quantity

			record.total_amount = record.amount_per_unit * transfer_quantity

	@api.model
	def default_get(self, default_fields):
		vals = super(FuelTransfer1, self).default_get(default_fields)
		user = self.env['res.users'].search([('id', '=', self.env.user.id)])
		if user:
			if user.employee_id:
				vals.update({'supervisor_id': user.employee_id.id,
							 })
			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'), _("User and Employee is not linked."))

		return vals

	@api.onchange('transfer_quantity')
	def onchange_qty(self):
		if not self.transfer_quantity <= self.available_quantity:
			raise osv.except_osv(_('Error!'), _("You cannot transfer fuel more than available quantity."))
# TRIANGLE CUSTOM

class TodayWorks(models.Model):
	_name = 'works.today'

	project_id = fields.Many2one('pro','Products')
class PartnerReceivedItemt(models.Model):
	_name = 'items.received'

	product_id = fields.Many2one('product.product','Products')

class PartnerDailyStatement(models.Model):
	_name = 'partner.daily.statement'
	_order = 'date desc'

	@api.multi
	def load_material(self):
		# obj = goods.recieve.report
		print("function working.........")
		self.recieved_items_ids = self.details_rqrd_item.site_purchase_item_line_ids.ids


	task_id = fields.Many2one('project.task')
	# work_ids = fields.Many2many(
	# 	comodel_name="task.details", string="Work List",)


	@api.onchange('date','location_ids')
	def onchange_date_location(self):
		# print 'test========================'
		if self.date and self.location_ids:
			if self.state == 'draft':
				rec = self.env['reception.temporary'].sudo().search([('date','=',self.date),('to_id','=',self.location_ids.id)])
				# print 'recc=======================', rec
				if rec:
					line_ids = []
					for line in rec:
						# print 'sssssssss=================', line.total,line.start_km
						values = {
						'from_id2':line.from_id2.id,
						'item_expense2':line.item_expense2.id,
						'qty':line.qty,
						'rate':line.rate,
						'total':line.total,
						'voucher_no':line.voucher_no,
						'contractor_id':line.contractor_id,
						'rent':line.rent,
						'start_km':line.start_km,
						'end_km':line.end_km,
						'total_km':line.total_km,
						'vehicle_id':line.vehicle_id.id,
						'remarks':line.remarks,
						'driver_stmt_id':line.driver_stmt_id,
						'status': 'new',
						'purchase_id': line.purchase_id.id,
						'invoice_date': line.invoice_date
						}
						line_ids.append((0, False, values ))
					self.received_ids = line_ids


	@api.multi
	@api.depends('rent_vehicle_stmts')
	def get_rent_vehicle_amount(self):
		advance = 0
		for line in self.rent_vehicle_stmts:
			advance += line.advance
		self.rent_vehicle = advance




	@api.multi
	def request_approve(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_construction', 'view_request_approve_line')
		view_id = view_ref[1] if view_ref else False
		res = {
		   'type': 'ir.actions.act_window',
		   'name': _('Add Approvers'),
		   'res_model': 'approver.lines',
		   'view_type': 'form',
		  'view_mode': 'form',
		   'view_id': view_id,
		   'target': 'new',
		   'context': {'default_name':self.id}
		}

		return res


	@api.multi
	@api.depends('pre_balance','receipts')
	def compute_total(self):
		for rec in self:
			rec.total = rec.pre_balance+rec.receipts


	@api.multi
	@api.depends('total','expense','transfer_amount')
	def compute_balance(self):
		for rec in self:
			rec.balance = rec.total-rec.expense -rec.transfer_amount
			rec.theoretical_balance = rec.balance - rec.get_transferred_amount1()[0] + rec.compute_received_amount1()[0]

	@api.multi
	@api.depends('line_ids','operator_daily_stmts','rent_vehicle_stmts')
	def compute_expense(self):
		for rec in self:
			expense = 0
			expense2 = 0
			operator_expense = 0
			operator_advance = 0
			rent_vehicle = 0
			for rent_lines in rec.rent_vehicle_stmts:
				rent_vehicle += rent_lines.advance + rent_lines.other_expenses

			# print "rent_vehiclepartner..................",rec.rent_vehicle
			for lines in rec.line_ids:
				expense += lines.payment_total
			for exp_lines in rec.expense_line_ids:

				expense2 += exp_lines.expense_payment
			for mou_exp_lines in rec.mou_expense_line_ids:

				expense2 += mou_exp_lines.amount

			if rec.operator_daily_stmts:
				for exp in rec.operator_daily_stmts:
					operator_expense += exp.other_expenses
					operator_advance += exp.advance

			rec.expense = expense + expense2 + operator_expense + operator_advance + rent_vehicle
	# @api.depends('line_ids','payment_line')
	# def compute_expense(self):
	# 	for rec in self:
	# 		expense = 0
	# 		for lines in rec.line_ids:
	# 			expense += lines.payment_total
	# 		for line in rec.payment_line:
	# 			expense += line.amount
	# 		rec.expense = expense

	@api.one
	def get_transferred_amount1(self):
		records = self.env['cash.confirm.transfer'].sudo().search([('date','<=',self.date),('name','=',self.employee_id.id),('state','=','pending')])
		amount = 0
		accepting_records = self.env['cash.confirm.transfer'].sudo().search([('date','<=',self.date),('name','=',self.employee_id.id),('state','=','accepted')])
		if records:
			for line in records:
				amount += line.amount

		return amount

	@api.one
	def compute_received_amount1(self):
		rec = self.env['cash.confirm.transfer'].search([('date','<=',self.date),('user_id','=',self.employee_id.id),('state','=','pending')])
		received = 0
		accepting_records = self.env['cash.confirm.transfer'].sudo().search(
			[('date', '<=', self.date), ('name', '=', self.employee_id.id), ('state', '=', 'accepted')])
		if rec:
			for line in rec:
				received += line.amount

		return received

	@api.one
	def get_transferred_amount(self):
		records = self.env['cash.confirm.transfer'].sudo().search([('date','=',self.date),('name','=',self.employee_id.id),('state','=','accepted')])
		amount = 0
		if records:
			for line in records:
				amount += line.amount
		self.transfer_amount = amount

	@api.one
	def compute_received_amount(self):
		rec = self.env['cash.confirm.transfer'].search([('date','=',self.date),('user_id','=',self.employee_id.id),('state','=','accepted')])
		received = 0
		if rec:
			for line in rec:
				received += line.amount
		self.receipts = received

	@api.model
	def default_get(self, default_fields):
		vals = super(PartnerDailyStatement, self).default_get(default_fields)
		user = self.env['res.users'].search([('id','=',self.env.user.id)])

		# statement = self.env['partner.daily.statement'].search([('state','=','draft'),('employee_id','=',user.employee_id.id)])
		# if statement:
		# 	raise osv.except_osv(_('Error!'),_("You have old statement to confirm."))

		if user:
			if user.employee_id:

				vals.update({'employee_id' : user.employee_id.id,
							 'pre_balance':user.employee_id.petty_cash_account.balance,
							 'account_id': user.employee_id.petty_cash_account.id,

							 })

			if not user.employee_id and user.id != 1:
				raise osv.except_osv(_('Error!'),_("User and Employee is not linked."))

		return vals

	@api.depends('employee_id')
	def compute_employee_id(self):
		for rec in self:
			if rec.employee_id:
				balance = 0
				for move_lines in rec.employee_id.petty_cash_account.move_lines:
					if move_lines.date<rec.date:
						balance += move_lines.debit
						balance -= move_lines.credit

				rec.pre_balance = balance
				rec.account_id =  rec.employee_id.petty_cash_account.id

	name = fields.Char('Name')
	date = fields.Date('Date', default=datetime.date.today())
	employee_id = fields.Many2one('hr.employee', 'Supervisor')
	account_id = fields.Many2one('account.account', 'Account',compute='compute_employee_id')
	location_ids = fields.Many2one('stock.location', 'Site', domain=[('usage','=','internal')])
	line_ids = fields.One2many('partner.daily.statement.line', 'report_id', 'Lines', domain=[('expense','!=',True)])
	partner_line_ids = fields.One2many('partner.daily.statement.line', 'report_id')
	expense_line_ids = fields.One2many('partner.daily.statement.expense', 'report_id', 'Lines')
	mou_expense_line_ids = fields.One2many('partner.daily.statement.mou.line', 'report_id', 'Lines')
	pre_balance = fields.Float('Pre. Balance',compute='compute_employee_id')
	receipts = fields.Float('Receipts', compute='compute_received_amount')
	total = fields.Float(compute='compute_total', string='Total')
	expense = fields.Float(compute='compute_expense', string='Expense')
	transfer_amount = fields.Float('Transferred Amount',compute="get_transferred_amount")
	balance = fields.Float(compute='compute_balance', string='Actual Balance')
	item_usage_lines = fields.One2many('item.usage', 'report_id', string='Materials Used')
	work_details = fields.Text('Details Of Work Done At Site',required=False)
	tmrw_work_arrangement = fields.Text(required=False)
	details_rqrd_item = fields.One2many('site.purchase','site_id')
	details_received_item_ids = fields.One2many('goods.recieve.report','partner_daily_statement_id')
	state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('approved','Approved'),('checked','Checked'),('cancelled','Cancelled')],default='draft')
	received_ids = fields.One2many('daily.statement.item.received', 'received_id', 'Receptions')
	next_approver = fields.Many2one('res.users','Next Approver',readonly=True)
	approvers  = fields.One2many('supervisor.statement.approvers','approver_id',readonly=True)
	theoretical_balance = fields.Float('Theoretical Balance', compute="compute_balance")
	reception = fields.Boolean(default=False,compute="get_reception_trenafer")
	transfer = fields.Boolean(default=False,compute="get_reception_trenafer")
	rent_vehicle = fields.Float('Rent Vehicle',compute="get_rent_vehicle_amount")
	approved_by = fields.Many2one('res.users','Approved By')
	approved_sign = fields.Binary('Sign')
	checked_by = fields.Many2one('res.users','Checked By')
	checked_sign = fields.Binary('Sign')
	rent_vehicle_stmts = fields.One2many('rent.vehicle.statement','rent_id')
	operator_daily_stmts = fields.One2many('operator.daily.statement','operator_id')
	operator_daily_stmts_rent = fields.One2many('operator.daily.statement.rent','operator_id')
	machinery_fuel_collection = fields.One2many('machinery.fuel.collection','collection_id')
	machinery_fuel_allocation = fields.One2many('machinery.fuel.allocation','allocation_id')
	rent_machinery_fuel_allocation = fields.One2many('machinery.fuel.allocation', 'rent_allocation_id')
	payment_line = fields.One2many('pay.labour','labour_id')
	product_ids = fields.One2many('partner.statement.products','line_id', compute="_get_product_ids", store=True)
	fuel_transfer_ids = fields.One2many('partner.fuel.transfer','daily_statement_id')
	rent_fuel_transfer_ids = fields.One2many('partner.fuel.transfer', 'rent_daily_statement_id')
	project_id = fields.Many2one('project.project',string="Project")
	item_received_lines = fields.One2many('items.received', 'product_id', 'Materials Used')
	labour_details_ids = fields.One2many('labour.employee.details.custom', 'supervisor_statement_id')
	products_received_lines = fields.One2many('partner.received.products', 'partner_id')
	products_used_lines = fields.One2many('partner.used.products', 'partner_id')
	subcontractor_products_used_lines = fields.One2many('partner.used.products', 'partner_id')
	# project_task_ids = fields.One2many('project.task', 'partner_statement_id')
	project_task_ids = fields.One2many('task.line.custom', 'partner_statement_id')
	project_task_id = fields.Many2one('project.task')
	project_task_line_ids = fields.One2many('task.line.custom', 'partner_statement_id')
	recieved_items_ids = fields.One2many('site.purchase.item.line',string="reieved items")

	@api.onchange('project_task_id')
	def onchange_project_task_id(self):
		self.project_task_ids = False
		self.project_task_line_ids = False
		project_task_ids = []
		project_task_line_ids = []
		if self.project_task_id:
			statements_ids = self.project_task_id.task_line_ids
			for statement in statements_ids:
				values_dict = statement.read()
				if 'project_task_id' in values_dict[0]:
					values_dict[0]['project_task_id'] = False
					project_task_line_ids.append((0,0,values_dict[0]))
				# self.write({'project_task_line_ids': [(0,0,values_dict[0])]})
				if statement.subcontractor:
					project_task_ids.append((0, 0, values_dict[0]))
		self.update({'project_task_line_ids': project_task_line_ids})
		self.update({'project_task_ids': project_task_ids})
		self.update({'partner_line_ids':project_task_line_ids})


					# new_subcontractor_line = self.env['task.line'].create(values_dict[0])
					# project_task_ids += new_subcontractor_line.ids
				# new_task_line = self.env['task.line'].create(values_dict[0])

			# if statements_ids:
			# 	new_partner_line_ids = statements_ids.copy()
			# 	project_task_line_ids += new_partner_line_ids.ids
			# self.project_task_line_ids = project_task_line_ids
			# 	if statement.subcontractor:
			# 		new_subcontractor_line = statement.copy()
			# 		project_task_ids += new_subcontractor_line
			# self.project_task_ids = project_task_ids

		return

	@api.onchange('project_id','location_ids')
	def onchange_partner_line_ids(self):
		self.partner_line_ids = False
		partner_line_ids = []
		for rec in self:
			if rec.project_id and rec.location_ids:
				statements_ids = self.search([('project_id', '=', rec.project_id.id),('location_ids', '=', rec.location_ids.id)])
				for statement in statements_ids:
					new_partner_line_ids = statement.partner_line_ids.copy()
					partner_line_ids += new_partner_line_ids.ids
				rec.partner_line_ids = partner_line_ids

	@api.onchange('project_id')
	def onchange_project(self):
		self.project_task_id = False
		self.location_ids = False
		if self.project_id:
			return {
			'domain': {
				'project_task_id': [('project_id', '=', self.project_id.id)],
				'location_ids': [('id', 'in', self.project_id.project_location_ids.ids)],
			},
		}



	# @api.onchange('location_ids')
	# def _onchange_date(self):
	# 	for recor in self:
	# 		result = []
	# 		obj = self.env['purchase.order'].search([('location_id','=',self.location_ids.id)])
	# 		print("00000000000")
	# 		print("objjjj",obj)
	# 		for record in obj:
	# 			for line in record.order_line:
	# 				print("11111111111")
	# 				val={
	# 					'product_id':line.product_id.id
	# 				}
	# 				result.append((val))
	#
	# 		print("dict values are",result)
	# 		for ite in result:
	# 			self.item_received_lines = ite
	# 		# obj2 = self.env['items.received'].browse()
	# 		# obj2.write(result)
	# 		# self.update({'item_received_lines': result})
	# 		print("updated.............................................")




	# @api.multi
	# @api.depends('location_ids','project_id')
	# def _onchange_location(self):
	# 	for rec in self:
	# 		lines = [{5,0,0}]
	# 		obj = self.env['purchase.order'].search([('project_id','=',self.project_id),
	# 												 ('location_id','=',self.location_ids),('date_order','=',self.date)])
	# 		for item in obj:
	# 			vals = {
	#
	# 			}

	@api.multi
	@api.depends('location_ids')
	def _get_product_ids(self):
		for record in self:

			list = []
			config = self.env['general.product.configuration'].search([], limit=1)
			for config_id in config.product_ids:
				qty = 0
				print '-------', config_id.product_id.id, record.location_ids.id
				# qty = self.env['location.product.quant'].search([('location_id','=', self.location_ids.id),('product_id','=', config_id.product_id.id)], limit=1).qty


				if record.location_ids:
					product = self.env['product.product'].search([('id','=',config_id.product_id.id)])
					qty = product.with_context({'location' : record.location_ids.id}).qty_available
					print 'qty----------------------------------------------------', qty
				list.append((0, 0, {'product_id':config_id.product_id.id,
									'quantity':qty,
									}))
			# vals.update({'product_ids': list})
			record.product_ids = list



	@api.multi
	def set_draft(self):
		self.state = 'draft'

	@api.multi
	def cancel_entry(self):
		if self.state !='confirmed':
			records = self.env['account.move'].search([('partner_stmt_id','=',self.id)])
			if records:
				for rec in records:
					rec.button_cancel()
					rec.unlink()
			expenses = self.env['expense.book.line'].search([('statement_id', '=', self.id)])
			if expenses:
				for exp in expenses:
					exp.unlink()
		stock_move = self.env['stock.move'].search([('partner_stmt_id','=',self.id)])
		print 'stock_move-------------------------------------', stock_move
		for move in stock_move:
			print 'move---------------------', move
			move.state = 'draft'
			move.unlink()

		self.state = 'cancelled'


	@api.multi
	def check_entry(self):
		employee = self.env['hr.employee'].search([('id','=',1)])
		self.checked_by = self.env.user.id
		self.checked_sign = self.env.user.employee_id.sign if self.env.user.id !=1 else employee.sign
		self.state = 'checked'


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


	@api.multi
	def action_confirm(self):
		duplicate = self.env['partner.daily.statement'].search([('id','!=',self.id),('date','=',self.date),('employee_id','!=',self.employee_id.id),('location_ids','=',self.location_ids.id)])
		if duplicate:
			record = []
			for lines in self.line_ids:
				record.append(lines.account_id.id)
			for line in duplicate:
				for account in line.line_ids:
					if account.account_id.id in record:
						raise except_orm(_('Warning'),_('Duplicate Records In The Same Date..'))

		# if self.theoretical_balance != self.balance:
		# 	raise except_orm(_('Warning'),_('Actual Balance And Theoretical Balance Must Be Same'))

		for line in self.products_used_lines:
			location = self.env['stock.location'].search([('usage', '=', 'customer')], limit=1).id
			move_out = self.env['stock.move'].create({'name': line.product_id.id,
													  'product_id': line.product_id.id,
													  'product_uom_qty': line.used_qty,
													  'product_uom': line.product_id.uom_id.id,
													  'location_id': line.partner_id.location_ids.id,
													  'location_dest_id': location,
													  'partner_stmt_id': line.partner_id.id
													  })
			move_out.action_done()


		for lines in self.received_ids:
			lines.recept_temp.unlink()
			driver_statement = lines.sudo().driver_stmt_id
			purchase = driver_statement.purchase_id
			pick_ids = []
			pick_ids += [picking.id for picking in purchase.picking_ids]

			###################################
			picking = pick_ids and pick_ids[0] or False

			picking = self.sudo().env['stock.picking'].browse(picking)
			picking.date_done = datetime.datetime.now()
			picking.sudo().approve_picking()

			values = {
				'picking_id':picking.id,
				}
			transfer = self.env['stock.transfer_details'].sudo().create(values)
			items = []
			packs = []
			if not picking.pack_operation_ids:
				picking.sudo().do_prepare_partial()
			for op in picking.sudo().pack_operation_ids:
				if op.product_id.id == lines.item_expense2.id:
					item = {
						'packop_id': op.id,
						'product_id': op.product_id.id,
						'product_uom_id': op.product_uom_id.id,
						'quantity': lines.qty,
						'price_unit': op.cost,
						'package_id': op.package_id.id,
						'lot_id': op.lot_id.id,
						'sourceloc_id': op.location_id.id,
						'destinationloc_id': op.location_dest_id.id,
						'result_package_id': op.result_package_id.id,
						'date': op.date,
						'owner_id': op.owner_id.id,
					}
					stock_move = self.env['stock.move'].sudo().search([('picking_id','=',op.picking_id.id),('product_id','=',op.product_id.id)], limit=1)
					# stock_move = self.env['stock.move'].browse(stock_move)
					item['price_unit'] = lines.rate
					item['transfer_id'] = transfer.id
					if op.product_id:
						items.append(item)
					elif op.package_id:
						packs.append(item)

			self.env['stock.transfer_details_items'].sudo().create(items[0])


			# transfer.write({'item_ids': (6, 0,  items)})
			# print 'packop wwww=================',picking.state
			transfer.sudo().do_detailed_transfer()
			# print 'packop_ids=================',packs, picking.state
			purchase.partner_ref = lines.voucher_no
			purchase.invoice_date = lines.invoice_date
			purcahse_order_line = self.sudo().env['purchase.order.line'].search([('order_id','=',purchase.id),('product_id','=',lines.item_expense2.id)])
			# print 'site_purchase_id============', purcahse_order_line.site_purchase_id
			site_purchase_id = purcahse_order_line.site_purchase_id
			site_purchase_id.invoice_date = lines.invoice_date
			site_purchase_id.invoice_no = lines.voucher_no
			# res.update(item_ids=items)
			# res.update(packop_ids=packs)
			# if purchase:
			# 	values1 = {
			# 			'source_location_id':purchase.picking_type_id.default_location_src_id.id
			# 			'date_done':datetime.datetime.now()
			# 			'date':datetime.datetime.now()
			# 			'min_date':datetime.datetime.now()
			# 			'origin':purchase.name
			# 		}
			# 	picking = self.env['stock.picking'].create(values1)
			# 	values2 = {
			# 			'product_id':driver_statement.item_expense2.id,
			# 			'product_uom_qty':driver_statement.qty
			# 			'price_unit':driver_statement.rate
			# 			'location_dest_id':purchase.location_id.id
			# 			'location_id':purchase.picking_type_id.default_location_src_id.id
			# 			'picking_id':picking.id
			# 	}
			# 	stock_move =
		# print 'gggg============================'
		self.state = 'confirmed'

		for line in self.item_usage_lines:
			if line.receipts != 0:
				location = self.env['stock.location'].search([('usage','=','supplier')], limit=1).id
				move_in = self.env['stock.move'].create({'name':line.product_id.id,
														'product_id':line.product_id.id,
														'product_uom_qty':line.receipts,
														'product_uom':line.product_id.uom_id.id,
														'location_id':location,
														'location_dest_id':line.report_id.location_ids.id,
														# 'picking_id': line.id
														})
				move_in.action_done()

				if self.project_id:
					for task in self.project_id.task_ids:
						for usage in task.usage_ids1:
							if usage.pro_id.id == line.product_id.id:
								usage.qty_assigned = line.receipts

			if line.usage != 0:
				location = self.env['stock.location'].search([('usage','=','customer')], limit=1).id
				move_out = self.env['stock.move'].create({'name':line.product_id.id,
														'product_id':line.product_id.id,
														'product_uom_qty':line.usage,
														'product_uom':line.product_id.uom_id.id,
														'location_id':line.report_id.location_ids.id,
														'location_dest_id':location,
														# 'picking_id': line.id
														})
				move_out.action_done()
				if self.project_id:
					for task in self.project_id.task_ids:
						for usage in task.usage_ids1:
							if usage.pro_id.id == line.product_id.id:
								usage.qty_used = line.usage


		for collect_id in self.machinery_fuel_collection:
			location =  self.env['stock.location'].search([('usage','=', 'supplier')], limit=1)

			stock_move = self.env['stock.move'].create({'name':collect_id.product_id.id,
													'product_id':collect_id.product_id.id,
													'product_uom_qty':collect_id.quantity,
													'product_uom':collect_id.uom_id.id,
													'location_id':location.id,
													'location_dest_id':collect_id.site_id.id,
													'price_unit': collect_id.amount_per_unit,
													'partner_stmt_id': collect_id.collection_id.id,
													'mach_collection_id': collect_id.id
													})
			stock_move.action_done()

		for alloc_id in self.machinery_fuel_allocation:
			location =  self.env['stock.location'].search([('name','=', 'Product Consumed'),('usage','=', 'inventory')], limit=1)

			stock_move = self.env['stock.move'].create({'name':alloc_id.product_id.id,
													'product_id':alloc_id.product_id.id,
													'product_uom_qty':alloc_id.quantity,
													'product_uom':alloc_id.uom_id.id,
													'location_id':alloc_id.site_id.id,
													'location_dest_id':location.id,
													'partner_stmt_id': alloc_id.allocation_id.id,
													'mach_allocation_id': alloc_id.id
													})
			stock_move.action_done()




		for received in self.details_received_item_ids:
			location_supplier = self.env['stock.location'].search([('usage','=','supplier')])
			stock = self.env['stock.picking'].create({
				'request_id': received.site_purchase_id.id,
				'source_location_id': location_supplier.id,
				'partner_id': received.expected_supplier.id,
				'site': received.site.id,
				'order_date': received.order_date,
				'account_id': received.expected_supplier.property_account_payable.id,
				'supervisor_id': received.site_purchase_id.supervisor_id.id,
				'is_purchase': True,
			})
			for received_item in received.goods_receive_report_line_ids:
				stock_move = self.env['stock.move'].create({'name': received_item.item_id.name,
															'product_id': received_item.item_id.id,
															'product_uom_qty': received_item.received_qty,
															'product_uom': received_item.unit.id,
															'location_id': location_supplier.id,
															'location_dest_id': received.site.id,
															'partner_stmt_id': received.partner_daily_statement_id.id,
															'picking_id':stock.id

															})
				stock_move.action_done()
			stock.action_done()

		for daily_line in self.line_ids:
			for particular in daily_line.particular_ids:
				employee = self.env['hr.employee'].search([('labour_accnt','=',particular.account_id.id)])
				if employee:
					attendance = self.env['hiworth.hr.attendance'].search([('name','=',employee.id),('date','=',self.date)])
					if not attendance:
						self.env['hiworth.hr.attendance'].create({'name':employee.id,
																  'date':self.date,
																  'labour':True,
																  'labour_category_account_id':particular.account_id.id,
																  'attendance':'full'})
				else:
					raise osv.except_osv(_('Warning!'), _("Please Configure Employee with this account %s"%(particular.account_id.name)))
		for operator_line in self.operator_daily_stmts:
			attendance = self.env['hiworth.hr.attendance'].search(
				[('name', '=', operator_line.employee_id.id), ('date', '=', self.date)])
			if not attendance:
				self.env['hiworth.hr.attendance'].create({'name': operator_line.employee_id.id,
														  'date': self.date,
														  'attendance_category':operator_line.employee_id.attendance_category,
														  'attendance': 'full'})

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
		   'context': {'default_name':self.employee_id.id}
		}

		return res

	@api.multi
	def view_transfer(self):
		for rec in self:

			res = {
			   'name': 'Cash Transferred',
				'view_type': 'form',
				'view_mode': 'tree,form',
				'res_model': 'cash.confirm.transfer',
				'domain': [('name', '=', rec.employee_id.id)],
				'target': 'current',
				'type': 'ir.actions.act_window',
				'context': {},

			}

		return res

	@api.multi
	def view_receipt(self):
		for rec in self:
			cash = self.env['cash.confirm.transfer'].search([('user_id', '=', rec.employee_id.id)])

			res = {
			   'name': 'Cash Transferred',
				'view_type': 'form',
				'view_mode': 'tree,form',
				'res_model': 'cash.confirm.transfer',
				'domain': [('id', 'in', cash.ids)],
				'target': 'current',
				'type': 'ir.actions.act_window',
				'context': {},

			}

		return res



	@api.multi
	def approve_entry(self):
		move_line = self.env['account.move.line']
		move = self.env['account.move']
		journal = self.env['account.journal'].sudo().search([('name','=','CASH')])
		if not journal:
			pass
			# raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
		if len(journal) > 1:
			raise except_orm(_('Warning'),_('Multiple Journal with same name Miscellaneous Journal'))
		for rec in self:
			values = {
					'journal_id': journal.id,
					'date': self.date,
					'partner_stmt_id':rec.id,
					'copy_to_expense': True
					}

			# Particulars line

			if rec.line_ids:
				# move_id = move.create(values)
				total_particulars = 0.0
				for line in rec.line_ids:
					if line.mason_lines:
						move = self.env['account.move'].create(values)
						total = 0
						for mason_lines in line.mason_lines:
							total += mason_lines.total
						if total != 0:
							values1 = {
									'account_id': line.account_id.id,
									'name': 'Mason Kooli',
									'debit': 0,
									'state': 'valid',
									'journal_id': journal.id,
									'period_id': move.period_id.id,
									'credit': total,
									'move_id': move.id,
									}
							print 'values1--------------------', values1
							line_id1 = move_line.create(values1)
							values2 = {
									'account_id': line.report_id.location_ids.related_account.id,
									'name': 'Mason Kooli',
									'debit': total,
									'state': 'valid',
									'journal_id': journal.id,
									'period_id': move.period_id.id,
									'credit': 0,
									'move_id': move.id,
									}
							line_id2 = move_line.create(values2)
							print "vallues 2", values2
						if line.payment != 0:
							total_particulars += line.payment
							values3 = {
									'account_id': line.report_id.employee_id.petty_cash_account.id,
									'name': 'Mason Kooli',
									'debit': 0,
									'state': 'valid',
									'period_id': move.period_id.id,
									'journal_id': journal.id,
									'credit': line.payment,
									'move_id': move.id,
									}
							line_id3 = move_line.create(values3)
							print "vallues 3",values3
							values4 = {
									'account_id': line.account_id.id,
									'name': 'Mason Kooli',
									'debit': line.payment,
									'state': 'valid',
									'period_id': move.period_id.id,
									'journal_id': journal.id,
									'credit': 0,
									'move_id': move.id,
									}
							line_id4 = move_line.create(values4)
							print "vallues 4", values4

							move.button_validate()
							# move.state = 'posted'


					if line.particular_ids:
						move = self.env['account.move'].create(values)
						total = 0
						payment = 0
						for particular_lines in line.particular_ids:
							total += particular_lines.total
							payment += particular_lines.payment
							total_particulars += particular_lines.payment
							values1 = {
									'account_id': particular_lines.account_id.id,
									'name': 'Narration',
									'state': 'valid',
									'journal_id': journal.id,
									'period_id': move.period_id.id,
									'credit': particular_lines.total,
									'debit': 0,
									'move_id': move.id,
									}
							line_id1 = move_line.create(values1)

							print "particular_lines vallues 1", values1

							values4 = {
								'account_id': particular_lines.account_id.id,
								'name': 'Narration',
								'state': 'valid',
								'period_id': move.period_id.id,
								'journal_id': journal.id,
								'credit': 0,
								'debit': particular_lines.payment,
								'move_id': move.id,
								}
							print "particular_lines vallues 4", values4
							line_id4 = move_line.create(values4)

						values2 = {
								'account_id': line.report_id.location_ids.related_account.id,
								'name': 'Narration',
								'state': 'valid',
								'journal_id': journal.id,
								'period_id': move.period_id.id,
								'credit': 0,
								'debit': total,
								'move_id': move.id,
								}
						print "particular_lines vallues 2", values2
						line_id2 = move_line.create(values2)

						values3 = {
								'account_id': line.report_id.employee_id.petty_cash_account.id,
								'name': 'Narration',
								'state': 'valid',
								'period_id': move.period_id.id,
								'journal_id': journal.id,
								'credit': payment,
								'debit': 0,
								'move_id': move.id,
								}
						print "particular_lines vallues 3", values3
						line_id3 = move_line.create(values3)
						move.button_validate()
						# move.state = 'posted'
				expense_book = self.env['expense.book'].search(
					[('date', '=', rec.date), ('state', '=', 'open')])
				if total_particulars > 0.0:
					self.env['expense.book.line'].create({
						'expense_book_id': expense_book.id,
						'narration': "Labour Expenses",
						'statement_id': self.id,
						'account_id': rec.location_ids.related_account.id,
						'debit': 0.0,
						'date': self.date,
						'location_ids':self.location_ids.id,
						'credit': total_particulars,
					})
			# Rent vehicle line

			for rent_line in rec.rent_vehicle_stmts:
				# if rent_line.direct_crusher ==  True:
				# 	if not self.env.user.company_id.gst_account_id:
				# 		raise osv.except_osv(_('Error!'),_("Please enter companys GST account"))
				if rent_line.advance != 0:
					if not rec.employee_id.petty_cash_account:
						raise except_orm(_('Warning'),_('You Have To Configure Supervisor Petty Account..!!'))
					if not rent_line.vehicle_no.vehicle_under.property_account_payable:
						raise except_orm(_('Warning'),_('You Have To Configure Payable Account of Rent Vehicle Owner..!!'))
					advance_move = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
					move_line.create({
								'move_id':advance_move.id,
								'state': 'valid',
								'name': 'Advance Rent Vehicle',
								'account_id':rent_line.vehicle_no.vehicle_under.property_account_payable.id,
								'journal_id': journal.id,
								'period_id' : advance_move.period_id.id,
								'debit':rent_line.advance,
								'credit':0,
								})
					expense_book = self.env['expense.book'].search(
						[('date', '=', rec.date), ('state', '=', 'open')])
					self.env['expense.book.line'].create({
						'expense_book_id': expense_book.id,
						'narration': "Labour Expenses",
						'account_id': rent_line.vehicle_owner.property_account_payable.id,
						'debit': 0.0,
						'statement_id': self.id,
						'date': self.date,
						'location_ids':self.location_ids.id,
						'credit': rent_line.advance,
					})
					move_line.create({
								'move_id':advance_move.id,
								'state': 'valid',
								'name': 'Advance Rent Vehicle',
								'account_id':rec.employee_id.petty_cash_account.id,
								'journal_id': journal.id,
								'period_id' : advance_move.period_id.id,
								'debit':0,
								'credit':rent_line.advance,
									})
					advance_move.button_validate()
					# advance_move.state = 'posted'
				if rent_line.other_expenses != 0:
					if not rec.employee_id.petty_cash_account:
						raise except_orm(_('Warning'),_('You Have To Configure Supervisor Petty Account..!!'))
					if not rent_line.vehicle_no.vehicle_under.property_account_payable:
						raise except_orm(_('Warning'),_('You Have To Configure Payable Account of Rent Vehicle Owner..!!'))
					other_move = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
					move_line.create({
								'move_id':other_move.id,
								'state': 'valid',
								'name': 'Other Expense Vehicle',
								'account_id':rent_line.other_account_id.id,
								'journal_id': journal.id,
								'period_id' : other_move.period_id.id,
								'debit':rent_line.other_expenses,
								'credit':0,
								})
					expense_book = self.env['expense.book'].search(
						[('date', '=', rec.date), ('state', '=', 'open')])
					self.env['expense.book.line'].create({
						'expense_book_id': expense_book.id,
						'narration': "Other Rent Vehicle Expenses",
						'account_id': rent_line.other_account_id.id,
						'debit': 0.0,
						'statement_id': self.id,
						'date': self.date,
						'location_ids':self.location_ids.id,
						'credit': rent_line.other_expenses,
					})
					move_line.create({
								'move_id':other_move.id,
								'state': 'valid',
								'name': 'Other Rent Vehicle Expenses',
								'account_id':rec.employee_id.petty_cash_account.id,
								'journal_id': journal.id,
								'period_id' : other_move.period_id.id,
								'debit':0,
								'credit':rent_line.other_expenses,
									})
					# advance_move.state = 'posted'
				if rent_line.rent:
					if not rent_line.vehicle_no.vehicle_under.property_account_payable:
						raise except_orm(_('Warning'),_('You Have To Configure Payable Account of Rent Vehicle Owner..!!'))

					rent_move = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
					move_line.create({
								'move_id':rent_move.id,
								'state': 'valid',
								'name': 'Rent Vehicle',
								'account_id':rent_line.site_id.related_account.id,
								'journal_id': journal.id,
								'period_id' : rent_move.period_id.id,
								'debit':rent_line.rent,
								'credit':0,
								})
					print "rent line ",rent_line.site_id.related_account.id
					move_line.create({
								'move_id':rent_move.id,
								'state': 'valid',
								'name': 'Rent Vehicle',
								'account_id':rent_line.vehicle_no.vehicle_under.property_account_payable.id,
								'journal_id': journal.id,
								'period_id' : rent_move.period_id.id,
								'debit':0,
								'credit':rent_line.rent,
									})
					print "rent line", rent_line.vehicle_no.vehicle_under.property_account_payable.id
					rent_move.button_validate()
					# rent_move.state = 'posted'
				if rent_line.diesel != 0:
					# fuel_taxes_ids = [i.id for i in rent_line.fuel_tax_ids]
					if rent_line.based_on == 'per_day':
						if not rent_line.diesel_pump.property_account_payable:
							raise except_orm(_('Warning'),_('You Have To Configure Payable Account of Diesel Pump..!!'))

						diesel = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
						move_line.create({
									'move_id':diesel.id,
									'state': 'valid',
									'name': 'Diesel Per Day',
									'account_id':rent_line.site_id.related_account.id,
									'journal_id': journal.id,
									'period_id' : diesel.period_id.id,
									'debit':rent_line.diesel,
									'credit':0,
									})
						print "diesel", rent_line.site_id.related_account.id
						move_line.create({
									'move_id':diesel.id,
									'state': 'valid',
									'name': 'Diesel Per Day',
									'account_id':rent_line.diesel_pump.property_account_payable.id,
									'journal_id': journal.id,
									'period_id' : diesel.period_id.id,
									'debit':0,
									'credit':rent_line.diesel,
									'fuel_line': True,
									'vehicle_id': rent_line.vehicle_no.id,
									'partner_id': rent_line.diesel_pump.id,
									'vehicle_owner': rent_line.vehicle_owner.id,
									'product_id': rent_line.fuel_item.id,

									'location_id':rent_line.site_id.id,
									'qty':rent_line.diesel_litre,
									'rate':rent_line.diesel_rate,
									'amount':rent_line.diesel,
									# 'round_off' : rent_line.fuel_round_off,
									# 'contractor_id':rent_line.contractor_id.id,
									# 'tax_ids': [(6, 0, fuel_taxes_ids)],
									'product_id': rent_line.fuel_item.id,
									'bill_no':rent_line.pump_bill_no,
									'rent_stmt_id':rent_line.id,
										})
						print "diesel line",rent_line.diesel_pump.property_account_payable.id
						diesel.button_validate()
						# diesel.state = 'posted'
					if rent_line.based_on == 'per_km':
						if not rent_line.diesel_pump.property_account_payable:
							raise except_orm(_('Warning'),_('You Have To Configure Payable Account of Diesel Pump..!!'))
						if not rent_line.vehicle_no.vehicle_under.property_account_payable:
							raise except_orm(_('Warning'),_('You Have To Configure Payable Account of Vehicle Owner..!!'))

						diesel = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
						move_line.create({
									'move_id':diesel.id,
									'state': 'valid',
									'name': 'Diesel Per Km',
									'account_id':rent_line.vehicle_no.vehicle_under.property_account_payable.id,
									'journal_id': journal.id,
									'period_id' : diesel.period_id.id,
									'debit':rent_line.diesel,
									'credit':0,
									})
						print "diesel ",rent_line.vehicle_no.vehicle_under.property_account_payable.id
						move_line.create({
									'move_id':diesel.id,
									'state': 'valid',
									'name': 'Diesel Per Km',
									'account_id':rent_line.diesel_pump.property_account_payable.id,
									'journal_id': journal.id,
									'period_id' : diesel.period_id.id,
									'debit':0,
									'credit':rent_line.diesel,
									'fuel_line': True,
									'vehicle_id': rent_line.vehicle_no.id,
									'partner_id': rent_line.diesel_pump.id,
									'vehicle_owner': rent_line.vehicle_owner.id,
									'product_id': rent_line.fuel_item.id,

									'location_id':rent_line.site_id.id,
									'qty':rent_line.diesel_litre,
									'rate':rent_line.diesel_rate,
									'amount':rent_line.diesel,
									# 'round_off' : rent_line.fuel_round_off,
									# 'contractor_id':rent_line.contractor_id.id,
									# 'tax_ids': [(6, 0, fuel_taxes_ids)],
									'product_id': rent_line.fuel_item.id,
									'bill_no':rent_line.pump_bill_no,
									'rent_stmt_id':rent_line.id,
										})
						diesel.button_validate()
						# diesel.state = 'posted'
						print "dieswel", rent_line.diesel_pump.property_account_payable.id

				taxes_ids = [i.id for i in rent_line.tax_ids]
				if rent_line.full_supply == False:
					if rent_line.direct_crusher == True:
						material_cost = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
						move_line.create({
									'move_id':material_cost.id,
									'state': 'valid',
									'name': 'Material Cost',
									'account_id':rent_line.site_id.related_account.id,
									'journal_id': journal.id,
									'period_id' : material_cost.period_id.id,
									'debit':rent_line.sub_total,
									'credit':0,
									})
						# if rent_line.tax_ids:
							# move_line.create({
							# 		'move_id':material_cost.id,
							# 		'state': 'valid',
							# 		'name': 'Tax Amount',
							# 		'account_id':self.env.user.company_id.gst_account_id.id,
							# 		'journal_id': journal.id,
							# 		'period_id' : material_cost.period_id.id,
							# 		'debit':rent_line.tax_amount,
							# 		'credit':0,
							# 		})

						if rent_line.tax_ids:
							for tax in  rent_line.tax_ids:

								if tax.child_ids:
									for lines in tax.child_ids:
										if not lines.account_collected_id:
											raise osv.except_osv(_('Warning!'),
													_('There is no account linked to the taxe.'))
										if lines.account_collected_id:
											move_line.create({'move_id':material_cost.id,
											'state': 'valid',
											'name': 'Tax Amount',
											'account_id':lines.account_collected_id.id,
											'journal_id': journal.id,
											'period_id' : material_cost.period_id.id,
											'debit':rent_line.sub_total*lines.amount,
											'credit':0,
											})
								else:
									if not tax.account_collected_id:
										raise osv.except_osv(_('Warning!'),
												_('There is no account linked to the taxes.'))
									if tax.account_collected_id:

										move_line.create({'move_id':material_cost.id,
											'state': 'valid',
											'name': 'Tax Amount',
											'account_id':tax.account_collected_id.id,
											'journal_id': journal.id,
											'period_id' : material_cost.period_id.id,
											'debit':rent_line.sub_total*tax.amount,
											'credit':0,
											})


						move_line.create({
									'move_id':material_cost.id,
									'state': 'valid',
									'name': 'Material Cost',
									'account_id':rent_line.crusher.property_account_payable.id,
									'journal_id': journal.id,
									'product_id':rent_line.item.id,
									'location_id':rent_line.site_id.id,
									'vehicle_id':rent_line.vehicle_no.id,
									'qty':rent_line.qty,
									'rent_stmt_id':rent_line.id,
									'rate':rent_line.rate,
									'crusher_line':True,
									'amount':rent_line.material_cost,
									'period_id' : material_cost.period_id.id,
									'debit':0,
									'credit':rent_line.invoice_value,
									'round_off' : rent_line.round_off,
									'contractor_id':rent_line.contractor_id.id,
									'bill_no':rent_line.bill_no,
									'tax_ids': [(6, 0, taxes_ids)],
									'rent_stmt_id':rent_line.id,
										})
						if rent_line.round_off != 0:
							if not self.env.user.company_id.write_off_account_id:
								raise osv.except_osv(_('Error!'),_("Please enter companys write off account"))
							credit = 0
							debit = 0
							if rent_line.round_off < 0:
								credit = -rent_line.round_off
							else:
								debit = rent_line.round_off
							move_line.create({
								'move_id':material_cost.id,
								'state': 'valid',
								'name': 'Round Off',
								'account_id':self.env.user.company_id.write_off_account_id.id,
								'journal_id': journal.id,
								'period_id' : material_cost.period_id.id,
								'credit':credit,
								'debit':debit,
								})
						material_cost.button_validate()
						# material_cost.state = 'posted'
					if rent_line.direct_crusher == False:
						material_cost = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
						move_line.create({
									'move_id':material_cost.id,
									'state': 'valid',
									'name': 'Material Cost',
									'account_id':rent_line.site_id.related_account.id,
									'journal_id': journal.id,
									'period_id' : material_cost.period_id.id,
									'debit':rent_line.material_cost,
									'credit':0,
									})
						move_line.create({
									'move_id':material_cost.id,
									'state': 'valid',
									'name': 'Material Cost',
									'account_id':rent_line.vehicle_no.vehicle_under.property_account_payable.id,
									'journal_id': journal.id,
									'period_id' : material_cost.period_id.id,
									'debit':0,
									'credit':rent_line.material_cost,
										})
						material_cost.button_validate()
						# material_cost.state = 'posted'
					rent_line.state = 'confirm'

				if rent_line.full_supply == True:
					if rent_line.direct_crusher == True:
						material_cost = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
						move_line.create({
									'move_id':material_cost.id,
									'state': 'valid',
									'name': 'Full Supply With Crusher Balance',
									'account_id':rent_line.vehicle_no.vehicle_under.property_account_payable.id,
									'journal_id': journal.id,
									'period_id' : material_cost.period_id.id,
									'debit':0,
									'credit':rent_line.full_cost - rent_line.material_cost,
									})
						move_line.create({
									'move_id':material_cost.id,
									'state': 'valid',
									'name': 'Full Supply With Crusher Balance',
									'account_id':rent_line.site_id.related_account.id,
									'journal_id': journal.id,
									'period_id' : material_cost.period_id.id,
									'debit':rent_line.full_cost - rent_line.material_cost,
									'credit':0,
									})

						move_line.create({
									'move_id':material_cost.id,
									'state': 'valid',
									'name': 'Full Supply With Crusher Balance',
									'account_id':rent_line.site_id.related_account.id,
									'journal_id': journal.id,
									'period_id' : material_cost.period_id.id,
									'debit':rent_line.total - rent_line.tax_amount,
									'credit':0,
									})
						# if rent_line.tax_ids:

						if rent_line.tax_ids:
							for tax in  rent_line.tax_ids:

								if tax.child_ids:
									for lines in tax.child_ids:
										if not lines.account_collected_id:
											raise osv.except_osv(_('Warning!'),
													_('There is no account linked to the taxe.'))
										if lines.account_collected_id:
											move_line.create({'move_id':material_cost.id,
											'state': 'valid',
											'name': 'Tax Amount',
											'account_id':lines.account_collected_id.id,
											'journal_id': journal.id,
											'period_id' : material_cost.period_id.id,
											'debit':rent_line.sub_total*lines.amount,
											'credit':0,
											})
								else:
									if not tax.account_collected_id:
										raise osv.except_osv(_('Warning!'),
												_('There is no account linked to the taxes.'))
									if tax.account_collected_id:

										move_line.create({'move_id':material_cost.id,
											'state': 'valid',
											'name': 'Tax Amount',
											'account_id':tax.account_collected_id.id,
											'journal_id': journal.id,
											'period_id' : material_cost.period_id.id,
											'debit':rent_line.sub_total*tax.amount,
											'credit':0,
											})
							# move_line.create({
							# 		'move_id':material_cost.id,
							# 		'state': 'valid',
							# 		'name': 'Tax Value',
							# 		'account_id':self.env.user.company_id.gst_account_id.id,
							# 		'journal_id': journal.id,
							# 		'period_id' : material_cost.period_id.id,
							# 		'debit':rent_line.tax_amount,
							# 		'credit':0,
							# 		})

						move_line.create({
									'move_id':material_cost.id,
									'state': 'valid',
									'name': 'Full Supply With Crusher Balance',
									'account_id':rent_line.crusher.property_account_payable.id,
									'journal_id': journal.id,
									'rent_stmt_id':rent_line.id,
									'period_id' : material_cost.period_id.id,
									'product_id':rent_line.item.id,
									'location_id':rent_line.site_id.id,
									'vehicle_id':rent_line.vehicle_no.id,
									'qty':rent_line.qty,
									'rate':rent_line.rate,
									'amount':rent_line.material_cost,
									'crusher_line':True,
									'debit':0,
									'credit':rent_line.invoice_value,
									'round_off' : rent_line.round_off,
									'contractor_id':rent_line.contractor_id.id,
									'bill_no':rent_line.bill_no,
									'tax_ids': [(6, 0, taxes_ids)],
										})
						if rent_line.round_off != 0:
							if not self.env.user.company_id.write_off_account_id:
								raise osv.except_osv(_('Error!'),_("Please enter companys write off account"))
							credit = 0
							debit = 0
							if rent_line.round_off < 0:
								credit = -rent_line.round_off
							else:
								debit = rent_line.round_off
							move_line.create({
								'move_id':material_cost.id,
								'state': 'valid',
								'name': 'Round Off',
								'account_id':self.env.user.company_id.write_off_account_id.id,
								'journal_id': journal.id,
								'period_id' : material_cost.period_id.id,
								'credit':credit,
								'debit':debit,
								})
						material_cost.button_validate()
						# material_cost.state = 'posted'
					if rent_line.direct_crusher == False:
						material_cost = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date})
						move_line.create({
									'move_id':material_cost.id,
									'state': 'valid',
									'name': 'Full Supply Material Cost',
									'account_id':rent_line.site_id.related_account.id,
									'journal_id': journal.id,
									'period_id' : material_cost.period_id.id,
									'debit':rent_line.full_cost,
									'credit':0,
									})
						move_line.create({
									'move_id':material_cost.id,
									'state': 'valid',
									'name': 'Full Supply Material Cost',
									'account_id':rent_line.vehicle_no.vehicle_under.property_account_payable.id,
									'journal_id': journal.id,
									'period_id' : material_cost.period_id.id,
									'debit':0,
									'credit':rent_line.full_cost,
										})
						material_cost.button_validate()
						# material_cost.state = 'posted'
					rent_line.state = 'confirm'


			#echinary operator line

			if rec.operator_daily_stmts:
				expense_book = self.env['expense.book'].search(
						[('date', '=', rec.date), ('state', '=', 'open')])
				for operator_line in rec.operator_daily_stmts:

					if not operator_line.machinery_id.related_account:
						raise osv.except_osv(_('Error!'),_("Please Configure Corresponding Machinery Account."))

					# Expense
					move_expense = self.env['account.move'].create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
					expenses = 0
					for expense_line in operator_line.expense_line:
						expenses += expense_line.payment

					move_line.create({
									'move_id':move_expense.id,
									'state': 'valid',
									'name': 'Operator Expenses',
									'account_id':operator_line.machinery_id.related_account.id,
									'journal_id': journal.id,
									'period_id' : move_expense.period_id.id,
									'debit':expenses,
									'credit':0,
									})
					self.env['expense.book.line'].create({
						'expense_book_id': expense_book.id,
						'narration': "Machinery Expense",
						'account_id': operator_line.machinery_id.related_account.id,
						'debit': 0.0,
						'statement_id': self.id,
						'date': self.date,
						'location_ids':self.location_ids.id,
						'credit': expenses,
					})
					move_line.create({
									'move_id':move_expense.id,
									'state': 'valid',
									'name': 'Operator Expenses',
									'account_id':rec.employee_id.petty_cash_account.id,
									'journal_id': journal.id,
									'period_id' : move_expense.period_id.id,
									'debit':0,
									'credit':expenses,
									})

					move_expense.button_validate()
					# move_expense.state = 'posted'

					# machinery rent

					machinery_move = self.env['account.move'].create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
					move_line.create({
									'move_id':machinery_move.id,
									'state': 'valid',
									'name': 'Machinery Rent',
									'account_id':operator_line.machinery_id.related_account.id,
									'journal_id': journal.id,
									'period_id' : machinery_move.period_id.id,
									'debit':0,
									'credit':operator_line.machinery_rent,
									})
					move_line.create({
									'move_id':machinery_move.id,
									'state': 'valid',
									'name': 'Machinery Rent',
									'account_id':rec.location_ids.related_account.id,
									'journal_id': journal.id,
									'period_id' : machinery_move.period_id.id,
									'debit':operator_line.machinery_rent,
									'credit':0,
									})
					# machinery_move.state = 'posted'
					machinery_move.button_validate()
					# operator amt
					if not operator_line.employee_id.payment_account:
						raise osv.except_osv(_('Error!'),_("Please Configure Corresponding Operator Account."))

					operator_move = self.env['account.move'].create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date':self.date,'copy_to_expense': True})
					move_line.create({
									'move_id':operator_move.id,
									'state': 'valid',
									'name': 'Operator Wage',
									'account_id':rec.location_ids.related_account.id,
									'journal_id': journal.id,
									'period_id' : operator_move.period_id.id,
									'debit':operator_line.operator_amt,
									'credit':0,
									})
					move_line.create({
									'move_id':operator_move.id,
									'state': 'valid',
									'name': 'Operator Wage',
									'account_id':operator_line.employee_id.payment_account.id,
									'journal_id': journal.id,
									'period_id' : operator_move.period_id.id,
									'debit':0,
									'credit':operator_line.operator_amt,
									})
					operator_move.button_validate()
					# operator_move.state = 'posted'

					if operator_line.advance != 0:
						if not rec.employee_id.petty_cash_account:
							raise except_orm(_('Warning'),_('You Have To Configure Supervisor Petty Account..!!'))
						if not operator_line.employee_id.payment_account:
							raise except_orm(_('Warning'),_('You Have To Configure Operator Payable Account..!!'))

						advance_move = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date': self.date,'copy_to_expense': True})
						move_line.create({
									'move_id':advance_move.id,
									'state': 'valid',
									'name': 'Operator Advance',
									'account_id':operator_line.employee_id.payment_account.id,
									'journal_id': journal.id,
									'period_id' : advance_move.period_id.id,
									'debit':operator_line.advance,
									'credit':0,
									})
						self.env['expense.book.line'].create({
							'expense_book_id': expense_book.id,
							'narration': "Operator Advance",
							'account_id': operator_line.employee_id.payment_account.id,
							'debit': 0.0,
							'statement_id': self.id,
							'date': self.date,
							'location_ids':self.location_ids.id,
							'credit': operator_line.advance,
						})
						move_line.create({
									'move_id':advance_move.id,
									'state': 'valid',
									'name': 'Operator Advance',
									'account_id':rec.employee_id.petty_cash_account.id,
									'journal_id': journal.id,
									'period_id' : advance_move.period_id.id,
									'debit':0,
									'credit':operator_line.advance,
										})
						advance_move.button_validate()
						# advance_move.state = 'posted'
# =======

			if rec.expense_line_ids:
				expense_total = 0
				expense_line_new = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date': self.date,'copy_to_expense': True})
				for expense in rec.expense_line_ids:
					expense_total += expense.total
					if expense.expense_other == True:
						account_id = self.env['account.account'].search([('name', '=', 'OTHER EXPENSES')])

						move_line.create({
							'move_id': expense_line_new.id,
							'state': 'valid',
							'name': expense.expense_char,
							'account_id': account_id.id,
							'journal_id': journal.id,
							'period_id': expense_line_new.period_id.id,
							'debit': expense.total,
							'credit': 0,
						})
					else:
						move_line.create({
									'move_id':expense_line_new.id,
									'state': 'valid',
									'name': 'Expenses',
									'account_id':expense.account_id.id,
									'journal_id': journal.id,
									'period_id' : expense_line_new.period_id.id,
									'debit':expense.total,
									'credit':0,
									})

				if expense_total != 0:
					print 'expense_total--------------------', expense_total
					values3 = {
							'move_id': expense_line_new.id,
							'state': 'valid',
							'name': 'Expenses',
							'account_id': rec.account_id.id,
							'journal_id': journal.id,
								'period_id' : expense_line_new.period_id.id,
							'debit': 0,
							'credit': expense_total,
							}
					line_id = move_line.create(values3)
					if expense_line_new.line_id:
						expense_line_new.button_validate()
					else:
						expense_line_new.unlink()
				expense_book = self.env['expense.book'].search(
					[('date', '=', rec.date), ('state', '=', 'open')])
				if expense_total > 0.0:
					self.env['expense.book.line'].create({
						'expense_book_id': expense_book.id,
						'narration': "Other Expenses",
						'account_id': rec.location_ids.related_account.id,
						'debit': 0.0,
						'statement_id': self.id,
						'date': self.date,
						'location_ids':self.location_ids.id,
						'credit': expense_total,
					})

			if rec.mou_expense_line_ids:
				expense_total = 0
				expense_line_new = move.create({'journal_id':journal.id,'partner_stmt_id':rec.id,'date': self.date,'copy_to_expense': True})
				for expense in rec.mou_expense_line_ids:
					expense_total += expense.amount
					move_line.create({
									'move_id':expense_line_new.id,
									'state': 'valid',
									'name': 'MOU Expenses',
									'account_id':expense.partner_id.property_account_payable.id,
									'journal_id': journal.id,
									'period_id' : expense_line_new.period_id.id,
									'debit':expense.amount,
									'credit':0,
									})

				if expense_total != 0:
					values3 = {
							'move_id': expense_line_new.id,
							'state': 'valid',
							'name': 'MOU Expenses',
							'account_id': rec.account_id.id,
							'journal_id': journal.id,
							'period_id' : expense_line_new.period_id.id,
							'debit': 0,
							'credit': expense_total,
							}
					line_id = move_line.create(values3)
					if expense_line_new.line_id:
						expense_line_new.button_validate()
					else:
						expense_line_new.unlink()
				expense_book = self.env['expense.book'].search(
					[('date', '=', rec.date), ('state', '=', 'open')])
				if expense_total > 0.0:
					self.env['expense.book.line'].create({
						'expense_book_id': expense_book.id,
						'narration': "MOU Expenses",
						'account_id': rec.location_ids.related_account.id,
						'debit': 0.0,
						'statement_id': self.id,
						'date': self.date,
						'location_ids':self.location_ids.id,
						'credit': expense_total,
					})

			if rec.machinery_fuel_collection:
				for collect_id in rec.machinery_fuel_collection:
					# location =  self.env['stock.location'].search([('usage','=', 'supplier')], limit=1)


					# stock_move = self.env['stock.move'].create({'name':collect_id.product_id.id,
					# 										'product_id':collect_id.product_id.id,
					# 										'product_uom_qty':collect_id.quantity,
					# 										'product_uom':collect_id.uom_id.id,
					# 										'location_id':location.id,
					# 										'location_dest_id':collect_id.site_id.id,
					# 										'price_unit': collect_id.amount_per_unit
					# 										# 'picking_id': 1
					# 										# 'picking_id': collect_id.id
					# 										})
					# stock_move.action_done()
					move_line = self.env['account.move.line']
					journal = self.env['account.journal'].sudo().search([('name','=','Miscellaneous Journal')])
					if not journal:
						pass
						# raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
					if len(journal) > 1:
						raise except_orm(_('Warning'),_('Multiple Journal with same name(Miscellaneous Journal)'))
					values = {
							'journal_id': journal.id,
							'date': collect_id.date,
							'partner_stmt_id':rec.id,
						'copy_to_expense': True
							}
					move_id = self.env['account.move'].create(values)
					values1 = {
							'account_id': collect_id.pump_id.property_account_payable.id,
							'name': 'Fuel Purchase',
							'debit': 0,
							'state': 'valid',
							'journal_id': journal.id,
							'period_id': move_id.period_id.id,
							'credit': collect_id.total_amount,
							'move_id': move_id.id,

							'fuel_line': True,
							'partner_id': collect_id.pump_id.id,
							'qty':collect_id.quantity,
							'rate':collect_id.amount_per_unit,
							'amount':collect_id.total_amount,
							'product_id': collect_id.product_id.id,
							'bill_no':collect_id.pump_bill_no,
							'mach_fuel_collection_id':collect_id.id,
							}
					move_line.create(values1)
					values2 = {
							'account_id': collect_id.site_id.related_account.id,
							'name': 'Fuel Purchase',
							'state': 'valid',
							'journal_id': journal.id,
							'period_id': move_id.period_id.id,
							'debit': collect_id.total_amount,
							'credit': 0,
							'move_id': move_id.id,
							}
					move_line.create(values2)
					move_id.button_validate()
					# move_id.state = 'posted'
					collect_id.state = 'approved'
					# collect_id.stock_move_id = stock_move.id
					collect_id.account_move_id = move_id.id




			if rec.machinery_fuel_allocation:
				for alloc_id in rec.machinery_fuel_allocation:
					# location =  self.env['stock.location'].search([('name','=', 'Product Consumed'),('usage','=', 'inventory')], limit=1)


					# stock_move = self.env['stock.move'].create({'name':alloc_id.product_id.id,
					# 										'product_id':alloc_id.product_id.id,
					# 										'product_uom_qty':alloc_id.quantity,
					# 										'product_uom':alloc_id.uom_id.id,
					# 										'location_id':alloc_id.site_id.id,
					# 										'location_dest_id':location.id,
					# 										# 'picking_id': 1
					# 										# 'picking_id': alloc_id.id
					# 										})
					# stock_move.action_done()
					move_line = self.env['account.move.line']
					journal = self.env['account.journal'].sudo().search([('name','=','Miscellaneous Journal')])
					if not journal:
						pass
						# raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
					if len(journal) > 1:
						raise except_orm(_('Warning'),_('Multiple Journal with same name(Miscellaneous Journal)'))
					values = {
							'journal_id': journal.id,
							'date': alloc_id.date,
							'partner_stmt_id':rec.id,
							'copy_to_expense': True
							}
					move_id = self.env['account.move'].create(values)
					values1 = {
							'account_id': alloc_id.site_id.related_account.id,
							'name': 'Fuel Allocation',
							'debit': 0,
							'state': 'valid',
							'journal_id': journal.id,
							'period_id': move_id.period_id.id,
							'credit': alloc_id.total_amount,
							'move_id': move_id.id,
							}
					move_line.create(values1)
					values2 = {
							'account_id': alloc_id.machinery_id.related_account.id,
							'name': 'Fuel Allocation',
							'state': 'valid',
							'journal_id': journal.id,
							'period_id': move_id.period_id.id,
							'debit': alloc_id.total_amount,
							'credit': 0,
							'move_id': move_id.id,
							}
					move_line.create(values2)
					move_id.button_validate()
					# move_id.state = 'posted'
					alloc_id.state = 'confirm'
					# alloc_id.stock_move_id = stock_move.id
					alloc_id.account_move_id = move_id.id




			if rec.fuel_transfer_ids:
				for transfer_id in rec.fuel_transfer_ids:

					move_line = self.env['account.move.line']
					journal = self.env['account.journal'].sudo().search([('name','=','Miscellaneous Journal')])
					if not journal:
						pass
						# raise except_orm(_('Warning'),_('Please Create Journal With name Miscellaneous Journal'))
					if len(journal) > 1:
						raise except_orm(_('Warning'),_('Multiple Journal with same name(Miscellaneous Journal)'))
					values = {
							'journal_id': journal.id,
							'date': transfer_id.transfer_id.date,
							'partner_stmt_id':rec.id,
							'copy_to_expense': True
							}
					move_id = self.env['account.move'].create(values)
					values1 = {
							'account_id': transfer_id.site_id.related_account.id,
							'name': 'Fuel Transfer',
							'state': 'valid',
							'journal_id': journal.id,
							'period_id': move_id.period_id.id,
							'debit': transfer_id.total_amount,
							'credit': 0,
							'move_id': move_id.id,
							}
					move_line.create(values1)
					values2 = {
							'account_id': transfer_id.to_location_id.related_account.id,
							'name': 'Fuel Transfer',
							'state': 'valid',
							'journal_id': journal.id,
							'period_id': move_id.period_id.id,
							'credit': transfer_id.total_amount,
							'debit': 0,
							'move_id': move_id.id,
							}
					move_line.create(values2)
					move_id.button_validate()
					# move_id.state = 'posted'
					# transfer_id.state = 'confirm'
					# transfer_id.stock_move_id = stock_move.id
					transfer_id.account_move_id = move_id.id



			# if rec.payment_line:
			# 	move_payment = self.env['account.move'].create({'journal_id':journal.id,'partner_stmt_id':rec.id})
			# 	for line in rec.payment_line:
			# 		raise UserError(str(rec.employee_id.petty_cash_account.id))
			# 		move_line.create({
			# 					'move_id':move_payment.id,
			# 					'state': 'valid',
			# 					'name': 'Payment',
			# 					'account_id':line.to_id.id,
			# 					'journal_id': journal.id,
			# 					'period_id' : move_payment.period_id.id,
			# 					'debit':line.amount,
			# 					'credit':0,
			# 					})
			# 		move_line.create({
			# 					'move_id':move_payment.id,
			# 					'state': 'valid',
			# 					'name': 'Payment',
			# 					'account_id':rec.employee_id.petty_cash_account.id,
			# 					'journal_id': journal.id,
			# 					'period_id' : move_payment.period_id.id,
			# 					'debit':0,
			# 					'credit':line.amount,
			# 						})
			# 	move_payment.state = 'posted'



# >>>>>>> 3f659781b8dd339503565c63805cf50fb3360343

		self.state = 'approved'
		employee = self.env['hr.employee'].search([('id','=',1)])
		self.approved_by = self.env.user.id
		self.approved_sign = self.env.user.employee_id.sign if self.env.user.id != 1 else employee.sign






	@api.model
	def create(self,vals):
		vals['name'] = self.env['ir.sequence'].next_by_code('partner.daily.statement')
		if vals.get('date'):
			if len(self.env['partner.daily.statement'].search([('employee_id','=',self.env.user.employee_id.id),('date','=',vals.get('date'))])) > 0:
					raise osv.except_osv(_('Error!'),_("Already created daily statement for today."))
		result = super(PartnerDailyStatement, self).create(vals)
		# if vals['date'] and vals['location_ids']:
		# 	if vals['state'] == 'draft':
		# 		rec = self.env['reception.temporary'].sudo().search([('date','=',vals['date']),('to_id','=',vals['location_ids'])])
		# 		if rec:
		# 			line_ids = []
		# 			for line in rec:
		# 				values = {
		# 				'from_id2':line.from_id2.id,
		# 				'item_expense2':line.item_expense2.id,
		# 				'qty':line.qty,
		# 				'rate':line.rate,
		# 				'vehicle_id':line.vehicle_id.id,
		# 				'remarks':line.remarks,
		# 				'driver_stmt_id':line.driver_stmt_id.id,
		# 				'total':line.total,
		# 				'recept_temp':line.id,
		# 				'voucher_no':line.voucher_no,
		# 				'contractor_id':line.contractor_id.id,
		# 				'rent':line.rent,
		# 				'start_km':line.start_km,
		# 				'end_km':line.end_km,
		# 				'total_km':line.total_km,
		# 				'status': 'new'
		# 				}
		# 				line_ids.append((0, False, values ))
		# 			result.received_ids = line_ids
		result.sudo().employee_id.current_location_id = self.env['partner.daily.statement'].search([('employee_id','=',result.employee_id.id)], order='date desc', limit=1).location_ids.id

		return result



	# @api.multi
	# def write(self, vals):
	# 	if vals.get('location_ids'):
	# 		latest = self.env['partner.daily.statement'].search([('employee_id','=',self.employee_id.id)], order='date desc', limit=1)
	# 		if latest.id != self.id:
	# 			self.sudo().employee_id.current_location_id = latest.location_ids.id
	# 		if latest.id == self.id:
	# 			self.sudo().employee_id.current_location_id = vals.get('location_ids')
	# 	result = super(PartnerDailyStatement, self).write(vals)
	# 	return result



class PayLabour(models.Model):
	_name = 'pay.labour'

	to_id = fields.Many2one('account.account')
	amount = fields.Float('Amount')
	labour_id = fields.Many2one('partner.daily.statement')


	@api.onchange('amount','to_id')
	def onchange_payment(self):
		if self.amount != False or self.amount != 0:
			if self.to_id:
				if self.to_id.balance1 < self.amount:
						self.amount = self.to_id.balance1
						return {
							'warning': {
								'title': 'Warning',
								'message': "You cannot give amount greater than due."
							}
							}



class ApproverLine(models.TransientModel):
	_name = 'approver.lines'

	name = fields.Many2one('partner.daily.statement')
	approver = fields.Many2one('res.users',string='Approvers')
	tick = fields.Boolean('Tick If No Other Approvers')

	@api.multi
	def next_approvers(self):
		if self.tick and self.approver:
			raise osv.except_osv(_('Error!'), _('Error: Either Tick Or Enter Next approver'))

		if self.name.next_approver.id == self.env.user.id:
			self.env['supervisor.statement.approvers'].create({'approver':self.name.next_approver.id,'status':'approved','approver_id':self.name.id,'date':fields.Datetime.now()})
		else:
			raise osv.except_osv(_('Error!'), _('Error: You Are Not The Next Approver'))
		if self.tick == True:
			self.name.state = 'approved'
		else:
			if self.approver:
				self.name.next_approver = self.approver.id
			else:
				raise osv.except_osv(_('Error!'), _('Error: Either Tick Or Enter Next approver'))
		return True


	@api.multi
	def confirm_approvers(self):
		self.name.next_approver = self.approver.id
		self.name.state = 'approve_in_progress'
		return True



class PartnerDailyStatementMouLine(models.Model):
	_name = 'partner.daily.statement.mou.line'


	@api.onchange('partner_id')
	def onchange_mou_id(self):
		for rec in self:
			if rec.partner_id:
				location_id = self._context.get('location_id')
				return {'domain':{'mou_id':[('site','=',location_id),('partner_id','=',rec.partner_id.id)]}}

	partner_id = fields.Many2one('res.partner',domain="['|','|',('is_rent_vehicle','=',True),('is_rent_mach_owner','=',True),('other_mou_supplier','=',True)]")
	mou_id = fields.Many2one('mou.mou', 'MOU')
	amount = fields.Float('Payment')
	remarks = fields.Text('Remarks')
	report_id = fields.Many2one('partner.daily.statement', 'Report')

class PartnerDailyStatementExpense(models.Model):
	_name = 'partner.daily.statement.expense'



		# return {'value': {'total': total}}
	@api.onchange('account_id')
	def onchange_account_id(self):
		for rec in self:
			if rec.account_id:
				rec.expense_char = rec.account_id.name

	@api.depends('rate','quantity')
	def compute_total(self):

		for rec in self:
			total = 0
			if rec.quantity != 0 and rec.rate !=0:
				total = int(rec.rate) * int(rec.quantity)
			rec.total = total

		# return {'value': {'total': total}}

	account_id = fields.Many2one('account.account', 'Account')
	quantity = fields.Float('Quantity')
	total = fields.Float('Total',compute='compute_total')
	rate = fields.Float('Rate')
	expense_other = fields.Boolean(String="other expense")
	expense_char = fields.Char("Expense")
	expense_payment = fields.Float("Payment")
	vr_no = fields.Char('VR No.')
	remarks = fields.Text('Remarks')
	report_id = fields.Many2one('partner.daily.statement', 'Report')
	desc = fields.Char("Description")


class PartnerDailyStatementLine(models.Model):
	_name = 'partner.daily.statement.line'


	# @api.onchange('quantity')
	# def onchange_quantity(self):
	# 	if self.quantity == 0:
	# 		self.total = 0
	# 	else:
	# 		self.total = self.rate * self.quantity


	@api.depends('rate','quantity')
	def compute_total(self):
		for rec in self:
			rec.total= int(rec.rate) * int(rec.quantity)




	# @api.onchange('total')
	# def onchange_total(self):
	# 	if self.total != 0:
	# 		if self.rate*self.quantity != self.total:
	# 			if self.rate == 0 and self.quantity != 0:
	# 				self.rate = round((self.total / self.quantity),2)
	# 			elif self.quantity == 0 and self.rate != 0:
	# 				self.quantity = round((self.total / self.rate),2)
	# 			else:
	# 				pass

	# @api.onchange('quantity','rate')
	# def onchange_qty_rate(self):
	# 	if self.quantity and self.rate:
	# 		self.total = self.quantity * self.rate
	# 	if self.quantity == 0 or self.rate == 0:
	# 		self.total = 0


	# @api.onchange('total','quantity')
	# def onchange_qty_total(self):
	# 	if self.total and self.quantity:
	# 		self.rate = self.total / self.quantity

	# @api.onchange('rate','total')
	# def onchange_rate_total(self):
	# 	if self.rate and self.total:
	# 		self.quantity = self.total / self.rate


	@api.onchange('payment')
	def onchange_payment(self):
		if self.expense != True:
			if self.payment != 0:
				print "kkkkkkkkkkkkkkkkkkkkkk",self.mason_bool
				if self.mason_bool == True:
					print "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu"
					total = 0
					for lines in self.mason_lines:
						total += (lines.qty * lines.rate)
						print "ppppppppppppppppppppppppppp",(lines.qty * lines.rate)
					print "uuuuuuuuuuuuuuuuuuuuuuuu",total
					if total < self.payment:

						return {
							'warning': {
								'title': 'Warning',
								'message': "You cannot give amount greater than due."
							}
						}

				else:
					if self.line_bool == True:
						for part in self.particular_ids:

							if part.total < part.payment:

								return {
									'warning': {
										'title': 'Warning',
										'message': "You cannot give amount greater than due."
									}
								}






	@api.multi
	@api.depends('qty_entered','particular_ids')
	def compute_qty(self):
		for rec in self:
			if rec.particular_ids:
				rec.qty += len(rec.particular_ids)
			if rec.qty_entered:
				rec.qty = rec.qty_entered

	@api.multi
	@api.depends('particular_ids','rate')
	def compute_rate_char(self):
		for rec in self:
			if rec.mason_bool == True:
				rate = ''
				for lines in rec.mason_lines:
					qyt_rount=lines.qty
					i, d = divmod(lines.qty, 1)
					if d == 0:
						qyt_rount = int(qyt_rount)
					rate = rate + ("+" if rate !='' else '')+str(qyt_rount)+"*"+ str(lines.rate)
				rec.rate_char = rate
			else:
				if rec.line_bool == True:
					rec.rate_char = str(rec.account_id.rate)
				else:
					rate1 = ''
					for lines in rec.particular_ids:
						# if lines.account_id.category_id.name == 'Labour':
							qyt_rount=lines.qty
							# rec.rep +=qyt_rount
							# rate1 = str(rec.rep)+"*"+ str(lines.rate)
							rate1 = rate1 + ("+" if rate1 !='' else '')+str(qyt_rount)+"*"+ str(lines.rate)
					rec.rate_char = rate1


			if rec.particular_ids:
				list = []
				rate_char = ''
				for line in rec.particular_ids:
					qyt_rount = line.qty

					# rec.rep +=qyt_rount
					# rate1 = str(rec.rep)+"*"+ str(lines.rate)
					print "keriyeeeeeeeeeeeeeeeeeeeeeeee",qyt_rount
					rate_char = rate_char + ("+" if rate_char != '' else '') + str(qyt_rount) + "*" + str(line.rate)

				rec.rate_char = rate_char



	@api.multi
	@api.depends('qty_entered','particular_ids','rate')
	def compute_qty_char(self):
		for rec in self:
			print "hhhhhhhhhhhhhhhhhhhhhhhh",rec.mason_bool
			if rec.mason_bool == True:
				code = ''
				for lines in rec.mason_lines:
					qyt_rount=lines.qty
					i, d = divmod(lines.qty, 1)
					if d==0:
						qyt_rount = int(qyt_rount)

					print '@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2================',qyt_rount,
					code = code +("+" if code != '' else '' )+str(qyt_rount)+ "*"+str(lines.name.code)
					rec.qty_no+=qyt_rount
					rec.qty_char = code
					print "uuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuuu",rec.qty_char




			else:

					qyt_rount=0
					for lines in rec.particular_ids:
						qyt_rount+=lines.qty

					rec.qty_no = qyt_rount
					rec.qty_char = qyt_rount


	@api.depends('payment','particular_ids',)
	def get_total_payment(self):
		for rec in self:
			if rec.particular_ids:
				for lines in rec.particular_ids:
					rec.payment_total += lines.payment
			else:
				rec.payment_total = rec.payment

	@api.multi
	@api.depends('account_id')
	def compute_category(self):
		for rec in self:
			if rec.account_id:
				rec.category_id = rec.account_id.category_id.id



	@api.onchange('account_id')
	def account_onchange(self):
		if not self.env['account.account'].search([('parent_id','=',self.account_id.id)]) and self.account_id.type == 'view':
			return {
				'warning': {
					'title': 'Warning',
					'message': "There is no accounts under this category"
				}
			}
		if self.account_id.is_mason == True:
			self.mason_bool = True
			record = []
			for lines in self.account_id.mason_line:
				record.append({'name':lines.name.id,'rate':lines.rate})
			self.mason_lines = record
		else:
			self.mason_bool = False

	@api.model
	def create(self,vals):
		res = super(PartnerDailyStatementLine, self).create(vals)
		if res.account_id.type == 'view':
			if not self.env['account.account'].search([('parent_id','=',res.account_id.id)]):
				raise osv.except_osv(_('warning!'), _("There is no accounts under this category"))

		return res

	estimation_line_id = fields.Many2one('task.line.custom')
	task_category_id = fields.Many2one("task.category.details")
	# estimation_line_id = fields.Many2one('estimation.line')
	# estimation_line_id = fields.Many2one('line.estimation')
	no_labours = fields.Integer('No of Labours')
	work_id = fields.Many2one('project.work', 'Description Of Work')
	qty_estimate = fields.Float('Quantity')
	sqft = fields.Float('Square Feet')
	unit = fields.Many2one('product.uom', 'Unit')
	duration = fields.Float('Duration(Days)')
	start_date = fields.Date('Start Date')
	finish_date = fields.Date('Finish Date')
	employee_id = fields.Many2one('hr.employee', 'Employee')
	# veh_categ_id = fields.Many2many('vehicle.category.type', string='Machinery')
	veh_categ_id = fields.Many2many('fleet.vehicle', string='Machinery')
	product_id = fields.Many2many('product.product', string='Products')
	estimate_cost = fields.Float('Estimate Cost')
	pre_qty = fields.Float('Previous Qty')
	upto_date_qty = fields.Float(store=True, string='Balance Qty')
	quantity = fields.Float(string='Work Order Qty')
	subcontractor = fields.Many2one('project.task')
	estimated_hrs = fields.Char('Time Allocated')

	qty_no=fields.Float('Total Qty',compute='compute_qty_char')
	rep = fields.Integer('Rep')
	account_id = fields.Many2one('account.account', 'Account')
	total = fields.Float('Total',compute='compute_total')
	# category_id = fields.Many2one('labour.category', 'Category')
	category_id = fields.Many2one('labour.category', compute='compute_category', store=True, string='Category')
	line_bool = fields.Boolean(default=True)
	is_labour = fields.Boolean(default=False)
	item_id = fields.Many2one('daily.statement.item', 'Item')
	qty_entered = fields.Float('Qty')
	qty = fields.Float(compute='compute_qty', store=True, string='Qty')
	qty_char = fields.Char(compute='compute_qty_char', string="Qty")
	# rate_char = fields.Char(compute='compute_amount_char', store=True, string="Rate")
	rate = fields.Float('Rate')
	rate_char = fields.Char('Rate',compute="compute_rate_char")
	expense_payment = fields.Float("Payment")
	expense_total = fields.Float("Total")
	payment = fields.Float('Payment')
	payment_total = fields.Float('Payment',compute="get_total_payment")
	vr_no = fields.Char('VR No.')
	remarks = fields.Text('Remarks')
	report_id = fields.Many2one('partner.daily.statement', 'Report')
	particular_ids = fields.One2many('statement.particular', 'line_id', 'Particulars')
	account_type = fields.Selection([
									('ie','Income/Expense'),
									('al','Asset/Liability')], 'Account Type')
	mason_bool = fields.Boolean(default=False)
	mason_lines = fields.One2many('mason.line','line_ids')
	expense = fields.Boolean(default=False)
	expense_other = fields.Boolean(String="other expense")
	expense_char = fields.Char("Expense")
	exp_account_id = fields.Many2one('account.account',"Account")
	date = fields.Date()

	sqft_completed = fields.Float(string="Sqft Completed")
	sqft_pending = fields.Float(string="Sqft Pending")
	total_attendance = fields.Integer(string="Total Attendance")
	total_absence = fields.Integer(string="Absentee")
	machines_used = fields.Many2many('fleet.vehicle',string="Machinery Used")


	# @api.onchange('date')
	# def onchange_date(self):
	# 	print("date on change working.............................")
	# 	tasks = self.env['task.line.custom'].search([('date_assigned','=',self.date)])
	# 	print("tasks are.......",tasks)
	@api.onchange('account_id','category_id')
	def onchange_account_id(self):
		if self.account_id:
			rec = self.env['account.account'].search([('parent_id','=',self.account_id.id)])
			if rec:
				self.line_bool = False
				# self.qty_entered = 0
				self.rate = 0
				self.category_id = False
			else:
				self.line_bool = True
			if self.account_id:
				self.rate = self.account_id.rate
			if self.account_id.is_labour == True:
				self.is_labour = True
			else:
				self.is_labour = False
			if self.account_id.user_type.report_type in ['income','expense']:
				self.account_type = 'ie'
			if self.account_id.user_type.report_type in ['asset','liability']:
				self.account_type = 'al'

	# @api.multi
	# def action_validate(self):
	# 	for rec in self:
	# 		print 'aaaaaaaaaaaaaaaaa'



class SupervisorStatementApprovers(models.Model):
	_name = 'supervisor.statement.approvers'

	approver_id = fields.Many2one('partner.daily.statement')
	approver = fields.Many2one('res.users','Approver')
	status = fields.Selection([('not_approved','Not Approved'),('approved','Approved')],default='not_approved',string="Approver")
	date = fields.Datetime('Date')


class OperatorDailyStatement(models.Model):
	_name = 'operator.daily.statement'

	estimation_id = fields.Many2one('estimation.estimation')
	operator_id = fields.Many2one('partner.daily.statement')
	date = fields.Date('Date')
	employee_id = fields.Many2one('hr.employee', string="Operator", domain=[('user_category','=','operators')])
	machinery_id = fields.Many2one('fleet.vehicle', string="Machinery", domain=[('machinery','=',True)])
	mou = fields.Many2one('mou.mou', 'MOU',domain="[('vehicle_number', '=', machinery_id)]")
	start_reading = fields.Float('Start Reading')
	end_reading = fields.Float('End Reading')
	working_hours = fields.Float('Working Hours', compute="compute_operator_details")
	quantity = fields.Float('Quantity',default="1")
	machinery_rent = fields.Float('Machinery Rent', compute="compute_operator_details")
	operator_amt = fields.Float('Operator Amount', compute="compute_operator_details")
	expense = fields.Float('Machinery Expense', compute="compute_total_expense")
	expense_line = fields.One2many('driver.daily.expense','expense_id')
	advance = fields.Float('Advance')
	other_expenses = fields.Float('Other Expenses')
	other_account_id = fields.Many2one('account.account', 'Other Expense Account')
	running_km = fields.Float('Running Km')




	@api.onchange('running_km','start_reading','end_reading','machinery_id')
	def onchange_readings(self):
		record = self.env['operator.daily.statement'].search([('machinery_id','=', self.machinery_id.id)], order="date desc",limit=1)
		print 'record-------------------------', record.date,record.start_reading,record.end_reading
		if record:
			if self.running_km:
				self.start_reading = record.end_reading + self.running_km
			else:
				self.start_reading = record.end_reading



	@api.onchange('quantity')
	def onchange_quantity(self):
		if self.quantity not in [0,1,1.5,2]:
			raise osv.except_osv(_('Error!'),_("The quantity given is not allowed."))

	@api.multi
	@api.depends('start_reading','end_reading','machinery_id','employee_id','quantity')
	def compute_operator_details(self):
		for record in self:
			record.working_hours = round((record.end_reading - record.start_reading),2)
			record.operator_amt = round((record.employee_id.per_day_eicher_rate * record.quantity),2)
			if record.machinery_id.mach_rent_type == 'hours':
				record.machinery_rent = round((record.machinery_id.per_day_rent * record.working_hours),2)
			else:
				record.machinery_rent = round((record.machinery_id.per_day_rent),2)


	@api.multi
	@api.depends('expense_line')
	def compute_total_expense(self):
		for record in self:
			for expense in record.expense_line:
				record.expense += expense.total

class OperatorDailyStatementRent(models.Model):
	_name = 'operator.daily.statement.rent'

	@api.onchange('employee_id')
	def onchange_mou_id(self):
		for rec in self:
			location_id = self._context.get('location_id')
			machinery_id = rec.employee_id.id
			return {'domain': {'mou': [('site', '=', location_id),('partner_id', '=', machinery_id)]}}

	operator_id = fields.Many2one('partner.daily.statement')
	date = fields.Date('Date')
	employee_id = fields.Many2one('res.partner', string="Rent Machinery Owner", domain=[('is_rent_mach_owner','=',True)])
	machinery_id = fields.Many2one('fleet.vehicle', string="Machinery", domain=[('machinery','=',True)])
	mou = fields.Many2one('mou.mou', 'MOU')
	start_reading = fields.Float('Start Reading')
	end_reading = fields.Float('End Reading')
	working_hours = fields.Float('Working Hours', compute="compute_operator_details")
	quantity = fields.Float('Quantity',default="1")
	machinery_rent = fields.Float('Machinery Rent', compute="compute_operator_details")
	operator_amt = fields.Float('Operator Amount', compute="compute_operator_details")
	expense = fields.Float('Machinery Expense', compute="compute_total_expense")
	expense_line = fields.One2many('driver.daily.expense','expense_id')
	advance = fields.Float('Advance')
	other_expenses = fields.Float('Other Expenses')
	other_account_id = fields.Many2one('account.account', 'Other Expense Account')
	running_km = fields.Float('Running Km')

	_defaults = {
		'date': date.today()
		}


	@api.onchange('running_km','start_reading','end_reading','machinery_id')
	def onchange_readings(self):
		record = self.env['operator.daily.statement'].search([('machinery_id','=', self.machinery_id.id)], order="date desc",limit=1)
		print 'record-------------------------', record.date,record.start_reading,record.end_reading
		if record:
			if self.running_km:
				self.start_reading = record.end_reading + self.running_km
			else:
				self.start_reading = record.end_reading



	@api.onchange('quantity')
	def onchange_quantity(self):
		if self.quantity not in [0,1,1.5,2]:
			raise osv.except_osv(_('Error!'),_("The quantity given is not allowed."))

	@api.multi
	@api.depends('start_reading','end_reading','machinery_id','employee_id','quantity')
	def compute_operator_details(self):
		for record in self:
			record.working_hours = round((record.end_reading - record.start_reading),2)
			record.operator_amt = round((record.mou.cost * record.quantity),2)
			if record.machinery_id.mach_rent_type == 'hours':
				record.machinery_rent = round((record.machinery_id.per_day_rent * record.working_hours),2)
			else:
				record.machinery_rent = round((record.machinery_id.per_day_rent),2)


	@api.multi
	@api.depends('expense_line')
	def compute_total_expense(self):
		for record in self:
			for expense in record.expense_line:
				record.expense += expense.total

class StatementParticular(models.Model):
	_name = 'statement.particular'

	@api.one
	def onchange_payment(self):
		if self.qty and self.rate:
			self.payment = self.qty * self.rate

	@api.multi
	@api.depends('qty','rate')
	def compute_total(self):
		for rec in self:
			if rec.qty and rec.rate:
				rec.total = rec.qty * rec.rate


	@api.onchange('payment')
	def onchange_payment(self):
		if self.payment != 0 and self.account_id.user_type.report_type in ['asset','liability']:
			if self.account_id.balance1+self.total < self.payment:
				self.payment = self.account_id.balance1+self.rate
				return {
					'warning': {
						'title': 'Warning',
						'message': "You cannot give amount greater than due."
					}
				}

	@api.multi
	@api.depends('account_id')
	def compute_rate(self):
		for rec in self:
			if rec.account_id:
				rec.rate = rec.account_id.rate

	@api.multi
	@api.depends('account_id')
	def compute_category(self):
		for rec in self:
			if rec.account_id:
				rec.category_id = rec.account_id.category_id.id


	account_id = fields.Many2one('account.account', 'Account')
	qty = fields.Float('Qty')
	payment = fields.Float('Payment')
	total = fields.Float(compute='compute_total', string="Total")
	category_id = fields.Many2one('labour.category', compute='compute_category', store=True, string='Category')
	rate = fields.Float(compute='compute_rate', store=True, string='Rate')
	line_id = fields.Many2one('partner.daily.statement.line', 'Line')


	@api.onchange("account_id")
	def onchange_accounts_id_line(self):
		# res = {}
		record = self.env['account.account'].search([('parent_id','=',self.line_id.account_id.id)])
		ids = []
		for item in record:
			ids.append(item.id)
		return {'domain': {'account_id': [('id', 'in', ids)]}}

class ItemUsage(models.Model):
	_name = 'item.usage'

	@api.multi
	@api.depends('pre_qty','receipts')
	def compute_total(self):
		for rec in self:
			rec.total = rec.pre_qty + rec.receipts

	@api.multi
	@api.depends('total','usage')
	def compute_balance(self):
		for rec in self:
			rec.balance = round((rec.total - rec.usage),2)

	estimation_id = fields.Many2one('estimation.estimation')
	product_id = fields.Many2one('product.product', 'Item')
	uom_id = fields.Many2one('product.uom', 'Item')
	pre_qty = fields.Float('Pre. Balance',readonly=True)
	receipts = fields.Float('Receipts')
	total = fields.Float(compute='compute_total', store=True, string='Total')
	usage = fields.Float('Usage')
	balance = fields.Float(compute='compute_balance', store=True, string='Balance')
	report_id = fields.Many2one('partner.daily.statement', 'Report')
	rqrd_id = fields.Many2one('partner.daily.statement', 'Required')
	rqrd_qty = fields.Float('Required Qty')
	name = fields.Char('Description')
	date = fields.Date('Date',default=fields.Date.today())
	rate = fields.Float()
	price = fields.Float()

	@api.model
	def create(self, vals):
		result = super(ItemUsage, self).create(vals)
		if result.pre_qty == 0:
			qty = 0
			if result.report_id.location_ids:
				product = self.env['product.product'].search([('id','=',result.product_id.id)])
				qty = product.with_context({'location' : result.report_id.location_ids.id}).qty_available

			# if result.product_id:
			# 	rec = self.env['stock.history'].search([('product_id','=',result.product_id.id),('location_id','=',result.report_id.location_ids.id)])
			# 	for vals in rec:
			# 		qty += vals.quantity
			# 	result.pre_qty = qty
			result.pre_qty = qty
		return result


	@api.onchange("usage")
	def onchange_usage(self):
		if self.usage:
			if self.usage > self.total:
				self.usage = self.total
				return {
							'warning': {
								'title': 'Warning',
								'message': "You cannot give usage greater than total quantity."
							}
							}

	@api.onchange("product_id")
	def onchange_pre_qty(self):
		qty = 0
		record = self.env['stock.history'].search([('location_id','=',self.report_id.location_ids.id)])
		if self.product_id:
			rec = self.env['stock.history'].search([('product_id','=',self.product_id.id),('location_id','=',self.report_id.location_ids.id)])
			for vals in rec:
				qty += vals.quantity
		self.pre_qty = qty
		list = []
		for item in record:
			list.append(item.product_id.id)
		return {'domain': {'product_id': [('id', 'in', list)]}}


class NextDayWork(models.Model):
	_name = 'next.day.work'


	name = fields.Char('Name')

class NextDayWorkItems(models.Model):
	_name = 'next.day.work.items'


	product_id = fields.Many2one('product.product')
	uom_id = fields.Many2one('product.uom', 'Item')
	qty = fields.Float('Qty')

class DailyStatementItem(models.Model):
	_name = 'daily.statement.item'

	@api.constrains('name')
	def _check_duplicate_name(self):
		names = self.search([])
		for c in names:
			if self.id != c.id:
				if self.name.lower() == c.name.lower() or self.name.lower().replace(" ", "") == c.name.lower().replace(" ", ""):
					raise osv.except_osv(_('Error!'), _('Error: name must be unique'))
			else:
				pass


	name = fields.Char('Name')
	# rate = fields.Float('Rate')


class LabourCategory(models.Model):
	_name = 'labour.category'

	name = fields.Char('Name')
	code = fields.Char('Code', size=3)
	# rate = fields.Float('Rate')

class AccountAccount(models.Model):
	_inherit = 'account.account'

	is_labour = fields.Boolean('Is Labour')
	category_id = fields.Many2one('labour.category', 'Category')


class DailyStatementItemReceived(models.Model):
	_name = 'daily.statement.item.received'

	@api.multi
	def approve_line(self):
		self.status = 'accepted'
		self.sudo().driver_stmt_id.status = 'accepted'
		self.sudo().driver_stmt_id.line_id._get_driver_status1()

	@api.multi
	def reject_line(self):
		self.status = 'rejected'
		# self.sudo().driver_stmt_id.line_id.driver_status1 = 'reject'
		self.sudo().driver_stmt_id.status = 'rejected'
		if not self.rejection_remarks:
			raise osv.except_osv(_('Error!'), _('Please enter the reason for rejection'))

		self.sudo().driver_stmt_id.rejection_remarks = self.rejection_remarks
		self.sudo().driver_stmt_id.line_id._get_driver_status1()
		# self.driver_stmt_id.line_id.cancel_entry()
		# self.driver_stmt_id.line_id.set_draft()


	name = fields.Char('Name')
	particulars = fields.Char('Particulars')
	from_id2 = fields.Many2one('res.partner','From')
	item_expense2 = fields.Many2one('product.product','Item')
	qty = fields.Float('Qty',default=1)
	rate = fields.Float('Rate')
	total = fields.Float('Total')
	vehicle_id = fields.Many2one('fleet.vehicle', 'Vehicle')
	start_km = fields.Float('Start KM')
	end_km = fields.Float('End KM')

	total_km = fields.Float('Total KM')
	# payment = fields.Float('Payment')
	voucher_no = fields.Char('Voucher No')
	contractor_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Contractor')
	rent = fields.Float('Rent')
	remarks  = fields.Char('Remarks')
	received_id = fields.Many2one('partner.daily.statement', 'Required')
	driver_stmt_id = fields.Many2one('driver.daily.statement.line')
	status = fields.Selection([('new','New'),('accepted','Accepted'),('rejected','Rejected')],readonly=True)
	recept_temp = fields.Many2one('reception.temporary')
	rejection_remarks  = fields.Text('Reason for Rejection')
	purchase_id = fields.Many2one('purchase.order', 'Purchase')
	invoice_date  = fields.Date('Invoice Date')





class GeneralFuelConfigurationWizard(models.TransientModel):
	_name = 'general.fuel.configuration.wizard'

	product_id = fields.Many2one('product.product', 'Fuel', domain=[('fuel_ok','=','True')])

	@api.model
	def default_get(self, vals):
		res = super(GeneralFuelConfigurationWizard, self).default_get(vals)
		config = self.env['general.fuel.configuration'].search([], limit=1)

		res.update({
			'product_id': config.product_id.id,
		})
		return res

	@api.multi
	def excecute(self):
		# print 'test=========================', asd
		config = self.env['general.fuel.configuration'].search([])
		for line in config:
			line.unlink()
		self.env['general.fuel.configuration'].create({'product_id': self.product_id.id,})
		return {
			'type': 'ir.actions.client',
			'tag': 'reload',
		}


	@api.multi
	def cancel(self):
		return {
			'type': 'ir.actions.client',
			'tag': 'reload',
		}



class GeneralFuelConfiguration(models.Model):
	_name = 'general.fuel.configuration'


	product_id = fields.Many2one('product.product', 'Fuel', domain=[('fuel_ok','=','True')])


class GeneralProductConfiguration(models.Model):
	_name = 'general.product.configuration'


	product_ids = fields.One2many('general.product.configuration.line','line_id')

class GeneralProductConfigurationLine(models.Model):
	_name = 'general.product.configuration.line'


	line_id = fields.Many2one('general.product.configuration')
	product_id = fields.Many2one('product.product', 'Product')



class PartnerStmtProducts(models.Model):
	_name = 'partner.statement.products'


	line_id = fields.Many2one('partner.daily.statement')
	product_id = fields.Many2one('product.product', 'Product')
	quantity = fields.Float('Quantity')


class LabourEmployeeDetails(models.Model):
	_name = 'labour.employee.details.custom'

	supervisor_id = fields.Many2one('hr.employee')
	item_id = fields.Many2one('daily.statement.item', 'Item')
	remarks = fields.Text('Remarks')
	details_ids = fields.One2many('labours.details.custom', 'labour_id')
	supervisor_statement_id = fields.Many2one('partner.daily.statement')
	start_time = fields.Datetime()
	end_time = fields.Datetime()
	mep = fields.Selection([('mechanical', 'Mechanical'), ('electricel', 'Electrical'), ('plumbing', 'Plumbing')], string="Work Category")
	site_id = fields.Many2one('stock.location',string='Site', related='supervisor_statement_id.location_ids')
	project_id = fields.Many2one('project.project', related='supervisor_statement_id.project_id')

	@api.model
	def create(self, vals):
		res = super(LabourEmployeeDetails, self).create(vals)
		if res.supervisor_id:
			lines = {'labour_name': res.supervisor_id.id,
					 'labour_id':res.id,
					 'site_id': res.site_id.id,
					 'project': res.project_id.id,
					 'end_time': res.end_time,
					'start_time':res.start_time,}
			res.details_ids.create(lines)
		return res


class LaboursDetails(models.Model):
	_name = 'labours.details.custom'

	labour_id = fields.Many2one('labour.employee.details.custom')
	labour_name = fields.Many2one('hr.employee', domain=[('attendance_category', '!=', 'office_staff')])
	remarks = fields.Text('Remarks')
	start_time = fields.Datetime()
	end_time = fields.Datetime()
	position = fields.Selection(related='labour_name.user_category')
	mep = fields.Selection([('mechanical', 'Mechanical'), ('electricel', 'Electrical'), ('plumbing', 'Plumbing')], string="Work Category")
	site_id = fields.Many2one('stock.location',string='Site', related='labour_id.site_id')
	project = fields.Many2one('project.project', related='labour_id.project_id', store=True)
	date = fields.Date(default=fields.Date.today())


class AttendanceEntryWizard(models.TransientModel):
	_name = 'attendance.entry.wizard.new'

	@api.model
	def default_get(self, default_fields):
		vals = super(AttendanceEntryWizard, self).default_get(default_fields)
		line_ids2 = []
		for line in self.env.context.get('active_ids'):
			employee = self.env['labours.details.custom'].browse(line).labour_name
			values = {
				'employee_id': employee.id,
				'attendance': 'full'
			}
			line_ids2.append((0, False, values ))
			vals['line_ids'] = line_ids2
		return vals

	date = fields.Date('Date',default=fields.Datetime.now())
	line_ids = fields.One2many('attendance.entry.wizard.line.new', 'wizard_id', 'Employees')
	user_id = fields.Many2one('res.users', 'User', default=lambda self: self.env.user)

	@api.multi
	def do_mass_update(self):
		for rec in self:
			attendance = self.env['hiworth.hr.attendance']
			for lines in rec.line_ids:
				entry = self.env['hiworth.hr.attendance'].search([('name','=',lines.employee_id.id),('date','=',rec.date)])
				print 'entry--------------------------', entry
				if len(entry) != 0:
					raise osv.except_osv(_('Warning!'), _("Already entered attendance for employee '%s'") % (lines.employee_id.name,))
				attendance_date = datetime.datetime.strptime(rec.date, "%Y-%m-%d")
				public_holiday = self.env['public.holiday'].search([('date', '=', attendance_date)])
				if public_holiday:
					raise osv.except_osv(_('Warning!'), _("It's a public holiday"))
				else:
					values = {'date': rec.date,
						  'name': lines.employee_id.id,
						  'user_id': rec.user_id.id,
						  'attendance': lines.attendance}
					attendance.create(values)


class AttendanceEntryWizardLine(models.TransientModel):
	_name = 'attendance.entry.wizard.line.new'

	employee_id = fields.Many2one('hr.employee', string='Employees', domain=[('cost_type','=','permanent')])
	attendance = fields.Selection([('full', 'Full Present'),
								('half','Half Present'),
								('absent','Absent')
								], default='full', string='Attendance')
	wizard_id = fields.Many2one('attendance.entry.wizard.new', string='Wizard')


class ReceivedProducts(models.Model):
	_name = 'partner.received.products'

	# goods_receive_report_id = fields.Many2one('goods.recieve.report', string="Goods Receive Report No")
	# goods_receive_report_line_id = fields.Many2one('goods.recieve.report.line', string="Product", _rec_name="item_id")
	po_no = fields.Many2one('purchase.order', string="Purchase Order")
	stock_transfer_id = fields.Char()
	type_of_good_transfer = fields.Selection([
		('store_to_site', 'Store to site'), ('site_to_site', 'Site to Site'), ('other_stock_move', 'Other stock Move'),
		('goods_receive_through_po', 'Goods received through Purchase Order')])
	unit = fields.Many2one('product.uom', readonly=True)
	stock_qty = fields.Float(readonly=True, compute="compute_quantity", store=True)
	product_id = fields.Many2one('product.product')
	po_qty = fields.Float()
	received_qty = fields.Float()
	vehicle_id = fields.Many2one('fleet.vehicle')
	partner_id = fields.Many2one('partner.daily.statement')
	bill_no = fields.Char()

	@api.onchange('product_id')
	def onchange_product_id(self):
		for record in self:
			if record.product_id:
				record.unit = record.product_id.uom_id.id
			if record.product_id and record.partner_id.location_ids:
				current_qty = sum(self.env['stock.quant'].search([('product_id', '=', record.product_id.id),
																  ('location_id', '=',
																   record.partner_id.location_ids.id)]).mapped('qty'))
				record.stock_qty = current_qty

	@api.depends('product_id')
	def compute_quantity(self):
		for record in self:
			if record.product_id and record.partner_id.location_ids:
				current_qty = sum(self.env['stock.quant'].search([('product_id', '=', record.product_id.id),
																  ('location_id', '=',
																   record.partner_id.location_ids.id)]).mapped('qty'))
				record.stock_qty = current_qty


class UsedProducts(models.Model):
	_name = 'partner.used.products'

	product_id = fields.Many2one('product.product')
	stock_qty = fields.Float(readonly=True, compute="compute_quantity", store=True)
	used_qty = fields.Float()
	balance_qty = fields.Float(readonly=True, compute="compute_quantity", store=True)
	unit = fields.Many2one('product.uom', readonly=True)
	partner_id = fields.Many2one('partner.daily.statement')

	@api.onchange('product_id', 'used_qty')
	def onchange_product_id(self):
		for record in self:
			if record.product_id:
				record.unit = record.product_id.uom_id.id
			if record.product_id and record.partner_id.location_ids:
				current_qty = sum(self.env['stock.quant'].search([('product_id', '=', record.product_id.id),
																  ('location_id', '=',
																   record.partner_id.location_ids.id)]).mapped('qty'))
				record.stock_qty = current_qty
				if record.used_qty:
					if record.stock_qty < record.used_qty:
						raise osv.except_osv(('Warning!'),
											 ('%s stock quantity is less than used quantity' % record.product_id.name))
					record.balance_qty = record.stock_qty - record.used_qty

	@api.depends('product_id', 'used_qty')
	def compute_quantity(self):
		for record in self:
			if record.product_id and record.partner_id.location_ids:
				current_qty = sum(self.env['stock.quant'].search([('product_id', '=', record.product_id.id),
																  ('location_id', '=',
																   record.partner_id.location_ids.id)]).mapped('qty'))
				record.stock_qty = current_qty
				if record.used_qty:
					if record.stock_qty < record.used_qty:
						raise osv.except_osv(('Warning!'),
											 ('%s stock quantity is less than used quantity' % record.product_id.name))
					record.balance_qty = record.stock_qty - record.used_qty

	@api.multi
	def unlink(self, cr, uid, ids, context=None):
		for rec in self:
			if rec.partner_id.state != 'draft':
				raise osv.except_osv(('Warning!'), ('Records in the %s state cannot be deleted' % rec.partner_id.state))
			super(UsedProducts, self).unlink(cr, uid, ids, context)


class SubcontractorDailywork(models.Model):
	_name="subcontractor.daily.work"


