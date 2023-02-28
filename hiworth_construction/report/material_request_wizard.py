from openerp import fields, models, api
import datetime, calendar
from openerp.osv import osv

class HiworthMaterialRequestWizard(models.TransientModel):
    _name='hiworth.material.request.wizard'

    from_date=fields.Date(default=lambda self: self.default_time_range('from'))
    to_date=fields.Date(default=lambda self: self.default_time_range('to'))

    # Calculate default time ranges
    @api.model
    def default_time_range(self, type):
        year = datetime.date.today().year
        month = datetime.date.today().month
        last_day = calendar.monthrange(datetime.date.today().year,datetime.date.today().month)[1]
        first_day = 1
        if type=='from':
            return datetime.date(year, month, first_day)
        elif type=='to':
            return datetime.date(year, month, last_day)

    @api.multi
    def print_material_request_report(self):
        self.ensure_one()
        stockPicking = self.env['stock.picking']
        stockPickingRecs = stockPicking.search([('date','>=',self.from_date),('date','<=',self.to_date),('is_task_related','=',True)])

        if not stockPickingRecs:
            raise osv.except_osv(('Error'), ('There are no material requests to display. Please make sure material requests exist.'))

        datas = {
            'ids': stockPickingRecs._ids,
			'model': stockPicking._name,
			'form': stockPicking.read(),
			'context':self._context,
        }
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_material_request_template',
            'datas': datas,
            'context':{'start_date': self.from_date, 'end_date': self.to_date}
        }
        
    @api.multi
    def view_material_request_report(self):
        self.ensure_one()
        stockPicking = self.env['stock.picking']
        stockPickingRecs = stockPicking.search([('date','>=',self.from_date),('date','<=',self.to_date),('is_task_related','=',True)])

        if not stockPickingRecs:
            raise osv.except_osv(('Error'), ('There are no material requests to display. Please make sure material requests exist.'))

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context':self._context,
        }
        return{
            'type' : 'ir.actions.report.xml',
            'report_name' : 'hiworth_construction.report_material_request_template_view',
            'datas': datas,
            'report_type': 'qweb-html',
#             'context':{'start_date': self.from_date, 'end_date': self.to_date}
        }
        
        
    @api.multi
    def get_picking(self):
        self.ensure_one() 
        stockPicking = self.env['stock.picking']
        stockPickingRecs = stockPicking.search([('date','>=',self.from_date),('date','<=',self.to_date),('is_task_related','=',True)]) 
        return stockPickingRecs
