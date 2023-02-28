from openerp import models, fields, api

class ViewPurchaseHistory(models.TransientModel):


    _name = 'view.purchase.history'


    products_id = fields.Many2many('product.product','purchase_product_rel','purchase_id','product_id',string='Products')
    

    @api.model
    def default_get(self,fields):
        res=super(ViewPurchaseHistory,self).default_get(fields)
        
        active_model=self._context.get('active_model')
        
        active_ids=self._context.get('active_ids')
        
        purchase_order=self.env['purchase.comparison']
        purchase_order_line = self.env['purchase.order']
        
        list_prod=[]
        if active_model=='purchase.comparison':
            for active in active_ids:
                browse_purchase_order=purchase_order.browse(active)
                
                for purchase in browse_purchase_order:
                    for products in purchase.comparison_line:

                            
                            
                            list_prod.append(products.product_id.id)
            
            
            res.update({'products_id':[(6,0,list_prod)]})
        if active_model=='purchase.order':
            for active in active_ids:
                browse_purchase_order=purchase_order_line.browse(active)
                
                for purchase in browse_purchase_order:
                    for products in purchase.order_line:

                            
                            
                            list_prod.append(products.product_id.id)
            
            
            res.update({'products_id':[(6,0,list_prod)]})
        return res

    @api.multi
    def purchase_history_submit(self):
        purchase_order_line = self.env['purchase.order.line'].search([('product_id','in',self.products_id.ids),])
        goods_received_report = self.env['goods.recieve.report']
        quantity = 0
        purchase_order_list = []

        for purchase_order in purchase_order_line:

            if purchase_order.order_id.state in ['approved','done']:
                goods_received_report = self.env['goods.recieve.report'].search([('purchase_id','=',purchase_order.order_id.id)])
                for goods_receive in goods_received_report:
                    for receive_line in goods_receive.goods_recieve_report_line_ids:
                        if receive_line.item_id.id in self.products_id.ids:
                            quantity += receive_line.quantity_reject
                purchase_order_list.append(purchase_order.id)
            # purchase_order.received_qty = quantity
       
       
        return {
                'type':'ir.actions.act_window',
                'name':'Purchase Order History',
                'res_model':'purchase.order.line',
                'view_type':'tree',
                'view_mode':'tree',
                'domain':"[('id','in',%s)]"%(purchase_order_list),
                'context':{'tree_view_ref':'hiworth_construcion.purchase_order_line_form_view'}
                
              }