//openerp.hiworth_construction = function (require) {
//    var FormView = require('web.FormView');
//    FormView.include({
//     load_record: function() {
//      this._super.apply(this, arguments);
//      if (this.model === 'site.purchase') {
//          if (this.datarecord && (this.datarecord.state in ['order'])) {
//            this.$buttons.find('.o_form_button_edit').css({'display':'none'});
//          }
//          else {
//            this.$buttons.find('.o_form_button_edit').css({'display':''});
//          }
//       }
//    }});
//};
