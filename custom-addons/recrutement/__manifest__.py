{
    "name": "Gestion recrutement",
    "version": "1.0",
    "category": "Sales",
    "summary": "Simple gestion recrutement module",
    "depends": ["base","mail", "hr", "hr_recruitment"],
    "data": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/sequences.xml',
        'views/recrutment_planning_header_views.xml',
        'views/recrutment_direction_views.xml',
        'views/recrutment_project_views.xml',
        'views/recruitment_menu.xml',
        'wizard/recruitment_planning_return_wizard_views.xml',
        
    ],
    "installable": True,
    "application": True,
}
