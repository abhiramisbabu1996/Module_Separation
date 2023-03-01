from openerp.exceptions import except_orm, ValidationError
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp import models, fields, api, _
from openerp import workflow
import time
import datetime
from datetime import date
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from datetime import timedelta
from pychart.arrow import default
from openerp.osv import osv, expression


class Number2Words(object):


		def __init__(self):
			'''Initialise the class with useful data'''

			self.wordsDict = {1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five', 6: 'six', 7: 'seven',
							  8: 'eight', 9: 'nine', 10: 'ten', 11: 'eleven', 12: 'twelve', 13: 'thirteen',
							  14: 'fourteen', 15: 'fifteen', 16: 'sixteen', 17: 'seventeen',
							  18: 'eighteen', 19: 'nineteen', 20: 'twenty', 30: 'thirty', 40: 'forty',
							  50: 'fifty', 60: 'sixty', 70: 'seventy', 80: 'eighty', 90: 'ninty' }

			self.powerNameList = ['thousand', 'lac', 'crore']


		def convertNumberToWords(self, number):

			# Check if there is decimal in the number. If Yes process them as paisa part.
			formString = str(number)
			if formString.find('.') != -1:
				withoutDecimal, decimalPart = formString.split('.')

				paisaPart =  str(round(float(formString), 2)).split('.')[1]
				inPaisa = self._formulateDoubleDigitWords(paisaPart)

				formString, formNumber = str(withoutDecimal), int(withoutDecimal)
			else:
				# Process the number part without decimal separately
				formNumber = int(number)
				inPaisa = None

			if not formNumber:
				return 'zero'

			self._validateNumber(formString, formNumber)

			inRupees = self._convertNumberToWords(formString)

			if inPaisa:
				return '%s and %s paisa' % (inRupees.title(), inPaisa.title())
			else:
				return '%s' % inRupees.title()


		def _validateNumber(self, formString, formNumber):

			assert formString.isdigit()

			# Developed to provide words upto 999999999
			if formNumber > 999999999 or formNumber < 0:
				raise AssertionError('Out Of range')


		def _convertNumberToWords(self, formString):

			MSBs, hundredthPlace, teens = self._getGroupOfNumbers(formString)

			wordsList = self._convertGroupsToWords(MSBs, hundredthPlace, teens)

			return ' '.join(wordsList)


		def _getGroupOfNumbers(self, formString):

			hundredthPlace, teens = formString[-3:-2], formString[-2:]

			msbUnformattedList = list(formString[:-3])

			#---------------------------------------------------------------------#

			MSBs = []
			tempstr = ''
			for num in msbUnformattedList[::-1]:
				tempstr = '%s%s' % (num, tempstr)
				if len(tempstr) == 2:
					MSBs.insert(0, tempstr)
					tempstr = ''
			if tempstr:
				MSBs.insert(0, tempstr)

			#---------------------------------------------------------------------#

			return MSBs, hundredthPlace, teens


		def _convertGroupsToWords(self, MSBs, hundredthPlace, teens):

			wordList = []

			#---------------------------------------------------------------------#
			if teens:
				teens = int(teens)
				tensUnitsInWords = self._formulateDoubleDigitWords(teens)
				if tensUnitsInWords:
					wordList.insert(0, tensUnitsInWords)

			#---------------------------------------------------------------------#
			if hundredthPlace:
				hundredthPlace = int(hundredthPlace)
				if not hundredthPlace:
					# Might be zero. Ignore.
					pass
				else:
					hundredsInWords = '%s hundred' % self.wordsDict[hundredthPlace]
					wordList.insert(0, hundredsInWords)

			#---------------------------------------------------------------------#
			if MSBs:
				MSBs.reverse()

				for idx, item in enumerate(MSBs):
					inWords = self._formulateDoubleDigitWords(int(item))
					if inWords:
						inWordsWithDenomination = '%s %s' % (inWords, self.powerNameList[idx])
						wordList.insert(0, inWordsWithDenomination)

			#---------------------------------------------------------------------#
			return wordList


		def _formulateDoubleDigitWords(self, doubleDigit):

			if not int(doubleDigit):
				# Might be zero. Ignore.
				return None
			elif self.wordsDict.has_key(int(doubleDigit)):
				# Global dict has the key for this number
				tensInWords = self.wordsDict[int(doubleDigit)]
				return tensInWords
			else:
				doubleDigitStr = str(doubleDigit)
				tens, units = int(doubleDigitStr[0])*10, int(doubleDigitStr[1])
				tensUnitsInWords = '%s %s' % (self.wordsDict[tens], self.wordsDict[units])
				return tensUnitsInWords



class partner_statement_line(models.Model):
	_name = 'partner.statement.line'

	def _get_line_numbers(self, cr, uid, ids, context=None):
		if context is None:
			context = {}
		line_num = 1
		if ids:
			first_line_rec = self.browse(cr, uid, ids[0], context=context)
			line_num = 1
			for line_rec in first_line_rec.statement_id.statement_ids:
				line_rec.line_no = line_num
				line_num += 1
			line_num = 1

	line_no = fields.Integer(compute='_get_line_numbers', string='Sl.No',readonly=False, default=False)
	name = fields.Char('Name')
	date = fields.Date('Date')
	amount = fields.Float('Amount')
#     credit = fields.Float('Credit')
	total = fields.Float('Total')
	statement_id = fields.Many2one('partner.statement', 'Statement')



class partner_statement(models.Model):
	_name = 'partner.statement'

	@api.multi
	@api.depends('statement_ids')
	def _compute_total(self):
		for line in self:
			line.total =0.0
			for lines in line.statement_ids:
				line.total += lines.amount

	name = fields.Char('Name')
	partner_id = fields.Many2one('res.partner', 'Partner')
	account_id = fields.Many2one('account.account', 'Related Account')
	statement_ids = fields.One2many('partner.statement.line', 'statement_id', 'Statement Lines')
	total = fields.Float(compute='_compute_total', string="Total Amount")
#     move_lines = fields.One2many(related='account_id.move_lines',  string='Payments',)

	@api.model
	def create(self,vals):
		if vals['account_id']:
			self_obj = self.env['partner.statement']
			line = self_obj.search([('account_id','=',vals['account_id'])])
			print 'qqqqqqqqqqqqqqqqqqq', line,len(line)
			if len(line) != 0:
				raise osv.except_osv(_('Warning'),_("The related account already selected for a Statement Entry. Please select other account"))
		return super(partner_statement, self).create(vals)


class ResCompany(models.Model):
	_inherit = 'res.company'

	tds_account_id = fields.Many2one('account.account', 'Default TDS Payable')

class PaymentVouchers(models.Model):
	_name = 'payment.vouchers'


	@api.one
	@api.onchange('journal_id')
	def onchange_journal(self):
		if self.types == 'payment':
			self.account_id = self.journal_id.default_credit_account_id
		if self.types == 'received':
			self.account_id = self.journal_id.default_debit_account_id

	@api.one
	@api.onchange('payment_invoice_ids')
	def onchange_payment_invoice_ids(self):
		if self.payment_invoice_ids:
			self.cash_amt = 0.0
			for line in self.payment_invoice_ids:
				self.cash_amt += line.amount

	@api.one
	@api.onchange('partner_id')
	def onchange_partner(self):
		if self.types == 'payment':
			self.opp_account_id = self.partner_id.property_account_payable
		if self.types == 'received':
			self.opp_account_id = self.partner_id.property_account_receivable

	@api.multi
	def _compute_total_amount(self):
		for record in self:
			for rec in record.invoice_many2many:
				record.total_amt += rec.balance

	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		if self.partner_id:
			line_ids = []
			for invoice in self.env['hiworth.invoice'].search([('partner_id','=',self.partner_id.id),('state','in',['approve','partial'])]):
				values = {
					'bill_no': invoice.id,
					'date': invoice.date_invoice,
					'balace' : invoice.balance,
					'amount': invoice.balance,
					'name': invoice.name + ' ' + 'Bill settlement' 
				}
				line_ids.append((0, False, values ))
			self.payment_invoice_ids = line_ids


	@api.onchange('journal_type1')
	def onchange_journal_type1(self):
		if self.journal_type1 == 'cash':
			self.journal_id = self.env['account.journal'].search([('type','=','cash')])[0]
		if self.journal_type1 == 'bank':
			self.journal_id = self.env['account.journal'].search([('type','=','bank')])[0]


	@api.onchange('payment_invoice_ids')
	def onchange_payment_invoice_ids2(self):
		if self.payment_invoice_ids:
			self.narration = 'Payment Against'+ ' '+ self.partner_id.name+' '
			temp = False
			for line in self.payment_invoice_ids:
				if temp == True:
					self.narration += ', '
				self.narration += 'Bill No'+' '+line.bill_no.name+' '+'dated'+' '+str(datetime.datetime.strptime(line.bill_no.date_invoice, '%Y-%m-%d').strftime('%m/%d/%y'))
				temp = True
			self.narration += '.'

	@api.multi
	@api.depends('account_id')
	def compute_acc_balance(self):
		for rec in self:
			if rec.account_id:
				rec.acc_balance = rec.account_id.balance

	@api.multi
	@api.depends('payment_invoice_ids.tds_amount')
	def compute_tds_amount(self):
		for rec in self:
			rec.tds_amount = 0
			for line in rec.payment_invoice_ids:
				if line.tds != 0.0:
					rec.tds_amount += (line.balace*line.tds)/100


	@api.model
	def _get_compant_tds(self):
		return self.env.user.company_id.tds_account_id

			
	READONLY_STATES = {
		'post': [('readonly', True)],
		'confirm': [('readonly', True)],
		'cancel': [('readonly', True)],
	}


	types = fields.Selection([
		('payment','Payment'),
		('received','Received')
		], string='Type')

	journal_type1 = fields.Selection([
		('cash','Cash'),
		('bank','Bank')
		], string='Payment Mode', states=READONLY_STATES)

	mode = fields.Selection([
		('general','General'),
		('supplier','Supplier')
		], string='Payment Type', states=READONLY_STATES)  

	state = fields.Selection([
		('draft','Draft'),
		('confirm','Confirm'),
		('post','Posted'),
		('cancel','Canceled')
		], string='State', readonly=True, default='draft')

	journal_id = fields.Many2one('account.journal', 'Mode of Payment', domain=[('type','in',['cash','bank'])], states=READONLY_STATES)
	# journal_type1 = fields.Selection(string="Type", states=READONLY_STATES)
	account_id = fields.Many2one('account.account', 'Account', states=READONLY_STATES)
	number = fields.Char('Number')
	date = fields.Date('Date', states=READONLY_STATES,default=lambda self: fields.datetime.now())
	partner_id = fields.Many2one('res.partner', 'Received From', states=READONLY_STATES)
	receiver_id = fields.Many2one('res.partner', 'Receiver Name', states=READONLY_STATES)
	opp_account_id = fields.Many2one('account.account', 'Account', states=READONLY_STATES)
	cash_amt = fields.Float('Amount', states=READONLY_STATES)
	narration = fields.Char('Towads', states=READONLY_STATES)
	cheque_dd = fields.Char('Cheque/DD Transfer No', states=READONLY_STATES)
	branch = fields.Char('Bank and Branch', states=READONLY_STATES)
	dd_date = fields.Date('Date', states=READONLY_STATES)
	amount_to_text = fields.Text(string='Amount In Words',
		store=True, readonly=True, compute='_amount_in_words')

	user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user, states=READONLY_STATES)
	# bill_details = fields.One2many('payment.vouchers.bill', 'bill_id')

	# paid_to = fields.Many2one('account.account', 'Paid To')
	# invoice_many2many = fields.Many2many('hiworth.invoice','invoice_many2many1','invoice_id','voucher_id')
	payment_invoice_ids = fields.One2many('payment.vouchers.bill', 'voucher_id', 'Invoices', states=READONLY_STATES)
	total_amt = fields.Float('Total', states=READONLY_STATES)
	move_id = fields.Many2one('account.move', 'Journal Entry', states=READONLY_STATES)
	select_bills = fields.Boolean('Select Bills', default=False, states=READONLY_STATES)
	reference = fields.Char('Reference', states=READONLY_STATES)
	purchase_id = fields.Many2one('purchase.order', 'Purchase Order')
	acc_balance = fields.Float(compute='compute_acc_balance', store=True, string="Current Balance")
	company_id = fields.Many2one('res.company', string='Company',required=True, readonly=True)
	tds_amount = fields.Float(compute='compute_tds_amount', store=True, string="TDS Amount")
	tds_account_id = fields.Many2one('account.account', 'TDS Account', default=_get_compant_tds, states=READONLY_STATES)

	_defaults = {
		'date' : lambda self: fields.datetime.now(),
		'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
	}


	@api.model
	def create(self,vals):
		code = self.env['account.journal'].browse(vals.get('journal_id')).code
		vals['number'] = self.env['ir.sequence'].next_by_code('voucher.receipt')
		# if vals.get('cash_amt') > self.env['account.account'].browse(vals.get('account_id')).balance:
		# 	raise osv.except_osv(_('Warning'),_("The amount is greater than balance amount"))
		return super(PaymentVouchers,self).create(vals)

	# @api.multi
	# def write(self,vals):
	# 	if vals.get('cash_amt') > self.acc_balance:
	# 		raise osv.except_osv(_('Warning'),_("The amount is greater than balance amount"))
	# 	return super(PaymentVouchers,self).write(vals)



	@api.one
	@api.depends('cash_amt')
	def _amount_in_words(self):
		wGenerator = Number2Words()
		if self.cash_amt >= 0.0: 
			print 'cash===================', self.cash_amt
			self.amount_to_text = wGenerator.convertNumberToWords(self.cash_amt)

	@api.multi
	def action_print_receipt(self):
		self.ensure_one()

		datas = {
			'ids': self._ids,
			'model': self._name,
			'form': self.read(),
			'context':self._context,
		}

		return{
			'type' : 'ir.actions.report.xml',
			'report_name' : 'hiworth_accounting.report_payment_voucher_receipt_template',
			'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
			# 'report_type' : 'qweb-html',
		}

	@api.multi
	def action_print_bank_payment(self):
		self.ensure_one()

		datas = {
			'ids': self._ids,
			'model': self._name,
			'form': self.read(),
			'context':self._context,
		}
		return{
			'type' : 'ir.actions.report.xml',
			'report_name' : 'hiworth_accounting.report_bank_payment_voucher_payment_template',
			# 'report_type' : 'qweb-html',
			'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
		}


	@api.multi
	def action_print_cash_payment(self):
		self.ensure_one()

		datas = {
			'ids': self._ids,
			'model': self._name,
			'form': self.read(),
			'context':self._context,
		}
		return{
			'type' : 'ir.actions.report.xml',
			'report_name' : 'hiworth_accounting.report_cash_payment_voucher_payment_template',
			'datas': datas,
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
		}

	@api.multi
	def action_confirm(self):
		move = self.env['account.move']
		move_line = self.env['account.move.line']
		values = {
				'journal_id': self.journal_id.id,
				'date': self.date,
				# 'period_id': self.period_id.id,623393
				}
		move_id = move.create(values)
		cheque_no = False
		if self.journal_type1 == 'bank':
			cheque_no = self.cheque_dd

		debit = 0
		credit = 0
		if self.types == 'received':
			debit = self.cash_amt
		if self.types == 'payment':
			credit = self.cash_amt

		values2 = {
				'account_id': self.account_id.id,
				'name': self.narration,
				'debit': debit,
				'credit': credit,
				'move_id': move_id.id,
				'cheque_no': cheque_no
				}
		line_id = move_line.create(values2)

		debit2 = 0
		credit2 = 0
		if self.payment_invoice_ids and self.types == 'payment':
			for line in self.payment_invoice_ids:
				values3 = {
				'account_id': self.opp_account_id.id,
				'name': self.narration,
				'debit': line.amount,
				'credit': 0,
				'move_id': move_id.id,
				'cheque_no': cheque_no,
				'invoice_no_id2': line.bill_no.id,
				}
				line_id = move_line.create(values3)
				if line.tds_amount != 0.0:
					if line.bill_no.move_id:
						line.bill_no.move_id.button_cancel()
						move_line = self.env['account.move.line'].search([('move_id','=',line.bill_no.move_id.id),('account_id','=',line.bill_no.account_id.id)], limit=1)
						# print 'move_line=================', move_line
						old_credit = move_line.credit
						move_line.credit = old_credit-line.tds_amount

						values4 = {
						'account_id': self.tds_account_id.id,
						'name': 'TDS For invoice No '+ line.bill_no.name,
						'debit': 0.0,
						'credit': line.tds_amount ,
						'move_id': line.bill_no.move_id.id,
						'cheque_no': cheque_no,
						'invoice_no_id2': line.bill_no.id,
						}
						line_id = move_line.create(values4)
						line.bill_no.move_id.button_validate()
					if not line.bill_no.move_id:
						values5 = {
								'journal_id': line.bill_no.journal_id.id,
								'date': line.bill_no.date_invoice,
								'tds_id': line.id
								# 'period_id': self.period_id.id,623393
								}
						move_id2 = move.create(values5)
						
						values4 = {
						'account_id': self.tds_account_id.id,
						'name': 'TDS For invoice No '+ line.bill_no.name,
						'debit': 0.0,
						'credit': line.tds_amount ,
						'move_id': move_id2.id,
						'cheque_no': cheque_no,
						'invoice_no_id2': line.bill_no.id,
						}
						line_id = move_line.create(values4)

						values6 = {
						'account_id': line.bill_no.account_id.id,
						'name': 'TDS For invoice No '+ line.bill_no.name,
						'debit': line.tds_amount,
						'credit':  0.0,
						'move_id': move_id2.id,
						'cheque_no': cheque_no,
						# 'invoice_no_id2': line.bill_no.id,
						}
						line_id = move_line.create(values6)

						move_id2.button_validate()
		else:
			if self.types == 'received':
				credit2 = self.cash_amt
			if self.types == 'payment':
				debit2 = self.cash_amt
			values3 = {
					'account_id': self.opp_account_id.id,
					'name': self.narration,
					'debit': debit2,
					'credit': credit2,
					'move_id': move_id.id,
					'cheque_no': cheque_no
					}
			line_id = move_line.create(values3)
		# move_id.button_validate()
		self.move_id = move_id.id
		self.state = 'confirm'


	@api.multi
	def action_post(self):

		if self.payment_invoice_ids and self.types == 'payment':
			for line in self.payment_invoice_ids:
				if line.bill_no.balance == 0.0:
					line.bill_no.action_paid()
				if line.bill_no.balance > 0 and line.bill_no.balance < line.bill_no.amount_to_be_paid:
					line.bill_no.action_paid_partial()
		self.move_id.button_validate()
		self.state = 'post'


	@api.multi
	def action_cancel(self):
		self.move_id.button_cancel()
		self.move_id.unlink()
		self.state = 'cancel'
	@api.multi
	def action_setto_draft(self):
		self.state = 'draft'

	@api.multi
	def unlink(self):
		for line in self:
			if line.state == 'posted':
				line.move_id.button_cancel()
				line.move_id.unlink()
			return super(PaymentVouchers, self).unlink()




class PaymentVouchersBill(models.Model):
	_name = 'payment.vouchers.bill'



	@api.multi
	@api.depends('bill_no')
	def onchange_bill_no(self):
		for rec in self:
			if rec.bill_no:
				rec.date = rec.bill_no.date_invoice
				rec.balace = rec.bill_no.balance


	@api.onchange('amount_to_pay')
	def _onchange_invoice_no(self):
		invoice_ids = []
		if self.voucher_id.partner_id:
			invoice_ids = [bill.id for bill in self.env['hiworth.invoice'].search([('partner_id','=',self.voucher_id.partner_id.id),('state','in',['approve','partial'])])]
		if self.bill_no:
			self.amount = self.amount_to_pay
			self.name = self.bill_no.name + ' ' + 'Bill settlement' 
		return {'domain': {'bill_no': [('id','in',invoice_ids)]}}

	@api.multi
	@api.depends('bill_no', 'tds_amount', 'balace')
	def compute_amount_to_pay(self):
		for rec in self:
			rec.amount_to_pay = rec.balace - rec.tds_amount

	@api.multi
	@api.depends('bill_no', 'tds', 'balace')
	def compute_tds_amount(self):
		for rec in self:
			if rec.tds != 0.0:
				rec.tds_amount = (rec.balace*rec.tds)/100

	bill_no = fields.Many2one('hiworth.invoice', 'Bill No')
	date = fields.Date('Date', compute='onchange_bill_no', store=True)
	name = fields.Char('Description')
	balace = fields.Float('Bill Amount', compute='onchange_bill_no', store=True)
	amount = fields.Float('payment Amount')
	tds = fields.Float('TDS %')
	tds_amount = fields.Float(compute='compute_tds_amount', string="TDS Amount", store=True)
	amount_to_pay = fields.Float(compute='compute_amount_to_pay',store=True, string="To Pay")
	voucher_id = fields.Many2one('payment.vouchers', "Voucher")
	company_id = fields.Many2one('res.company', string='Company',required=True, readonly=True)

	_defaults = {
		'company_id': lambda self, cr, uid, c: self.pool.get('res.users').browse(cr, uid, uid, c).company_id.id,
	}


