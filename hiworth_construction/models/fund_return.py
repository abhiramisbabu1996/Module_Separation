from openerp.exceptions import except_orm, ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import Warning as UserError
from openerp import models, fields, api, _
import time
import datetime
from datetime import date
from datetime import timedelta



class FundReturn(models.Model):
	_name = 'fund.return'
	_rec_name = 'date'
	
	
	@api.model
	def default_get(self, fields):
		res = super(FundReturn, self).default_get(fields)
		line_id = self.env['account.journal'].search([('name','=','CASH')], limit=1)
		if line_id:
			# return line_id.account_id.id
			res.update({'account_id': line_id.id})
		return res

	date = fields.Date(string='Date', default=fields.Date.today())
	account_id = fields.Many2one('account.journal', string="Journal")
	user_id = fields.Many2one('res.users', string='Users', default=lambda self: self.env.user)
	state = fields.Selection([('draft', "Draft"),
							  ('post', "Post")
							 ],string="State", required=True, default='draft')
	line_ids = fields.One2many('fund.return.line', 'return_id', string="Return Details")


	@api.multi
	def button_post(self):
		#journal entry
		move = self.env['account.move'].create({
												'journal_id':self.account_id.id,
												'date':self.date
												})
		move_line = self.env['account.move.line']
		amt1 = 0.0
		count = 1
		for val in self.line_ids:
			amt1 += val.amount
			move_line.create({'move_id':move.id,
							  'state': 'valid',
							  'name': 'Z3-'+str(count)+' - '+val.account_id.name,
							  'account_id':val.account_id.id,
							  'debit':0,
							  'credit':val.amount,
							  'closed':True
							})
			count += 1

		move_line.create({'move_id':move.id,
						  'state': 'valid',
						  'name': 'Cash Return',
						  'account_id':self.account_id.default_credit_account_id.id,
						  'debit':amt1,
						  'credit':0,
						  'closed':True
						})
		

		if move:
			move.button_validate()
			self.state = 'post'
			


class FundReturnLine(models.Model):
	_name = 'fund.return.line'

	# @api.onchange('account_id')
	# def onchange_account_id(self):
	# 	acc_list = []
	# 	line_id = self.env['account.account'].search([('parent_id.name', '=', 'CASH IN HAND')])
	# 	for val in line_id:
	# 		acc_list.append(val.id)
	#
	# 	return {'domain': {'account_id': [('id','in',acc_list)]}}

	return_id = fields.Many2one('fund.return', string="Fund Return")

	seq = fields.Integer(string="Sequence")
	account_id = fields.Many2one('account.account', string="Account", domain="[('type', '!=', 'view'),('parent_id.name', 'in',['CASH IN HAND', 'CASH IN HAND - DRIVERS', 'CASH IN HAND - ELECTRICAL STAFFS', 'CASH IN HAND - JOSHY SCARIAH - PROJECT - 1', 'CASH IN HAND - LAISON DEPARTMENT', 'CASH IN HAND - MANAGEMENT', 'CASH IN HAND - CHITTY VASAM', 'CASH IN HAND - OFFICE STAFF', 'CASH IN HAND - PALATHRA BRICKS & TILES', 'CASH IN HAND - SAJEEV D - PROJECT - 2', 'CASH IN HAND - SIVARAJAN - PROJECT - 3'])]")
	amount = fields.Float(string="Amount")
	note = fields.Text(string="Narration")



	