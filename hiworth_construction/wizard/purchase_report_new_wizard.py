from openerp import models, fields, api
from datetime import datetime


class PurchaseRequestReport(models.TransientModel):
    _name = 'purchase.request.report.new'
    
    
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")
    department = fields.Selection([('general','General'),('vehicle','Vehicle'),
                                  ('bitumen','Bitumen'),('interlocks','Interlocks'),
                                  ('site','Site')],"Department")
    location_id = fields.Many2one('stock.location',"Location",domain=[('usage','=','internal')])
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
                'report_name': 'hiworth_construction.purchase_request_new',
                'datas': datas,
                'report_type': 'qweb-html',
            }
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hiworth_construction.purchase_request_new_stock',
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
                'report_name': 'hiworth_construction.purchase_request_new',
                'datas': datas,
                'report_type': 'qweb-pdf',
            }
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'hiworth_construction.purchase_request_new_stock',
                'datas': datas,
                'report_type': 'qweb-pdf',
            }



    @api.multi
    def get_products(self):
        self.ensure_one()

        start_date = datetime.strptime(self.date_from,"%Y-%m-%d").strftime("%Y-%m-%d 00:00:00")
        end_date = datetime.strptime(self.date_to,"%Y-%m-%d").strftime("%Y-%m-%d 23:59:59")
        temp_dict = {}
        data_list = []
        count = 1
        dom = []
        if self.date_from:
            dom.append(('max_expected_date','>=',self.date_from))
        if self.date_to:
            dom.append(('max_expected_date','<=',self.date_to))
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
        genral_dep = self.env['site.purchase'].search(dom,order='order_date desc')

        for gene in genral_dep:

            purchase_order_pool = self.env['purchase.order']
            purchase_dom = []
            purchase_dom.append(('state', 'in', ['approved']))
            purchase_dom.append('|')
            purchase_dom.append(('site_purchase_id', '=', gene.id))
            purchase_dom.append(('site_purchase_ids', 'in', gene.id))


            if self.company_contractor_id:
                purchase_dom.append(('company_contractor_id', '=', self.company_contractor_id.id))

            for purchase_order_line in purchase_order_pool.search(purchase_dom, order='name asc'):
                for line in purchase_order_line.order_line:
                    tax_name = ''
                    for tax in line.taxes_id:
                        tax_name += tax.name + ','
                    department = ''
                    if purchase_order_line.site_purchase_id.general_purchase:
                        department = 'General Purchase'
                    elif purchase_order_line.site_purchase_id.bitumen_purchase:
                        department = 'Bitumen Purchase'
                    elif purchase_order_line.site_purchase_id.vehicle_purchase:
                        department = 'Vehicle Purchase'
                    elif purchase_order_line.site_purchase_id.interlocks_purchase:
                        department = 'Interlocks Purchase'
                    else:
                        department = 'Site Request'
                    status = ''
                    if purchase_order_line.state == 'approved':
                        status = 'Order Placed'
                    pr_nos = ''
                    for site_pur in purchase_order_line.site_purchase_ids:
                        pr_nos += site_pur.name
                    if purchase_order_line.site_purchase_id:
                        pr_nos += purchase_order_line.site_purchase_id.name
                    temp_dict.update({count: {
                        'date': datetime.strptime(purchase_order_line.date_order, "%Y-%m-%d %H:%M:%S").strftime("%d-%m-%Y"),
                        'pr_no':pr_nos,
                    'po_no':purchase_order_line.name,
                    'department':department,
                    'location':purchase_order_line.location_id.name,
                        'supplier':purchase_order_line.partner_id.name,
                    'item':line.product_id.name,
                    'unit':line.product_uom.name,
                    'quantity':line.required_qty,
                    'rate':line.expected_rate,
                    'taxes':tax_name,
                    'received_qty':line.received_qty,
                    'received_rate':line.received_rate,
                    'foreclosure_qty':line.closed_qty,
                    'total_qty_reced':line.received_qty + line.closed_qty,
                        'balance_qty': line.required_qty - (line.received_qty + line.closed_qty),
                    'status':status}})

                    data_list.append(temp_dict)
                    count += 1




        return data_list