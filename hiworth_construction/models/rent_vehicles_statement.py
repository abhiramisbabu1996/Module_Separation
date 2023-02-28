from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
from openerp.osv import osv

class RentVehicleInvoiceLines(models.Model):
	_name = 'rent.vehicle.invoice.line'

	invoice_id = fields.Many2one('rent.vehicle.invoice')
	date = fields.Date('Date')
	vehicle_no = fields.Many2one('fleet.vehicle','Vehicle No:')
	vehicle_owner = fields.Many2one('res.partner')
	crusher  =fields.Many2one('res.partner','Crusher')	
	supervisor = fields.Many2one('hr.employee','Supervisor')
	site_id = fields.Many2one('stock.location','Site')
	item = fields.Many2one('product.product','Item')
	fullsupply_qty = fields.Float('Full Supply Qty')
	fullsupply_rate = fields.Float('Fullsupply Rate')
	qty = fields.Float('Qty')
	rate = fields.Float('Rate')
	material_cost = fields.Float('Material Cost')
	km = fields.Float('Km')
	trip = fields.Float('Trip')
	rate_trip = fields.Float('Rate')
	rent = fields.Float('Rent')
	diesel = fields.Float('Diesel')
	advance = fields.Float('Advance')
	vehicle_stmt_id = fields.Many2one('rent.vehicle.statement')
	diesel_pump = fields.Many2one('res.partner','Diesel Pump')
	direct_crusher = fields.Boolean(string="Directly Crusher?")
	based_on = fields.Selection([('per_km','Per Km'),('per_day','Per Day')],string="Based On")

class RentVehiclePayment(models.Model):
	_name = 'rent.vehicle.payment'

	rec = fields.Many2one('rent.vehicle.invoice')
	pay_amount = fields.Float('Paid Amount')
	journal_id = fields.Many2one('account.journal','Journal')

	@api.multi
	def invoice_record(self):
		if self.pay_amount > self.rec.net_balance:
			raise except_orm(_('Warning'),_('Paid Amount Is Greater Than Net Balance...!!'))
		else:
			self.rec.write({'paid_amount': self.pay_amount,'state':'paid'})
			for lines in self.rec.invoice_lines:
				lines.vehicle_stmt_id.state = 'paid'
			move_line = self.env['account.move.line']

			move = self.env['account.move'].create({'journal_id':self.journal_id.id})
			move_line.create({
						'move_id':move.id,
						'state': 'valid',
						'name': 'Rent Vehicle',
						'account_id':self.rec.vehicle_owner.property_account_payable.id,
						'journal_id': self.journal_id.id,
						'period_id' : move.period_id.id,
						'debit': float(self.pay_amount),
						'credit':0,
						})
			move_line.create({
						'move_id':move.id,
						'state': 'valid',
						'name': 'Rent Vehicle',
						'account_id':self.journal_id.default_credit_account_id.id,
						'journal_id': self.journal_id.id,
						'period_id' : move.period_id.id,
						'debit':0,
						'credit': float(self.pay_amount),
							})
			if self.rec.tds_applicable == True:
				move_line.create({
						'move_id':move.id,
						'state': 'valid',
						'name': 'TDS',
						'account_id':self.rec.vehicle_owner.property_account_payable.id,
						'journal_id': self.journal_id.id,
						'period_id' : move.period_id.id,
						'debit': float(self.rec.tds_amount),
						'credit':0,
						})
				move_line.create({
						'move_id':move.id,
						'state': 'valid',
						'name': 'TDS',
						'account_id':self.rec.tds_account.id,
						'journal_id': self.journal_id.id,
						'period_id' : move.period_id.id,
						'debit':0,
						'credit': float(self.rec.tds_amount),
								})

			move.button_validate()
			# move.state = 'posted'
		return True


class RentVehicleInvoice(models.Model):
	_name = 'rent.vehicle.invoice'
	_order = 'id desc'


	@api.model
	def default_get(self, default_fields):
		vals = super(RentVehicleInvoice, self).default_get(default_fields)
		rec = self.env['rent.vehicle.invoice'].search([])
		amount = 0
		if len(rec) != 0:
			new_rec = self.env['rent.vehicle.invoice'].search([('id','=',len(rec))])
			amount = new_rec.closing_balance
		vals.update({'opening' : amount,
					 })
	

		return vals

	@api.multi
	def pay_amount(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_construction', 'view_invoice_rent_vehicle')
		view_id = view_ref[1] if view_ref else False
		res = {
		   'type': 'ir.actions.act_window',
		   'name': _('Payment'),
		   'res_model': 'rent.vehicle.payment',
		   'view_type': 'form',
		   'view_mode': 'form',
		   'view_id': view_id,
		   'target': 'new',
		   'context': {'default_rec':self.id}
	   }

		return res
		

	@api.multi
	def name_get(self):
		result = []
		for record in self:
			if record.date_from and record.date_to and record.vehicle_owner:
				result.append((record.id,u"%s (%s-%s)" % (record.vehicle_owner.name, record.date_from, record.date_to)))
		return result

	@api.multi
	@api.depends('invoice_lines')
	def compute_values(self):
		for rec in self:
			total_rent = balance = advance = diesel = 0
			for line in rec.invoice_lines:
				total_rent += line.rent
				diesel += line.diesel
				advance += line.advance

			rec.total_rent = total_rent
			rec.diesel_amt = diesel
			rec.advance = advance
			rec.balance = total_rent-advance-diesel



	date_from = fields.Date('Period From')
	date_to = fields.Date('Period To')
	vehicle_owner = fields.Many2one('res.partner','Vehicle Owner')
	invoice_lines = fields.One2many('rent.vehicle.invoice.line','invoice_id')
	verified_by  =fields.Many2one('res.users','Verfied By')
	approved_by = fields.Many2one('res.users','Approved By')
	checked_by = fields.Many2one('res.users','Checked By')
	date1 = fields.Date('Date')
	date2 = fields.Date('Date')
	date3 = fields.Date('Date')
	sign1 = fields.Binary('Sign')
	sign2 = fields.Binary('Sign')
	sign3 = fields.Binary('Sign')
	state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('paid','Invoiced'),('verified','Verified'),('approved','Approved'),('checked','Checked')],default='draft')
	total_rent = fields.Float('Total Rent',compute="compute_values")
	opening = fields.Float('Opening',readonly=True)
	advance = fields.Float('Less : Advance',compute="compute_values")
	diesel_amt = fields.Float('Less : Diesel',compute="compute_values")
	balance = fields.Float('Balance',compute="compute_values")
	tds = fields.Float('TDS')
	multiple_line = fields.Boolean(default=False)
	tds_line = fields.One2many('tds.line','line_id')
	tds_amount = fields.Float('TDS Amount',compute="_tds_amount_sum")
	net_balance = fields.Float('Net Balance',compute="compute_net_balance")
	tds_account = fields.Many2one('account.account',string='TDS Account')
	tds_applicable = fields.Boolean(readonly=False,related='vehicle_owner.tds_applicable')
	paid_amount = fields.Float('Paid Amount',readonly=True)
	closing_balance = fields.Float('Closing Balance',compute="compute_closing_balance")

	@api.model
	def create(self,vals):
		record = self.env['rent.vehicle.invoice'].search([])
		# id_val = int(self.id) - 1
		# if id_val >= 1:
		# 	rec = self.env['rent.vehicle.statement'].search([('id','=',id_val)])
		# 	if rec.state != 'checked':
		# 		raise except_orm(_('Warning'),_('Last Record Did Not Checked Yet....Please Check!!'))
		

		return super(RentVehicleInvoice, self).create(vals)


	@api.multi
	@api.depends('paid_amount','net_balance')
	def compute_closing_balance(self):
		for lines in self:
			lines.closing_balance = lines.net_balance - lines.paid_amount

	@api.multi
	def verify_record(self):
		self.state = 'verified'
		return

	@api.multi
	def approve_record(self):
		self.state = 'approved'
		return

	@api.multi
	def check_record(self):
		self.state = 'checked'
		return

	@api.multi
	def confirm_record(self):
		self.state = 'confirmed'

		return

	@api.multi
	@api.depends('balance','tds_amount')
	def compute_net_balance(self):
		for line in self:
			line.net_balance = line.balance - line.tds_amount

	@api.multi
	@api.depends('multiple_line','tds_line','tds')
	def _tds_amount_sum(self):
		for line in self:
			if line.multiple_line == False:
				line.tds_amount = line.tds
			if line.multiple_line == True:
				total = 0
				for lines in line.tds_line:
					total += lines.amount
				line.tds_amount = total


	@api.onchange('date_from','date_to','vehicle_owner')
	def onchange_invoice_line(self):
		if self.date_from:
			rec = self.env['rent.vehicle.statement'].search([('date','<',self.date_from),('state','in',('draft','confirm'))])
			if rec:
				raise except_orm(_('Warning'),_('Some Records Before The Period Are Still Not In Invoiced State!!'))
		if self.date_from and self.date_to and self.vehicle_owner:
			record = []
			rent_record = self.env['rent.vehicle.statement'].search([('state','=','confirm'),('date','<=',self.date_to),('date','>=',self.date_from)])
			if rent_record:
				for lines in rent_record:
					if lines.vehicle_owner.id == self.vehicle_owner.id:
						line_record = {
							'date':lines.date,
							'vehicle_no':lines.vehicle_no.id,
							'crusher':lines.crusher.id if lines.crusher else False,
							'site_id':lines.site_id.id,
							'item':lines.item.id,
							'qty':float(lines.qty),
							'rate':float(lines.rate),
							'material_cost':float(lines.material_cost),
							'km':float(lines.km),
							'rate_trip':float(lines.rate_trip),
							'rent':float(lines.rent),
							'diesel':float(lines.diesel),
							'advance':float(lines.advance),
							'vehicle_stmt_id':lines.id,
							'vehicle_owner':lines.vehicle_owner.id,
							'supervisor':lines.supervisor.id,
							'based_on':lines.based_on,
							'direct_crusher':lines.direct_crusher,
							'diesel_pump':lines.diesel_pump.id if lines.diesel_pump else False

							}
						record.append((0, False, line_record ))
			self.invoice_lines = record

				 


class TdsLine(models.Model):
	_name = 'tds.line'

	line_id = fields.Many2one('rent.vehicle.invoice')
	name = fields.Many2one('tds.sector','Sector')
	amount = fields.Float('Amount')

class TdsSector(models.Model):
	_name = 'tds.sector'

	name = fields.Char('Name', required=True)

class RentVehicleStatement(models.Model):

	_name = 'rent.vehicle.statement'
	_order = 'id desc'



	@api.onchange('fullsupply_qty','fullsupply_rate')
	def onchange_fullsupply_qty_rate(self):
		if self.fullsupply_qty and self.fullsupply_rate:
			self.full_cost = self.fullsupply_qty * self.fullsupply_rate
		if self.fullsupply_rate == 0 or self.fullsupply_qty == 0:
			self.full_cost = 0
		if self.full_cost < self.material_cost:
			raise osv.except_osv(_('Error!'),_("Full cost amount is always larger than material cost"))



	# @api.onchange('qty','rate')
	# def onchange_material_cost(self):
	# 	if self.qty and self.rate:
	# 		self.material_cost = self.qty * self.rate
	# 	if self.qty == 0 or self.rate == 0:
	# 		self.material_cost = 0
	# 	if self.qty == False or self.rate == False:
	# 		self.material_cost = 0


	# @api.onchange('material_cost','rate')
	# def onchange_qty(self):
	# 	if self.material_cost and self.rate:
	# 		self.qty = self.material_cost / self.rate

	@api.onchange('qty','material_cost','full_supply','direct_crusher','item','site_id','vehicle_no','rent_id')
	def onchange_rate(self):
		if self.full_supply == False:
			self.fullsupply_rate = False
			self.fullsupply_qty = False
			self.full_cost = False
			if self.qty and self.material_cost:
				self.rate = self.material_cost / self.qty
		if self.full_supply == True and self.direct_crusher == True:
			if self.site_id and self.item and self.vehicle_no:
				rec = self.env['fullsupply.line'].sudo().search([('line_id','=',self.vehicle_no.id),('location_id','=',self.site_id.id),('product_id','=',self.item.id),('date_from','<=',self.rent_id.date),('date_to','>=',self.rent_id.date)],limit=1)
				if rec:
					self.fullsupply_rate = rec.rate
				self.fullsupply_qty = self.vehicle_no.capacity
				self.full_cost = self.fullsupply_qty * self.fullsupply_rate
		if self.direct_crusher == False:
			self.rate = False
			self.qty = False
			self.crusher = False











	@api.onchange('qty')
	def onchange_qty_rate(self):
		if self.qty == 0:
			self.material_cost = 0
		else:
			if self.material_cost != 0 and self.rate != 0 and self.qty != round((self.material_cost / self.rate),2):
				self.qty = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Qty field, Rate or Material Cost should be Zero"
						}
					}	
			if self.qty != 0 and self.rate != 0:
				if self.rate*self.qty != self.material_cost:
					pass
				if self.material_cost == 0.0:
					self.material_cost = round((self.qty * self.rate),2)
			if self.material_cost != 0 and self.qty != 0:
				if self.rate == 0.0:
					self.rate = round((self.material_cost / self.qty),2)	


	@api.onchange('rate')
	def onchange_rate_material_cost(self):
		if self.rate == 0:
			self.material_cost = 0
		else:
			if self.material_cost != 0 and self.qty != 0 and self.rate != round((self.material_cost / self.qty),2):
				self.rate = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Rate field, Qty or Material Cost should be Zero."
						}
					}
			if self.qty != 0 and self.rate != 0:
				if self.rate*self.qty != self.material_cost:
					pass
				if self.material_cost == 0.0:
					self.material_cost = round((self.qty * self.rate),2)
			if self.material_cost != 0 and self.rate != 0:
				if self.qty == 0.0:
					self.qty = round((self.material_cost / self.rate),2)		
			
	
	@api.onchange('material_cost')
	def onchange_qty_material_cost(self):
		if self.material_cost != 0:
			if self.rate*self.qty != self.material_cost:
				if self.rate != 0 and self.qty != 0:
					self.material_cost = 0.0
					return {
						'warning': {
							'title': 'Warning',
							'message': "For Entering value to Material Cost field, Qty or Rate should be Zero."
							}
						}
				elif self.rate == 0 and self.qty != 0:
					self.rate = round((self.material_cost / self.qty),2)
				elif self.qty == 0 and self.rate != 0:
					self.qty = round((self.material_cost / self.rate),2)				
				else:
					pass


	# @api.multi
	# @api.depends('diesel_rate','diesel_litre')
	# def get_diesel_rate(self):
	# 	for line in self:
	# 		line.diesel = float(line.diesel_litre) * float(line.diesel_rate)

	@api.onchange('diesel_litre')
	def onchange_diesel_litre_rate(self):
		if self.diesel_litre == 0:
			self.diesel = 0
		else:
			if self.diesel != 0 and self.diesel_rate != 0 and self.diesel_litre != round((self.diesel / self.diesel_rate),2):
				self.diesel_litre = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Qty field, Rate or Total should be Zero"
						}
					}	
			if self.diesel_litre != 0 and self.diesel_rate != 0:
				if self.diesel_rate*self.diesel_litre != self.diesel:
					pass
				if self.diesel == 0.0:
					self.diesel = round((self.diesel_litre * self.diesel_rate),2)
			if self.diesel != 0 and self.diesel_litre != 0:
				if self.diesel_rate == 0.0:
					self.diesel_rate = round((self.diesel / self.diesel_litre),2)	


	@api.onchange('diesel_rate')
	def onchange_diesel_rate_diesel(self):
		if self.diesel_rate == 0:
			self.diesel = 0
		else:
			if self.diesel != 0 and self.diesel_litre != 0 and self.diesel_rate != round((self.diesel / self.diesel_litre),2):
				self.diesel_rate = 0.0
				return {
					'warning': {
						'title': 'Warning',
						'message': "For Entering value to Rate field, Qty or Total should be Zero."
						}
					}
			if self.diesel_litre != 0 and self.diesel_rate != 0:
				if self.diesel_rate*self.diesel_litre != self.diesel:
					pass
				if self.diesel == 0.0:
					self.diesel = round((self.diesel_litre * self.diesel_rate),2)
			if self.diesel != 0 and self.diesel_rate != 0:
				if self.diesel_litre == 0.0:
					self.diesel_litre = round((self.diesel / self.diesel_rate),2)		
			


	@api.onchange('diesel')
	def onchange_diesel(self):
		if self.diesel != 0:
			if self.diesel_rate*self.diesel_litre != self.diesel:
				if self.diesel_rate != 0 and self.diesel_litre != 0:
					self.diesel = 0.0
					return {
						'warning': {
							'title': 'Warning',
							'message': "For Entering value to Total field, Qty or Rate should be Zero."
							}
						}
				elif self.diesel_rate == 0 and self.diesel_litre != 0:
					self.diesel_rate = round((self.diesel / self.diesel_litre),2)
				elif self.diesel_litre == 0 and self.diesel_rate != 0:
					self.diesel_litre = round((self.diesel / self.diesel_rate),2)				
				else:
					pass

	@api.multi
	@api.depends('rent','material_cost','diesel','advance')
	def _compute_balance(self):
		for line in self:
			line.balance = line.rent + line.material_cost - float(line.diesel) - float(line.advance)

	# @api.multi
	# @api.depends('qty','rate')
	# def _compute_material_cost(self):
	# 	for line in self:
	# 		line.material_cost = line.qty * line.rate

	@api.multi
	@api.depends('based_on','km','full_cost','material_cost')
	def _compute_rent(self):
		for line in self:
			if not line.full_cost:
				if line.based_on == 'per_km':
					line.rent = line.km * line.vehicle_no.rate_per_km
				if line.based_on == 'per_day':
					if line.vehicle_no:
						line.rent = line.vehicle_no.per_day_rent

			else:
				line.rent = line.full_cost - line.material_cost


	date = fields.Date('Date')
	vehicle_no = fields.Many2one('fleet.vehicle','Vehicle No:')
	mou = fields.Many2one('mou.mou', 'MOU', domain="[('vehicle_number', '=', vehicle_no),('site','=',site_id)]")
	vehicle_owner = fields.Many2one('res.partner','Vehicle Owner')
	crusher  =fields.Many2one('res.partner','Crusher')	
	supervisor = fields.Many2one('hr.employee','Supervisor')
	site_id = fields.Many2one('stock.location','Site', domain=[('usage','=','internal')])
	item = fields.Many2one('product.product','Item')
	qty = fields.Float('Qty')
	rate = fields.Float('Rate')
	fullsupply_qty = fields.Float('Qty')
	fullsupply_rate = fields.Float('Rate')
	material_cost = fields.Float('Material Cost')
	km = fields.Float('Km')
	trip = fields.Float('Trip')
	rate_trip = fields.Float('Rate')
	rent = fields.Float('Rent',compute="_compute_rent")
	diesel_litre = fields.Float('Diesel: Litre')
	diesel_rate = fields.Float('Diesel: Rate')
	diesel = fields.Float('Diesel')
	advance = fields.Float('Advance')
	other_expenses = fields.Float('Other Expenses')
	other_account_id = fields.Many2one('account.account', 'Other Expense Account')
	balance = fields.Float('Balance', compute="_compute_balance")
	state = fields.Selection([('draft','Draft'),('confirm','Confirmed'),('paid','Invoiced'),('cancelled','Cancelled')],default='draft')
	remarks = fields.Text() 
	based_on = fields.Selection([('per_km','Per Km'),('per_day','Per Day')],string="Based On")
	diesel_pump = fields.Many2one('res.partner','Diesel Pump')
	move_id = fields.Many2one('account.move','Move_id')
	direct_crusher = fields.Boolean(default=True,string="Directly To Crusher?")
	from_date = fields.Date('Period From')
	to_date = fields.Date('Period To')
	rent_id = fields.Many2one('partner.daily.statement')
	full_supply = fields.Boolean(default=False)
	full_cost = fields.Float('Full Cost')
	bill_no = fields.Char('Bill No')
	contractor_id = fields.Many2one('res.partner',domain="[('company_contractor', '=', True)]", string='Contractor')
	tax_ids = fields.Many2many('account.tax',string="Tax")
	tax_amount = fields.Float('Tax Amount',compute="_get_subtotal_crusher_report")
	sub_total = fields.Float('Sub Total',compute="_get_subtotal_crusher_report")
	total = fields.Float('Total',compute="_get_subtotal_crusher_report")
	round_off = fields.Float('Round Off')
	invoice_value = fields.Float('Invoice Value',compute="_get_subtotal_crusher_report")

	pump_bill_no = fields.Char('Bill No.')
	fuel_item = fields.Many2one('product.product', 'Fuel Item')



	@api.onchange('item')
	def tax_relation(self):
		for rec in self:
			# tax_rel = self.env['product.template'].search([('id','=',rec.item.id)])
			print '==================================tax',rec.item.taxes_id
			rec.tax_ids=rec.item.taxes_id


	@api.model
	def default_get(self, vals):
		res = super(RentVehicleStatement, self).default_get(vals)
		config = self.env['general.fuel.configuration'].search([], limit=1)

		res.update({
			'fuel_item': config.product_id.id,
		})
		return res

	# fuel_tax_ids = fields.Many2many('account.tax',string="Tax")
	# fuel_tax_amount = fields.Float('Tax Amount',compute="_get_subtotal_fuel_report")
	# fuel_sub_total = fields.Float('Sub Total',compute="_get_subtotal_fuel_report")
	# fuel_total = fields.Float('Total',compute="_get_subtotal_fuel_report")
	# fuel_round_off = fields.Float('Round Off')
	# fuel_invoice_value = fields.Float('Invoice Value',compute="_get_subtotal_fuel_report")

	@api.multi
	@api.depends('tax_ids','material_cost','round_off')
	def _get_subtotal_crusher_report(self):
		for lines in self:
			taxi = 0
			taxe = 0
			for tax in lines.tax_ids:
				if tax.price_include == True:
					taxi = tax.amount
				if tax.price_include == False:
					taxe += tax.amount
			lines.tax_amount = (lines.material_cost)/(1+taxi)*(taxi+taxe)
			lines.sub_total = (lines.material_cost)/(1+taxi)
			lines.total = lines.tax_amount + lines.sub_total
			lines.invoice_value = lines.total + lines.round_off

	# @api.multi
	# @api.depends('fuel_tax_ids','diesel','fuel_round_off')
	# def _get_subtotal_fuel_report(self):
	# 	for lines in self:
	# 		taxi = 0
	# 		taxe = 0
	# 		for tax in lines.fuel_tax_ids:
	# 			if tax.price_include == True:
	# 				taxi = tax.amount
	# 			if tax.price_include == False:
	# 				taxe += tax.amount
	# 		lines.fuel_tax_amount = (lines.diesel)/(1+taxi)*(taxi+taxe)
	# 		lines.fuel_sub_total = (lines.diesel)/(1+taxi)
	# 		lines.fuel_total = lines.fuel_tax_amount + lines.fuel_sub_total
	# 		lines.fuel_invoice_value = lines.fuel_total + lines.fuel_round_off
	


	@api.model
	def create(self,vals):
		result = super(RentVehicleStatement, self).create(vals)
		self.env['crusher.report'].sudo().create({
										'date':result.rent_id.date,
										'site_id':result.site_id.id,
										'vehicle_no':result.vehicle_no.id,
										'item_id':result.item.id,
										'qty':result.qty,
										'rate':result.rate,
										'amount':result.material_cost,
										'total':result.material_cost,
										'crusher':result.crusher.id,
										'rent_vehicle_id':result.id,
										})
		if result.diesel_pump:
			self.env['fuel.report'].sudo().create({
										'date':result.rent_id.date,
										'vehicle_owner':result.vehicle_owner.id,
										'vehicle_no':result.vehicle_no.id,
										'item_char':'Diesel',
										'qty':result.diesel_litre,
										'rate':result.diesel_rate,
										'amount':result.diesel,
										'rent_vehicle_id':result.id,
										'diesel_pump':result.diesel_pump.id
										})



		return result


	@api.multi
	def write(self,vals):
		result = super(RentVehicleStatement, self).write(vals)
		fuel_report = self.env['fuel.report'].search([('rent_vehicle_id','=',self.id)])
		if fuel_report:
			if vals.get('diesel_pump'):
				fuel_report.write({'diesel_pump':vals['diesel_pump']})
			if vals.get('diesel_litre'):
				fuel_report.write({'qty':vals['diesel_litre']})
			if vals.get('diesel_rate'):
				fuel_report.write({'rate':vals['diesel_rate']})
			if vals.get('diesel'):
				fuel_report.write({'amount':vals['diesel']})
			if vals.get('vehicle_no'):
				fuel_report.write({'vehicle_no':vals['vehicle_no']})
			if vals.get('vehicle_owner'):
				fuel_report.write({'vehicle_owner':vals['vehicle_owner']})
		crusher_report = self.env['crusher.report'].search([('rent_vehicle_id','=',self.id)])
		if crusher_report:
			if vals.get('site_id'):
				crusher_report.write({'site_id':vals['site_id']})
			if vals.get('vehicle_no'):
				crusher_report.write({'vehicle_no':vals['vehicle_no']})
			if vals.get('item'):
				crusher_report.write({'item_id':vals['item']})
			if vals.get('qty'):
				crusher_report.write({'qty':vals['qty']})
			if vals.get('rate'):
				crusher_report.write({'rate':vals['rate']})
			if vals.get('material_cost'):
				crusher_report.write({'amount':vals['material_cost']})
			if vals.get('crusher'):
				crusher_report.write({'crusher':vals['crusher']})


		return result

	@api.onchange("vehicle_owner")
	def onchange_vehicle_owner(self):
		if self.vehicle_owner:
			self.date = self.rent_id.date
			self.supervisor = self.rent_id.employee_id.id
			ids = []
			record = self.env['fleet.vehicle'].sudo().search([('vehicle_under','=',self.vehicle_owner.id)])
			if record:
				for item in record:
					ids.append(item.id)
				mou = self.env['mou.mou'].sudo().search([('partner_id', '=', self.vehicle_owner.id), ('site', '=', self.site_id.id),('vehicle_number', 'in', ids)])
				self.mou = mou.id
				return {'domain': {'vehicle_no': [('id', 'in', ids)]}}

	@api.multi
	def confirm_entry(self):
		journal = self.env['account.journal'].search([('code','=','MISC'),('type','=','general')])
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		if self.advance != 0:
			supervisor_record = self.env['partner.daily.statement'].sudo().search([('date','=',self.date),('employee_id','=',self.supervisor.id)])
			if supervisor_record:
				supervisor_record.rent_vehicle += self.advance
				supervisor_record.compute_expense()
			else:
				raise except_orm(_('Warning'),_('Please Open Todays Supervisor Record!!'))
			if not self.supervisor.petty_cash_account:
				raise except_orm(_('Warning'),_('You Have To Configure Supervisor Petty Account..!!'))
			advance_move = move.create({'journal_id':journal.id,'rent_vehicle_stmt':self.id})
			move_line.create({
						'move_id':advance_move.id,
						'state': 'valid',
						'name': 'Advance Rent Vehicle',
						'account_id':self.vehicle_no.vehicle_under.property_account_payable.id,
						'journal_id': journal.id,
						'period_id' : advance_move.period_id.id,
						'debit':self.advance,
						'credit':0,
						})
			move_line.create({
						'move_id':advance_move.id,
						'state': 'valid',
						'name': 'Advance Rent Vehicle',
						'account_id':self.supervisor.petty_cash_account.id,
						'journal_id': journal.id,
						'period_id' : advance_move.period_id.id,
						'debit':0,
						'credit':self.advance,
							})
			
			advance_move.button_validate()
			# advance_move.state = 'posted'
		if self.rent:
			rent_move = move.create({'journal_id':journal.id,'rent_vehicle_stmt':self.id})
			move_line.create({
						'move_id':rent_move.id,
						'state': 'valid',
						'name': 'Rent Vehicle',
						'account_id':self.site_id.related_account.id,
						'journal_id': journal.id,
						'period_id' : rent_move.period_id.id,
						'debit':self.rent,
						'credit':0,
						})
			move_line.create({
						'move_id':rent_move.id,
						'state': 'valid',
						'name': 'Rent Vehicle',
						'account_id':self.vehicle_no.vehicle_under.property_account_payable.id,
						'journal_id': journal.id,
						'period_id' : rent_move.period_id.id,
						'debit':0,
						'credit':self.rent,
							})
			
			rent_move.button_validate()
			# rent_move.state = 'posted'
		if self.diesel:
			if self.based_on == 'per_day':
				diesel = move.create({'journal_id':journal.id,'rent_vehicle_stmt':self.id})
				move_line.create({
							'move_id':diesel.id,
							'state': 'valid',
							'name': 'Diesel Per Day',
							'account_id':self.site_id.related_account.id,
							'journal_id': journal.id,
							'period_id' : diesel.period_id.id,
							'debit':self.diesel,
							'credit':0,
							})
				move_line.create({
							'move_id':diesel.id,
							'state': 'valid',
							'name': 'Diesel Per Day',
							'account_id':self.diesel_pump.property_account_payable.id,
							'journal_id': journal.id,
							'period_id' : diesel.period_id.id,
							'debit':0,
							'credit':self.diesel,
								})
				
				diesel.button_validate()
				# diesel.state = 'posted'
			if self.based_on == 'per_km':
				diesel = move.create({'journal_id':journal.id,'rent_vehicle_stmt':self.id})
				move_line.create({
							'move_id':diesel.id,
							'state': 'valid',
							'name': 'Diesel Per Km',
							'account_id':self.vehicle_no.vehicle_under.property_account_payable.id,
							'journal_id': journal.id,
							'period_id' : diesel.period_id.id,
							'debit':self.diesel,
							'credit':0,
							})
				move_line.create({
							'move_id':diesel.id,
							'state': 'valid',
							'name': 'Diesel Per Km',
							'account_id':self.diesel_pump.property_account_payable.id,
							'journal_id': journal.id,
							'period_id' : diesel.period_id.id,
							'debit':0,
							'credit':self.diesel,
								})
				
				diesel.button_validate()
				# diesel.state = 'posted'
		

		if self.direct_crusher == True:
			material_cost = move.create({'journal_id':journal.id,'rent_vehicle_stmt':self.id})
			move_line.create({
						'move_id':material_cost.id,
						'state': 'valid',
						'name': 'Material Cost',
						'account_id':self.site_id.related_account.id,
						'journal_id': journal.id,
						'period_id' : material_cost.period_id.id,
						'debit':self.material_cost,
						'credit':0,
						})
			move_line.create({
						'move_id':material_cost.id,
						'state': 'valid',
						'name': 'Material Cost',
						'account_id':self.crusher.property_account_payable.id,
						'journal_id': journal.id,
						'period_id' : material_cost.period_id.id,
						'debit':0,
						'credit':self.material_cost,
							})
			
			material_cost.button_validate()
			# material_cost.state = 'posted'
		if self.direct_crusher == False:
			material_cost = move.create({'journal_id':journal.id,'rent_vehicle_stmt':self.id})
			move_line.create({
						'move_id':material_cost.id,
						'state': 'valid',
						'name': 'Material Cost',
						'account_id':self.site_id.related_account.id,
						'journal_id': journal.id,
						'period_id' : material_cost.period_id.id,
						'debit':self.material_cost,
						'credit':0,
						})
			move_line.create({
						'move_id':material_cost.id,
						'state': 'valid',
						'name': 'Material Cost',
						'account_id':self.vehicle_no.vehicle_under.property_account_payable.id,
						'journal_id': journal.id,
						'period_id' : material_cost.period_id.id,
						'debit':0,
						'credit':self.material_cost,
							})
			material_cost.button_validate()
			# material_cost.state = 'posted'
		self.state = 'confirm'

	@api.multi
	def cancel_entry(self):
		records = self.env['account.move'].search([('rent_vehicle_stmt','=',self.id)])
		if records:
			for rec in records:
				rec.button_cancel()
				rec.unlink()

		self.state = 'cancelled'

	@api.multi
	def set_to_draft(self):
		self.state = 'draft'
		return True

	@api.multi
	def name_get(self):
		result = []
		for record in self:
			if record.vehicle_no.vehicle_under:
				result.append((record.id,u"%s (%s)" % (record.date, record.vehicle_no.vehicle_under.name)))
			else:
				result.append((record.id,u"%s (%s)" % (record.date, record.vehicle_no.license_plate)))
		return result


