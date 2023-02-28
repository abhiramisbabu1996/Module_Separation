from openerp import fields, models, api,exceptions,_
from datetime import datetime
# import datetime
# from openerp.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
from openerp.osv import osv
from openerp import tools
from openerp.exceptions import ValidationError


class District(models.Model):
	_name = 'location.district'


	name = fields.Char('District Name')
	code = fields.Char('District Code')


class ContractAwarder(models.Model):
	_name = 'contract.awarder'

	name = fields.Char("Name")

class RejectionReason(models.Model):
	_name = 'rejection.reason'

	name = fields.Char('Reason of Rejection')

class HiworthTender(models.Model):
	_name = 'hiworth.tender'
	_rec_name = 'tender_no'

	name = fields.Char('Work Name')
	tender_code = fields.Char('Code')
	work_nature = fields.Text('Nature of work')
	creation_date = fields.Date('Date of Creation', default=fields.Date.today)
	location_id = fields.Many2one('stock.location', 'Location', domain=[('usage','=','internal'),('tender_location','=',True)], context={'default_tender_location':True})
	district_id = fields.Many2one('location.district', string='District')
	# contractor_id1 = fields.Many2one('res.partner', 'Contractor', domain=[('contractor','=',True)])    
	contractor_id1 = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Contractor')
	customer_id = fields.Many2one('contract.awarder', string='Contract Awarder')    
	tender_no = fields.Char('Tender No.')
	last_date = fields.Datetime('Last Date of Tender')
	postponed_date = fields.Date('Postponed Date of Tender')

	emd_date = fields.Date('Date of EMD')
	bank_id = fields.Many2one('res.partner.bank', 'Bank Account')
	bank_id_emd = fields.Many2one('res.partner.bank', 'Bank Account')
	emd = fields.Float('EMD Amount')
	emd_account = fields.Many2one('account.account', string="EMD Account")
	tender_cost = fields.Float('Tender Fee')
	tender_cost_account = fields.Many2one('account.account', string="Tender Account")

	pac = fields.Float('EPAC', help="Probable Acceptable Contract")
	remarks_of_rejection = fields.Text('Remarks')
	return_emd = fields.Float('Returned EMD Amount')
	return_emd_date = fields.Date('Date of EMD Returned')
	no_emd_days = fields.Integer('No. of days taken to receive EMD Amount',compute="_compute_no_emd")
	return_bank_id = fields.Many2one('res.partner.bank', 'Bank Account')
	apac = fields.Float('Quoted Amount', help="Accepted Probable Acceptable Contract")
	status = fields.Selection([('above','+'),
							   ('below','-'),
							   ('equal','Equal'),
							   ('cancel','Not Defined')
							   ], 'Status', compute="_compute_apac_details")
	percent = fields.Float('Percentage', compute="_compute_apac_details")

	technical_opening_date = fields.Date('Technical Bid Opening Date')
	financial_opening_date = fields.Date('Financial Bid Opening Date')
	
	tender_fee = fields.Float('Tender Fee')
	# attachment_ids = fields.One2many('ir.attachment', 'tender_id', 'Attachments')
	initial_state = fields.Selection([('draft','Draft'),
							   ('approved','Accepted'),
							   ('rejected','Rejected'),
							   # ('apac_approval','APAC Approval'),
									  ('cancel','Cancel'),
							   ], 'Status', default="draft")
	state = fields.Selection([('draft','Draft'),
							  ('apac_approve','QPAC Approve'),
							  ('emd_payment','EMD Paid'),
							   ('transfer_quot','Tender Submission'),
							   ('technical_bid','Technical Bid'),
							   ('financial_bid','Financial Bid'),
							   ('selected','Selected'),
							   ('processing','Gaurantee Generated'),
							   ('submission','Gaurantee Submission'),
							   ('rejected','Rejected'),
							   ('closed','Closed'),
							   ('cancel','Cancelled')
							   ], 'Status', default="draft")

	party_status_ids1 = fields.One2many('party.history', 'tender_id')
	party_status_ids2 = fields.One2many('party.history', 'tender_id', domain=[('status','=','approved')])
	emd_return_ids2 = fields.One2many('tender.emd.return.status', 'tender_id')
	attachment_ids = fields.One2many('tender.attachments', 'tender_id')
	notice_received_date = fields.Date('Selection Notice Received Date')
	last_agreement_date = fields.Date('Last Date of Agreement')
	agreement_date = fields.Date('Date of Agreement')
	agreement_no = fields.Char('Agreement No')
	notice_no = fields.Char('Selection Notice No')
	package_no = fields.Char('Package No')


	security_deposit_based = fields.Selection([('pac','PAC'),
												('apac','APAC')
												],string="Security Deposit Based On")
	
	security_deposit_percent = fields.Float('% of Security Deposit')
	security_wo_round_off = fields.Float('Amount w/o round-off')
	security_round_off = fields.Float('Round Off')
	security_deposit_amount = fields.Float('Security Deposit Amount')
	bg_percent = fields.Float('% of Security Deposit Through Bank')
	treasury_percent = fields.Float('% of Security Deposit Through Treasury')

	bg_date = fields.Date('Gaurantee Submission Date', default=fields.Date.today)
	bg_amount = fields.Float('Bank Gaurantee Amount')
	available_collateral = fields.Float('Available Collateral', compute="_compute_collateral", store=True)
	fd_percent = fields.Float('FD Percent')
	fd_amount_wo_roundoff = fields.Float('FD Amount w/o round-off')
	fd_round_off = fields.Float('Round-Off')
	fd_amount = fields.Float('FD Amount')
	fd_payment_mode = fields.Many2one('res.partner.bank', string='FD Payment Mode')
	fd_account = fields.Many2one('account.account','FD Account')
	fd_number = fields.Char('FD Number')
	fd_period = fields.Char('Period')
	expected_bg_release_date = fields.Date('Maturity Date')
	release_bg = fields.Float('Released FD Amount')
	release_bg_date = fields.Date('Released FD Date')
	release_bg_account = fields.Many2one('account.account', 'Released FD Account')

	cs_date = fields.Date('Date', default=fields.Date.today)
	com_security_amount = fields.Float('Normal Security Amount')
	com_security_account = fields.Many2one('account.account','Normal Security Account')
	com_security_payment_mode = fields.Many2one('account.journal', string='Normal Security Payment Mode', domain="[('type','in',['cash','bank'])]")
	expected_cs_release_date = fields.Date('Maturity Date')
	cs_treasury_id = fields.Many2one('res.partner', 'Treasury Name')
	treasury_number = fields.Char('Treasury Number')
	treasury_period = fields.Char('Period')
	release_cs = fields.Float('Released CS Amount')
	release_cs_date = fields.Date('Released CS Date')
	release_cs_account = fields.Many2one('account.account', 'Released CS Account')

	ps_date = fields.Date('Date', default=fields.Date.today)
	perf_security_mode = fields.Selection([('bank','Bank'),
											('treasury','Treasury')
											], string="Performance Security Deposit Through")
	ps_wo_round_off = fields.Float('PS Amount w/o round-off')
	ps_round_off = fields.Float('Round Off')
	performance_security_amount = fields.Float('PS Amount')
	ps_fd_percent = fields.Float('FD Percent')
	ps_fd_amount = fields.Float('FD Amount')
	# fd_amount_wo_roundoff = fields.Float('FD Amount w/o round-off')
	# fd_round_off = fields.Float('Round-Off')
	performance_security_account = fields.Many2one('account.account','PS Account')
	perf_bank_id = fields.Many2one('res.partner.bank', string='PS Payment Mode(Bank)')
	performance_security_payment_mode = fields.Many2one('account.journal', string='PS Payment Mode', domain="[('type','in',['cash','bank'])]")
	expected_ps_release_date = fields.Date('Expected Release Date')
	ps_treasury_id = fields.Many2one('res.partner', 'Treasury Name')
	perf_security_period = fields.Char('Period')
	perf_security_number = fields.Char('Performance Security Number')
	release_ps = fields.Float('Released PS Amount')
	release_ps_date = fields.Date('Released PS Date')
	release_ps_account = fields.Many2one('account.account', 'Released PS Account')
	ps_treasury_id = fields.Many2one('res.partner', 'Treasury Name')

	remarks = fields.Text('Remarks')

	reject = fields.Boolean('Reject')
	emd_boolean = fields.Boolean('EMD')
	bg_boolean = fields.Boolean('BG')
	cs_boolean = fields.Boolean('CS')
	ps_boolean = fields.Boolean('PS')
	is_project_created = fields.Boolean('Project Created')

	company_id = fields.Many2one('res.company', 'Company')
	period_of_comple_from = fields.Date(string="Period of Completion From")
	period_of_comple_to = fields.Date(string="To")

	no_month = fields.Float(string="Period of Completion(in no. of months)")
	location = fields.Char(string="Location")

	mode_emd_pay = fields.Selection([('bg_fd','BG and Related BG caution deposit FD'),
									 ('fd','FD'),
									 ('dd','DD'),
									 ('nsc','NSC'),
									 ('online','Online Payment - Bank')],'Mode of EMD Payment')
	mode_tender_fee_pay = fields.Selection([('bg_fd','BG and Related BG caution deposit FD'),
									 ('fd','FD'),
									 ('dd','DD'),
									 ('nsc','NSC'),
									 ('cash','Cash'),
									 ('online','Online Payment - Bank')],'Mode of Tender Fee Payment')
	emd_bank_detail = fields.Text('Bank Name')
	tender_bank_detail = fields.Text('Bank Name')

	tender_nature = fields.Selection([('percent','% - Type'),
									  ('item_rate','Item rate - Type'),
									  ('lump_sum','Lump sum - Type')],'Nature of Tender')
	tender_type = fields.Selection([('etender','Open Tender-  e-tender'),
									('manual','Open Tender- Manual'),
									('quotation','Quotation'),
									('limited_tender','Limited tender')],'Type of Tender')

	reason_reject = fields.Many2one('rejection.reason',string="Reason of Rejection")
	partner_id = fields.Many2one('res.partner',"Name of Supplier/Owner")
	quoted_amt = fields.Float(string="Quoted Amount")
	percent = fields.Float(string="% Amount")
	# remark = fields.Text('Remarks')
	line_ids = fields.One2many('unattended.tender.line','hiworth_tender_id')
	s_check = fields.Boolean('Status Check')
	district_loc = fields.Char()

	emd_number = fields.Char('EMD Reference')

	@api.onchange('line_ids')
	def set_contractor(self):
		print("function")
		for rec in self:
			for x in rec.line_ids:
				if x.s_check :
					print("checked")
					print (x.partner_id.id , rec.contractor_id1.id)
					rec.contractor_id1 = x.partner_id.id

	@api.constrains('line_ids')
	def _check_contractor(self):
		for rec in self:
			# print "check num"
			search_obj = self.env['unattended.tender.line'].search(
				[('hiworth_tender_id', '=', rec.id), ('s_check', '=', True)])
			# print "ppppppppppppppppppppppppppppppppppppppppp", len(search_obj.ids)
			if len(search_obj.ids) > 1:
				raise exceptions.ValidationError("Not more than one contractor is to be selected")


	_defaults = {
		'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
		}




	@api.onchange('postponed_date')
	def _check_postponed_date(self):
		for record in self:
			# print record.postponed_date,record.creation_date
			if record.postponed_date:
				if record.postponed_date < record.creation_date :
					raise exceptions.ValidationError("Postponed date of tender should be greater than the Date of creation")
				if record.postponed_date < record.last_date :
					raise exceptions.ValidationError("Postponed date of tender should be greater than the Last date of tender")

	# @api.onchange('last_date')
	# def _check_last_date(self):
	# 	for record in self:
	# 			if record.last_date > record.postponed_date :
	# 				raise exceptions.ValidationError("Postponed date of tender should be greater than the Last date of tender")




	@api.onchange('technical_opening_date')
	def onchange_technical_date(self):
		if self.technical_opening_date:
			if self.technical_opening_date < self.emd_date:
				raise osv.except_osv(_('Error!'),_("Technical opening date must be greater than date of emd"))


	@api.onchange('financial_opening_date')
	def onchange_financial_date(self):
		if self.financial_opening_date:
			if self.financial_opening_date < self.technical_opening_date:
				raise osv.except_osv(_('Error!'),_("Financial bid opening is possible only after technical bid opening"))


	@api.onchange('notice_received_date')
	def onchange_notice_received_date(self):
		if self.notice_received_date:
			if self.notice_received_date < self.financial_opening_date:
				raise osv.except_osv(_('Error!'),_("Selection notice is received only after financial bid opening"))


	@api.onchange('last_agreement_date')
	def onchange_last_agreement_date(self):
		if self.last_agreement_date:
			if self.last_agreement_date < self.financial_opening_date:
				raise osv.except_osv(_('Error!'),_("Last date of agreement must be greater than financial opening date"))
	

	@api.onchange('agreement_date')
	def onchange_agreement_date(self):
		if self.agreement_date:
			if self.agreement_date > self.last_agreement_date:
				raise osv.except_osv(_('Error!'),_("You cannot submit the agreement after last date of agreement"))


	@api.onchange('bg_date')
	def onchange_bg_date(self):
		if self.bg_date:
			if self.bg_date < self.notice_received_date or self.cs_date < self.notice_received_date or self.ps_date < self.notice_received_date:
				raise osv.except_osv(_('Error!'),_("Gaurantee submission is allowed only after the reception of selection notice"))

	@api.onchange('expected_bg_release_date')
	def onchange_expected_bg_release_date(self):
		if self.expected_bg_release_date:
			if self.expected_bg_release_date < self.bg_date:
				raise osv.except_osv(_('Error!'),_("Gaurantee release is allowed only after gaurantee submission"))


	@api.onchange('expected_ps_release_date')
	def onchange_expected_ps_release_date(self):
		if self.expected_ps_release_date:
			if self.expected_ps_release_date < self.ps_date:
				raise osv.except_osv(_('Error!'),_("Gaurantee release is allowed only after gaurantee submission"))


	@api.onchange('expected_cs_release_date')
	def onchange_expected_cs_release_date(self):
		if self.expected_cs_release_date:
			if self.expected_cs_release_date < self.cs_date:
				raise osv.except_osv(_('Error!'),_("Gaurantee release is allowed only after gaurantee submission"))

	@api.multi
	@api.depends('fd_payment_mode')
	def _compute_collateral(self):
		for record in self:
			amount = 0
			collateral = self.env['hiworth.collateral'].search([('date','<=', record.bg_date),('bank_id','=', record.fd_payment_mode.id)],order='date desc', limit=1)
			# print 'chck@--------------------------', collateral, record.fd_payment_mode.limit
			if collateral:
				# print '1---------'
				record.available_collateral = collateral.balance
			else:
				# print '2--------'
				record.available_collateral = record.fd_payment_mode.limit
			# record.fd_amount = (record.fd_percent * record.bg_amount)/100

	@api.multi
	@api.depends('pac','apac')
	def _compute_apac_details(self):
		for record in self:
			if record.pac != 0 and record.apac != 0:
				if record.pac < record.apac:
					record.status = 'above'
					record.percent = ((record.apac - record.pac)/record.pac)*100

				elif record.pac > record.apac:
					record.status = 'below'
					record.percent = ((record.pac - record.apac)/record.pac)*100

				if record.pac - record.apac == 0:
					record.status = 'equal'
			else:
				record.status = 'cancel'




	@api.multi
	def button_approve(self):
		self.initial_state = 'approved'
		
	@api.multi
	def button_cancel_initial(self):
		# print "rrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr"
		self.initial_state = 'cancel'
	
	@api.multi
	def button_reset_draft_intial(self):
		self.initial_state = 'draft'
		

	@api.multi
	def button_reject(self):
		unattended_obj = self.env['unattended.tender']
		self.initial_state = 'rejected'
		vals = {}
		vals.update({'date': datetime.now(),
					 'epac': self.apac,
					 'name_of_work': self.name,
					 'district': self.district_id.id})
		unattended_obj.create(vals)

	@api.multi
	def button_apac_approval(self):
		self.state = 'apac_approve'
		
	
	@api.multi
	def action_transfer_quot(self):
		self.state = 'transfer_quot'

	@api.multi
	def button_transfer_qout(self):
		
		record = self.env['hiworth.tender.emd'].search([('tender_id', '=', self.id)])
		
		if record:
			res_id = record[0].id
		else:
			res_id = False
		view_id = self.env.ref('hiworth_construction.view_hiworth_tender_emd_form').id
		
		# res = {
		# 	'name': 'EMD Deposit',
		# 	'view_type': 'form',
		# 	'view_mode': 'form',
		# 	'res_model': 'hiworth.tender.emd',
		# 	# 'domain': [('id', '=', self.id),('date','=',self.date)],
		# 	'res_id': res_id,
		# 	'view_id': view_id,
		# 	'target': 'current',
		# 	'type': 'ir.actions.act_window',
		# 	'context': {},
		# 	'target': 'new'
		#
		# }
		#
		# return res
		
		res = {
			'name': 'EMD Payment',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hiworth.tender.emd',
			# 'domain': [('line_id', '=', self.id),('date','=',self.date)],
			'res_id': res_id,
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_tender_id': self.id,'default_emd': self.emd,'default_tender_cost': self.tender_cost,'default_technical_opening_date': self.technical_opening_date,'default_financial_opening_date': self.financial_opening_date},

		}

		return res

	@api.multi
	def create_tender_code(self):
		self.tender_code = self.env['ir.sequence'].next_by_code('hiworth.tender.code')

	@api.multi
	def button_technical_bid_open(self):
		self.state = 'technical_bid'
		self.env['party.history'].create({
							'tender_id': self.id,
							'partner_id' : self.contractor_id1.id,
							'quoted_amount' : self.apac
							})


	@api.multi
	def button_financial_bid_open(self):
		if not self.financial_opening_date:
			raise osv.except_osv(_('Warning'),_("Please Enter Financial Opening Date"))
		self.state = 'financial_bid'

	@api.multi
	def button_receive_selection(self):
		self.state = 'selected'
		# print 'ooooooo-----------', self.notice_received_date
		if self.notice_received_date == False:
			raise osv.except_osv(_('Error!'),_("Please enter selection notice received date"))
		
		if self.notice_no == False:
			raise osv.except_osv(_('Error!'),_("Please enter selection notice number"))
		
		if self.last_agreement_date == False:
			raise osv.except_osv(_('Error!'),_("Please enter last date of agreement"))
		
		# if self.package_no == False:
		# 	raise osv.except_osv(_('Error!'),_("Please enter package number"))

	
	

	@api.multi
	def button_gaurantee_entries(self):

		res = {
			'name': 'Security Deposit Form',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hiworth.security.deposit',
			# 'domain': [('line_id', '=', self.id),('date','=',self.date)],
			# 'res_id': res_id,
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_work_id': self.id,
						'default_contractor_id': self.contractor_id1.id,
						'default_department': self.customer_id.id,
						'default_tender_amount': self.pac,
						'default_accepted_pac': self.apac,
						'default_status': self.status
						},

		}

		return res


	@api.multi
	def view_security_deposit(self):
		record =  self.env['hiworth.security.deposit'].search([('work_id','=',self.id)])

		if record:
			res_id = record[0].id
		else:
			res_id = False
		view_id = self.env.ref('hiworth_construction.view_tender_security_deposit_form').id

		res = {
		   'name': 'Security Deposit',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hiworth.security.deposit',
			# 'domain': [('id', '=', self.id),('date','=',self.date)],
			'res_id': res_id,
			'view_id': view_id,
			'target': 'current',
			'type': 'ir.actions.act_window',
			'context': {},
			'target': 'new'

		}

		return res


	@api.multi
	def view_emd_deposit(self):
		record =  self.env['hiworth.tender.emd'].search([('tender_id','=',self.id)])

		if record:
			res_id = record[0].id
		else:
			res_id = False
		view_id = self.env.ref('hiworth_construction.view_hiworth_tender_emd_form').id

		res = {
		   'name': 'EMD Deposit',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hiworth.tender.emd',
			# 'domain': [('id', '=', self.id),('date','=',self.date)],
			'res_id': res_id,
			'view_id': view_id,
			'target': 'current',
			'type': 'ir.actions.act_window',
			'context': {},
			'target': 'new'

		}

		return res
		

	@api.multi
	def button_technical_reject(self):
		if self.state in ['draft','apac_approve','emd_payment']:
			unattended_obj = self.env['unattended.tender']
			vals = {}
			vals.update({'date': datetime.now(),
						 'epac': self.apac,
						 'name_of_work': self.name,
						 'district': self.district_id.id})
			unattended_obj.create(vals)
			self.state = 'cancel'
		else:
			self.state = 'rejected'
			self.reject = True
		
		

	@api.multi
	def button_cancel(self):
		self.state = 'cancel'
		self.emd_boolean = False
		self.bg_boolean = False
		self.cs_boolean = False
		self.ps_boolean = False
		moves = self.env['account.move'].search([('tender_id','=',self.id)])
		for move in moves:
			move.button_cancel()
			move.unlink()

	@api.multi
	def button_create_project(self):
		# print 'company====================='
		# print asd
		project = self.env['project.project'].create({'name':self.name,
											'contractor_id':self.contractor_id1.id,
											'awarder_id':self.customer_id.id,
											'location_id':self.location_id.id,
											'tender_id':self.id,
											'company_id':self.company_id.id,
											'tender_location':False,
											'state': 'draft'
											})
		for attach in self.attachment_ids:
			attach.project_id = project.id
		self.is_project_created = True

	@api.multi
	def button_reset_draft(self):
		self.state = 'draft'


	@api.multi
	@api.depends('emd_date','return_emd_date')
	def _compute_no_emd(self):
		for record in self:
			if record.emd_date and record.return_emd_date: 
				d1 = datetime.strptime(record.emd_date, "%Y-%m-%d")
				d2 = datetime.strptime(record.return_emd_date, "%Y-%m-%d")
				record.no_emd_days = abs((d2 - d1).days)


	@api.multi
	def button_payment(self):
		res = {
			'name': 'EMD Payment',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hiworth.tender.emd',
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_tender_id': self.id},

		}

		return res

	

	

	@api.multi
	def button_emd_return(self):
		res = {
			'name': 'EMD Release',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'hiworth.tender.emd.return',
			# 'domain': [('line_id', '=', self.id),('date','=',self.date)],
			# 'res_id': res_id,
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_tender_id': self.id,'default_emd': self.emd},

		}

		return res

	@api.multi
	def button_bg_release(self):
		res = {
			'name': 'Bank Gaurantee Release',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'tender.bg.release',
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_tender_id': self.id,'default_bg_amount': self.bg_amount,'default_fd_amount': self.fd_amount},

		}

		return res

	@api.multi
	def button_common_security_release(self):
		res = {
			'name': 'Common Security Release',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'tender.cs.release',
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_tender_id': self.id,'default_cs_amount': self.com_security_amount},

		}

		return res

	@api.multi
	def button_performance_security_release(self):
		res = {
			'name': 'Performance Security Release',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'tender.ps.release',
			'target': 'new',
			'type': 'ir.actions.act_window',
			'context': {'default_tender_id': self.id,'default_ps_amount': self.performance_security_amount},

		}

		return res

class Tender_bg_release(models.TransientModel):
	_name = 'tender.bg.release'


	bg_amount = fields.Float('Released BG Amount')
	fd_amount = fields.Float('Released FD Amount')
	date = fields.Date('Released Date', default=fields.Date.today)
	account_id = fields.Many2one('account.account', 'Account')
	tender_id = fields.Many2one('hiworth.tender')

	@api.onchange('date')
	def onchange_date(self):
		if self.date:
			if self.date < self.tender_id.bg_date:
				raise osv.except_osv(_('Error!'),_("Gaurantee release is allowed only after gaurantee submission"))


	@api.multi
	def button_confirm(self):
		collateral = self.env['hiworth.collateral'].create({
											'date': datetime.now(),
											'bank_id': self.tender_id.fd_payment_mode.id,
											'credit': 0,
											'debit': self.bg_amount,
											})
		collateral._compute_collateral_balance()
		collateral.state = 'approve'
		# print 'asassasas-------------------11'
		self.tender_id.bg_boolean = True
		self.tender_id.release_bg = self.bg_amount
		self.tender_id.release_bg_date = self.date
		self.tender_id.release_bg_account = self.account_id.id

		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		# print 'asassasas-------------------21', self.tender_id.fd_payment_mode.journal_id.id, self.date, self.id
		move_id = move.create({
							'journal_id': self.tender_id.fd_payment_mode.journal_id.id,
							'date': datetime.now(),
							'tender_id': self.tender_id.id
							})
		# print 'asassasas-------------------22'
		
		line_id = move_line.create({
								'account_id': self.account_id.id,
								'name': 'Released FD Amount',
								'credit': self.fd_amount,
								'debit': 0,
								'move_id': move_id.id,
								})
			
		# print 'asassasas-------------------23'
		line_id = move_line.create({
								'account_id': self.tender_id.fd_payment_mode.journal_id.default_debit_account_id.id,
								'name': 'Released FD Amount',
								'credit': 0,
								'debit': self.fd_amount,
								'move_id': move_id.id,
								})
		move_id.button_validate()
		# print 'asassasas-------------------33'

		if self.tender_id.emd_boolean == True and self.tender_id.bg_boolean == True and self.tender_id.cs_boolean == True and self.tender_id.ps_boolean == True:
			self.tender_id.state = 'closed'

class Tender_cs_release(models.TransientModel):
	_name = 'tender.cs.release'


	cs_amount = fields.Float('Released CS Amount')
	date = fields.Date('Released Date', default=fields.Date.today)
	account_id = fields.Many2one('account.account', 'Account')
	tender_id = fields.Many2one('hiworth.tender')

	@api.onchange('date')
	def onchange_date(self):
		if self.date:
			if self.date < self.tender_id.cs_date:
				raise osv.except_osv(_('Error!'),_("Gaurantee release is allowed only after gaurantee submission"))


	@api.multi
	def button_confirm(self):
		self.tender_id.cs_boolean = True
		self.tender_id.release_cs = self.cs_amount
		self.tender_id.release_cs_date = self.date
		self.tender_id.release_cs_account = self.account_id.id

		move = self.env['account.move']
		move_line = self.env['account.move.line']

		move_id1 = move.create({
							'journal_id': self.tender_id.com_security_payment_mode.journal_id.id,
							'date': datetime.now(),
							'tender_id': self.tender_id.id
							})

		line_id = move_line.create({
								'account_id': self.account_id.id,
								'name': 'Released Common Security Amount',
								'credit': self.cs_amount,
								'debit': 0,
								'move_id': move_id1.id,
								})
			
		line_id = move_line.create({
								'account_id': self.tender_id.com_security_payment_mode.journal_id.default_debit_account_id.id,
								'name': 'Released Common Security Amount',
								'credit': 0,
								'debit': self.cs_amount,
								'move_id': move_id1.id,
								})
		move_id1.button_validate()
		# print 'asassasas-------------------00000'
		if self.tender_id.emd_boolean == True and self.tender_id.bg_boolean == True and self.tender_id.cs_boolean == True and self.tender_id.ps_boolean == True:
			self.tender_id.state = 'closed'



class Tender_ps_release(models.TransientModel):
	_name = 'tender.ps.release'


	ps_amount = fields.Float('Released PS Amount')
	date = fields.Date('Released Date', default=fields.Date.today)
	account_id = fields.Many2one('account.account', 'Account')
	tender_id = fields.Many2one('hiworth.tender')

	@api.onchange('date')
	def onchange_date(self):
		if self.date:
			if self.date < self.tender_id.ps_date:
				raise osv.except_osv(_('Error!'),_("Gaurantee release is allowed only after gaurantee submission"))


	@api.multi
	def button_confirm(self):
		self.tender_id.ps_boolean = True
		self.tender_id.release_ps = self.ps_amount
		self.tender_id.release_ps_date = self.date
		self.tender_id.release_ps_account = self.account_id.id

		move = self.env['account.move']
		move_line = self.env['account.move.line']

		# Performance Security

		move_id2 = move.create({
						'journal_id': self.tender_id.performance_security_payment_mode.journal_id.id,
						'date': datetime.now(),
						'tender_id': self.tender_id.id
						})

		line_id = move_line.create({
							'account_id': self.account_id.id,
							'name': 'Released Performance Security Amount',
							'credit': self.ps_amount,
							'debit': 0,
							'move_id': move_id2.id,
							})
		
		line_id = move_line.create({
							'account_id': self.tender_id.performance_security_payment_mode.journal_id.default_debit_account_id.id,
							'name': 'Released Performance Security Amount',
							'credit': 0,
							'debit': self.ps_amount,
							'move_id': move_id2.id,
							})

		move_id2.button_validate()
		if self.tender_id.emd_boolean == True and self.tender_id.bg_boolean == True and self.tender_id.cs_boolean == True and self.tender_id.ps_boolean == True:
			self.tender_id.state = 'closed'
		


class HiworthTenderEMD(models.Model):
	_name = 'hiworth.tender.emd'


	
	
	emd_number = fields.Char('EMD Reference')
	emd_date = fields.Date('Date of EMD',default=fields.Date.today)
	tender_id = fields.Many2one('hiworth.tender')
	bank_id = fields.Many2one('res.partner.bank', 'Bank Account')
	bank_id_emd = fields.Many2one('res.partner.bank', 'Bank Account')
	emd = fields.Float('EMD Amount')
	emd_account = fields.Many2one('account.account', string="EMD Account")

	tender_cost = fields.Float('Cost Of Tender')
	tender_cost_account = fields.Many2one('account.account', string="Tender Cost Account")

	technical_opening_date = fields.Date('Technical Bid Opening Date')
	financial_opening_date = fields.Date('Financial Bid Opening Date')
	state = fields.Selection([('draft','Draft'),
							('confirm','Confirmed'),
							('paid','Paid'),
							  ('cancel','Cancel'),
							], default="draft")

	emd_mode = fields.Selection([('bg','BG'),
							('bank','Bank'),
							('fd','FD'),
							('dd','DD'),
							('nsc','NSC'),
							('without_emd','Without EMD'),
							], string="Mode of EMD")

	tender_cost_mode = fields.Selection([('bg','BG'),
							('bank','Bank'),
							('cash','Cash'),
							('dd','DD'),
							('without_tender','Without tender'),
							], string="Mode of Tender Cost")

	account_id = fields.Many2one('account.account',string="Account")
	tender_account_id = fields.Many2one('account.account',string="Account")
	percent = fields.Float(string="% Amount")
	fd = fields.Float(string="FD", compute="_compute_fd")

	mode_tender_fee_pay = fields.Selection([('bg_fd','BG and Related BG caution deposit FD'),
									 ('fd','FD'),
									 ('dd','DD'),
									 ('nsc','NSC'),
									 ('cash','Cash'),
									 ('online','Online Payment - Bank')],'Mode of Tender Fee Payment')
	mode_emd_pay = fields.Selection([('bg_fd','BG and Related BG caution deposit FD'),
									 ('fd','FD'),
									 ('dd','DD'),
									 ('nsc','NSC'),
									 ('online','Online Payment - Bank')],'Mode of EMD Payment')
	
	
	
	
		
	
	
	
	@api.one
	@api.depends('emd','percent')
	def _compute_fd(self):
		if self.emd and self.percent:
			self.fd = (self.emd*self.percent)/100

	@api.onchange('technical_opening_date')
	def onchange_technical_date(self):
		if self.technical_opening_date:
			if self.technical_opening_date < self.emd_date:
				raise osv.except_osv(_('Error!'),_("Technical opening date must be greater than date of emd"))


	@api.onchange('financial_opening_date')
	def onchange_financial_date(self):
		if self.financial_opening_date:
			if self.financial_opening_date < self.technical_opening_date:
				raise osv.except_osv(_('Error!'),_("Financial bid opening is possible only after technical bid opening"))


	@api.multi
	def button_confirm(self):
		if not self.emd_number:
			self.emd_number = self.env['ir.sequence'].next_by_code('emd.payment')
		self.state = 'confirm'

	@api.multi
	def button_payment(self):
		self.state = 'paid'
		self.tender_id.state = 'emd_payment'
		""" self.tender_id.emd = self.emd"""
		self.tender_id.emd_number = self.emd_number
		self.tender_id.emd_date = self.emd_date
		self.tender_id.bank_id = self.bank_id.id
		self.tender_id.bank_id_emd = self.bank_id_emd.id
		""" self.tender_id.tender_cost = self.tender_cost"""
		self.tender_id.emd_account = self.emd_account.id
		self.tender_id.tender_cost_account = self.tender_cost_account.id
		self.tender_id.technical_opening_date = self.technical_opening_date
		self.tender_id.financial_opening_date = self.financial_opening_date
		self.tender_id.mode_emd_pay = self.mode_emd_pay
		self.tender_id.tender_cost = self.tender_cost
		self.tender_id.mode_tender_fee_pay = self.mode_tender_fee_pay
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		values1 = {
				'journal_id': self.bank_id.journal_id.id,
				'date': datetime.now(),
				'tender_id': self.tender_id.id
				}
		move_id = move.create(values1)
		
		values2 = {
				'account_id': self.emd_account.id,
				'name': 'EMD Amount',
				'debit': self.emd,
				'credit': 0,
				'move_id': move_id.id,
				}

		line_id = move_line.create(values2)
			
		values3 = {
			'account_id': self.bank_id.journal_id.default_credit_account_id.id,
			'name': 'EMD Amount',
			'debit': 0,
			'credit': self.emd,
			'move_id': move_id.id,
			}
		line_id = move_line.create(values3)
		move_id.button_validate()

		values4 = {
				'journal_id': self.bank_id.journal_id.id,
				'date': datetime.now(),
				'tender_id': self.tender_id.id
				}
		move_id = move.create(values4)
		
		values2 = {
				'account_id': self.tender_cost_account.id,
				'name': 'Cost of Tender Amount',
				'debit': self.tender_cost,
				'credit': 0,
				'move_id': move_id.id,
				}

		line_id = move_line.create(values2)
			
		values = {
			'account_id': self.bank_id.journal_id.default_credit_account_id.id,
			'name': 'Cost of Tender Amount',
			'debit': 0,
			'credit': self.tender_cost,
			'move_id': move_id.id,
			}
		line_id = move_line.create(values)
		move_id.button_validate()
		self.tender_id.create_tender_code()
		# print "=-=-=-=-=-=-=-==-=-=--2222"

	@api.multi
	def button_cancel(self):
		self.state = 'cancel'
	
	@api.multi
	def button_set_to_draft(self):
		self.state = 'draft'


class HiworthTenderEMD(models.TransientModel):
	_name = 'hiworth.tender.emd.return'


	emd = fields.Float('EMD Amount Returned')
	emd_date = fields.Date('Date of Return', default=fields.Date.today)
	bank_id = fields.Many2one('res.partner.bank', 'Bank Account')
	tender_id = fields.Many2one('hiworth.tender')

	@api.onchange('emd_date')
	def onchange_emd_date(self):
		if self.emd_date:
			if self.emd_date < self.tender_id.emd_date:
				raise osv.except_osv(_('Error!'),_("EMD release is allowed only after the date of EMD"))


	@api.multi
	def button_confirm(self):
		# print 'self.tender_id.state-----------',self.tender_id.state
		if self.tender_id.state == 'rejected':
			self.tender_id.state = 'closed'
			# print 'self.tender_id.state1111-----------',self.tender_id.state

		self.tender_id.emd_boolean = True
		# self.tender_id.state = 'closed'
		self.tender_id.return_emd = self.emd
		self.tender_id.return_emd_date = self.emd_date
		self.tender_id.return_bank_id = self.bank_id.id
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		values = {
				'journal_id': self.bank_id.journal_id.id,
				'date': datetime.now(),
				'tender_id': self.tender_id.id
				}
		move_id = move.create(values)
		
		values2 = {
				'account_id': self.bank_id.journal_id.default_credit_account_id.id,
				'name': 'EMD Amount Returned',
				'debit': self.emd,
				'credit': 0,
				'move_id': move_id.id,
				}

		line_id = move_line.create(values2)
			
		values = {
			'account_id': self.tender_id.emd_account.id,
			'name': 'EMD Amount Returned',
			'debit': 0,
			'credit': self.emd,
			'move_id': move_id.id,
			}
		line_id = move_line.create(values)
		move_id.button_validate()
		if self.tender_id.emd_boolean == True and self.tender_id.bg_boolean == True and self.tender_id.cs_boolean == True and self.tender_id.ps_boolean == True:
			self.tender_id.state = 'closed'



class SecurityDepositForm(models.Model):
	_name = 'hiworth.security.deposit'
	_rec_name = 'road_name'
	
	company_id = fields.Many2one('res.company','Name of Company')
	road_name = fields.Char('Name of Road')
	bank_name = fields.Char('BG Bank Name')
	work_id = fields.Many2one('hiworth.tender','Name of Work')
	contractor_id = fields.Many2one('res.partner',domain="[('contractor', '=', True)]", string='Name of Contractor')
	department = fields.Many2one('res.partner')
	tender_amount = fields.Float('Tender Amount')
	accepted_pac = fields.Float('Accepted PAC')
	status = fields.Selection([('above','Above'),
							   ('below','Below'),
							   ('equal','Equal')
							   ], 'Status')
	state = fields.Selection([('draft','Draft'),
							('confirm','Confirmed'),
							('verify','Verified'),
							('approve','Approved'),
							('submission','Submitted')
							], default="draft")

	security_deposit_based = fields.Selection([('pac','PAC'),
												('apac','APAC')
												],string="Security Deposit Based On")
	
	security_deposit_percent = fields.Float('% of Security Deposit')

	security_wo_round_off = fields.Float('Amount w/o round-off', compute="_compute_amount", store=True)
	security_round_off = fields.Float('Round Off')
	security_deposit_amount = fields.Float('Security Deposit Amount', compute="_compute_amount", store=True)
	
	bg_percent = fields.Float('% of Security Deposit Through Bank')
	treasury_percent = fields.Float('% of Security Deposit Through Treasury')

	bg_date = fields.Date('Date', default=fields.Date.today)
	bg_issue_date = fields.Date('BG Issue Date')
	bg_expiry_date = fields.Date('BG Expiry Date')
	bg_amount = fields.Float('Bank Guarantee Amount', compute="_compute_amount", store=True)
	bg_amount_roundoff = fields.Float('BG Amount Round-Off')
	available_collateral = fields.Float('Available Collateral', compute="_compute_collateral", store=True)
	fd_percent = fields.Float('FD Percent')
	fd_amount_wo_roundoff = fields.Float('FD Amount w/o round-off', compute="_compute_fd_amount", store=True)
	fd_round_off = fields.Float('Round-Off')
	fd_amount = fields.Float('BG-FD amount', compute="_compute_fd_amount", store=True)
	fd_payment_mode = fields.Many2one('res.partner.bank', string='FD Payment Mode')
	fd_account = fields.Many2one('account.account','FD Account')
	fd_issue_date = fields.Date('Date of Issue FD')
	fd_number = fields.Char('FD Number')
	fd_no_of_days = fields.Float('FD No. of Days')
	fd_holder = fields.Char('FD Holder Name')
	fd_mature_value = fields.Float('FD Mature Value')
	fd_interest = fields.Float('FD Interest')
	fd_period = fields.Char('BG Duration')
	expected_bg_release_date = fields.Date('FD Maturity Date')

	cs_date = fields.Date('Date', default=fields.Date.today)
	com_security_amount = fields.Float('Normal Security Amount', compute="_compute_amount", store=True)
	com_security_amount_round_off = fields.Float('Normal Security Amount Round-Off')
	com_security_account = fields.Many2one('account.account','Normal Security Account')
	com_security_payment_mode = fields.Many2one('account.journal', string='Normal Security Payment Mode', domain="[('type','in',['cash','bank'])]")
	expected_cs_release_date = fields.Date('Maturity Date')
	cs_treasury_id = fields.Many2one('res.partner', 'Treasury Name')
	treasury_number = fields.Char('Treasury Number')
	treasury_period = fields.Char('Period')

	ps_date = fields.Date('Date', default=fields.Date.today)
	perf_security_mode = fields.Selection([('bank','Bank'),
											('treasury','Treasury')
											], string="Performance Security Deposit Through")
	ps_wo_round_off = fields.Float('PS Amount w/o Round-off')
	ps_round_off = fields.Float('Round Off')
	performance_security_amount = fields.Float('PS Amount', compute="_compute_amount", store=True)
	ps_fd_percent = fields.Float('FD Percent')
	ps_fd_amount = fields.Float('PS-FD Amount', compute="_compute_amount", store=True)
	performance_security_account = fields.Many2one('account.account','PS Account')
	perf_bank_id = fields.Many2one('res.partner.bank', string='PS Payment Mode(Bank)')
	performance_security_payment_mode = fields.Many2one('account.journal', string='PS Payment Mode', domain="[('type','in',['cash','bank'])]")
	expected_ps_release_date = fields.Date('Maturity Date')
	ps_treasury_id = fields.Many2one('res.partner', 'Treasury Name')
	perf_security_period = fields.Char('Period')
	perf_security_number = fields.Char('Performance Security Number')

	remarks = fields.Text('Remarks')

	prepared_by = fields.Many2one('res.users', 'Prepared By')
	verified_by = fields.Many2one('res.users', 'Verified By')
	approved_by = fields.Many2one('res.users', 'Approved By')

	@api.multi
	@api.depends('security_deposit_based','security_deposit_percent','security_wo_round_off','security_round_off','ps_wo_round_off','ps_round_off','treasury_percent','bg_percent')
	def _compute_amount(self):
		for record in self:
			if record.security_deposit_based == 'pac':
				record.security_wo_round_off = (record.tender_amount * record.security_deposit_percent)/100
			elif record.security_deposit_based == 'apac':
				record.security_wo_round_off = (record.accepted_pac * record.security_deposit_percent)/100
			else:
				pass
			record.security_deposit_amount = record.security_wo_round_off + record.security_round_off
			record.performance_security_amount = record.ps_wo_round_off + record.ps_round_off
			
			record.bg_amount = (record.security_deposit_amount * record.bg_percent)/100
			record.com_security_amount = (record.security_deposit_amount * record.treasury_percent)/100

			record.ps_fd_amount = (record.performance_security_amount * record.ps_fd_percent)/100

	@api.multi
	@api.depends('bg_amount','fd_percent','fd_round_off')
	def _compute_fd_amount(self):
		for record in self:

			record.fd_amount_wo_roundoff = (record.bg_amount_roundoff * record.fd_percent)/100
			record.fd_amount = record.fd_amount_wo_roundoff + record.fd_round_off


	@api.multi
	def button_confirm(self):
		self.prepared_by = self.env.user.id
		self.state = 'confirm'
		self.work_id.state = 'processing'


	@api.multi
	def button_verify(self):
		self.verified_by = self.env.user.id
		self.state = 'verify'

	@api.multi
	def button_approve(self):
		self.approved_by = self.env.user.id
		self.state = 'approve'

	@api.multi
	def button_submit(self):
		self.work_id.state = 'submission'
		self.state = 'submission'
		
		self.work_id.security_deposit_based = self.security_deposit_based
		self.work_id.security_deposit_percent = self.security_deposit_percent
		self.work_id.security_wo_round_off = self.security_wo_round_off
		self.work_id.security_round_off = self.security_round_off
		self.work_id.security_deposit_amount = self.security_deposit_amount
		self.work_id.bg_percent = self.bg_percent
		self.work_id.treasury_percent = self.treasury_percent
		self.work_id.bg_date = self.bg_date
		self.work_id.cs_date = self.cs_date
		self.work_id.ps_date = self.ps_date

		self.work_id.bg_amount = self.bg_amount
		self.work_id.available_collateral = self.available_collateral
		self.work_id.fd_percent = self.fd_percent
		self.work_id.fd_amount_wo_roundoff = self.fd_amount_wo_roundoff
		self.work_id.fd_round_off = self.fd_round_off
		self.work_id.fd_amount = self.fd_amount
		self.work_id.fd_payment_mode = self.fd_payment_mode.id
		self.work_id.fd_account = self.fd_account.id
		self.work_id.fd_number = self.fd_number
		self.work_id.fd_period = self.fd_period
		self.work_id.expected_bg_release_date = self.expected_bg_release_date
		self.work_id.com_security_amount = self.com_security_amount
		self.work_id.com_security_account = self.com_security_account.id
		self.work_id.com_security_payment_mode = self.com_security_payment_mode.id
		self.work_id.expected_cs_release_date = self.expected_cs_release_date
		self.work_id.cs_treasury_id = self.cs_treasury_id.id
		self.work_id.treasury_number = self.treasury_number
		self.work_id.treasury_period = self.treasury_period

		self.work_id.perf_security_mode = self.perf_security_mode
		self.work_id.performance_security_amount = self.performance_security_amount
		self.work_id.ps_wo_round_off = self.ps_wo_round_off
		self.work_id.ps_round_off = self.ps_round_off
		self.work_id.ps_fd_percent = self.ps_fd_percent
		self.work_id.ps_fd_amount = self.ps_fd_amount
		self.work_id.performance_security_account = self.performance_security_account.id
		self.work_id.perf_bank_id = self.perf_bank_id.id
		self.work_id.performance_security_payment_mode = self.performance_security_payment_mode.id
		# self.work_id.ps_security_type = self.ps_security_type.id
		self.work_id.expected_ps_release_date = self.expected_ps_release_date
		self.work_id.ps_treasury_id = self.ps_treasury_id.id
		self.work_id.perf_security_period = self.perf_security_period
		self.work_id.perf_security_number = self.perf_security_number
		self.work_id.remarks = self.remarks
		# print 'test0-----------------------------'


		collateral = self.env['hiworth.collateral'].create({
											'date': datetime.now(),
											'bank_id': self.fd_payment_mode.id,
											'debit': 0,
											'credit': self.bg_amount,
											})
		collateral._compute_collateral_balance()
		collateral.state = 'approve'

		if self.perf_security_mode == 'bank':
			collateral = self.env['hiworth.collateral'].create({
											'date': datetime.now(),
											'bank_id': self.perf_bank_id.id,
											'debit': 0,
											'credit': self.ps_fd_amount,
											})
		collateral._compute_collateral_balance()
		collateral.state = 'approve'

		# print 'test1-----------------------------'

		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		# FD
		if self.fd_amount != 0:
			move_id = move.create({
								'journal_id': self.fd_payment_mode.journal_id.id,
								'date': datetime.now(),
								'tender_id': self.work_id.id
								})
			
			# print 'test11-----------------------------'
			line_id = move_line.create({
									'account_id': self.fd_account.id,
									'name': 'FD Amount',
									'debit': self.fd_amount,
									'credit': 0,
									'move_id': move_id.id,
									'status': 'draft'
									})
			# print 'test22-----------------------------'
				
			line_id = move_line.create({
									'account_id': self.fd_payment_mode.journal_id.default_credit_account_id.id,
									'name': 'FD Amount',
									'debit': 0,
									'credit': self.fd_amount,
									'move_id': move_id.id,
									'status': 'draft'
									})
			# print 'test33-----------------------------'
			move_id.button_validate()
			# print 'test2-----------------------------'
		# Common Security

		if self.com_security_amount != 0:

			move_id1 = move.create({
								# 'journal_id': self.com_security_payment_mode.journal_id.id,
								'journal_id': self.com_security_payment_mode.id,
								'date': datetime.now(),
								'tender_id': self.work_id.id
								})

			line_id = move_line.create({
									'account_id': self.com_security_account.id,
									'name': 'Common Security Amount',
									'debit': self.com_security_amount,
									'credit': 0,
									'move_id': move_id1.id,
									'status': 'draft'
									})
				
			line_id = move_line.create({
									'account_id': self.com_security_payment_mode.default_credit_account_id.id,
									'name': 'Common Security Amount',
									'debit': 0,
									'credit': self.com_security_amount,
									'move_id': move_id1.id,
									'status': 'draft'
									})
			move_id1.button_validate()

		# print 'test3-----------------------------'
		# Performance Security
		# if self.status == 'below' and self.performance_security_amount != 0:
		if self.performance_security_amount != 0:

			if self.perf_security_mode == 'bank':
				move_id2 = move.create({
								'journal_id': self.perf_bank_id.journal_id.id,
								'date': datetime.now(),
								'tender_id': self.work_id.id
								})

				line_id = move_line.create({
									'account_id': self.performance_security_account.id,
									'name': 'Performance Security Amount',
									'debit': self.performance_security_amount,
									'credit': 0,
									'move_id': move_id2.id,
									'status': 'draft'
									})

				line_id = move_line.create({
								'account_id': self.perf_bank_id.journal_id.default_credit_account_id.id,
								'name': 'Performance Security Amount',
								'debit': 0,
								'credit': self.performance_security_amount,
								'move_id': move_id2.id,
								'status': 'draft'
								})
				move_id2.button_validate()
			elif self.perf_security_mode == 'treasury':
				move_id2 = move.create({
								'journal_id': self.performance_security_payment_mode.id,
								'date': datetime.now(),
								'tender_id': self.work_id.id
								})

				line_id = move_line.create({
									'account_id': self.performance_security_account.id,
									'name': 'Performance Security Amount',
									'debit': self.performance_security_amount,
									'credit': 0,
									'move_id': move_id2.id,
									'status': 'draft'
									})
				line_id = move_line.create({
								'account_id': self.performance_security_payment_mode.default_credit_account_id.id,
								'name': 'Performance Security Amount',
								'debit': 0,
								'credit': self.performance_security_amount,
								'move_id': move_id2.id,
								'status': 'draft'
								})

				move_id2.button_validate()

			else:
				pass
		# print 'test4-----------------------------'



	@api.multi
	@api.depends('fd_payment_mode')
	def _compute_collateral(self):
		for record in self:
			amount = 0
			collateral = self.env['hiworth.collateral'].search([('date','<=', record.bg_date),('bank_id','=', record.fd_payment_mode.id)],order='date desc', limit=1)
			# print 'chck@--------------------------', collateral, record.fd_payment_mode.limit
			if collateral:
				# print '1---------'
				record.available_collateral = collateral.balance
			else:
				# print '2--------'
				record.available_collateral = record.fd_payment_mode.limit
			# record.fd_amount = (record.fd_percent * record.bg_amount)/100


class PartyHistory1(models.Model):
	_name = 'party.history'


	tender_id = fields.Many2one('hiworth.tender')
	partner_id = fields.Many2one('res.partner', string="Party Name", domain=[('contractor','=',True)])
	status = fields.Selection([('approved','Approved'),
							('rejected','Rejected'),
							('cancel','Cancelled')
							], string='Status')
	quoted_amount = fields.Float('Quoted Amount')
	percentage = fields.Float('Percentage', compute="_compute_status")
	tender_position = fields.Char('Status', compute="_compute_status")
	remarks = fields.Char("Remarks")

	@api.multi
	def _compute_status(self):
		for record in self:
			vals = 1
			parties = self.env['party.history'].search([('tender_id','=', record.tender_id.id)], order='quoted_amount asc')
			for party in parties:
				party.tender_position = 'L' + str(vals)
				vals += 1

			if record.tender_id.pac != 0 and record.quoted_amount != 0:
				if record.tender_id.pac < record.quoted_amount:
					record.percentage = ((record.quoted_amount - record.tender_id.pac)/record.tender_id.pac)*100

				elif record.tender_id.pac > record.quoted_amount:
					record.percentage = -((record.tender_id.pac - record.quoted_amount)/record.tender_id.pac)*100

				if record.tender_id.pac - record.quoted_amount == 0:
					record.percentage = 100
					




class TenderEMDReturnStatus(models.Model):
	_name = 'tender.emd.return.status'


	tender_id = fields.Many2one('hiworth.tender')
	date = fields.Date('Date',default=fields.Date.today)
	followup_date = fields.Date('Next Follow Up Date')
	contact_person = fields.Char('Contacted  Person')
	remarks = fields.Text('Remarks')


class TenderAttachments(models.Model):
	_name = 'tender.attachments'


	tender_id = fields.Many2one('hiworth.tender',"Tender")
	date = fields.Date('Date',default=fields.Date.today)
	name = fields.Char('Name')
	binary_field = fields.Binary('File')
	filename = fields.Char('Filename')
	project_id = fields.Many2one('project.project',"Project")


class HiworthCollateral(models.Model):
	_name = 'hiworth.collateral'


	date = fields.Datetime('Date',default=fields.Datetime.now)
	bank_id = fields.Many2one('res.partner.bank', string="Related Bank Account")
	debit = fields.Float('Debit')
	credit = fields.Float('Credit')
	limit = fields.Float('Limit', related='bank_id.limit', store=True,)
	balance = fields.Float('Balance', compute="_compute_collateral_balance", store=True)
	state = fields.Selection([('draft','Draft'),
							('approve','Approved')
							], default="draft")
	
	type = fields.Selection([('bg','BG'),('trasurey','Treasury Deposit')],string="Type")

	# @api.multi
	# def _compute_limit(self):
	#     for record in self:
	#         record.limit = record.bank_id.limit


	@api.multi
	def button_approve(self):
		for record in self:
			record.state = 'approve'


	@api.multi
	@api.depends('debit','credit')
	def _compute_collateral_balance(self):
		for record in self:
			debit = 0
			credit = 0
			collateral = self.env['hiworth.collateral'].search([('bank_id','=',record.bank_id.id)])
			# print 'collateral-------------------------', collateral
			for col_id in collateral:
				debit += col_id.debit
				credit += col_id.credit
			# print 'bal-----------------------------------', debit, credit, record.limit
			record.balance = record.limit + (debit - credit)

	# @api.multi
	# @api.depends('debit','credit')
	# def _compute_collateral_balance(self):
	#     for record in self:
	#         balance = 0
	#         balance = self.env['hiworth.collateral'].search([('bank_id','=',record.bank_id.id),('date','<', record.date)], order="date desc", limit=1).balance
	#         record.balance = balance + (record.debit - record.credit)


class bank(models.Model):
	_inherit = 'res.partner.bank'

	limit = fields.Float('Collateral Limit')
	bank_acc_type_id = fields.Many2one('res.bank.type', string='Bank Account Type')
	ac_number = fields.Char("Account Number")
	ifsc_number = fields.Char("IFSC Number")

	_defaults = {
		'owner_name': lambda obj, cursor, user, context: obj._default_value(
			cursor, user, 'name', context=context),
		'street': lambda obj, cursor, user, context: obj._default_value(
			cursor, user, 'street', context=context),
		'city': lambda obj, cursor, user, context: obj._default_value(
			cursor, user, 'city', context=context),
		'zip': lambda obj, cursor, user, context: obj._default_value(
			cursor, user, 'zip', context=context),
		'country_id': lambda obj, cursor, user, context: obj._default_value(
			cursor, user, 'country_id', context=context),
		'state_id': lambda obj, cursor, user, context: obj._default_value(
			cursor, user, 'state_id', context=context),
		'name': '/',
		'state': 'bank'
	}


	@api.multi
	def write(self,vals):
		result = super(bank, self).write(vals)
		journal = self.env['account.journal'].search([('id','=', self.journal_id.id)])
		journal.name = (self.bank_name or '') + ' ' + (self.acc_number or '')

		account = self.env['account.account'].search([('id','=', self.journal_id.default_debit_account_id.id)])
		account.name = (self.bank_name or '') + ' ' + (self.acc_number or '')

		return result


class ResPartnerBankType(models.Model):
	_name = 'res.bank.type'

	name = fields.Char('Name')

	@api.multi
	def unlink(self):
		for rec in self:
			# print 'qqqqqqqqqqqqq--------------------------------',rec.id
			# print 'qqqqqqqqqqqqq--------------------------------', self.env.ref('hiworth_construction.bank_account_type_od').id
			if self.env.ref('hiworth_construction.bank_account_type_od').id == rec.id:
				raise osv.except_osv(_('Error!'),_("You have no permission to delete OD Account"))
			elif self.env.ref('hiworth_construction.bank_account_type_current').id == rec.id:
				raise osv.except_osv(_('Error!'),_("You have no permission to delete Current Account"))
			else:
				pass

		return super(ResPartnerBankType, self).unlink()

class ResBank1(models.Model):
	_inherit = 'res.bank'

	branch = fields.Char('Branch Name')

	def name_get(self, cr, uid, ids, context=None):
		result = []
		for bank in self.browse(cr, uid, ids, context):
			result.append((bank.id, bank.name + (bank.branch and (' - ' + bank.branch ) or '') ))
		return result


class AccountMove1(models.Model):
	_inherit = 'account.move'

	tender_id = fields.Many2one('hiworth.tender')


class SecurityType(models.Model):
	_name = 'security.type'

	name = fields.Char('Security Type')

class StockLocation(models.Model):
	_inherit = 'stock.location'

	tender_location = fields.Boolean('Is Tender Location', default=False)



	
class UnattendedTender(models.Model):
	_name = 'unattended.tender'
	_rec_name = "name_of_work"

	date = fields.Date(string="Date")
	name_of_work = fields.Char(string="Name of Work")
	epac = fields.Float(string="EPAC")
	district = fields.Many2one('master.district',string="District")
	line_ids = fields.One2many('unattended.tender.line','line_id')

	partner_id = fields.Many2one('res.partner', string="Contractor")
	s_check = fields.Boolean('Status Check')


class UnattendedTenderLine(models.Model):
	_name = 'unattended.tender.line'
	
	@api.depends('partner_id')
	def compute_line_id(self):
		for rec in self:
				rec.date = rec.line_id.date
				rec.epac = rec.line_id.epac
				rec.district = rec.line_id.district.id
				rec.name_of_work = rec.line_id.name_of_work


	





	
	
	line_id = fields.Many2one('unattended.tender')
	date = fields.Date(string="Date",compute='compute_line_id',store=True)
	epac = fields.Float(string="EPAC",compute='compute_line_id',store=True)
	district = fields.Many2one('master.district',compute='compute_line_id', string="District",store=True)
	name_of_work = fields.Char(string="Name of Work",compute='compute_line_id',store=True)
	partner_id = fields.Many2one('res.partner', domain="[('tender_contractor','=',True)]",string="Contractor")
	contractor = fields.Char(string="Contractor")
	quoted_amt = fields.Float(string="Quoted Amount")
	percent = fields.Float(string="Percentage")
	remark = fields.Text(string="Remarks")
	s_check = fields.Boolean('Status Check')
	hiworth_tender_id = fields.Many2one('hiworth.tender')
	contractor_id1 = fields.Many2one('res.partner',string='Contractor')


class RenewalBgHistory(models.Model):
	_name='renewal.bg.history'

	renewal_date = fields.Date("Renewal Date")
	renewal_amount = fields.Float("Renewal Amount")
	bg_id = fields.Many2one('bank.gurantee.details')


class PurposePurpose(models.Model):
	_name = 'purpose.purpose'
	name = fields.Char("Name")


class BankGuranteeDetails(models.Model):
	_name='bank.gurantee.details'
	
	@api.multi
	@api.depends('bg_percent')
	def _compute_amount(self):
		for record in self:
			
			record.bg_amount = record.bg_percent / 100


	@api.multi
	def get_renewal_details(self):
		res = self.env['bank.gurantee.details'].search([])
		return res

	@api.depends('renewal_bg_history_ids')
	def compute_renewal_history(self):
		for rec in self:
			rec.no_of_renewal = len(rec.renewal_bg_history_ids.ids)
	@api.depends('fd_issue_date','expected_bg_release_date')
	def compute_no_of_days(self):
		for i in self:
			d1 = datetime.strptime(str(i.fd_issue_date),"%Y-%m-%d").date()
			d2 = datetime.strptime(str(i.expected_bg_release_date),"%Y-%m-%d").date()
			days = (d2-d1).days
			year = int(days/365)
			months = int((days%365)/12)
			days = days%365%12
			fd_days = str(year)+'years ' +str(months)+'months '+str(days)+'days'
			i.fd_no_of_days = str(fd_days)
	@api.depends('bg_issue_date','bg_expiry_date')
	def compute_no_of_days_2(self):
		for i in self:
			d1 = datetime.strptime(str(i.bg_issue_date),"%Y-%m-%d").date()
			d2 = datetime.strptime(str(i.bg_expiry_date),"%Y-%m-%d").date()
			days = (d2-d1).days
			year = int(days/365)
			months = int((days%365)/12)
			days = days%365%12
			fd_days = str(year)+'years ' +str(months)+'months '+str(days)+'days'
			i.fd_period = str(fd_days)
	state = fields.Selection([('draft', 'Draft'),
							  ('confirm', 'Confirmed'),
							  ('verify', 'Verified'),
							  ('approve', 'Approved'),
							  ('submission', 'Submitted')
							  ], default="draft")

	company_contractor_id = fields.Many2one('res.partner', 'Name of Company Contractor')
	purpose_id = fields.Many2one('purpose.purpose',"Type of Security")
	name_of_work = fields.Char("Name of Work")
	submitted_to = fields.Text("Submitted To")
	
	
	security_deposit_percent = fields.Float('% of Security Deposit')
	
	security_wo_round_off = fields.Float('Amount w/o round-off', compute="_compute_amount", store=True)
	security_round_off = fields.Float('Round Off')
	security_deposit_amount = fields.Float('Security Deposit Amount', compute="_compute_amount", store=True)
	
	bg_percent = fields.Float('% of Security Deposit Through Bank')
	treasury_percent = fields.Float('% of Security Deposit Through Treasury')
	bg_date = fields.Date('Date', default=lambda self: fields.datetime.now())
	bg_no = fields.Char("BG Number")
	bg_issue_date = fields.Date('BG Issue Date')
	bg_expiry_date = fields.Date('BG Expiry Date')
	bg_amount = fields.Float('Bank Guarantee Amount', )
	bg_amount_roundoff = fields.Float('BG Amount Round-Off')
	available_collateral = fields.Float('Available Balance', compute="_compute_collateral", store=True)
	fd_percent = fields.Float('FD Percent')
	fd_amount_wo_roundoff = fields.Float('FD Amount w/o round-off', compute="_compute_fd_amount", store=True)
	fd_round_off = fields.Float('Round-Off')
	fd_amount = fields.Float('FD Amount', )
	fd_payment_mode = fields.Many2one('res.partner.bank', string='FD Payment Mode')
	fd_account = fields.Many2one('account.account', 'FD Account')
	fd_issue_date = fields.Date('Date of Issue FD')
	fd_number = fields.Char('FD Number')
	fd_no_of_days = fields.Char('FD No. of Days',compute="compute_no_of_days")
	fd_holder = fields.Char('FD Holder Name')
	fd_mature_value = fields.Float('FD Mature Value')
	fd_interest = fields.Float('FD Interest')
	fd_period = fields.Char('BG Duration',compute="compute_no_of_days_2")
	expected_bg_release_date = fields.Date('Maturity Date')
	remarks = fields.Text('Remarks')
	state = fields.Selection([('draft','Draft'),
							  ('submit','Submit')],default='draft')
	renewal_bg_history_ids = fields.One2many('renewal.bg.history','bg_id',"Rnenwal History")
	no_of_renewal = fields.Float("No of Renewals",compute='compute_renewal_history')




	@api.multi
	@api.depends('bg_amount', 'fd_percent', 'fd_round_off')
	def _compute_fd_amount(self):
		for record in self:
			record.fd_amount_wo_roundoff = (record.bg_amount_roundoff * record.fd_percent) / 100
			record.fd_amount = record.fd_amount_wo_roundoff + record.fd_round_off
	

	
	@api.multi
	def button_submit(self):
		

		
		
		collateral = self.env['hiworth.collateral'].create({
			'date': datetime.now(),
			'bank_id': self.fd_payment_mode.id,
			'debit': 0,
			'credit': self.bg_amount,
		})
		collateral._compute_collateral_balance()
		collateral.state = 'approve'
		
		
		
		# print 'test1-----------------------------'
		
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		
		# FD
		if self.fd_amount != 0:
			move_id = move.create({
				'journal_id': self.fd_payment_mode.journal_id.id,
				'date': datetime.now(),

			})
			
			# print 'test11-----------------------------'
			line_id = move_line.create({
				'account_id': self.fd_account.id,
				'name': 'FD Amount',
				'debit': self.fd_amount,
				'credit': 0,
				'move_id': move_id.id,
				'status': 'draft'
			})
			# print 'test22-----------------------------'
			
			line_id = move_line.create({
				'account_id': self.fd_payment_mode.journal_id.default_credit_account_id.id,
				'name': 'FD Amount',
				'debit': 0,
				'credit': self.fd_amount,
				'move_id': move_id.id,
				'status': 'draft'
			})
			# print 'test33-----------------------------'
			move_id.button_validate()
			# print 'test2-----------------------------'
			self.state='submit'
	
	@api.multi
	@api.depends('fd_payment_mode')
	def _compute_collateral(self):
		for record in self:

			record.available_collateral = record.fd_payment_mode.account_balance



class NormalSecurityDetails(models.Model):
	_name='normal.security.details'
	
	company_id = fields.Many2one('res.company', 'Name of Company')
	purpose_id = fields.Many2one('purpose.purpose', "Purpose")
	name_of_work = fields.Char("Name of Work")
	submitted_to = fields.Text("Submitted To")

	security_deposit_amount = fields.Float('Security Deposit Amount', )
	
	bg_percent = fields.Float('% of Security Deposit Through Bank')
	treasury_percent = fields.Float('% of Security Deposit Through Treasury')
	
	cs_date = fields.Date('Date', default=fields.Date.today)
	com_security_amount = fields.Float('Normal Security Amount')
	com_security_amount_round_off = fields.Float('Normal Security Amount Round-Off')
	com_security_account = fields.Many2one('account.account', 'Normal Security Account')
	com_security_payment_mode = fields.Many2one('account.journal', string='Normal Security Payment Mode',
												domain="[('type','in',['cash','bank'])]")
	security_payment_mode = fields.Many2one('res.partner.bank',"Normal Security Payment Mode")
	expected_cs_release_date = fields.Date('Maturity Date')
	cs_treasury_id = fields.Many2one('res.partner', 'Treasury Name')
	treasury_number = fields.Char('Treasury Number')
	treasury_period = fields.Char('Period')
	remarks = fields.Text('Remarks')
	state = fields.Selection([('draft', 'Draft'),
							  ('submit', 'Submit')], default='draft')
	available_collateral = fields.Float('Available Balance', compute="_compute_collateral", store=True)

	@api.multi
	@api.depends('com_security_payment_mode')
	def _compute_collateral(self):
		for record in self:
			record.available_collateral = record.security_payment_mode.account_balance

	@api.multi
	@api.depends('treasury_percent')
	def _compute_amount(self):
		for record in self:
			
			record.com_security_amount = (record.security_deposit_amount * record.treasury_percent) / 100
	
	@api.multi
	def button_submit(self):

		# Common Security
		
		if self.com_security_amount != 0:
			move_id1 = move.create({
				# 'journal_id': self.com_security_payment_mode.journal_id.id,
				'journal_id': self.com_security_payment_mode.id,
				'date': datetime.now(),
				# 'tender_id': self.work_id.id
			})
			
			line_id = move_line.create({
				'account_id': self.com_security_account.id,
				'name': 'Common Security Amount',
				'debit': self.com_security_amount,
				'credit': 0,
				'move_id': move_id1.id,
				'status': 'draft'
			})
			
			line_id = move_line.create({
				'account_id': self.com_security_payment_mode.default_credit_account_id.id,
				'name': 'Common Security Amount',
				'debit': 0,
				'credit': self.com_security_amount,
				'move_id': move_id1.id,
				'status': 'draft'
			})
			move_id1.button_validate()
		self.state='submit'

			

class PerformanceSecurityDetails(models.Model):
	_name='performance.security.details'
	
	company_id = fields.Many2one('res.company', 'Name of Company')
	ps_date = fields.Date('Date', default=fields.Date.today)
	perf_security_mode = fields.Selection([('bank', 'Bank'),
										   ('treasury', 'Treasury')
										   ], string="Performance Security Deposit Through")
	ps_wo_round_off = fields.Float('PS Amount w/o round-off')
	ps_round_off = fields.Float('Round Off')
	performance_security_amount = fields.Float('PS Amount')
	ps_fd_percent = fields.Float('FD Percent')
	ps_fd_amount = fields.Float('FD Amount')
	# fd_amount_wo_roundoff = fields.Float('FD Amount w/o round-off')
	# fd_round_off = fields.Float('Round-Off')
	performance_security_account = fields.Many2one('account.account', 'PS Account')
	perf_bank_id = fields.Many2one('res.partner.bank', string='PS Payment Mode(Bank)')
	performance_security_payment_mode = fields.Many2one('account.journal', string='PS Payment Mode',
														domain="[('type','in',['cash','bank'])]")
	expected_ps_release_date = fields.Date('Expected Release Date')
	ps_treasury_id = fields.Many2one('res.partner', 'Treasury Name')
	perf_security_period = fields.Char('Period')
	perf_security_number = fields.Char('Performance Security Number')
	release_ps = fields.Float('Released PS Amount')
	release_ps_date = fields.Date('Released PS Date')
	release_ps_account = fields.Many2one('account.account', 'Released PS Account')
	ps_treasury_id = fields.Many2one('res.partner', 'Treasury Name')
	remarks = fields.Text('Remarks')
	state = fields.Selection([('draft', 'Draft'),
							  ('submit', 'Submit')], default='draft')
	
	@api.multi
	@api.depends('ps_wo_round_off', 'ps_round_off')
	def _compute_amount(self):
		for record in self:
			
			
			record.performance_security_amount = record.ps_wo_round_off + record.ps_round_off
			
			record.ps_fd_amount = (record.performance_security_amount * record.ps_fd_percent) / 100
	
	@api.multi
	def button_submit(self):
		print 'test3-----------------------------'
		# Performance Security
		# if self.status == 'below' and self.performance_security_amount != 0:
		if self.performance_security_amount != 0:
			
			if self.perf_security_mode == 'bank':
				move_id2 = move.create({
					'journal_id': self.perf_bank_id.journal_id.id,
					'date': datetime.now(),
					# 'tender_id': self.work_id.id
				})
				
				line_id = move_line.create({
					'account_id': self.performance_security_account.id,
					'name': 'Performance Security Amount',
					'debit': self.performance_security_amount,
					'credit': 0,
					'move_id': move_id2.id,
					'status': 'draft'
				})
				
				line_id = move_line.create({
					'account_id': self.perf_bank_id.journal_id.default_credit_account_id.id,
					'name': 'Performance Security Amount',
					'debit': 0,
					'credit': self.performance_security_amount,
					'move_id': move_id2.id,
					'status': 'draft'
				})
				move_id2.button_validate()
			elif self.perf_security_mode == 'treasury':
				move_id2 = move.create({
					'journal_id': self.performance_security_payment_mode.id,
					'date': datetime.now(),
					'tender_id': self.work_id.id
				})
				
				line_id = move_line.create({
					'account_id': self.performance_security_account.id,
					'name': 'Performance Security Amount',
					'debit': self.performance_security_amount,
					'credit': 0,
					'move_id': move_id2.id,
					'status': 'draft'
				})
				line_id = move_line.create({
					'account_id': self.performance_security_payment_mode.default_credit_account_id.id,
					'name': 'Performance Security Amount',
					'debit': 0,
					'credit': self.performance_security_amount,
					'move_id': move_id2.id,
					'status': 'draft'
				})
				
				move_id2.button_validate()
			
			else:
				pass
			self.state='submit'
		print 'test4-----------------------------'