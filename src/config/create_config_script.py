# Script to create the medical_config.py file
import os

# Ensure the config directory exists
os.makedirs("src/config", exist_ok=True)

# Create __init__.py
with open("src/config/__init__.py", "w") as f:
    f.write("# Configuration package\n")

# Create medical_config.py with all the configuration
config_content = '''"""
Complete medical-specific configuration for radiology study assistant
"""

# 1. MEDICAL-SPECIFIC MODEL CONFIGURATION
MEDICAL_MODELS = {
    'embedding_models': {
        'radiology_primary': {
            # RadBERT - Best for radiology
            'name': 'sentence-transformers/all-MiniLM-L6-v2',  # Fallback if RadBERT unavailable
            'radbert_alternative': 'zzxslp/RadBERT-RoBERTa-4m',  # Try this first
            'description': 'Radiology-specific BERT model trained on 4M reports'
        },
        'biomedical_backup': {
            'name': 'microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract',
            'description': 'PubMed biomedical literature trained'
        },
        'clinical_backup': {
            'name': 'emilyalsentzer/Bio_ClinicalBERT',
            'description': 'Clinical notes trained BERT'
        }
    },
    
    'llm_models': {
        'radiology_optimized': {
            'primary': 'llama3.1:8b',
            'high_performance': 'llama3.1:70b',
            'medical_focused': 'meditron:7b',  # If available
            'temperature': 0.1,  # Low for medical accuracy
            'system_prompt_style': 'radiology_expert'
        }
    }
}

# 2. CORE EXAM SPECIFIC CUSTOMIZATIONS
CORE_EXAM_CONFIG = {
    'exam_areas': {
        'physics': {
            'weight': 15,  # % of exam
            'topics': ['radiation physics', 'image formation', 'quality assurance', 'safety'],
            'prompt_style': 'physics_focused',
            'keywords': ['dose', 'attenuation', 'kvp', 'mas', 'contrast resolution']
        },
        'chest': {
            'weight': 20,
            'topics': ['pneumonia', 'nodules', 'masses', 'pneumothorax', 'pleural disease'],
            'prompt_style': 'case_based',
            'keywords': ['consolidation', 'ground glass', 'air bronchograms', 'silhouette sign']
        },
        'cardiac': {
            'weight': 10,
            'topics': ['coronary arteries', 'heart failure', 'valvular disease', 'congenital'],
            'prompt_style': 'anatomy_focused',
            'keywords': ['ejection fraction', 'wall motion', 'perfusion', 'stenosis']
        },
        'gastrointestinal': {
            'weight': 15,
            'topics': ['bowel obstruction', 'inflammatory', 'liver lesions', 'biliary'],
            'prompt_style': 'differential_focused',
            'keywords': ['enhancement patterns', 'transit time', 'wall thickening']
        },
        'neuroradiology': {
            'weight': 15,
            'topics': ['stroke', 'trauma', 'tumors', 'spine', 'pediatric'],
            'prompt_style': 'emergency_focused',
            'keywords': ['midline shift', 'hemorrhage', 'edema', 'mass effect']
        },
        'musculoskeletal': {
            'weight': 10,
            'topics': ['fractures', 'arthritis', 'tumors', 'infection', 'sports injuries'],
            'prompt_style': 'case_based',
            'keywords': ['cortical breach', 'marrow edema', 'joint effusion']
        },
        'genitourinary': {
            'weight': 8,
            'topics': ['renal masses', 'stones', 'infection', 'bladder', 'prostate'],
            'prompt_style': 'protocol_focused',
            'keywords': ['enhancement washout', 'hydronephrosis', 'calculi']
        },
        'interventional': {
            'weight': 7,
            'topics': ['vascular access', 'embolization', 'drainage', 'biopsy'],
            'prompt_style': 'procedural',
            'keywords': ['catheter placement', 'coil embolization', 'complications']
        }
    }
}

# 3. MEDICAL TERMINOLOGY AND KEYWORDS
RADIOLOGY_KEYWORDS = {
    'imaging_modalities': [
        'ct scan', 'computed tomography', 'mri', 'magnetic resonance',
        'ultrasound', 'x-ray', 'radiograph', 'fluoroscopy', 'mammography',
        'nuclear medicine', 'pet scan', 'spect', 'angiography'
    ],
    
    'imaging_findings': [
        'consolidation', 'ground glass opacity', 'nodule', 'mass', 'lesion',
        'enhancement', 'attenuation', 'signal intensity', 'echogenicity',
        'calcification', 'hemorrhage', 'edema', 'ischemia', 'infarction'
    ],
    
    'anatomy_systems': [
        'cardiovascular', 'respiratory', 'gastrointestinal', 'genitourinary',
        'musculoskeletal', 'neurological', 'hepatobiliary', 'endocrine'
    ],
    
    'pathology_terms': [
        'malignancy', 'benign', 'metastasis', 'inflammation', 'infection',
        'ischemia', 'hemorrhage', 'thrombosis', 'embolism', 'stenosis'
    ],
    
    'core_exam_buzzwords': [
        'differential diagnosis', 'first-line imaging', 'contraindication',
        'radiation dose', 'contrast reaction', 'patient safety',
        'bi-rads', 'lung-rads', 'pi-rads', 'ti-rads', 'acr appropriateness'
    ]
}

# 4. RESPONSE TEMPLATES
RESPONSE_TEMPLATES = {
    'case_study_analysis': """
    **Clinical Scenario Analysis**
    
    **Key Imaging Findings:**
    {findings}
    
    **Differential Diagnosis (ranked):**
    {differentials}
    
    **Most Likely Diagnosis:**
    {primary_diagnosis}
    
    **Next Steps/Recommendations:**
    {recommendations}
    
    **CORE Exam Teaching Points:**
    {teaching_points}
    
    **Relevant ACR Guidelines:**
    {acr_guidelines}
    """,
    
    'physics_explanation': """
    **Physics Principle**
    {principle}
    
    **Clinical Application**
    {application}
    
    **Mathematical Relationships**
    {formulas}
    
    **Safety Considerations**
    {safety}
    
    **Quality Control**
    {qc_points}
    
    **CORE Exam Focus**
    {exam_relevance}
    """,
    
    'differential_diagnosis': """
    **Primary Differential Considerations:**
    
    1. **{diagnosis_1}**
       - Supporting features: {features_1}
       - Distinguishing characteristics: {distinguishing_1}
    
    2. **{diagnosis_2}**
       - Supporting features: {features_2}
       - Distinguishing characteristics: {distinguishing_2}
    
    3. **{diagnosis_3}**
       - Supporting features: {features_3}
       - Distinguishing characteristics: {distinguishing_3}
    
    **Key Differentiating Features:**
    {key_differentiators}
    """,
    
    'protocol_review': """
    **Imaging Protocol: {modality}**
    
    **Indications:**
    {indications}
    
    **Patient Preparation:**
    {preparation}
    
    **Technical Parameters:**
    {parameters}
    
    **Contrast Considerations:**
    {contrast}
    
    **Safety Checklist:**
    {safety_checklist}
    
    **Expected Findings:**
    {expected_findings}
    """
}

# 5. UI THEME (RADSREVIEW.NET INSPIRED)
UI_THEME_CONFIG = {
    'color_scheme': {
        'primary': '#1e40af',        # Medical blue
        'secondary': '#059669',      # Success green  
        'accent': '#dc2626',         # Alert red
        'background': '#f8fafc',     # Light gray
        'surface': '#ffffff',        # White
        'text_primary': '#1f2937',   # Dark gray
        'text_secondary': '#6b7280'  # Medium gray
    },
    
    'layout': {
        'sidebar_style': 'collapsible',
        'content_width': 'max-width-6xl',
        'card_design': 'elevated_shadow',
        'button_style': 'rounded_professional'
    },
    
    'typography': {
        'heading_font': 'Inter',
        'body_font': 'system-ui',
        'code_font': 'SF Mono',
        'medical_terms': 'bold_highlight'
    },
    
    'components': {
        'progress_bars': 'animated',
        'notifications': 'toast_style',
        'modals': 'centered_overlay',
        'tables': 'striped_hover'
    }
}

# 6. ADVANCED FEATURES CONFIG
ADVANCED_FEATURES = {
    'spaced_repetition': {
        'intervals': {
            'poor_performance': 1,      # Review next day
            'fair_performance': 3,      # Review in 3 days  
            'good_performance': 7,      # Review in 1 week
            'excellent_performance': 14  # Review in 2 weeks
        },
        'performance_tracking': True,
        'adaptive_scheduling': True
    },
    
    'question_generation': {
        'enabled': True,
        'types': ['multiple_choice', 'case_based', 'image_interpretation'],
        'difficulty_adaptation': True,
        'core_exam_style': True
    },
    
    'progress_tracking': {
        'session_analytics': True,
        'weak_area_identification': True,
        'study_recommendations': True,
        'exam_readiness_assessment': True
    },
    
    'multimodal_support': {
        'image_analysis': False,  # Enable when vision model added
        'dicom_support': False,   # Future feature
        'annotation_tools': False  # Future feature
    }
}
'''

with open("src/config/medical_config.py", "w", encoding="utf-8") as f:
    f.write(config_content)

print("✅ Created src/config/medical_config.py successfully!")
print("✅ Created src/config/__init__.py successfully!")
print("\nYou can now run: streamlit run src/ui/radiology_streamlit_app.py")
