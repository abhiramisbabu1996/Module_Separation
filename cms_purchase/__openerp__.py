{
    'name': 'cms_purchase',
    'version': '1.0',
    'author': 'Hiworth Solutions Pvt Ltd',
    'description': '''
        Purchase Management for Construction
    ''',
    'category': 'Themes/Backend',
    'depends': [
        'base','purchase','project','account','hr','fleet','stock','cms_project',

    ],
    'data': [
        'views/purchase_form.xml',
        'views/view_stock_history_views.xml',
        'views/goods_tranfer_note.xml',
        'views/site_purchase.xml',

        'views/material_request.xml',
        'views/material_cost_transfer_views.xml',
        'views/material_issue_slip_views.xml',
        'views/purchase_view.xml',
        'views/purchase_comparison.xml',
        'views/purchase_return_views.xml',
        'views/purchase_form.xml',
        'views/purchase_order_action_data.xml',

    ],
    'css': ['static/src/css/styles.css'],
    'auto_install': False,
    'installable': True,
}
