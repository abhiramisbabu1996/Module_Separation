from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError
import datetime

class DriverPayableReport(models.Model):
	_name = 'driver.payable.report'

	period_from = fields.Date('From')
	period_to = fields.Date('To')
	driver_id = fields.Many2one('hr.employee','Driver')

	@api.onchange('driver_id')
	def onchange_driver_id(self):
		print 'sdsfmmn-------------'
		driver_list = []
		print 'self.env.user.partner_id.user_category--------------11', self.env.user
		print 'self.env.user.partner_id.user_category--------------', self.env.user.employee_id
		if self.env.user.employee_id.user_category in ['driver','eicher_driver']:
			driver_ids = self.env['hr.employee'].search([('id', '=', self.env.user.employee_id.id)])
		else:
			print 'chck-------------------------'
			driver_ids = self.env['hr.employee'].search([('user_category', 'in', ['driver','eicher_driver'])])
		print 'driver_ids------------------------', driver_ids
		for employee in driver_ids:
			driver_list.append(employee.id)
		return {
				'domain': {
					'driver_id': [('id','in',driver_list)]
				}
			}


	@api.multi
	def get_opening_balance(self,no,period_from,driver):
		debit = 0
		credit = 0 
		value = 0
		move_line = self.env['account.move.line'].search([('date','<',period_from),('account_id','=',driver.payment_account.id)])
		for line in move_line:
			credit += line.credit
			debit += line.debit
		value = debit - credit
		if value < 0:
			if no == 0:
				return -value
		if value > 0:
			if no == 1:
				return value
		else:
			return 0

	@api.multi
	def get_line(self,period_from,period_to,driver):
		list = []
		move_line = self.env['account.move.line'].search([('account_id','=',driver.payment_account.id),('date','>=',period_from),('date','<=',period_to)],order='date asc')
		for line in move_line:
			date = ''
			date_fmt = datetime.datetime.strptime(line.date, "%Y-%m-%d")
			date = str(date_fmt.day)+ str('/')+str(date_fmt.month)+ str('/') + str(date_fmt.year)

			values = {
				'date':date,
				'ref_no':line.driver_stmt_id.reference,
				'desc': line.vehicle_id.name,
				'debit':line.debit,
				'credit':line.credit
			}

			list.append(values)
		return list



	@api.multi
	def print_report(self):
		datas = {
		   'ids': self._ids,
		   'model': self._name,
		   'form': self.read(),
		   'context':self._context,
				}
		return{
		   'name' : 'Print',
		   'type' : 'ir.actions.report.xml',
		   'report_name' : 'hiworth_construction.report_driver_payable_account',
		   'datas': datas,
		   'report_type': 'qweb-pdf'
				}
		
	@api.multi
	def view_report(self):
		datas = {
		   'ids': self._ids,
		   'model': self._name,
		   'form': self.read(),
		   'context':self._context,
	   }
		return{
		   'name' : 'Print',
		   'type' : 'ir.actions.report.xml',
		   'report_name' : 'hiworth_construction.report_driver_payable_account',
		   'datas': datas,
		   'report_type': 'qweb-html'
	   }

		

class ReportWizard(models.Model):
	_name = 'report.wizard'

	period_from = fields.Date('From')
	period_to = fields.Date('To')
	site_id = fields.Many2one('stock.location','Site')
	supervisor = fields.Many2one('hr.employee','Supervisor')
	labour_id = fields.Many2one('account.account','Labour')
	based_on = fields.Selection([('site','Site'),('supervisor','Supervisor'),('labour','Labour')],required=True)





class CrusherReport(models.Model):
	_name = 'crusher.report'

	@api.multi
	@api.depends('total','amount_paid')
	def get_balance(self):
		balance = 0
		for lines in self:
			lines.balance = balance + lines.total - lines.amount_paid
			balance = lines.balance
			# lines.


	date = fields.Date('Date')
	site_id = fields.Many2one('stock.location','Site Name')
	contractor_id = fields.Many2one('res.partner','Contractor')
	bill_no = fields.Char('Bill No')
	vehicle_no = fields.Many2one('fleet.vehicle','Vehicle')
	item_id = fields.Many2one('product.product','Materials')
	crusher = fields.Many2one('res.partner','Crusher')
	qty = fields.Float('Qty')
	rate = fields.Float('Rate')
	amount = fields.Float('Amount')
	total = fields.Float('Total')
	amount_paid = fields.Float('Amount Paid')
	gst = fields.Many2one('account.tax','GST')
	bank_account = fields.Char('Bank A/c')
	balance = fields.Float(compute="get_balance",string='Balance')
	driver_stmt_id = fields.Many2one('driver.daily.statement.line')
	rent_vehicle_id = fields.Many2one('rent.vehicle.statement')



class FuelReport(models.Model):
	_name = 'fuel.report'

	@api.multi
	@api.depends('amount','amount_paid')
	def get_balance(self):
		balance = 0
		for lines in self:
			lines.balance = balance + lines.amount - lines.amount_paid
			balance = lines.balance

	date = fields.Date('Date')
	bill_no = fields.Char('Bill No')
	vehicle_owner = fields.Many2one('res.partner','Vehicle Owner')
	vehicle_no = fields.Many2one('fleet.vehicle','Vehicle')
	item_char = fields.Char('Item')
	qty = fields.Float('Qty')
	rate = fields.Float('Rate')
	amount = fields.Float('Amount')
	amount_paid = fields.Float('Amount Paid')
	bank_account = fields.Char('Bank A/c')
	balance = fields.Float('Balance',compute="get_balance")
	diesel_pump = fields.Many2one('res.partner','Diesel Pump')
	rent_vehicle_id = fields.Many2one('rent.vehicle.statement')
	diesel_pump_id = fields.Many2one('diesel.pump.line')
	machinery_pump_id = fields.Many2one('machinery.fuel.collection')


class PartnerDailyStatementCancel(models.Model):
	_name = 'partner.daily.statement.cancel'

	@api.multi
	def cancel_statements(self):
		cancel_statements = self.env.context.get('active_ids')
		for line in cancel_statements:
			partner_statements = self.env['partner.daily.statement'].search([('id','=',line)])				
			for val in partner_statements:
				if val.state == 'draft' or val.state == 'cancel':
					raise except_orm(_('Warning'),_('Can not cancel the entries which are in draft and cancel states..!!'))			
				else:
					val.cancel_entry()
			if not partner_statements:
					raise except_orm(_('Warning'),_('Select Atleast One Record...!!'))			
				
		return True


class DriverDailyStatementCancel(models.Model):
	_name = 'driver.daily.statement.cancel'

	@api.multi
	def cancel_statements(self):
		cancel_statements = self.env.context.get('active_ids')
		for line in cancel_statements:
			driver_statements = self.env['driver.daily.statement'].search([('id','=',line)])				
			for val in driver_statements:
				if val.state == 'draft' or val.state == 'cancelled':
					raise except_orm(_('Warning'),_('Can not cancel the entries which are in draft and cancel states..!!'))			
				else:
					val.cancel_entry()
			if not driver_statements:
					raise except_orm(_('Warning'),_('Select Atleast One Record...!!'))
		return True



