from openerp import models, fields, api
from datetime import datetime


class PurchaseReturnWizard(models.TransientModel):
    _name = 'purchase.return.wizard'

    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    department = fields.Selection([('general', 'General'), ('vehicle', 'Vehicle'),
                                   ('bitumen', 'Bitumen'), ('interlocks', 'Interlocks'),
                                   ('site', 'Site')], "Department")
    location_id = fields.Many2one('stock.location', "Location", domain=[('usage', '=', 'internal')])
    purchase_order_id = fields.Many2one('purchase.order',"Purchase Order",domain=[('state', 'in', ['approved','done'])])
    detailed_report = fields.Boolean("Detailed Report")
    company_contractor_id = fields.Many2one('res.partner', domain=[('company_contractor', '=', True)], string="Company")


    @api.multi
    def action_view_purchase_request(self):
        self.ensure_one()

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_construction.purchase_return_new',
            'datas': datas,
            'report_type': 'qweb-html',
        }

    @api.multi
    def action_print_purchase_request(self):
        self.ensure_one()

        datas = {
            'ids': self._ids,
            'model': self._name,
            'form': self.read(),
            'context': self._context,
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'hiworth_construction.purchase_return_new',
            'datas': datas,
            'report_type': 'qweb-pdf',
        }

    @api.multi
    def get_products(self):
        self.ensure_one()

        start_date = datetime.strptime(self.date_from, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
        end_date = datetime.strptime(self.date_to, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")

        temp_dict = {}
        data_list = []
        count = 1
        dom = []

        if self.department:
            if self.department == 'general':
                dom.append(('general_purchase', '=', True))
            if self.department == 'vehicle':
                dom.append(('vehicle_purchase', '=', True))
            if self.department == 'bitumen':
                dom.append(('bitumen_purchase', '=', True))
            if self.department == 'interlocks':
                dom.append(('interlocks_purchase', '=', True))
            if self.department == 'site':
                dom.append(('site_request', '=', True))
        if self.location_id:
            dom.append(('site', '=', self.location_id.id))
        genral_dep = self.env['site.purchase'].search(dom, order='order_date asc')
        goods_dom = []
        if self.date_from:
            dom.append(('date', '>=', self.date_from))
        if self.date_to:
            dom.append(('date', '<=', self.date_to))
        if genral_dep:
            goods_dom.append(('mpr_id', 'in', genral_dep.ids))
        if self.purchase_order_id:
            goods_dom.append(('purchase_id', '=', self.purchase_order_id.id))
        if self.location_id:
            goods_dom.append(('site', '=', self.location_id.id))
        if self.company_contractor_id:
            goods_dom.append(('company_contractor_id', '=', self.company_contractor_id.id))
        goods_recieve_report_pool = self.env['purchase.return']

        for goods_report in goods_recieve_report_pool.search(goods_dom,order='date asc'):
            department = ''
            if goods_report.mpr_id.general_purchase:
                department = 'General Purchase'
            elif goods_report.mpr_id.bitumen_purchase:
                department = 'Bitumen Purchase'
            elif goods_report.mpr_id.vehicle_purchase:
                department = 'Vehicle Purchase'
            elif goods_report.mpr_id.interlocks_purchase:
                department = 'Interlocks Purchase'
            else:
                department = 'Site Request'
            if self.detailed_report:
                for line in goods_report.goods_recieve_report_line_ids:
                    tax_name = ''
                    for tax in line.tax_ids:
                        tax_name += tax.name + ','


                    temp_dict.update({count: {
                        'date': datetime.strptime(goods_report.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                        'pr_no': goods_report.mpr_id.name,
                        'po_no': goods_report.purchase_id.name,
                        'department': department,
                        'location': goods_report.site.name,
                        'grn_no':goods_report.name,
                        'supplier':goods_report.supplier_id.name,
                        'invoice_no':line.po_quantity,
                        'invoice_date':'',
                        'item': line.item_id.name,
                        'unit': line.unit_id.name,
                        'quantity': line.quantity_accept,
                        'rate': line.rate,
                        'taxes': tax_name,
                        'taxable_amt': round(line.taxable_amount,2),
                        'cgst_amt': round(line.cgst_amount,2),
                        'sgst_amt': round(line.sgst_amount,2),
                        'igst_amt': round(line.igst_amount,2) ,
                        'non_taxable_amt': round(line.non_taxable_amount,2),
                        'other_charge': '',
                    'round_off_amount':'',
                        'total_amount':'',
                    }})

                    data_list.append(temp_dict)
                    count += 1
                for other in goods_report.other_charge_details_ids:

                    tax_name = ''
                    for tax in other.tax_id:
                        tax_name += tax.name + ','

                    temp_dict.update({count: {
                        'date': datetime.strptime(goods_report.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                        'pr_no': goods_report.mpr_id.name,
                        'po_no': goods_report.purchase_id.name,
                        'department': department,
                        'location': goods_report.site.name,
                        'grn_no':goods_report.name,
                        'supplier':goods_report.supplier_id.name,
                        'invoice_no':'',
                        'invoice_date':'',
                        'item': other.other_charge_id.name,
                        'unit': '',
                        'quantity': '',
                        'rate': other.amount,
                        'taxes': tax_name,
                        'taxable_amt': round(other.taxable_amount,2),
                        'cgst_amt': round(other.cgst_amount,2),
                        'sgst_amt': round(other.sgst_amount,2),
                        'igst_amt': round(other.igst_amount,2) ,
                        'non_taxable_amt': '',
                        'other_charge': not other.is_tax_applicable and other.amount,
                    'round_off_amount':'',
                        'total_amount':'',
                    }})

                    data_list.append(temp_dict)
                    count += 1

            temp_dict.update({count: {
                'date': datetime.strptime(goods_report.date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                'pr_no': goods_report.mpr_id.name,
                'po_no': goods_report.purchase_id.name,
                'department': department,
                'location': goods_report.site.name,
                'grn_no': goods_report.name,
                'supplier': goods_report.supplier_id.name,
                'invoice_no': '',
                'invoice_date': '',
                'item':'',
                'unit':'' ,
                'quantity': '',
                'rate': '',
                'taxes': '',
                'taxable_amt': round(goods_report.taxable_amount,2),
                'cgst_amt': round(goods_report.cgst_amount,2),
                'sgst_amt': round(goods_report.sgst_amount,2),
                'igst_amt': round(goods_report.igst_amount,2),
                'non_taxable_amt': round(goods_report.non_taxable_amount,2),
                'other_charge': round(goods_report.other_charge,2),
                'round_off_amount': round(goods_report.round_off_amount,2),
                'total_amount': round(goods_report.total_amount,2),
            }})

            data_list.append(temp_dict)
            count += 1

        return data_list
