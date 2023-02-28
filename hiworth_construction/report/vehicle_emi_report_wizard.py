from openerp import fields, models, api
import datetime, calendar
from datetime import timedelta
from openerp.osv import osv

class VehicleEmiReportWizard(models.TransientModel):
	_name='vehicle.emi.report.wizard'

	from_date=fields.Date("Date From")
	to_date=fields.Date("Date To")




	@api.multi
	def view_vehicle_emi_report(self):
		
		datas = {
			'ids': self._ids,
			'model': self._name,
			'form': self.read(),
			'context':self._context,
		}
		return{
			'type' : 'ir.actions.report.xml',
			'report_name' : 'hiworth_construction.report_vehicle_emi_report_template',
			'datas': datas,
			'report_type': 'qweb-html',
		}


	@api.model
	def get_vehicle_emi(self):
		res = self.env['fleet.emi'].search([('start_date','>=',self.from_date),('start_date','<=',self.to_date)])
		print 'eeeeeeeeeeeeeeeeeeeeeeeee',res
		return res

	@api.multi
	def print_vehicle_emi_report(self):
		
		datas = {
			'ids': self._ids,
			'model': self._name,
			'form': self.read(),
			'context':self._context,
		}
		return{
			'type' : 'ir.actions.report.xml',
			'report_name' : 'hiworth_construction.report_vehicle_emi_report_template',
			'datas': datas,
			'report_type': 'qweb-pdf',
#
		}