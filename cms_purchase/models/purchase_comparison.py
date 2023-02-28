from __future__ import division
from openerp.exceptions import Warning
from openerp import models, fields, api , _
from datetime import datetime
from lxml import etree

class PurchaseComparison(models.Model):
    _name = 'purchase.comparison'
    _rec_name = 'number'
    _order = 'id desc'


    @api.model
    def create(self,vals):

        res = super(PurchaseComparison, self).create(vals)
        res.number = self.env['ir.sequence'].next_by_code('purchase.comparison.code')
        return res

    @api.multi
    def write(self,vals):
        partner_id1 = ''
        partner_id2 = ''
        partner_id3 = ''
        partner_id4 = ''
        partner_id5 = ''
        partner_id1 = vals.get('partner_id1', False) and vals.get('partner_id1') or self.partner_id1.id
        partner_id2 = vals.get('partner_id2', False) and vals.get('partner_id2') or self.partner_id2.id
        partner_id3 = vals.get('partner_id3', False) and vals.get('partner_id3') or self.partner_id3.id
        partner_id4 = vals.get('partner_id4', False) and vals.get('partner_id4') or self.partner_id4.id
        partner_id5 = vals.get('partner_id5', False) and vals.get('partner_id5') or self.partner_id5.id

        if vals.get('partner_id1'):
            if (partner_id1 == partner_id2 or partner_id1 == partner_id3 or partner_id1 == partner_id4 or partner_id1 == partner_id5):
                raise Warning(_('You have already selected this supplier'))
            # if partner_id2 == partner_id3 != False:
            #     if (partner_id2 == partner_id3 or partner_id1 == partner_id3):
            #         raise Warning(_('You have already selected this supplier'))

        if vals.get('partner_id2'):
            if (partner_id2 == partner_id1 or partner_id2 == partner_id3 or partner_id2 == partner_id4 or partner_id2 == partner_id5):
                raise Warning(_('You have already selected this supplier'))
            # if partner_id1 == partner_id3 != False:
            #     if (partner_id2 == partner_id3 or partner_id1 == partner_id3):
            #         raise Warning(_('You have already selected this supplier'))

        if vals.get('partner_id3'):
            if (partner_id3 == partner_id2 or partner_id1 == partner_id3 or partner_id3 == partner_id4 or partner_id3 == partner_id5):
                raise Warning(_('You have already selected this supplier'))

        if vals.get('partner_id4'):
            if (partner_id4 == partner_id2 or partner_id4 == partner_id3 or partner_id1 == partner_id4 or partner_id4 == partner_id5):
                raise Warning(_('You have already selected this supplier'))

        if vals.get('partner_id5'):
            if (partner_id5 == partner_id2 or partner_id5 == partner_id3 or partner_id5 == partner_id4 or partner_id1 == partner_id5):
                raise Warning(_('You have already selected this supplier'))

            # if partner_id1 == partner_id2 != False:
            #     if (partner_id2 == partner_id3 or partner_id1 == partner_id3):
            #         raise Warning(_('You have already selected this supplier'))

        res = super(PurchaseComparison, self).write(vals)
        return res

    @api.onchange('mpr_id')
    def onchange_mpr_id(self):
        for rec in self:
            if rec.mpr_id:
                values = []
                rec.project_id = rec.mpr_id.project_id.id
                for mpr_line in rec.mpr_id.site_purchase_item_line_ids:
                    values.append((0,0,{'product_id':mpr_line.item_id.id,
                        'qty':mpr_line.quantity,
                        'uom':mpr_line.unit.id}))
                rec.comparison_line = values
            partner_list = self._context.get('default_supplier_ids')
            if partner_list == 'None':
                partner_list = rec.quotation_id.supplier_ids.ids
            return{
                'domain':{'partner_id1':[('id','in',partner_list)],
                          'partner_id2':[('id','in',partner_list)],
                          'partner_id3':[('id','in',partner_list)],
                          'partner_id4':[('id','in',partner_list)],
                          'partner_id5':[('id','in',partner_list)],
                          'partner_selected':[('id','in',partner_list)]}
            }



    # @api.onchange('supplier_ids')
    # def onchange_partner_selected(self):
    #     for rec in self:
    #
    #         partner_list = rec.supplier_ids.ids
    #         if partner_list == []:
    #             partner_list.append(self.partner_id1.id)
    #             partner_list.append(self.partner_id2.id)
    #             partner_list.append(self.partner_id3.id)
    #             partner_list.append(self.partner_id4.id)
    #             partner_list.append(self.partner_id5.id)
    #         return{
    #             'domain':{'partner_id1':[('id','in',partner_list)],
    #                       'partner_id2':[('id','in',partner_list)],
    #                       'partner_id3':[('id','in',partner_list)],
    #                       'partner_id4':[('id','in',partner_list)],
    #                       'partner_id5':[('id','in',partner_list)],
    #                       'partner_selected':[('id','in',partner_list)]}
    #         }

    @api.one
    def button_request(self):
        if not self.partner_id1 and not self.partner_id2 and not self.partner_id3:
            raise Warning(_('Atleast Select one Supplier Details'))
        self.state = 'requested'

    @api.one
    def button_approve1(self):
        self.user_id1 = self.env.user.id
        self.state = 'first_approve'


    @api.one
    def button_approve2(self):
        # if self.partner_selected.id == self.partner_id1.id:
        #     if self.total_amt1 > 1000:
        #         if self.env.user.has_group('hiworth_construction.group_warehouse_user') and not self.env.user.has_group('base.group_erp_manager'):
        #             raise Warning(_('You have not access to approve this comparison.'))
        # if self.partner_selected.id == self.partner_id2.id:
        #     if self.total_amt2 > 1000:
        #         if self.env.user.has_group('hiworth_construction.group_warehouse_user') and not self.env.user.has_group(
        #                 'base.group_erp_manager'):
        #             raise Warning(_('You have not access to approve this comparison.'))
        # if self.partner_selected.id == self.partner_id3.id:
        #     if self.total_amt3 > 1000:
        #         if self.env.user.has_group('hiworth_construction.group_warehouse_user') and not self.env.user.has_group(
        #                 'base.group_erp_manager'):
        #             raise Warning(_('You have not access to approve this comparison.'))
        # if self.partner_selected.id == self.partner_id3.id:
        #     if self.total_amt3 > 1000:
        #         if self.env.user.has_group('hiworth_construction.group_warehouse_user') and not self.env.user.has_group(
        #                 'base.group_erp_manager'):
        #             raise Warning(_('You have not access to approve this comparison.'))
        # if self.partner_selected.id == self.partner_id3.id:
        #     if self.total_amt3 > 1000:
        #         if self.env.user.has_group('hiworth_construction.group_warehouse_user') and not self.env.user.has_group(
        #                 'base.group_erp_manager'):
        #             raise Warning(_('You have not access to approve this comparison.'))
        if self.env.user.has_group('hiworth_construction.group_warehouse_user') and not self.env.user.has_group(
                'base.group_erp_manager'):
            raise Warning(_('You have not access to approve this comparison.'))

        self.user_id2 = self.env.user.id
        self.state = 'validated2'
    @api.one
    def button_approve3(self):
        if self.env.user.has_group('hiworth_construction.group_warehouse_user') and not self.env.user.has_group(
                'base.group_erp_manager'):
            raise Warning(_('You have not access to approve this comparison.'))

        self.user_id1 = self.env.user.id
        self.state = 'ceo_approval'


    # @api.onchange('partner_id')
    # def onchange_partner_id2
        
    @api.one
    def button_cancel(self):
        for rec in self:
            rec.state = 'draft'

    @api.one
    def button_po_create(self):

        list = []
        purchase_ids = []

        vals = {
            'state':'approved',
            'site_purchase_id':self.mpr_id.id,
            'pricelist_id': self.partner_selected.property_product_pricelist_purchase.id,
            'minimum_plann_date': self.mpr_id.min_expected_date,
            'maximum_planned_date':self.mpr_id.max_expected_date,
            'project_id': self.project_id.id,
            'location_id': self.mpr_id.site.id,
            'account_id': self.partner_selected.property_account_payable.id,
            'mpr_id':self.mpr_id.id,
            'origin':self.mpr_id.name,
            'comparison_id':self.id,
            'quotation_id':self.quotation_id.id,
            'company_contractor_id':self.quotation_id.company_contractor_id.id,
            'vehicle_agent_id': self.mpr_id.vehicle_agent.id,
            'vehicle_id':self.vehicle_id.id,
            'currency_id':self.quotation_id.currency_id.id,
            'notes': self.remark,

        }

        partner1_lines = self.comparison_line.filtered(lambda l: l.vendor_select_id == self.partner_id1)
        partner2_lines = self.comparison_line.filtered(lambda l: l.vendor_select_id == self.partner_id2)
        partner3_lines = self.comparison_line.filtered(lambda l: l.vendor_select_id == self.partner_id3)
        partner4_lines = self.comparison_line.filtered(lambda l: l.vendor_select_id == self.partner_id4)
        partner5_lines = self.comparison_line.filtered(lambda l: l.vendor_select_id == self.partner_id5)
        
        if partner1_lines:
            for l in partner1_lines:
                dictionary = {
                    'product_id': l.product_id.id,
                    'name': l.product_id.name,
                    'required_qty': l.qty,
                    'brand_name':l.brand_name.id,
                    'product_uom': l.product_id.uom_id.id,
                    'price_unit': 0.0,
                    'taxes_id':l.tax_id and [(6,0,[l.tax_id.id])] or [],
                    'account_id': self.env['account.account'].search([('name', '=', 'Purchase')]).id,
                }
                dictionary['expected_rate'] = l.rate1
                dictionary['price_unit'] = l.rate1
                l.product_id.standard_price = l.rate1
                list.append((0, 0, dictionary))

            vals['partner_id'] = self.partner_id1.id
            vals['payment_term_id'] = self.payment_term1.id
            vals['notes'] = str(self.remark)
            vals['packing_charge'] = self.p_n_f1
            vals['packing_tax_id'] = self.p_n_f1_tax_id.id
            vals['loading_tax'] = self.loading_charge1
            vals['loading_tax_id'] = self.loading1_tax_id.id
            vals['transport_cost'] = self.transport_cost1
            vals['transport_cost_tax_id'] = self.transport1_tax_id.id
            vals['other_charge'] = self.other_charge1

            if len(list) > 0:
                vals['order_line'] = list
                purchase_id = self.env['purchase.order'].create(vals)
                purchase_id.state = 'approved'
                purchase_ids.append(purchase_id.id)
        list = []

        if partner2_lines:
            vals['partner_id'] = self.partner_id2.id
            vals['payment_term_id'] = self.payment_term2.id
            vals['notes'] = str(self.remark) + " " +str(self.remark2) or ''
            vals['packing_charge'] = self.p_n_f2
            vals['packing_tax_id'] = self.p_n_f2_tax_id.id
            vals['loading_tax'] = self.loading_charge2
            vals['loading_tax_id'] = self.loading2_tax_id.id
            vals['transport_cost'] = self.transport_cost2
            vals['transport_cost_tax_id'] = self.transport2_tax_id.id
            vals['other_charge'] = self.other_charge2

            for l in partner2_lines:

                dictionary = {
                    'product_id': l.product_id.id,
                    'name': l.product_id.name,
                    'required_qty': l.qty,
                    'brand_name': l.brand_name.id,
                    'product_uom': l.product_id.uom_id.id,
                    'price_unit': 0.0,
                    'taxes_id': l.tax_id and [(6, 0, [l.tax_id.id])] or [],
                    'account_id': self.env['account.account'].search([('name', '=', 'Purchase')]).id,
                }
                dictionary['expected_rate'] = l.rate2
                dictionary['price_unit'] = l.rate2
                l.product_id.standard_price = l.rate2
                list.append((0, 0, dictionary))

            # if self.partner_selected.id == self.partner_id2.id:
            #     flag = 2
            #     if flag == 2:

            if len(list) > 0:
                vals['order_line'] = list
                purchase_id = self.env['purchase.order'].create(vals)
                purchase_id.state = 'approved'
                purchase_ids.append(purchase_id.id)
                
        if partner3_lines:
            vals['partner_id'] = self.partner_id3.id
            vals['payment_term_id'] = self.payment_term3.id
            vals['notes'] = str(self.remark) + " " +str(self.remark3) or ''
            vals['packing_charge'] = self.p_n_f3
            vals['packing_tax_id'] = self.p_n_f3_tax_id.id
            vals['loading_tax'] = self.loading_charge3
            vals['loading_tax_id'] = self.loading3_tax_id.id
            vals['transport_cost'] = self.transport_cost3
            vals['transport_cost_tax_id'] = self.transport3_tax_id.id
            
            for l in partner3_lines:
                dictionary = {
                    'product_id': l.product_id.id,
                    'name': l.product_id.name,
                    'required_qty': l.qty,
                    'brand_name': l.brand_name.id,
                    'product_uom': l.product_id.uom_id.id,
                    'price_unit': 0.0,
                    'taxes_id': l.tax_id and [(6, 0, [l.tax_id.id])] or [],
                    'account_id': self.env['account.account'].search([('name', '=', 'Purchase')]).id,
                }
                dictionary['expected_rate'] = l.rate3
                dictionary['price_unit'] = l.rate3
                l.product_id.standard_price = l.rate3
                list.append((0, 0, dictionary))
                
            if len(list) > 0:
                vals['order_line'] = list
                purchase_id = self.env['purchase.order'].create(vals)
                purchase_id.state = 'approved'
                purchase_ids.append(purchase_id.id)
                
        if partner4_lines:
            vals['partner_id'] = self.partner_id4.id
            vals['payment_term_id'] = self.payment_term4.id
            vals['notes'] = str(self.remark) + " " + str(self.remark4) or ''
            vals['packing_charge'] = self.p_n_f4
            vals['packing_tax_id'] = self.p_n_f4_tax_id.id
            vals['loading_tax'] = self.loading_charge4
            vals['loading_tax_id'] = self.loading4_tax_id.id
            vals['transport_cost'] = self.transport_cost4
            vals['transport_cost_tax_id'] = self.transport4_tax_id.id

            for l in partner4_lines:
                dictionary = {
                    'product_id': l.product_id.id,
                    'name': l.product_id.name,
                    'required_qty': l.qty,
                    'brand_name': l.brand_name.id,
                    'product_uom': l.product_id.uom_id.id,
                    'price_unit': 0.0,
                    'taxes_id': l.tax_id and [(6, 0, [l.tax_id.id])] or [],
                    'account_id': self.env['account.account'].search([('name', '=', 'Purchase')]).id,
                }
                dictionary['expected_rate'] = l.rate4
                dictionary['price_unit'] = l.rate4
                l.product_id.standard_price = l.rate4
                list.append((0, 0, dictionary))

 
            if len(list) > 0:
                vals['order_line'] = list
                purchase_id = self.env['purchase.order'].create(vals)
                purchase_id.state = 'approved'
                purchase_ids.append(purchase_id.id)
        
        if partner5_lines:
            vals['partner_id'] = self.partner_id5.id
            vals['payment_term_id'] = self.payment_term5.id
            vals['notes'] = str(self.remark) + " " + str(self.remark5) or ''
            vals['packing_charge'] = self.p_n_f5
            vals['packing_tax_id'] = self.p_n_f5_tax_id.id
            vals['loading_tax'] = self.loading_charge5
            vals['loading_tax_id'] = self.loading5_tax_id.id
            vals['transport_cost'] = self.transport_cost5
            vals['transport_cost_tax_id'] = self.transport5_tax_id.id

            for l in partner5_lines:
                dictionary = {
                    'product_id': l.product_id.id,
                    'name': l.product_id.name,
                    'required_qty': l.qty,
                    'brand_name': l.brand_name.id,
                    'product_uom': l.product_id.uom_id.id,
                    'price_unit': 0.0,
                    'taxes_id': l.tax_id and [(6, 0, [l.tax_id.id])] or [],
                    'account_id': self.env['account.account'].search([('name', '=', 'Purchase')]).id,
                }
                dictionary['expected_rate'] = l.rate5
                dictionary['price_unit'] = l.rate5
                l.product_id.standard_price = l.rate5
                list.append((0, 0, dictionary))

            if len(list) > 0:
                vals['order_line'] = list
                purchase_id = self.env['purchase.order'].create(vals)
                purchase_id.state = 'approved'
                purchase_ids.append(purchase_id.id)

        self.purchase_ids = purchase_ids
        self.state = 'po'
        self.mpr_id.state = 'order'

    @api.multi
    def button_view_purchase(self):
        res = {
            'type': 'ir.actions.act_window',
            'name': 'Purchases',
            'res_model': 'purchase.order',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('id', '=', self.purchase_ids.ids)]
        }

        return res


            

            


    @api.one
    @api.depends('comparison_line','tax_id1','p_n_f1_tax_id','p_n_f2_tax_id','p_n_f3_tax_id','loading_charge1','loading_charge2','loading_charge3','transport_cost1','transport_cost2','transport_cost3','loading1_tax_id','loading2_tax_id','loading3_tax_id','transport1_tax_id','transport2_tax_id','transport2_tax_id','p_n_f1','p_n_f2','p_n_f3')
    def get_total(self):
        for s in self:
            t1 = 0.0
            t2 = 0.0
            t3 = 0.0
            t4 = 0.0
            t5 = 0.0

            nt1 = 0.0
            nt2 = 0.0
            nt3 = 0.0
            nt4 = 0.0
            nt5 = 0.0

            tax1 = 0.0
            tax2 = 0.0
            tax3 = 0.0
            tax4 = 0.0
            tax5 = 0.0

            igst1 = 0.0
            igst2 = 0.0
            igst3 = 0.0
            igst4 = 0.0
            igst5 = 0.0

           
            for l in s.comparison_line:
                if l.non_tax_charge1==0:
                    t1 += l.sub_total1
                else:
                    nt1 += l.non_tax_charge1
                if l.non_tax_charge2==0:
                    t2 += l.sub_total2
                else:
                    nt2 += l.non_tax_charge2
                if l.non_tax_charge3==0:
                    t3 += l.sub_total3
                else:
                    nt3 += l.non_tax_charge3
                # if l.non_tax_charge4==0:
                #     t4 += l.sub_total4
                # else:
                #     nt4 += l.non_tax_charge4
                # if l.non_tax_charge5==0:
                #     t5 += l.sub_total5
                # else:
                #     nt5 += l.non_tax_charge5
                t4 += l.sub_total4
                t5 += l.sub_total5
                if l.tax_id.tax_type == 'gst':
                    tax1 += l.sub_total1 * l.tax_id.amount
                    tax2 += l.sub_total2 * l.tax_id.amount
                    tax3 += l.sub_total3 * l.tax_id.amount
                    tax4 += l.sub_total4 * l.tax_id.amount
                    tax5 += l.sub_total5 * l.tax_id.amount
                if l.tax_id.tax_type == 'igst':
                    igst1 += l.sub_total1 * l.tax_id.amount
                    igst2 += l.sub_total2 * l.tax_id.amount
                    igst3 += l.sub_total3 * l.tax_id.amount
                    igst4 += l.sub_total4 * l.tax_id.amount
                    igst5 += l.sub_total5 * l.tax_id.amount
                if not s.tax_id1.price_include:
                    t4 = t4 + t4 * s.tax_id1.amount
                if not s.tax_id1.price_include:
                    t5 = t5 + t5 * s.tax_id1.amount
            loading_charge1 = 0.0
            other_charge1=0
            other_charge2=0
            other_charge3=0
            gtax_loading_charge1 =0
            igstax_loading_charge1 = 0
            tax =0
            gst_tax_amount =0
            igst_tax_amount =0
            if s.loading1_tax_id:
                for taxes in s.loading1_tax_id:
                    if taxes.price_include==True:
                        tax +=(1+taxes.amount)
                    if taxes.tax_type == 'gst':
                        gst_tax_amount +=  taxes.amount
                    if taxes.tax_type == 'igst':
                        igst_tax_amount += taxes.amount
                if tax == 0:
                    tax = 1
                loading_charge1 = s.loading_charge1/tax
                gtax_loading_charge1 = loading_charge1 * gst_tax_amount
                igstax_loading_charge1 = loading_charge1 * igst_tax_amount
            else:
                other_charge1 += s.loading_charge1

            loading_charge2 = 0.0
            gtax_loading_charge2 = 0
            igstax_loading_charge2 = 0
            tax = 0
            gst_tax_amount = 0
            igst_tax_amount = 0
            if s.loading2_tax_id:
                for taxes in s.loading2_tax_id:
                    if taxes.price_include == True:
                        tax += (1 + taxes.amount)
                    if taxes.tax_type == 'gst':
                        gst_tax_amount += taxes.amount
                    if taxes.tax_type == 'igst':
                        igst_tax_amount += taxes.amount
                if tax == 0:
                    tax = 1
                loading_charge2 = s.loading_charge2 / tax
                gtax_loading_charge2 = loading_charge2 * gst_tax_amount
                igstax_loading_charge2 = loading_charge2 * igst_tax_amount
            else:
                other_charge2 += s.loading_charge2
            loading_charge3 = 0.0
            gtax_loading_charge3 = 0
            igstax_loading_charge3 = 0
            tax = 0
            gst_tax_amount = 0
            igst_tax_amount = 0
            if s.loading3_tax_id:
                for taxes in s.loading3_tax_id:
                    if taxes.price_include == True:
                        tax += (1 + taxes.amount)
                    if taxes.tax_type == 'gst':
                        gst_tax_amount += taxes.amount
                    if taxes.tax_type == 'igst':
                        igst_tax_amount += taxes.amount
                if tax == 0:
                    tax = 1
                loading_charge3 = s.loading_charge3 / tax
                gtax_loading_charge3 = loading_charge3 * gst_tax_amount
                igstax_loading_charge3 = loading_charge3 * igst_tax_amount
            else:
                other_charge3 += s.loading_charge3
            transport_cost1 = 0.0
            gtax_transport_cost1 = 0
            igstax_transport_cost1 = 0
            tax = 0
            gst_tax_amount = 0
            igst_tax_amount = 0
            if s.transport1_tax_id:
                for taxes in s.transport1_tax_id:
                    if taxes.price_include == True:
                        tax += (1 + taxes.amount)
                    if taxes.tax_type == 'gst':
                        gst_tax_amount += taxes.amount
                    if taxes.tax_type == 'igst':
                        igst_tax_amount += taxes.amount
                if tax == 0:
                    tax = 1
                transport_cost1 = s.transport_cost1 / tax
                gtax_transport_cost1 = transport_cost1 * gst_tax_amount
                igstax_transport_cost1 = transport_cost1 * igst_tax_amount
            else:
                other_charge1 += s.transport_cost1
            transport_cost2 = 0.0
            gtax_transport_cost2 = 0
            igstax_transport_cost2 = 0
            tax = 0
            gst_tax_amount = 0
            igst_tax_amount = 0
            if s.transport2_tax_id:
                for taxes in s.transport2_tax_id:
                    if taxes.price_include == True:
                        tax += (1 + taxes.amount)
                    if taxes.tax_type == 'gst':
                        gst_tax_amount += taxes.amount
                    if taxes.tax_type == 'igst':
                        igst_tax_amount += taxes.amount
                if tax == 0:
                    tax = 1
                transport_cost2 = s.transport_cost2 / tax
                gtax_transport_cost2 = transport_cost2 * gst_tax_amount
                igstax_transport_cost2 = transport_cost2 * igst_tax_amount
            else:
                other_charge2 += s.transport_cost2
            transport_cost3 = 0.0
            gtax_transport_cost3 = 0
            igstax_transport_cost3 = 0
            tax = 0
            gst_tax_amount = 0
            igst_tax_amount = 0
            if s.transport3_tax_id:
                for taxes in s.transport3_tax_id:
                    if taxes.price_include == True:
                        tax += (1 + taxes.amount)
                    if taxes.tax_type == 'gst':
                        gst_tax_amount += taxes.amount
                    if taxes.tax_type == 'igst':
                        igst_tax_amount += taxes.amount
                if tax == 0:
                    tax = 1
                transport_cost3 = s.transport_cost3 / tax
                gtax_transport_cost3 = transport_cost3 * gst_tax_amount
                igstax_transport_cost3 = transport_cost3 * igst_tax_amount
            else:
                other_charge3 += s.transport_cost3
            p_n_f1 = 0.0
            gtax_p_n_f1 = 0
            igstax_p_n_f1 = 0
            tax = 0
            gst_tax_amount = 0
            igst_tax_amount = 0
            if s.p_n_f1_tax_id:
                for taxes in s.p_n_f1_tax_id:
                    if taxes.price_include == True:
                        tax += (1 + taxes.amount)
                    if taxes.tax_type == 'gst':
                        gst_tax_amount += taxes.amount
                    if taxes.tax_type == 'igst':
                        igst_tax_amount += taxes.amount
                if tax == 0:
                    tax = 1
                p_n_f1 = s.p_n_f1 / tax
                gtax_p_n_f1 = p_n_f1 * gst_tax_amount
                igstax_p_n_f1 = p_n_f1 * igst_tax_amount
            else:
                other_charge1 += s.p_n_f1
            p_n_f2 = 0.0
            gtax_p_n_f2 = 0
            igstax_p_n_f2 = 0
            tax = 0
            gst_tax_amount = 0
            igst_tax_amount = 0
            if s.p_n_f2_tax_id:
                for taxes in s.p_n_f2_tax_id:
                    if taxes.price_include == True:
                        tax += (1 + taxes.amount)
                    if taxes.tax_type == 'gst':
                        gst_tax_amount += taxes.amount
                    if taxes.tax_type == 'igst':
                        igst_tax_amount += taxes.amount
                if tax == 0:
                    tax = 1
                p_n_f2 = s.p_n_f2 / tax
                gtax_p_n_f2 = p_n_f2 * gst_tax_amount
                igstax_p_n_f2 = p_n_f2 * igst_tax_amount
            else:
                other_charge2 += s.p_n_f2
            p_n_f3 = 0.0
            gtax_p_n_f3 = 0
            igstax_p_n_f3 = 0
            tax = 0
            gst_tax_amount = 0
            igst_tax_amount = 0
            if s.p_n_f3_tax_id:
                for taxes in s.p_n_f3_tax_id:
                    if taxes.price_include == True:
                        tax += (1 + taxes.amount)
                    if taxes.tax_type == 'gst':
                        gst_tax_amount += taxes.amount
                    if taxes.tax_type == 'igst':
                        igst_tax_amount += taxes.amount
                if tax == 0:
                    tax = 1
                p_n_f3 = s.p_n_f3 / tax
                gtax_p_n_f3 = p_n_f3 * gst_tax_amount
                igstax_p_n_f3 = p_n_f3 * igst_tax_amount
            else:
                other_charge3 += s.p_n_f3

            s.taxable1 = t1 +loading_charge1 + transport_cost1 + p_n_f1
            s.taxable2 = t2+loading_charge2 +transport_cost2 + p_n_f2
            s.taxable3 = t3+loading_charge3 + transport_cost3 + p_n_f3
            # s.taxable4 = t4+loading_charge4 + transport_cost4 + p_n_f4
            # s.taxable5 = t5+loading_charge5 + transport_cost5 + p_n_f5

            s.cgst_id1 = tax1/2 + gtax_loading_charge1/2  + gtax_transport_cost1/2 + gtax_p_n_f1/2
            s.cgst_id2 =tax2/2  + gtax_loading_charge2/2 +gtax_transport_cost2/2 + gtax_p_n_f2/2
            s.cgst_id3 = tax3/2 + gtax_loading_charge3/2 + gtax_transport_cost3/2 + gtax_p_n_f3/2
            s.sgst_id1 = tax1/2 + gtax_loading_charge1/2 + gtax_transport_cost1/2 +gtax_p_n_f1/2
            s.sgst_id2 =tax2/2 + gtax_loading_charge2/2 +gtax_transport_cost2/2 + gtax_p_n_f2/2
            s.sgst_id3 = tax3/2 + gtax_loading_charge3/2 + gtax_transport_cost3/2 + gtax_p_n_f3/2
            s.igst_id1 = igst1 + igstax_loading_charge1 + igstax_transport_cost1 + igstax_p_n_f1
            s.igst_id2 = igst2 + igstax_loading_charge2 + igstax_transport_cost2 + igstax_p_n_f2
            s.igst_id3 = igst3 + igstax_loading_charge3 + igstax_transport_cost3 + igstax_p_n_f3
            s.other_charge1 = other_charge1
            s.other_charge2 = other_charge2
            s.other_charge3 = other_charge3
            s.non_tax_charge1 = nt1
            s.non_tax_charge2 = nt2
            s.non_tax_charge3 = nt3
            s.total_amt1 = s.taxable1 + s.non_tax_charge1 + s.cgst_id1+s.igst_id1+s.sgst_id1 + s.other_charge1
            s.total_amt2 = s.taxable2 + s.non_tax_charge2 + s.cgst_id2+s.igst_id2+s.sgst_id2 + s.other_charge2
            s.total_amt3 = s.taxable3 + s.non_tax_charge3 + s.cgst_id3+s.igst_id3+s.sgst_id3 + s.other_charge3
            # s.total_amt4 = s.taxable4 + s.non_tax_charge4 + s.cgst_id3+s.igst_id3+s.sgst_id4 + s.other_charge4
            # s.total_amt5 = s.taxable5 + s.non_tax_charge5 + s.cgst_id3+s.igst_id3+s.sgst_id5 + s.other_charge5
                 

            s.total_amt4 = t4 + s.loading_charge4 + s.transport_cost5 + s.p_n_f4
            s.total_amt5 = t5 + s.loading_charge5 + s.transport_cost5 + s.p_n_f5


    @api.depends('quotation_id')
    def compute_supplier_ids(self):
        for rec in self:
            if rec.quotation_id:
                rec.supplier_ids = [(6,0,rec.quotation_id.supplier_ids.ids)]

    @api.onchange('partner_id1', 'partner_id2','partner_id3','partner_id4','partner_id5')
    def onchnage_partner_id1(self):
        for rec in self:
            if rec.partner_id1:
                if rec.partner_id1 == rec.partner_id2 or rec.partner_id1 == rec.partner_id3 or rec.partner_id1 == rec.partner_id4 or rec.partner_id1 == rec.partner_id5:
                    raise Warning(_('You have already selected this supplier'))
            if rec.partner_id2:
                if rec.partner_id2 == rec.partner_id1 or rec.partner_id2 == rec.partner_id3 or rec.partner_id2 == rec.partner_id4 or rec.partner_id2 == rec.partner_id5:
                    raise Warning(_('You have already selected this supplier'))
            if rec.partner_id3:
                if rec.partner_id3 == rec.partner_id1 or rec.partner_id3 == rec.partner_id2 or rec.partner_id3 == rec.partner_id4 or rec.partner_id3 == rec.partner_id5:
                    raise Warning(_('You have already selected this supplier'))
            if rec.partner_id4:
                if rec.partner_id4 == rec.partner_id1 or rec.partner_id4 == rec.partner_id2 or rec.partner_id4 == rec.partner_id3 or rec.partner_id1 == rec.partner_id5:
                    raise Warning(_('You have already selected this supplier'))
            if rec.partner_id5:
                if rec.partner_id5 == rec.partner_id1 or rec.partner_id5 == rec.partner_id2 or rec.partner_id5 == rec.partner_id3 or rec.partner_id5 == rec.partner_id4:
                    raise Warning(_('You have already selected this supplier'))

                value_list = []
                if rec.partner_id1:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id1.id,
                                              'balance': rec.partner_id1.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id1.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id1.property_account_receivable.balance) + "Dr"}))
                if rec.partner_id2:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id2.id,
                                              'balance': rec.partner_id2.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id2.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id2.property_account_receivable.balance) + "Dr"}))
                if rec.partner_id3:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id3.id,
                                              'balance': rec.partner_id3.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id3.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id3.property_account_receivable.balance) + "Dr"}))
                if rec.partner_id4:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id4.id,
                                              'balance': rec.partner_id4.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id4.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id4.property_account_receivable.balance) + "Dr"}))
                if rec.partner_id5:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id5.id,
                                              'balance': rec.partner_id5.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id5.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id5.property_account_receivable.balance) + "Dr"}))

                rec.debit_balance_ids = value_list

    @api.onchange('partner_id2')
    def onchnage_partner_id2(self):
        for rec in self:
            if rec.partner_id2:
                if rec.partner_id1.id == rec.partner_id2.id or rec.partner_id2.id == rec.partner_id3.id:
                    raise Warning(_('You have already selected this supplier'))
                value_list = []
                if rec.partner_id1:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id1.id,
                                              'balance': rec.partner_id1.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id1.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id1.property_account_receivable.balance) + "Dr"}))
                if rec.partner_id2:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id2.id,
                                              'balance': rec.partner_id2.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id2.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id2.property_account_receivable.balance) + "Dr"}))
                if rec.partner_id3:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id3.id,
                                              'balance': rec.partner_id3.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id3.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id3.property_account_receivable.balance) + "Dr"}))

                rec.debit_balance_ids = value_list


    @api.onchange('partner_id3')
    def onchnage_partner_id3(self):
        for rec in self:
            if rec.partner_id3:
                if rec.partner_id1.id == rec.partner_id3.id or rec.partner_id2.id == rec.partner_id3.id:
                    raise Warning(_('You have already selected this supplier'))
                value_list = []
                if rec.partner_id1:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id1.id,
                                              'balance': rec.partner_id1.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id1.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id1.property_account_receivable.balance) + "Dr"}))
                if rec.partner_id2:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id2.id,
                                              'balance': rec.partner_id2.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id2.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id2.property_account_receivable.balance) + "Dr"}))
                if rec.partner_id3:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id3.id,
                                              'balance': rec.partner_id3.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id3.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id3.property_account_receivable.balance) + "Dr"}))
                if rec.partner_id4:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id4.id,
                                              'balance': rec.partner_id4.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id4.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id4.property_account_receivable.balance) + "Dr"}))
                if rec.partner_id5:
                    value_list.append((0, 0, {'supplier_id': rec.partner_id5.id,
                                              'balance': rec.partner_id5.property_account_receivable.balance >= 0 and str(
                                                  rec.partner_id5.property_account_receivable.balance) + "Cr" or str(
                                                  rec.partner_id5.property_account_receivable.balance) + "Dr"}))

                rec.debit_balance_ids = value_list

    notes = fields.Text()
    project_id = fields.Many2one('project.project', 'Project')
    number = fields.Char('Comparison No')
    mpr_id = fields.Many2one('site.purchase',string="P.R No")
    date = fields.Datetime('Comparison Date',default=lambda self: fields.datetime.now())
    partner_id1 = fields.Many2one('res.partner', 'Supplier')
    remark1 = fields.Char('Remark')
    partner_id2 = fields.Many2one('res.partner', 'Supplier')
    remark2 = fields.Char('Remark')
    partner_id3 = fields.Many2one('res.partner', 'Supplier')
    remark3 = fields.Char('Remark')
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")
    partner_id4 = fields.Many2one('res.partner', 'Supplier')
    remark4 = fields.Char('Remark')
    partner_id5 = fields.Many2one('res.partner', 'Supplier')
    remark5 = fields.Char('Remark')
    state = fields.Selection([('draft', 'Draft'),
                              ('requested', 'Requested'),
                              ('first_approve','PM Approval'),
                              ('validated2', 'Com. Dept. Approval'),
                              ('ceo_approval', 'Accounts/CEO approval'),
                              ('po', 'Purchase Order'),
                              ('cancel',"Cancel")],default='draft',string="Status")
    comparison_line = fields.One2many('purchase.comparison.line', 'res_id', 'Comparison Line')
    purchase_id = fields.Many2one('purchase.order', 'Purchase Order')
    purchase_ids = fields.Many2many('purchase.order', 'purchase_comparison_new_id', 'purchase_relation_id', 'comparison_id')
    quotation_id = fields.Many2one('purchase.order',"RFQ No")
    approved_date = fields.Datetime('Approved Date', default=datetime.now())

    tax_id1 = fields.Many2one('account.tax', 'GST')
    # tax_id2 = fields.Many2one('account.tax', 'GST')
    # tax_id3 = fields.Many2one('account.tax', 'GST')
    # tax_id4 = fields.Many2one('account.tax', 'GST')
    # tax_id5 = fields.Many2one('account.tax', 'GST')

    p_n_f1 =fields.Float('P&F')
    p_n_f2 =fields.Float('P&F')
    p_n_f3 =fields.Float('P&F')
    p_n_f4 =fields.Float('P&F')
    p_n_f5 =fields.Float('P&F')

    p_n_f1_tax_id = fields.Many2one('account.tax',"Taxes",domain="[('parent_id','=',False)]")
    p_n_f2_tax_id = fields.Many2one('account.tax', "Taxes",domain="[('parent_id','=',False)]")
    p_n_f3_tax_id = fields.Many2one('account.tax',"Taxes",domain="[('parent_id','=',False)]")
    p_n_f4_tax_id = fields.Many2one('account.tax',"Taxes",domain="[('parent_id','=',False)]")
    p_n_f5_tax_id = fields.Many2one('account.tax',"Taxes",domain="[('parent_id','=',False)]")

    loading_charge1 = fields.Float('Loading Charge')
    loading_charge2 = fields.Float('Loading Charge')
    loading_charge3 = fields.Float('Loading Charge')
    loading_charge4 = fields.Float('Loading Charge')
    loading_charge5 = fields.Float('Loading Charge')

    loading1_tax_id = fields.Many2one('account.tax',"Taxes",domain="[('parent_id','=',False)]")
    loading2_tax_id = fields.Many2one('account.tax', "Taxes",domain="[('parent_id','=',False)]")
    loading3_tax_id = fields.Many2one('account.tax',"Taxes",domain="[('parent_id','=',False)]")
    loading4_tax_id = fields.Many2one('account.tax',"Taxes",domain="[('parent_id','=',False)]")
    loading5_tax_id = fields.Many2one('account.tax',"Taxes",domain="[('parent_id','=',False)]")

    transport_cost1 = fields.Float('Transport Cost')
    transport_cost2 = fields.Float('Transport Cost')
    transport_cost3 = fields.Float('Transport Cost')
    transport_cost4 = fields.Float('Transport Cost')
    transport_cost5 = fields.Float('Transport Cost')

    transport1_tax_id = fields.Many2one('account.tax',  "Taxes",domain="[('parent_id','=',False)]")
    transport2_tax_id = fields.Many2one('account.tax',"Taxes",domain="[('parent_id','=',False)]")
    transport3_tax_id = fields.Many2one('account.tax',  "Taxes",domain="[('parent_id','=',False)]")
    transport4_tax_id = fields.Many2one('account.tax',  "Taxes",domain="[('parent_id','=',False)]")
    transport5_tax_id = fields.Many2one('account.tax',  "Taxes",domain="[('parent_id','=',False)]")

    delivery_period1 = fields.Char('Ready To Stock')
    delivery_period2 = fields.Char('Ready To Stock')
    delivery_period3 = fields.Char('Ready To Stock')
    delivery_period4 = fields.Char('Ready To Stock')
    delivery_period5 = fields.Char('Ready To Stock')

    payment_term1 = fields.Many2one('account.payment.term', 'Term Of Payment')
    payment_term2 = fields.Many2one('account.payment.term', 'Term Of Payment')
    payment_term3 = fields.Many2one('account.payment.term', 'Term Of Payment')
    payment_term4 = fields.Many2one('account.payment.term', 'Term Of Payment')
    payment_term5 = fields.Many2one('account.payment.term', 'Term Of Payment')

    total_amt5 = fields.Float('Total Amount', compute='get_total',store=True)
    total_amt4 = fields.Float('Total Amount', compute='get_total',store=True)
    total_amt3 = fields.Float('Total Amount', compute='get_total',store=True)
    total_amt2 = fields.Float('Total Amount', compute='get_total',store=True)
    total_amt1 = fields.Float('Total Amount', compute='get_total',store=True)

    partner_selected = fields.Many2one('res.partner', 'Vendor Selected',domain="[('supplier','=',True)]")
    remark = fields.Text('Note')
    user_id1 = fields.Many2one('res.users', 'First approval')
    user_id2 = fields.Many2one('res.users', 'Second approval')

    taxable1= fields.Float(compute="get_total",store=True)
    taxable2= fields.Float(compute="get_total",store=True)
    taxable3= fields.Float(compute="get_total",store=True)
    taxable4= fields.Float(compute="get_total",store=True)
    taxable5= fields.Float(compute="get_total",store=True)

    cgst_id1 = fields.Float(compute="get_total",store=True)
    cgst_id2 = fields.Float(compute="get_total",store=True)
    cgst_id3 = fields.Float(compute="get_total",store=True)
    sgst_id1 = fields.Float(compute="get_total",store=True)
    sgst_id2 = fields.Float(compute="get_total",store=True)
    sgst_id3 = fields.Float(compute="get_total",store=True)
   
    igst_id1 = fields.Float(compute="get_total",store=True)
    igst_id2 = fields.Float(compute="get_total",store=True)
    igst_id3 = fields.Float(compute="get_total",store=True)

    other_charge1 = fields.Float(compute="get_total", store=True)
    other_charge2 = fields.Float(compute="get_total", store=True)
    other_charge3 = fields.Float(compute="get_total", store=True)
    other_charge4 = fields.Float(compute="get_total", store=True)
    other_charge5 = fields.Float(compute="get_total", store=True)

    non_tax_charge1 = fields.Float(compute="get_total", store=True)
    non_tax_charge2 = fields.Float(compute="get_total", store=True)
    non_tax_charge3 = fields.Float(compute="get_total", store=True)
    non_tax_charge4 = fields.Float(compute="get_total", store=True)
    non_tax_charge5 = fields.Float(compute="get_total", store=True)

    read_boolean = fields.Boolean("Read and understood the approval points")
    supplier_ids = fields.Many2many('res.partner','comparison_partner_rel','comparison_id','partner_id',compute='compute_supplier_ids')
    location_id = fields.Many2one('stock.location',"Location")
    debit_balance_ids = fields.One2many('debit.balance','comparison_id',"Debit Balance")
    # attachment1 = fields.Many2many('ir.attachment', 'attach_rel', 'doc_id', 'attach_id3', string="Supplier1 Quatation",)
    # attachment2 = fields.Many2many('ir.attachment', 'attach_rel', 'doc_id', 'attach_id3', string="Supplier2 Quatation",)
    # attachment3 = fields.Many2many('ir.attachment', 'attach_rel', 'doc_id', 'attach_id3', string="Supplier3 Quatation",)
    # attachment4 = fields.Many2many('ir.attachment', 'attach_rel', 'doc_id', 'attach_id3', string="Supplier4 Quatation",)
    # attachment5 = fields.Many2many('ir.attachment', 'attach_rel', 'doc_id', 'attach_id3', string="Supplier5 Quatation",)
    # field_name = fields.Binary(string='Name of field')


    # binary_field = fields.Binary('File')
    # file_name = fields.Char('Filename')


    # tax_ids = fields.Many2many('account.tax','comparison_line_account_tax_rel','comparison_line_id','tax_id','GST')




class PurchaseComparisonLine(models.Model):

    _name = 'purchase.comparison.line'

    

    @api.onchange('product_id')
    def onchange_product(self):
        self.uom = self.product_id.uom_id.id

    @api.one
    def get_total(self):
        tax = 0
        non_tax1= 0
        non_tax2 = 0
        non_tax3 = 0
        non_tax4 = 0
        non_tax5 = 0
        for s in self:
            if s.tax_id:
                for taxes in s.tax_id:
                    if taxes.price_include:
                        tax +=(1+taxes.amount)
            else:
                non_tax1 += s.rate1 * s.qty
                non_tax2 += s.rate2 * s.qty
                non_tax3 += s.rate3 * s.qty
                non_tax4 += s.rate4 * s.qty
                non_tax5 += s.rate5 * s.qty
        
            if tax==0:
                tax=1
            s.sub_total1 = (s.rate1/tax) * s.qty
            s.sub_total2 = (s.rate2/tax) * s.qty
            s.sub_total3 = (s.rate3/tax) * s.qty
            s.sub_total4 = (s.rate4/tax) * s.qty
            s.sub_total5 = (s.rate5/tax) * s.qty

            s.non_tax_charge1 = non_tax1
            s.non_tax_charge2 = non_tax2
            s.non_tax_charge3 = non_tax3
            s.non_tax_charge4 = non_tax4
            s.non_tax_charge5 = non_tax5

    @api.onchange('product_id','vendor_select_id')
    def onchange_vendor_select_id(self):
        vendor_ids = []
        if self.res_id:
            vendor_ids.append(self.res_id.partner_id1.id) if self.res_id.partner_id1 else vendor_ids
            vendor_ids.append(self.res_id.partner_id2.id) if self.res_id.partner_id2 else vendor_ids
            vendor_ids.append(self.res_id.partner_id3.id) if self.res_id.partner_id3 else vendor_ids
            vendor_ids.append(self.res_id.partner_id4.id) if self.res_id.partner_id4 else vendor_ids
            vendor_ids.append(self.res_id.partner_id5.id) if self.res_id.partner_id5 else vendor_ids

        return {
            'domain': {'vendor_select_id': [('id', 'in', vendor_ids)]}
        }

    vendor_select_id = fields.Many2one('res.partner', 'Selected Supplier',domain="[('supplier','=',True)]")
    res_id = fields.Many2one('purchase.comparison', 'Purchase Comparison')
    product_id = fields.Many2one('product.product', 'Description',size=10)
    qty = fields.Float('Quantity',size=10)
    uom = fields.Many2one('product.uom', 'Unit')
    tax_id = fields.Many2one('account.tax',string="Tax",domain="[('parent_id','=',False)]")
    brand_name = fields.Many2one('material.brand')

    rate1 = fields.Float('Supplier1 Rate ')
    rate2 = fields.Float('Supplier2 Rate')
    rate3 = fields.Float('Supplier3 Rate')
    rate4 = fields.Float('Supplier4 Rate')
    rate5 = fields.Float('Supplier5 Rate')

    sub_total1 = fields.Float('Subtotal ', compute="get_total")
    sub_total2 = fields.Float('Subtotal ', compute="get_total")
    sub_total3 = fields.Float('Subtotal', compute="get_total")
    sub_total4 = fields.Float('Subtotal', compute="get_total")
    sub_total5 = fields.Float('Subtotal', compute="get_total")

    non_tax_charge1 = fields.Float(compute="get_total", store=True)
    non_tax_charge2 = fields.Float(compute="get_total", store=True)
    non_tax_charge3 = fields.Float(compute="get_total", store=True)
    non_tax_charge4 = fields.Float(compute="get_total", store=True)
    non_tax_charge5 = fields.Float(compute="get_total", store=True)


class DebitBalance(models.Model):
    _name = 'debit.balance'

    supplier_id = fields.Many2one('res.partner')
    balance = fields.Char("Balance")
    comparison_id = fields.Many2one('purchase.comparison')
