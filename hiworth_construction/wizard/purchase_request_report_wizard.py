from openerp import models, fields, api
from datetime import datetime


class PurchaseRequestReport(models.TransientModel):
    _name = 'purchase.request.report'
    
    
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    department = fields.Selection([('general', 'General'), ('vehicle', 'Vehicle'),
                                   ('bitumen', 'Bitumen'), ('interlocks', 'Interlocks'),
                                   ('site', 'Site')], "Department")
    location_id = fields.Many2one('stock.location', "Location", domain=[('usage', '=', 'internal')])
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
       
        if not self._context.get('from_stock',False):
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hiworth_construction.report_purchase_request_view',
                'datas': datas,
                'report_type': 'qweb-html',
            }
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hiworth_construction.report_purchase_request_view_stock',
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
                'report_name': 'hiworth_construction.report_purchase_request_view',
                'datas': datas,
                'report_type': 'qweb-pdf',
            }
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hiworth_construction.report_purchase_request_view_stock',
                'datas': datas,
                'report_type': 'qweb-pdf',
            }

    @api.multi
    def get_products(self):
        self.ensure_one()

        start_date = datetime.strptime(self.date_from, "%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
        end_date = datetime.strptime(self.date_to, "%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")

        temp_dict={}
        data_list = []
        count = 1
        dom = []
        if self.date_from:
            dom.append(('order_date', '>=', start_date))
        if self.date_to:
            dom.append(('order_date', '<=', end_date))
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
        dom.append(('state','in',['draft','confirm','accept','order']))

        ordered_qty = 0
        genral_dep = self.env['site.purchase'].search(dom, order='order_date desc')
        for gne in genral_dep:
            for gne_line in gne.site_purchase_item_line_ids:
                tax_name = ''
                status = ''
                if gne.state == 'draft':
                    status='Request Draft'
                elif gne.state =='confirm':
                    status='Requested'
                else:
                    status='Request Intiated'

                department = ''
                if gne.general_purchase:
                    department = 'General Purchase'
                elif gne.bitumen_purchase:
                    department = 'Bitumen Purchase'
                elif gne.vehicle_purchase:
                    department = 'Vehicle Purchase'
                elif gne.interlocks_purchase:
                    department = 'Interlocks Purchase'
                else:
                    department = 'Site Request'
                ordered_qty = gne_line.quantity
                rfq = self.env['purchase.order'].search([('site_purchase_id','=',gne.id),('state','in',['draft','sent'])])
                rfq_name = ''
                if rfq:
                    if rfq.state == 'draft':
                        status = 'RFQ Draft'
                    else:
                        status = 'RFQ'
                    rfq_name = rfq.name
                comp_name = ''
                comparison = self.env['purchase.comparison'].search([('state', 'in', ['draft', 'requested','first_approve','validated2']),('mpr_id','=',gne.id)])
                if comparison:
                    for comp_line in comparison.comparison_line:

                        tax_name = ''
                        if comp_line.product_id.id == gne_line.item_id.id:
                            for tax in comp_line.tax_id:
                                tax_name = tax_name + tax.name + ','
                        status = ''
                        if comparison.state == 'draft':
                            status = 'Comparison Draft'
                        elif comparison.state == 'requested':
                            status = 'Requested'
                        elif comparison.state == 'first_approve':
                            status = 'First Approval'
                        else:
                            status = 'Second Approval'
                        rfq_name = comparison.quotation_id.name
                        comp_name = comparison.number
                purchase_order_name = ''

                received_qty = 0
                closed_qty = 0
                order_rate = 0
                recei_rate = 0
                sub_total = 0
                tax_amount = 0
                total = 0
                purchase_order  = self.env['purchase.order'].search([('site_purchase_id','=',gne.id),('state', 'in', ['confirmed','approved1'])])
                if purchase_order:
                    if purchase_order.state == 'confirmed':
                        status = 'First Approval'
                    else:
                        status = 'Second Approval'
                    rfq_name = purchase_order.quotation_id.name
                    comp_name = purchase_order.comparison_id.number
                    purchase_order_name = purchase_order.partner_id.name
                    for purchase_line in purchase_order.order_line:
                        if purchase_line.product_id.id == gne_line.item_id.id:
                            tax_name = ''
                            for tax in purchase_line.taxes_id:
                                tax_name += tax.name + ','
                            received_qty = purchase_line.received_qty
                            ordered_qty = purchase_line.required_qty
                            closed_qty = purchase_line.closed_qty
                            order_rate = purchase_line.expected_rate
                            recei_rate = purchase_line.received_rate
                            sub_total = purchase_line.price_subtotal
                            tax_amount = purchase_line.tax_amount
                            total = purchase_line.total


                temp_dict.update({count: {
                    'date': datetime.strptime(gne.order_date, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y"),
                    'department': department,
                    'order_by': gne.order_by,
                    'mode_order': gne.mode_of_order,
                    'pr': gne.name,
                    'rfq': rfq_name,
                    'comp': comp_name,
                    'supplier': purchase_order_name,
                    'location': gne.site.name,
                    'product': gne_line.item_id.name,
                    'desc': gne_line.desc,
                    'ordered_qty': ordered_qty,
                    'received_qty': received_qty,
                    'closed_qty': closed_qty,
                    'uom': gne_line.unit.name,
                    'ordered_rate':order_rate,
                    'received_rate':recei_rate,
                    'tax': tax_name,
                    'subtotal': sub_total,
                    'tax_amount': tax_amount,
                    'total': total,
                    'status': status}})

                data_list.append(temp_dict)
                count += 1




            
        
        return data_list
        