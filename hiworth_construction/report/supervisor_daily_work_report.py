from openerp import fields, models, api


class SupervisorDailyReport(models.TransientModel):
    _name = "supervisor.daily.report"

    from_date = fields.Date()
    to_date = fields.Date()
    supervisor = fields.Many2one('hr.employee')
    project = fields.Many2one('project.project')
    site = fields.Many2one('stock.location')

    @api.multi
    def view_supervisor_daily_report(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_construction.subcontractor_daily_report_template',
            'datas': datas,
            'report_type': 'qweb-html',
        }

    @api.model
    def get_daily_report(self):
        domain = []
        if self.from_date:
            domain+=[('date', '>=', self.from_date)]
        if self.to_date:
            domain+=[('date', '<=', self.to_date)]
        res = self.env['partner.daily.statement'].search(domain)
        print 'eeeeeeeeeeeeeeeeeeeeeeeee', res
        return res

    @api.multi
    def print_supervisor_daily_report(self):
        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_construction.subcontractor_daily_report_template',
            'datas': datas,
            'report_type': 'qweb-pdf',
            #
        }
