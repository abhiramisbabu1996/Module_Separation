{
    'name': 'cms_project',
    'version': '1.0',
    'author': 'Hiworth Solutions Pvt Ltd',
    'description': '''
        Project Management for Construction
    ''',
    'category': 'Themes/Backend',
    'depends': [
        'base','project',

    ],
    'data': [
        'views/project.xml',
        'views/master_plan.xml',
        'views/planning_chart.xml',
        'views/task.xml',
    ],
    'css': ['static/src/css/styles.css'],
    'auto_install': False,
    'installable': True,
}
