{
    'name': 'cms_activity_report',
    'version': '1.0',
    'author': 'Hiworth Solutions Pvt Ltd',
    'description': '''
        Activity Report for Construction
    ''',
    'category': 'Themes/Backend',
    'depends': [
        'base','project','account','hr','fleet','stock','cms_project',

    ],
    'data': [
        'views/supervisor_statement.xml',

    ],
    'css': ['static/src/css/styles.css'],
    'auto_install': False,
    'installable': True,
}
