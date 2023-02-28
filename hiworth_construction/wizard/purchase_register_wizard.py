from openerp import models, fields, api
from datetime import datetime


class PurchaseRegisterWizard(models.TransientModel):
    _name = 'purchase.register.wizard'

    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    department = fields.Selection([('general', 'General'), ('vehicle', 'Vehicle'),
                                   ('bitumen', 'Bitumen'), ('interlocks', 'Interlocks'),
                                   ('site', 'Site')], "Department")
    category_id = fields.Many2one('product.category',"Category")
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
        if not self._context.get('from_stock', False):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hiworth_construction.purchase_register_new',
                'datas': datas,
                'report_type': 'qweb-html',
            }
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hiworth_construction.purchase_register_new_stock',
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

        if not self._context.get('from_stock', False):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hiworth_construction.purchase_register_new',
                'datas': datas,
                'report_type': 'qweb-pdf',
            }
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hiworth_construction.purchase_register_new_stock',
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
        dom.append(('state', 'in', ['order','received']))
        if self.location_id:
            dom.append(('site', '=', self.location_id.id))
        genral_dep = self.env['site.purchase'].search(dom, order='order_date desc')
        for genral in genral_dep:

            goods_dom = []
            if self.date_from:
                goods_dom.append(('Date', '>=', start_date))
            if self.date_to:
                goods_dom.append(('Date', '<=', end_date))


            goods_dom.append(('mpr_id', '=', genral.id))


            if self.location_id:
                goods_dom.append(('site', '=', self.location_id.id))

            if self.purchase_order_id:
                goods_dom.append(('purchase_id', '=', self.purchase_order_id.id))

            if self.company_contractor_id:
                goods_dom.append(('company_contractor_id', '=', self.company_contractor_id.id))


            goods_recieve_report_pool = self.env['goods.recieve.report']

            for goods_report in goods_recieve_report_pool.search(goods_dom,order='grr_no desc,purchase_id desc'):

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
                        date = ''
                        if goods_report.invoice_date:
                            date = datetime.strptime(goods_report.invoice_date, "%Y-%m-%d").strftime("%d-%m-%Y")
                        purchase_request = ''
                        if goods_report.mpr_id:
                            purchase_request = goods_report.mpr_id.name
                        else:
                            for pur in goods_report.site_purchase_ids:
                                purchase_request =purchase_request + pur.name + ','
                        if self.category_id:
                            if line.item_id.categ_id.id == self.category_id.id:
                                temp_dict.update({count: {
                                    'date': datetime.strptime(goods_report.Date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y"),
                                    'pr_no': purchase_request,
                                    'po_no': goods_report.purchase_id.name,
                                    'category': self.category_id and self.category_id.name or '',
                                    'location': goods_report.site.name,
                                    'grn_no':goods_report.grr_no,
                                    'supplier':goods_report.supplier_id.name,
                                    'invoice_no':goods_report.invoice_no,
                                    'invoice_date':date,
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
                        else:
                            temp_dict.update({count: {
                                'date': datetime.strptime(goods_report.Date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y"),
                                'pr_no': goods_report.mpr_id.name,
                                'po_no': goods_report.purchase_id.name,
                                'category': line.item_id.categ_id.name,
                                'department': department,
                                'location': goods_report.site.name,
                                'grn_no': goods_report.grr_no,
                                'supplier': goods_report.supplier_id.name,
                                'invoice_no': goods_report.invoice_no,
                                'invoice_date': date,
                                'item': line.item_id.name,
                                'unit': line.unit_id.name,
                                'quantity': line.quantity_accept,
                                'rate': line.rate,
                                'taxes': tax_name,
                                'taxable_amt': round(line.taxable_amount, 2),
                                'cgst_amt': round(line.cgst_amount, 2),
                                'sgst_amt': round(line.sgst_amount, 2),
                                'igst_amt': round(line.igst_amount, 2),
                                'non_taxable_amt': round(line.non_taxable_amount, 2),
                                'other_charge': '',
                                'round_off_amount': '',
                                'total_amount': '',
                            }})
                            data_list.append(temp_dict)
                            count += 1

                    for other in goods_report.other_charge_details_ids:
                        date = ''
                        if goods_report.invoice_date:
                            date = datetime.strptime(goods_report.invoice_date, "%Y-%m-%d").strftime("%d-%m-%Y")

                        tax_name = ''
                        for tax in other.tax_id:
                            tax_name += tax.name + ','

                        temp_dict.update({count: {
                            'date': datetime.strptime(goods_report.Date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y"),
                            'pr_no': goods_report.mpr_id.name,
                            'po_no': goods_report.purchase_id.name,
                            'department': department,
                            'category':self.category_id and self.category_id.name or '',
                            'location': goods_report.site.name,
                            'grn_no':goods_report.grr_no,
                            'supplier':goods_report.supplier_id.name,
                            'invoice_no':goods_report.invoice_no,
                            'invoice_date':date,
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
                date = ''
                if goods_report.invoice_date:
                    date = datetime.strptime(goods_report.invoice_date, "%Y-%m-%d").strftime("%d-%m-%Y")

                temp_dict.update({count: {
                    'date': datetime.strptime(goods_report.Date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y"),
                    'pr_no': goods_report.mpr_id.name,
                    'po_no': goods_report.purchase_id.name,
                    'department': department,
                    'category': self.category_id and self.category_id.name or '',
                    'location': goods_report.site.name,
                    'grn_no': goods_report.grr_no,
                    'supplier': goods_report.supplier_id.name,
                    'invoice_no': goods_report.invoice_no,
                    'invoice_date': date,
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
        if self.department == 'vehicle' or not self.department:
            driver_dom = []
            if self.date_from:
                driver_dom.append(('invoice_date','>=',self.date_from))
            if self.date_to:
                driver_dom.append(('invoice_date','<=',self.date_to))
            if self.location_id:
                driver_dom.append(('to_id2', '=', self.location_id.id))
            driver_daily_statement = self.env['driver.daily.statement.line'].search(driver_dom,order='invoice_date desc')

            for driver in driver_daily_statement:
                tax_name = ''
                tax_type=''
                for tax in driver.tax_ids:
                    tax_name += tax.name + ','
                    tax_type = tax.tax_type
                temp_dict.update({count: {
                    'date': datetime.strptime(driver.invoice_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    'pr_no': '',
                    'po_no': '',
                    'department': '',
                    'category': self.category_id and self.category_id.name or '',
                    'location': driver.to_id2.name,
                    'grn_no': driver.line_id.reference,
                    'supplier': driver.from_id2.name,
                    'invoice_no': driver.voucher_no,
                    'invoice_date':datetime.strptime(driver.invoice_date, "%Y-%m-%d").strftime("%d-%m-%Y"),
                    'item': driver.item_expense2.name,
                    'unit': '',
                    'quantity': driver.qty,
                    'rate': driver.rate,
                    'taxes': tax_name,
                    'taxable_amt': driver.sub_total,
                    'cgst_amt': tax_type=='gst' and (driver.tax_amount/2) or '' ,
                    'sgst_amt': tax_type=='gst' and (driver.tax_amount/2) or '',
                    'igst_amt': tax_type=='igst' and (driver.tax_amount) or '',
                    'non_taxable_amt': '',
                    'other_charge': '',
                    'round_off_amount': driver.round_off,
                    'total_amount': round(driver.sub_total_amount,2),
                }})
                data_list.append(temp_dict)
                count += 1
        return data_list
