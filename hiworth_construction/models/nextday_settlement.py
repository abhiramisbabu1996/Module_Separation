from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
from openerp.osv import osv
import time
from datetime import date
from datetime import datetime
from datetime import timedelta
from dateutil import relativedelta


class SendApproval(models.Model):
	_name = 'send.approval'

	rec = fields.Many2one('nextday.settlement')
	users = fields.Many2many('res.users',string='Users',required=True)

	@api.multi
	def send_approve(self):
		group_id_button = self.env['ir.model.data'].get_object('hiworth_construction',  'group_nextday_settl_button_approve').id
		for user in self.users:
			# user.write({'groups_id': [(4, group_id_button)]})
			self.env['approver.line'].create({'name':user.id,'status':'notapproved','line_id':self.rec.id})
		self.rec.state = 'send_approval'
		record = self.env['settlement.line'].search([('line_id','=',self.rec.id)])
		for val in record:
			val.head_state = 'send_approval'
		rec1 = self.env['settlement.bank.line'].search([('line_id','=',self.rec.id)])
		for line1 in rec1:
			line1.head_state = 'send_approval'
		return True

class NextdaySettlement(models.Model):
	_name = 'nextday.settlement'


	@api.model
	def create(self, vals):
		total = 0.0
		banks = self.env['res.partner.bank'].search([('common_usage', '=', True)])
		for b in banks:
			if b.bank_acc_type_id.name == 'OD Account':
				total += b.usable_balance
			else:
				total += b.account_balance
		vals['total_balance'] = total
		res = super(NextdaySettlement, self).create(vals)
		for n in self.env['settlement.line'].search([('state','=','cancel')]):
			n.state = 'draft'
			n.head_state = 'draft'
			n.line_id = res.id
		return res

	date = fields.Date('Date',required=True)
	settlement_line = fields.One2many('settlement.line','line_id',domain=[('state','in',('draft','approve'))])
	other_settlement_line = fields.One2many('other.settlements.line','line_id')
	settlement_bank_line = fields.One2many('settlement.bank.line','line_id')
	cancelled_line = fields.One2many('settlement.line','line_id',domain=[('state','=','cancel')])
	state = fields.Selection([('draft','Draft'),('send_approval','Sending For Approval'),('approved','Approve In Progress'),('validate','Validated')],default='draft')
	approvers_line = fields.One2many('approver.line','line_id')
	journal_id = fields.Many2one('account.journal','Journal(Cr)')
	button_visible = fields.Boolean(default=False)
	total_balance = fields.Float('Total Balance')

	_defaults = {
	'date': lambda *a: str(datetime.now() + relativedelta.relativedelta(days=1))[:10],
	}

	# @api.onchange('approvers_line')
	# def approver_line_onchange(self):
	# 	approve_line = self.env['approver.line'].search([('name','=',self.env.user.id),('status','=','notapproved'),('line_id','=',self.id)])
	# 	if approve_line:
	# 		self.button_visible = True


	# @api.model
	# def default_get(self, default_fields):
	# 	vals = super(NextdaySettlement, self).default_get(default_fields)
	# 	print "2222222222222222222", vals
	# 	print "self.id================", self.id
	# 	approve_line = self.env['approver.line'].search([('name','=',self.env.user.id),('status','=','notapproved'),('line_id','=',self.id)])
	# 	if approve_line:
	# 		vals.update({'button_visible' : True})

	# 	return vals


	@api.multi
	def validate_entry(self):
		self.state = 'validate'
		rec = self.env['settlement.line'].search([('line_id','=',self.id)])
		for line in rec:
			line.head_state = 'validate'
		rec1 = self.env['settlement.bank.line'].search([('line_id','=',self.id)])
		for line1 in rec1:
			line1.head_state = 'validate'


	@api.multi
	def approve_entry(self):
		self.state = 'approved'
		rec = self.env['approver.line'].search([('line_id','=',self.id),('name','=',self.env.user.id)])
		if rec:
			rec.status = 'approved'
			rec.date_approved = fields.Datetime.now()

	@api.multi
	def send_approval(self):
		view_ref = self.env['ir.model.data'].get_object_reference('hiworth_construction', 'view_send_approval_form')
		view_id = view_ref[1] if view_ref else False
		res = {
		   'type': 'ir.actions.act_window',
		   'name': _('For Approvals'),
		   'res_model': 'send.approval',
		   'view_type': 'form',
		   'view_mode': 'form',
		   'view_id': view_id,
		   'target': 'new',
		   'context': {'default_rec':self.id}
	    }

		return res


class ApproverLine(models.Model):
	_name = 'approver.line'

	line_id = fields.Many2one('nextday.settlement')
	name = fields.Many2one('res.users','Approver')
	date_approved = fields.Datetime('Date')
	status = fields.Selection([('notapproved','Not Approved'),('approved','Approved')],default='notapproved')

class OtherSettlementLine(models.Model):
	_name = 'other.settlements.line'

	line_id = fields.Many2one('nextday.settlement')
	particulars = fields.Char('Particulars')
	amount = fields.Char('Amount')

class SettlementLine(models.Model):
	_name = 'settlement.line'

	line_id = fields.Many2one('nextday.settlement')
	journal_id = fields.Many2one('account.journal','Journal')
	credit_ac_balance = fields.Float(related='journal_id.default_credit_account_id.balance',string="journal Balance",readonly=True)
	account_id = fields.Many2one('account.account','Account',required=True)
	debit_ac_balance = fields.Float(related='account_id.balance',string="Account Balance",readonly=True)
	amount = fields.Float('Amount')
	tally = fields.Boolean(default=False)
	head_state = fields.Selection([('draft','Draft'),('send_approval','Sending For Approval'),('approved','Approved'),('validate','Validated')],default='draft')
	tds_amount = fields.Float('TDS Amount')
	tds_account = fields.Many2one('tds.configuration', 'TDS Account')
	total = fields.Float('Total',compute="get_total")
	state = fields.Selection([('draft','Draft'),('approve','Approved'),('cancel','cancelled')],default='draft',readonly=True)
	particulars = fields.Char('Particulars')
	yesterdays_cancel = fields.Boolean('Yesterdays Cancel')

	@api.model
	def create(self, vals):
		res = super(SettlementLine, self).create(vals)
		res.journal_id = res.line_id.journal_id.id
		return res

	@api.multi
	def tally_line(self):
		self.tally = True

	@api.multi
	def journal_line(self):
		accnt_move = self.env['account.move']
		move_line = self.env['account.move.line']
		if self.line_id.journal_id:
			move = accnt_move.create({'journal_id':self.line_id.journal_id.id})
			move_line.create({
							'debit':self.amount,
							'credit':0,
							'move_id':move.id,
							'account_id':self.account_id.id,
							'name':'Settle',
							'state':'valid',
				})
			if self.tds_amount > 0.0:
				move_line.create({
							'debit':self.tds_amount,
							'credit':0,
							'move_id':move.id,
							'account_id':self.account_id.id,
							'name':'Settle',
							'state':'valid',
				})
				move_line.create({
								'debit':0.0,
								'credit':self.tds_amount,
								'move_id':move.id,
								'account_id':self.tds_account.tds_related_account_id.id,
								'name':'Settle',
								'state':'valid',
					})
			move_line.create({
							'debit':0,
							'credit':self.amount,
							'move_id':move.id,
							'account_id':self.journal_id.default_credit_account_id.id,
							'name':'Settle',
							'state':'valid',
				})
			self.head_state = 'approved'
		else:
			raise except_orm(_('Warning'),
                             _('Please Set Journal'))





	@api.multi
	def cancel_line(self):
		self.state = 'cancel'
		self.yesterdays_cancel = True

	@api.multi
	def approve_line(self):
		self.state = 'approve'


	@api.multi
	def get_total(self):
		for lines in self:
			lines.total = lines.amount + lines.tds_amount

class SettlementBankLine(models.Model):
	_name = 'settlement.bank.line'

	line_id = fields.Many2one('nextday.settlement')
	bank_from = fields.Many2one('res.partner.bank','Bank(Dr)')
	bank_from_balance = fields.Float(related='bank_from.journal_id.default_credit_account_id.balance',string="Bank(Dr) Balance",readonly=True)
	bank_to = fields.Many2one('res.partner.bank','Bank(Cr)')
	bank_to_balance = fields.Float(related='bank_to.journal_id.default_credit_account_id.balance',string="Bank(Cr) Balance",readonly=True)
	amount = fields.Float('Amount')
	tally = fields.Boolean(default=False)
	head_state = fields.Selection([('draft','Draft'),('send_approval','Sending For Approval'),('approved','Approved'),('validate','Validated')],default='draft')
	state = fields.Selection([('draft','Draft'),('approve','Approved'),('cancel','cancelled')],default='draft',readonly=True)
	particulars = fields.Char('Particulars')

	@api.multi
	def tally_line(self):
		self.tally = True

	@api.multi
	def journal_line(self):
		accnt_move = self.env['account.move']
		move_line = self.env['account.move.line']
		if self.line_id.journal_id:
			move = accnt_move.create({'journal_id':self.bank_to.journal_id.id})
			move_line.create({
							'debit':0.0,
							'credit':self.amount,
							'move_id':move.id,
							'account_id':self.bank_to.journal_id.default_credit_account_id.id,
							'name':'Settle',
							'state':'valid',
				})

			move_line.create({
							'debit':self.amount,
							'credit':0.0,
							'move_id':move.id,
							'account_id':self.bank_from.journal_id.default_credit_account_id.id,
							'name':'Settle',
							'state':'valid',
				})
			self.head_state = 'approved'
		else:
			raise except_orm(_('Warning'),
                             _('Please Set Journal'))





	@api.multi
	def cancel_line(self):
		self.state = 'cancel'

	@api.multi
	def approve_line(self):
		self.state = 'approve'