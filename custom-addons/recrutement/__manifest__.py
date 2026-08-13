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
        'views/recruitment_planning_header_views.xml',
        'views/recruitment_menu.xml',
        
    ],
    "installable": True,
    "application": True,
}
