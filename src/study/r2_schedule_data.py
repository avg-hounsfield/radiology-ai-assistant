#!/usr/bin/env python3
"""
R2 Study Schedule Data Structure
Contains all rotation schedules, lessons, and quiz questions
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any

# Calculate rotation dates starting September 22, 2024
START_DATE = datetime(2024, 9, 22)
ROTATION_LENGTH = 28  # 4 weeks

def get_rotation_dates(rotation_index: int) -> tuple:
    """Get start and end dates for a rotation"""
    start = START_DATE + timedelta(days=rotation_index * ROTATION_LENGTH)
    end = start + timedelta(days=ROTATION_LENGTH - 1)
    return start, end

R2_STUDY_SCHEDULE = {
    "rotations": [
        {
            "id": "ir",
            "name": "Interventional Radiology",
            "abbreviation": "IR",
            "order": 1,
            "start_date": get_rotation_dates(0)[0],
            "end_date": get_rotation_dates(0)[1],
            "color": "#FF6B6B",
            "icon": "🩸",
            "description": "Master interventional procedures, vascular anatomy, and radiation safety",
            "weekly_schedule": {
                "Monday": {
                    "title": "Active Reading - IR Procedures",
                    "duration": "2 hours",
                    "topics": [
                        {
                            "week": 1,
                            "title": "Vascular Access & Angiography Basics",
                            "lessons": [
                                "Femoral artery access technique",
                                "Radial artery access",
                                "Angiographic contrast agents",
                                "Basic catheter and guidewire selection"
                            ],
                            "questions": [
                                {
                                    "question": "What is the most common complication of femoral artery catheterization?",
                                    "options": ["Bleeding", "Infection", "Thrombosis", "Dissection"],
                                    "correct": "Bleeding",
                                    "explanation": "Bleeding is the most common complication, occurring in 2-8% of cases."
                                },
                                {
                                    "question": "Which contrast agent property is most important for patient safety?",
                                    "options": ["Viscosity", "Osmolality", "Iodine concentration", "Cost"],
                                    "correct": "Osmolality",
                                    "explanation": "Low osmolality contrast agents reduce adverse reactions and patient discomfort."
                                }
                            ]
                        },
                        {
                            "week": 2,
                            "title": "Embolization Procedures",
                            "lessons": [
                                "GI bleeding embolization",
                                "Trauma embolization protocols",
                                "Embolic agents selection",
                                "Post-embolization syndrome"
                            ],
                            "questions": [
                                {
                                    "question": "Which embolic agent is preferred for acute GI bleeding?",
                                    "options": ["Coils", "Gelfoam", "PVA particles", "Glue"],
                                    "correct": "Gelfoam",
                                    "explanation": "Gelfoam provides temporary occlusion, allowing for potential recanalization."
                                }
                            ]
                        },
                        {
                            "week": 3,
                            "title": "Biliary Interventions",
                            "lessons": [
                                "PTC technique and indications",
                                "Biliary stent placement",
                                "Cholangioscopy basics",
                                "Complications management"
                            ],
                            "questions": [
                                {
                                    "question": "What is the most serious complication of PTC?",
                                    "options": ["Bleeding", "Sepsis", "Bile leak", "Pneumothorax"],
                                    "correct": "Sepsis",
                                    "explanation": "Sepsis can be life-threatening and requires immediate antibiotic treatment."
                                }
                            ]
                        },
                        {
                            "week": 4,
                            "title": "Genitourinary Interventions",
                            "lessons": [
                                "Nephrostomy tube placement",
                                "Ureteral stent insertion",
                                "Renal artery embolization",
                                "Varicocele embolization"
                            ],
                            "questions": [
                                {
                                    "question": "What is the target for nephrostomy tube placement?",
                                    "options": ["Upper pole", "Mid pole", "Lower pole", "Pelvis"],
                                    "correct": "Lower pole",
                                    "explanation": "Lower pole access minimizes risk of pleural injury and bleeding."
                                }
                            ]
                        }
                    ]
                },
                "Tuesday": {
                    "title": "Vascular Anatomy Focus",
                    "duration": "1.5 hours",
                    "topics": [
                        {
                            "week": 1,
                            "title": "Celiac and SMA Anatomy",
                            "lessons": [
                                "Celiac trunk branches",
                                "SMA territory and collaterals",
                                "Anatomic variants",
                                "Pancreaticoduodenal arcades"
                            ]
                        },
                        {
                            "week": 2,
                            "title": "Renal and Iliac Anatomy", 
                            "lessons": [
                                "Renal arterial anatomy",
                                "Iliac artery branches",
                                "Pelvic collateral circulation",
                                "Variant anatomy"
                            ]
                        }
                    ]
                }
                # Continue with other days...
            }
        },
        {
            "id": "us",
            "name": "Ultrasound",
            "abbreviation": "US", 
            "order": 2,
            "start_date": get_rotation_dates(1)[0],
            "end_date": get_rotation_dates(1)[1],
            "color": "#4ECDC4",
            "icon": "🔊",
            "description": "Master ultrasound physics, technique, and interpretation across all organ systems"
        },
        {
            "id": "research",
            "name": "Research",
            "abbreviation": "RESEARCH",
            "order": 3,
            "start_date": get_rotation_dates(2)[0], 
            "end_date": get_rotation_dates(2)[1],
            "color": "#45B7D1",
            "icon": "🔬",
            "description": "Focus on research methodology while maintaining clinical knowledge"
        },
        {
            "id": "msk1",
            "name": "Musculoskeletal",
            "abbreviation": "MSK",
            "order": 4,
            "start_date": get_rotation_dates(3)[0],
            "end_date": get_rotation_dates(3)[1], 
            "color": "#96CEB4",
            "icon": "🦴",
            "description": "Build foundation in MSK anatomy, pathology, and imaging protocols"
        },
        {
            "id": "thoracic",
            "name": "Thoracic",
            "abbreviation": "THORACIC",
            "order": 5,
            "start_date": get_rotation_dates(4)[0],
            "end_date": get_rotation_dates(4)[1],
            "color": "#FFEAA7",
            "icon": "🫁",
            "description": "Master chest imaging including lung nodules, ILD, and emergency presentations"
        },
        {
            "id": "nucs",
            "name": "Nuclear Medicine", 
            "abbreviation": "NUCS",
            "order": 6,
            "start_date": get_rotation_dates(5)[0],
            "end_date": get_rotation_dates(5)[1],
            "color": "#DDA0DD",
            "icon": "☢️",
            "description": "Learn nuclear medicine physics, radiopharmaceuticals, and interpretation"
        },
        {
            "id": "mammo",
            "name": "Mammography",
            "abbreviation": "MAMMO", 
            "order": 7,
            "start_date": get_rotation_dates(6)[0],
            "end_date": get_rotation_dates(6)[1],
            "color": "#FFB6C1",
            "icon": "🎗️",
            "description": "Achieve proficiency in mammographic interpretation and BI-RADS reporting"
        },
        {
            "id": "msk2", 
            "name": "Musculoskeletal Advanced",
            "abbreviation": "MSK",
            "order": 8,
            "start_date": get_rotation_dates(7)[0],
            "end_date": get_rotation_dates(7)[1],
            "color": "#98FB98",
            "icon": "🦴",
            "description": "Advanced MSK topics including tumors, interventions, and specialized techniques"
        },
        {
            "id": "neuro",
            "name": "Neuroradiology",
            "abbreviation": "NEURO",
            "order": 9,
            "start_date": get_rotation_dates(8)[0],
            "end_date": get_rotation_dates(8)[1],
            "color": "#F0E68C",
            "icon": "🧠", 
            "description": "Master neuroimaging including stroke, tumors, and advanced techniques"
        },
        {
            "id": "abd",
            "name": "Abdominal",
            "abbreviation": "ABD",
            "order": 10,
            "start_date": get_rotation_dates(9)[0],
            "end_date": get_rotation_dates(9)[1],
            "color": "#FFA07A",
            "icon": "🫄",
            "description": "Complete abdominal imaging competency and final CORE preparation"
        }
    ]
}

def get_current_rotation() -> Dict[str, Any]:
    """Get the current rotation based on today's date"""
    today = datetime.now().date()
    
    for rotation in R2_STUDY_SCHEDULE["rotations"]:
        start_date = rotation["start_date"].date()
        end_date = rotation["end_date"].date()
        
        if start_date <= today <= end_date:
            return rotation
    
    # If no current rotation found, return the first one
    return R2_STUDY_SCHEDULE["rotations"][0]

def get_current_week(rotation_id: str) -> int:
    """Get the current week (1-4) within a rotation"""
    today = datetime.now().date()
    
    for rotation in R2_STUDY_SCHEDULE["rotations"]:
        if rotation["id"] == rotation_id:
            start_date = rotation["start_date"].date()
            if today >= start_date:
                days_elapsed = (today - start_date).days
                week = min((days_elapsed // 7) + 1, 4)
                return week
    
    return 1

# Additional detailed schedule data for other rotations
DETAILED_SCHEDULES = {
    "us": {
        "weekly_schedule": {
            "Monday": {
                "title": "US Physics & Knobology",
                "topics": [
                    {
                        "week": 1,
                        "title": "Basic Physics & Transducers",
                        "lessons": [
                            "Sound wave properties",
                            "Transducer types and frequencies",
                            "Acoustic impedance",
                            "Attenuation and absorption"
                        ],
                        "questions": [
                            {
                                "question": "What frequency transducer is best for abdominal imaging?",
                                "options": ["2-5 MHz", "5-10 MHz", "10-15 MHz", "15-20 MHz"],
                                "correct": "2-5 MHz",
                                "explanation": "Lower frequencies penetrate deeper, making them ideal for abdominal imaging."
                            }
                        ]
                    }
                ]
            }
        }
    }
    # Add other rotations as needed
}