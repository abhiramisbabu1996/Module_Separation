from openerp import models, fields, api

class RecivablesandPayables(models.Model):
    _inherit='account.account'

    @api.model
    def get_childs(self, parent_id): 
        
#         print 'qqqqqqqqqqqqqq855555555555555555555', self.env['account.account'].search([('parent_id','=',parent_id)]), self._context
        start_date = self._context['start_date']
        end_date = self._context['end_date']
        
        parent_obj = self.env['account.account'].search([('id','=',parent_id)])
        parent_obj.temp_start_date = start_date
        parent_obj.temp_end_date = end_date
        
        
        for line in self.env['account.account'].search([('parent_id','=',parent_id)]):
            line.temp_debit = 0.0
            line.temp_credit = 0.0
            line.temp_balance = 0.0
#             if line.balance!=0.0:
            move_lines = self.env['account.move.line'].search([('account_id','=',line.id), ('date','>=',start_date), ('date','<=',end_date)])
#             if actual_status == True:
#                 move_lines = self.env['account.move.line'].search([('account_id','=',line.id),('date','>=',date_from), ('date','<=',date_to),('review','=',False)])
#             print 'move_lines======================', move_lines
            total_debit = 0.0
            total_credit = 0.0
#                     line.temp_balance = 0.0
            for moves in move_lines:
                if moves.debit != 0.0:
                    total_debit += moves.debit
                if moves.credit != 0.0:
                    total_credit += moves.credit
#                 print 'total_debit=========================',total_debit,total_credit
            line.temp_debit = total_debit
            line.temp_credit = total_credit
            line.temp_balance =  total_debit - total_credit
#             line.temp_start_date = start_date
#             line.temp_end_date = end_date
#             print 'temp_balance -=============================',line, line.temp_balance
#         for line in acc_obj:
#             if line.child_id and line.temp_balance == 0.0:
#                 for child in line.child_id:
#                     line.temp_balance += child.temp_balance
        res = self.env['account.account'].search([('parent_id','=',parent_id)])
        recordset = res.sorted(key=lambda r: r.name)
        return recordset
