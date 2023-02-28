from openerp import fields, models, api
from datetime import datetime
from openerp.osv import osv
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta
from dateutil import tz
from pytz import timezone


class AccountsReportWizard(models.TransientModel):
    _name = 'accounts.report.wizard'

    from_date = fields.Date('Date From')
    to_date = fields.Date('Date To')
    # location_id = fields.Many2one('stock.location', 'Location')

    month = fields.Selection([('January', 'January'),
                              ('February', 'February'),
                              ('March', 'March'),
                              ('April', 'April'),
                              ('May', 'May'),
                              ('June', 'June'),
                              ('July', 'July'),
                              ('August', 'August'),
                              ('September', 'September'),
                              ('October', 'October'),
                              ('November', 'November'),
                              ('December', 'December')], 'Month', )

    @api.onchange('month')
    def onchange_month(self):
        if self.month:
            date = '1 ' + self.month + ' ' + str(datetime.now().year)

            date_object = datetime.strptime(date, '%d %B %Y')
            self.from_date = date_object
            end_date = date_object + relativedelta(day=31)

            self.to_date = end_date



    @api.multi
    def generate_xls_report(self):

        return self.env["report"].get_action(self, report_name='AccountsReport.xlsx')


class BillReportXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, invoices):
        worksheet = workbook.add_worksheet("AccountsReport")
        # raise UserError(str(invoices.invoice_no.id))

        boldc = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#D3D3D3', 'font': 'height 10'})
        heading_format = workbook.add_format({'bold': True, 'align': 'center', 'size': 10})
        bold = workbook.add_format({'bold': True})
        rightb = workbook.add_format({'align': 'right', 'bold': True})
        right = workbook.add_format({'align': 'right'})
        regular = workbook.add_format({'align': 'center', 'bold': False, 'size': 8})
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#D3D3D3',
            'font_color': '#000000',
        })
        format_hidden = workbook.add_format({
            'hidden': True
        })
        align_format = workbook.add_format({
            'align': 'right',
        })
        row = 6
        col = 1
        new_row = row

        worksheet.set_column('A:A', 13)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('D:S', 13)

        worksheet.merge_range('A1:S1', 'Palathra Constructions', boldc)
        worksheet.merge_range('A3:S3', 'Accounts Details From %s To %s' % (
        datetime.strptime(invoices.from_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
        datetime.strptime(invoices.to_date, "%Y-%m-%d").strftime("%d-%m-%Y")), boldc)
        worksheet.merge_range('A4:A5', 'Sl.NO', regular)
        worksheet.merge_range('B4:D4', 'Accounts', regular)
        worksheet.merge_range('E4:E5', 'Available Balance', regular)


        count = 1
        for rec in invoices:
            date_from = datetime.strptime(invoices.from_date, "%Y-%m-%d")
            date_to = datetime.strptime(invoices.to_date, "%Y-%m-%d")
            accounts = self.env['res.partner.bank'].search([('common_usage','=',True)])
            count =1
            for acc in accounts:
                if acc.account_balance>0:

                    worksheet.write('A%s' % (new_row), count, regular)
                    worksheet.merge_range('B%s:D%s'% (new_row,new_row), acc.bank_name + '-' + acc.acc_number, regular)
                    worksheet.write('E%s' % (new_row), acc.account_balance, regular)
                    count += 1
                    new_row += 1

            new_row +=3
            worksheet.merge_range('A%s:A%s'% (new_row,new_row), 'Sl.NO', regular)
            worksheet.merge_range('B%s:D%s'% (new_row,new_row), 'Accounts', regular)
            worksheet.merge_range('E%s:E%s'% (new_row,new_row), 'Available Balance', regular)
            worksheet.merge_range('F%s:F%s' % (new_row, new_row), 'Availed Balance', regular)
            accounts = self.env['res.partner.bank'].search([])
            count = 1
            for acc in accounts:

                worksheet.write('A%s' % (new_row), count, regular)
                worksheet.merge_range('B%s:D%s' % (new_row, new_row), acc.bank_name and acc.bank_name or ''  + '-' + acc.acc_number and acc.acc_number or '', regular)
                worksheet.write('E%s' % (new_row), acc.account_balance, regular)
                worksheet.write('F%s' % (new_row), acc.usable_balance, regular)
                count += 1
                new_row += 1




BillReportXlsx('report.AccountsReport.xlsx', 'accounts.report.wizard')




