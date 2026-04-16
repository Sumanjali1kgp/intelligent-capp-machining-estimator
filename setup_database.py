import os
import sqlite3
from datetime import datetime
from extensions import db
from models.job_models import Job, Part, PartOperation, OperationMaster
from models.material import Material
from models.machining_parameter import MachiningParameter
import logging

logger = logging.getLogger(__name__)


REFERENCE_TABLES = [
    'Materials',
    'Features',
    'Operations',
    'FeatureOperations',
    'MachiningParameters',
]


def _reference_data_present(cursor):
    existing_tables = {
        row[0]
        for row in cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }

    if not all(table in existing_tables for table in REFERENCE_TABLES):
        return False

    material_count = cursor.execute('SELECT COUNT(*) FROM Materials').fetchone()[0]
    operation_count = cursor.execute('SELECT COUNT(*) FROM Operations').fetchone()[0]
    feature_count = cursor.execute('SELECT COUNT(*) FROM Features').fetchone()[0]
    return all(count > 0 for count in (material_count, operation_count, feature_count))




def create_database(force_reset=False):
    os.makedirs('instance', exist_ok=True)
    # Create database file
    conn = sqlite3.connect('instance/machining.db')
    cursor = conn.cursor()

    if not force_reset and _reference_data_present(cursor):
        logger.info("Reference tables already initialized; skipping seed reset.")
        conn.close()
        return
    
    # Drop existing tables if they exist
    cursor.executescript('''
        DROP TABLE IF EXISTS FeatureOperations;
        DROP TABLE IF EXISTS Features;
        DROP TABLE IF EXISTS MachiningParameters;
        DROP TABLE IF EXISTS Operations;
        DROP TABLE IF EXISTS Materials;
        DROP TABLE IF EXISTS operation_extra_times;
        DROP TABLE IF EXISTS setup_time_table;
        DROP TABLE IF EXISTS material_costs;
        DROP TABLE IF EXISTS cost_rates;    
    ''')
    logger.info("✅ Dropped existing tables")
    
    # Create tables
    cursor.executescript('''
        CREATE TABLE Materials (
            material_id INTEGER PRIMARY KEY,
            material_name VARCHAR(100) NOT NULL,
            material_grade VARCHAR(50),
            material_type VARCHAR(50),
            hardness FLOAT,
            density FLOAT,
            cost_per_kg FLOAT,
            machinability_rating FLOAT,
            recommended_tool VARCHAR(100),
            notes TEXT
        );


        CREATE TABLE Features (
            feature_id INTEGER PRIMARY KEY,
            feature_name VARCHAR(100) NOT NULL,
            description TEXT
        );

        CREATE TABLE Operations (
            operation_id INTEGER PRIMARY KEY,
            operation_name VARCHAR(100) NOT NULL,
            description TEXT
        );

        CREATE TABLE FeatureOperations (
            feature_id INTEGER,
            operation_id INTEGER,
            PRIMARY KEY (feature_id, operation_id),
            FOREIGN KEY (feature_id) REFERENCES Features(feature_id),
            FOREIGN KEY (operation_id) REFERENCES Operations(operation_id)
        );

        CREATE TABLE MachiningParameters (
            param_id INTEGER PRIMARY KEY AUTOINCREMENT,
            material_id INTEGER,
            operation_id INTEGER,
            spindle_speed_min INTEGER,
            spindle_speed_max INTEGER,
            feed_rate_min FLOAT,
            feed_rate_max FLOAT,
            depth_of_cut_min FLOAT,
            depth_of_cut_max FLOAT,
            notes TEXT,
            FOREIGN KEY (material_id) REFERENCES Materials(material_id),
            FOREIGN KEY (operation_id) REFERENCES Operations(operation_id)
        );

     
        
        CREATE TABLE material_costs (
            material_id INTEGER PRIMARY KEY,
            rate_per_kg REAL NOT NULL DEFAULT 0.0,
            density_kg_mm3 REAL NOT NULL DEFAULT 0.0,
            FOREIGN KEY (material_id) REFERENCES Materials(material_id) ON DELETE CASCADE
        );
        CREATE TABLE cost_rates (
            id INTEGER PRIMARY KEY,
            labor_rate_per_hr REAL NOT NULL DEFAULT 0.0,
            overhead_factor REAL NOT NULL DEFAULT 1.4
        );


    ''')
    
    # Insert operations
    operations = [
        (1, 'Facing', 'Machining the end surface of a job'),
        (2, 'Turning', 'Machining cylindrical surface'),
        (3, 'Taper Turning', 'Producing taper on cylindrical jobs'),
        (4, 'Contouring', 'Machining complex profiles'),
        (5, 'Drilling', 'Making a hole with a drill bit'),
        (6, 'Boring', 'Enlarging and finishing drilled holes'),
        (7, 'Reaming', 'Improving hole accuracy and finish'),
        (8, 'Threading', 'Cutting screw threads'),
        (9, 'Grooving', 'Making a narrow groove on OD/ID'),
        (10, 'Knurling', 'Producing a textured surface'),
        (11, 'Chamfering', 'Creating a beveled edge'),
        (12, 'Parting', 'Cutting off a section of workpiece')
    ]
    
    cursor.executemany('INSERT INTO Operations (operation_id, operation_name, description) VALUES (?, ?, ?)', operations)
    
    # Insert features
    features = [
        (1, 'Finished Face', 'Machined flat end surface of workpiece'),
        (2, 'Cylindrical Section', 'Basic turning to achieve cylindrical geometry'),
        (3, 'External Step / Shoulder', 'Stepped shaft with reduced diameters'),
        (4, 'Knurl Pattern', 'Textured grip surface'),
        (5, 'Through / Blind Hole', 'Drilled hole (through or blind)'),
        (6, 'Counterbore', 'Flat-bottomed enlarged hole'),
        (7, 'Countersink', 'Conical enlarged hole'),
        (8, 'Chamfer / Beveled Edge', 'Beveled or angled edge'),
        (9, 'Rounded Corner (Fillet)', 'External or internal radius edge'),
        (10, 'Groove / O-Ring Groove', 'Narrow groove on OD/ID'),
        (11, 'Undercut / Relief Groove', 'Relief groove for clearance'),
        (12, 'Threads (External)', 'Screw thread on OD'),
        (13, 'Threads (Internal)', 'Screw thread on ID'),
        (14, 'Taper / Conical Section', 'Straight taper geometry'),
        (15, 'Concave Profile', 'Inward curved contour'),
        (16, 'Convex Profile', 'Outward curved contour'),
        (17, 'Complex Contour', 'Freeform contour turning'),
        (18, 'Component Severance', 'Cutting off the workpiece')
    ]
    
    cursor.executemany('INSERT INTO Features (feature_id, feature_name, description) VALUES (?, ?, ?)', features)
    
    # Insert feature-operation mappings
    feature_operations = [
        # Finished Face → Facing
        (1, 1),
        # Cylindrical Section → Turning
        (2, 2),
        # External Step / Shoulder → Turning, Facing
        (3, 2), (3, 1),
        # Knurl Pattern → Knurling
        (4, 10),
        # Through/Blind Hole → Drilling, Boring, Reaming
        (5, 5), (5, 6), (5, 7),
        # Counterbore → Drilling, Boring
        (6, 5), (6, 6),
        # Countersink → Drilling
        (7, 5),
        # Chamfer / Beveled Edge → Chamfering, Facing
        (8, 11), (8, 1),
        # Rounded Corner (Fillet) → Turning
        (9, 2),
        # Groove / O-Ring Groove → Grooving
        (10, 9),
        # Undercut / Relief Groove → Grooving
        (11, 9),
        # Threads (External) → Threading
        (12, 8),
        # Threads (Internal) → Drilling, Threading
        (13, 5), (13, 8),
        # Taper / Conical Section → Taper Turning
        (14, 3),
        # Concave Profile → Contouring
        (15, 4),
        # Convex Profile → Contouring
        (16, 4),
        # Complex Contour → Contouring
        (17, 4),
        # Component Severance → Parting
        (18, 12)
    ]
    
    cursor.executemany('INSERT INTO FeatureOperations (feature_id, operation_id) VALUES (?, ?)', feature_operations)
    
    cursor.executemany('''
    INSERT INTO Materials (
        material_id, material_name, material_grade, material_type, hardness,
        density, cost_per_kg, machinability_rating, recommended_tool, notes
    ) 
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
''', [
    (1, 'Aluminum', '6061', 'Metal', 95, 2.7, 300, 0.9, 'HSS', 'Soft material, high machinability'),
    (2, 'Brass', 'C360', 'Metal', 100, 8.5, 450, 0.8, 'HSS', 'Excellent machinability, self-lubricating'),
    (3, 'Copper', 'C110', 'Metal', 80, 8.96, 600, 0.6, 'HSS', 'Good machinability, good thermal conductivity'),
    (4, 'Stainless Steel', '304', 'Metal', 200, 7.9, 500, 0.5, 'Solid Carbide', 'Difficult to machine, requires carbide tools'),
    (5, 'Mild Steel', 'A36', 'Metal', 120, 7.85, 350, 0.7, 'HSS', 'Good machinability, suitable for general machining'),
    (6, 'Nylon', 'PA6', 'Plastic', 30, 1.15, 150, 0.85, 'HSS', 'Soft thermoplastic, requires sharp tool and cooling'),
    (7, 'Acrylic', 'PMMA', 'Plastic', 25, 1.18, 200, 0.75, 'HSS', 'Brittle plastic, risk of cracking, needs high rake angle'),
    (8, 'Teflon', 'PTFE', 'Plastic', 20, 2.2, 600, 0.65, 'HSS', 'Low friction, soft but tends to deform under cutting')
])

    # Insert machining parameters - All set for Aluminum (material_id: 1)
    parameters = [
        # Facing
        
 
        # ------------------- ALUMINUM (material_id = 1) -------------------
        # Facing (1)
        (1, 1, 170, 285, 0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 1, 285, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Turning (2)
        (1, 2, 170, 285, 0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 2, 285, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Taper Turning (3)
        (1, 3, 170, 285, 0.12, 0.16, 0.8, 1.8, 'Rough cut'),
        (1, 3, 285, 480, 0.08, 0.12, 0.05, 0.5, 'Finish cut'),

        # Contouring (4)
        (1, 4, 170, 285, 0.12, 0.16, 0.5, 1.5, 'Rough cut'),
        (1, 4, 285, 480, 0.08, 0.12, 0.05, 0.5, 'Finish cut'),

        # Drilling (5)
        (1, 5, 100, 100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (1, 5, 100, 100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Boring (6)
        (1, 6, 170, 285, 0.14, 0.18, 0.5, 1.5, 'Rough cut'),
        (1, 6, 285, 480, 0.10, 0.14, 0.05, 0.3, 'Finish cut'),

        # Reaming (7)
        (1, 7, 100, 170, 0.12, 0.16, 0.2, 0.6, 'Rough cut'),
        (1, 7, 170, 285, 0.08, 0.12, 0.05, 0.2, 'Finish cut'),

        # Threading (8)
        (1, 8, 60, 60, 0.16, 0.18, 0.5, 2, 'Rough cut'),
        (1, 8, 60, 60, 0.14, 0.12, 0.05, 0.5, 'Finish cut'),

        # Grooving (9)
        (1, 9, 170, 285, 0.08, 0.14, 0.5, 2, 'Rough cut'),
        (1, 9, 285, 480, 0.06, 0.10, 0.05, 0.5, 'Finish cut'),

        # Knurling (10)
        (1, 10, 100, 170, 0.12, 0.16, 0.5, 1.5, 'Rough cut'),
        (1, 10, 170, 220, 0.08, 0.12, 0.1, 0.4, 'Finish cut'),

        # Chamfering (11)
        (1, 11, 170, 285, 0.10, 0.14, 0.3, 1.0, 'Rough cut'),
        (1, 11, 285, 480, 0.06, 0.10, 0.05, 0.3, 'Finish cut'),

        # Parting (12)
        (1, 12, 170, 285, 0.12, 0.18, 0.8, 2, 'Rough cut'),
        (1, 12, 285, 480, 0.08, 0.12, 0.05, 0.8, 'Finish cut'),


        # ------------------- BRASS (material_id = 2) -------------------
        # Facing (1)
        (2, 1, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 1, 285, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Turning (2)
        (2, 2, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 2, 285, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Taper Turning (3)
        (2, 3, 170, 285, 0.12, 0.16, 0.8, 1.8, 'Rough cut'),
        (2, 3, 285, 480, 0.08, 0.12, 0.05, 0.5, 'Finish cut'),

        # Contouring (4)
        (2, 4, 170, 285, 0.12, 0.16, 0.5, 1.5, 'Rough cut'),
        (2, 4, 285, 480, 0.08, 0.12, 0.05, 0.5, 'Finish cut'),

        # Drilling (5)
        (2, 5, 100, 100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (2, 5, 100, 100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Boring (6)
        (2, 6, 170, 480, 0.14, 0.18, 0.5, 1.5, 'Rough cut'),
        (2, 6, 285, 480, 0.10, 0.14, 0.05, 0.3, 'Finish cut'),

        # Reaming (7)
        (2, 7, 100, 170, 0.12, 0.16, 0.2, 0.6, 'Rough cut'),
        (2, 7, 170, 285, 0.08, 0.12, 0.05, 0.2, 'Finish cut'),

        # Threading (8)
        (2, 8, 60, 60, 0.16, 0.18, 0.5, 2, 'Rough cut'),
        (2, 8, 60, 60, 0.14, 0.12, 0.05, 0.5, 'Finish cut'),

        # Grooving (9)
        (2, 9, 100, 285, 0.08, 0.14, 0.5, 2, 'Rough cut'),
        (2, 9, 285, 480, 0.06, 0.10, 0.05, 0.5, 'Finish cut'),

        # Knurling (10)
        (2, 10, 100, 100, 0.12, 0.16, 0.5, 1.5, 'Rough cut'),
        (2, 10, 120, 160, 0.08, 0.12, 0.1, 0.4, 'Finish cut'),

        # Chamfering (11)
        (2, 11, 170, 285, 0.10, 0.14, 0.3, 1.0, 'Rough cut'),
        (2, 11, 285, 480, 0.06, 0.10, 0.05, 0.3, 'Finish cut'),

        # Parting (12)
        (2, 12, 100, 285, 0.12, 0.18, 0.8, 2, 'Rough cut'),
        (2, 12, 285, 480, 0.08, 0.12, 0.05, 0.8, 'Finish cut'),


        # ------------------- COPPER (material_id = 3) -------------------
        # Facing (1)
        (3, 1, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 1, 285, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Turning (2)
        (3, 2, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 2, 285, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Taper Turning (3)
        (3, 3, 170, 285, 0.12, 0.16, 0.8, 1.8, 'Rough cut'),
        (3, 3, 285, 480, 0.08, 0.12, 0.05, 0.5, 'Finish cut'),

        # Contouring (4)
        (3, 4, 170, 285, 0.12, 0.16, 0.5, 1.5, 'Rough cut'),
        (3, 4, 285, 480, 0.08, 0.12, 0.05, 0.5, 'Finish cut'),

        # Drilling (5)
        (3, 5, 100, 100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (3, 5, 100, 100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Boring (6)
        (3, 6, 170, 480, 0.14, 0.18, 0.5, 1.5, 'Rough cut'),
        (3, 6, 285, 480, 0.10, 0.14, 0.05, 0.3, 'Finish cut'),

        # Reaming (7)
        (3, 7, 100, 170, 0.12, 0.16, 0.2, 0.6, 'Rough cut'),
        (3, 7, 170, 285, 0.08, 0.12, 0.05, 0.2, 'Finish cut'),

        # Threading (8)
        (3, 8, 60, 60, 0.16, 0.18, 0.5, 2, 'Rough cut'),
        (3, 8, 60, 60, 0.14, 0.12, 0.05, 0.5, 'Finish cut'),

        # Grooving (9)
        (3, 9, 100, 285, 0.08, 0.14, 0.5, 2, 'Rough cut'),
        (3, 9, 285, 480, 0.06, 0.10, 0.05, 0.5, 'Finish cut'),

        # Knurling (10)
        (3, 10, 100, 100, 0.12, 0.16, 0.5, 1.5, 'Rough cut'),
        (3, 10, 120, 160, 0.08, 0.12, 0.1, 0.4, 'Finish cut'),

        # Chamfering (11)
        (3, 11, 170, 285, 0.10, 0.14, 0.3, 1.0, 'Rough cut'),
        (3, 11, 285, 480, 0.06, 0.10, 0.05, 0.3, 'Finish cut'),

        # Parting (12)
        (3, 12, 100, 285, 0.12, 0.18, 0.8, 2, 'Rough cut'),
        (3, 12, 285, 480, 0.08, 0.12, 0.05, 0.8, 'Finish cut'),


        # ------------------- STAINLESS STEEL (material_id = 4) -------------------
        # Facing (1)
        (4, 1, 170, 285, 0.14, 0.16, 0.8, 1.8, 'Rough cut'),
        (4, 1, 285, 480, 0.10, 0.12, 0.05, 0.2, 'Finish cut'),

        # Turning (2)
        (4, 2, 170, 285, 0.14, 0.16, 0.8, 1.8, 'Rough cut'),
        (4, 2, 285, 480, 0.10, 0.12, 0.05, 0.2, 'Finish cut'),

        # Taper Turning (3)
        (4, 3, 170, 285, 0.10, 0.14, 0.5, 1.2, 'Rough cut'),
        (4, 3, 285, 480, 0.06, 0.10, 0.05, 0.2, 'Finish cut'),

        # Contouring (4)
        (4, 4, 170, 285, 0.10, 0.14, 0.4, 1.2, 'Rough cut'),
        (4, 4, 285, 480, 0.06, 0.10, 0.05, 0.2, 'Finish cut'),

        # Drilling (5)
        (4, 5, 100, 100, 0.12, 0.16, 0.5, 1.5, 'Rough cut'),
        (4, 5, 100, 100, 0.08, 0.12, 0.05, 0.3, 'Finish cut'),

        # Boring (6)
        (4, 6, 170, 285, 0.10, 0.14, 0.4, 1.2, 'Rough cut'),
        (4, 6, 285, 480, 0.06, 0.10, 0.05, 0.3, 'Finish cut'),

        # Reaming (7)
        (4, 7, 100, 170, 0.10, 0.14, 0.2, 0.5, 'Rough cut'),
        (4, 7, 170, 285, 0.06, 0.10, 0.05, 0.2, 'Finish cut'),

        # Threading (8)
        (4, 8, 60, 60, 0.10, 0.14, 0.5, 1.5, 'Rough cut'),
        (4, 8, 60, 60, 0.06, 0.10, 0.05, 0.5, 'Finish cut'),

        # Grooving (9)
        (4, 9, 170, 285, 0.06, 0.10, 0.3, 1.0, 'Rough cut'),
        (4, 9, 285, 480, 0.04, 0.08, 0.05, 0.3, 'Finish cut'),

        # Knurling (10)
        (4, 10, 100, 170, 0.10, 0.14, 0.4, 1.2, 'Rough cut'),
        (4, 10, 120, 160, 0.06, 0.10, 0.1, 0.3, 'Finish cut'),

        # Chamfering (11)
        (4, 11, 170, 285, 0.08, 0.12, 0.2, 0.8, 'Rough cut'),
        (4, 11, 285, 480, 0.04, 0.08, 0.05, 0.2, 'Finish cut'),

        # Parting (12)
        (4, 12, 170, 285, 0.08, 0.12, 0.6, 1.6, 'Rough cut'),
        (4, 12, 285, 480, 0.05, 0.09, 0.05, 0.6, 'Finish cut'),


        # ------------------- MILD STEEL (material_id = 5) -------------------
        # Facing (1)
        (5, 1, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 1, 285, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Turning (2)
        (5, 2, 170, 480, 0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 2, 285, 480, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Taper Turning (3)
        (5, 3, 170, 285, 0.12, 0.16, 0.8, 1.8, 'Rough cut'),
        (5, 3, 285, 480, 0.08, 0.12, 0.05, 0.5, 'Finish cut'),

        # Contouring (4)
        (5, 4, 170, 285, 0.12, 0.16, 0.5, 1.5, 'Rough cut'),
        (5, 4, 285, 480, 0.08, 0.12, 0.05, 0.5, 'Finish cut'),

        # Drilling (5)
        (5, 5, 100, 100, 0.16, 0.18, 1, 2, 'Rough cut'),
        (5, 5, 100, 100, 0.14, 0.12, 0.05, 0.1, 'Finish cut'),

        # Boring (6)
        (5, 6, 170, 480, 0.14, 0.18, 0.5, 1.5, 'Rough cut'),
        (5, 6, 285, 480, 0.10, 0.14, 0.05, 0.3, 'Finish cut'),

        # Reaming (7)
        (5, 7, 100, 170, 0.12, 0.16, 0.2, 0.6, 'Rough cut'),
        (5, 7, 170, 285, 0.08, 0.12, 0.05, 0.2, 'Finish cut'),

        # Threading (8)
        (5, 8, 60, 60, 0.16, 0.18, 0.5, 2, 'Rough cut'),
        (5, 8, 60, 60, 0.14, 0.12, 0.05, 0.5, 'Finish cut'),

        # Grooving (9)
        (5, 9, 100, 285, 0.08, 0.14, 0.5, 2, 'Rough cut'),
        (5, 9, 285, 480, 0.06, 0.10, 0.05, 0.5, 'Finish cut'),

        # Knurling (10)
        (5, 10, 100, 170, 0.12, 0.16, 0.5, 1.5, 'Rough cut'),
        (5, 10, 120, 180, 0.08, 0.12, 0.1, 0.4, 'Finish cut'),

        # Chamfering (11)
        (5, 11, 170, 285, 0.10, 0.14, 0.3, 1.0, 'Rough cut'),
        (5, 11, 285, 480, 0.06, 0.10, 0.05, 0.3, 'Finish cut'),

        # Parting (12)
        (5, 12, 170, 285, 0.12, 0.18, 0.8, 2, 'Rough cut'),
        (5, 12, 285, 480, 0.08, 0.12, 0.05, 0.8, 'Finish cut'),


        # ------------------- NYLON (PA6) (material_id = 6) -------------------
        # (plastics: skip knurling)
        # Facing (1)
        (6, 1, 285, 480, 0.20, 0.25, 1.0, 1.5, 'Rough cut'),
        (6, 1, 480, 480, 0.10, 0.15, 0.3, 0.6, 'Finish cut'),

        # Turning (2)
        (6, 2, 285, 480, 0.20, 0.25, 1.0, 1.5, 'Rough cut'),
        (6, 2, 480, 480, 0.10, 0.15, 0.3, 0.6, 'Finish cut'),

        # Taper Turning (3)
        (6, 3, 285, 480, 0.18, 0.22, 0.8, 1.2, 'Rough cut'),
        (6, 3, 480, 480, 0.10, 0.15, 0.2, 0.5, 'Finish cut'),

        # Contouring (4)
        (6, 4, 285, 480, 0.16, 0.20, 0.6, 1.2, 'Rough cut'),

        # Drilling (5)
        (6, 5, 100, 100, 0.18, 0.22, 0.8, 1.5, 'Rough cut'),
        (6, 5, 100, 100, 0.10, 0.14, 0.05, 0.3, 'Finish cut'),

        # Boring (6)
        (6, 6, 285, 480, 0.14, 0.18, 0.4, 1.0, 'Rough cut'),

        # Reaming (7)
        (6, 7, 100, 170, 0.12, 0.16, 0.15, 0.4, 'Rough cut'),

        # Threading (8)
        (6, 8, 60, 60, 0.10, 0.14, 0.3, 1.0, 'Rough cut'),

        # Grooving (9)
        (6, 9, 285, 480, 0.08, 0.12, 0.4, 1.0, 'Rough cut'),

        # Chamfering (11)
        (6, 11, 285, 480, 0.08, 0.12, 0.1, 0.4, 'Rough cut'),

        # Parting (12)
        (6, 12, 285, 480, 0.08, 0.14, 0.4, 1.0, 'Rough cut'),


        # ------------------- ACRYLIC (PMMA) (material_id = 7) -------------------
        # Facing (1)
        (7, 1, 170, 285, 0.12, 0.18, 0.8, 1.5, 'Rough cut'),
        (7, 1, 285, 480, 0.08, 0.12, 0.2, 0.5, 'Finish cut'),

        # Turning (2)
        (7, 2, 170, 285, 0.12, 0.18, 0.8, 1.5, 'Rough cut'),
        (7, 2, 285, 480, 0.08, 0.12, 0.2, 0.5, 'Finish cut'),

        # Taper Turning (3)
        (7, 3, 170, 285, 0.10, 0.14, 0.6, 1.2, 'Rough cut'),
        (7, 3, 285, 480, 0.06, 0.10, 0.15, 0.4, 'Finish cut'),

        # Contouring (4)
        (7, 4, 170, 285, 0.10, 0.14, 0.5, 1.0, 'Rough cut'),

        # Drilling (5)
        (7, 5, 100, 100, 0.12, 0.18, 0.6, 1.2, 'Rough cut'),
        (7, 5, 100, 100, 0.06, 0.10, 0.05, 0.2, 'Finish cut'),

        # Boring (6)
        (7, 6, 170, 285, 0.10, 0.14, 0.3, 0.8, 'Rough cut'),

        # Reaming (7)
        (7, 7, 100, 170, 0.08, 0.12, 0.12, 0.35, 'Rough cut'),

        # Threading (8)
        (7, 8, 60, 60, 0.08, 0.12, 0.2, 0.8, 'Rough cut'),

        # Grooving (9)
        (7, 9, 170, 285, 0.06, 0.10, 0.3, 0.8, 'Rough cut'),

        # Chamfering (11)
        (7, 11, 170, 285, 0.06, 0.10, 0.08, 0.3, 'Rough cut'),

        # Parting (12)
        (7, 12, 170, 285, 0.06, 0.12, 0.3, 0.8, 'Rough cut'),


        # ------------------- TEFLON (PTFE) (material_id = 8) -------------------
        # Facing (1)
        (8, 1, 285, 480, 0.10, 0.16, 0.5, 1.0, 'Rough cut'),
        (8, 1, 480, 480, 0.05, 0.10, 0.1, 0.3, 'Finish cut'),

        # Turning (2)
        (8, 2, 285, 480, 0.10, 0.16, 0.5, 1.0, 'Rough cut'),
        (8, 2, 480, 480, 0.05, 0.10, 0.1, 0.3, 'Finish cut'),

        # Taper Turning (3)
        (8, 3, 285, 480, 0.09, 0.14, 0.4, 0.9, 'Rough cut'),
        (8, 3, 480, 480, 0.05, 0.09, 0.08, 0.25, 'Finish cut'),

        # Contouring (4)
        (8, 4, 285, 480, 0.08, 0.12, 0.4, 0.8, 'Rough cut'),

        # Drilling (5)
        (8, 5, 100, 100, 0.10, 0.16, 0.5, 1.0, 'Rough cut'),
        (8, 5, 100, 100, 0.05, 0.09, 0.05, 0.2, 'Finish cut'),

        # Boring (6)
        (8, 6, 285, 480, 0.08, 0.12, 0.3, 0.8, 'Rough cut'),

        # Reaming (7)
        (8, 7, 100, 170, 0.06, 0.10, 0.1, 0.3, 'Rough cut'),

        # Threading (8)
        (8, 8, 60, 60, 0.06, 0.10, 0.15, 0.6, 'Rough cut'),

        # Grooving (9)
        (8, 9, 285, 480, 0.05, 0.10, 0.2, 0.6, 'Rough cut'),

        # Chamfering (11)
        (8, 11, 285, 480, 0.05, 0.10, 0.05, 0.2, 'Rough cut'),

        # Parting (12)
        (8, 12, 285, 480, 0.05, 0.10, 0.2, 0.6, 'Rough cut'),
    ]
  
      
    

    
    cursor.executemany('''
        INSERT INTO MachiningParameters 
        (material_id, operation_id, spindle_speed_min, spindle_speed_max, 
         feed_rate_min, feed_rate_max, depth_of_cut_min, depth_of_cut_max, notes) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', parameters)

    
    cursor.execute('''
        INSERT INTO cost_rates (id, labor_rate_per_hr, overhead_factor) 
        VALUES (1, 500.0, 1.4)
    ''')

    # Create indexes
    cursor.executescript('''
        CREATE INDEX idx_machining_params ON MachiningParameters(material_id, operation_id, notes);
        CREATE INDEX idx_materials_name ON Materials(material_name);
        CREATE INDEX idx_operations_name ON Operations(operation_name);
    ''')
    conn.commit()
    logger.info("Database setup completed successfully!")
    conn.close()

# ✅ Add this new function (correctly indented)
def initialize_database(force_reset=False):
    """Initialize the machining database (used by app.py)."""
    logger.info("Initializing database from setup_database.py ...")
    create_database(force_reset=force_reset)
    logger.info("✅ Database created successfully via initialize_database()!")


if __name__ == '__main__':
    # Create instance directory if it doesn't exist
    os.makedirs('instance', exist_ok=True)
    
    # Initialize the database with logging
    logger.info("Starting database initialization...")
    initialize_database(force_reset=True)
    logger.info("Database setup completed successfully via __main__!")
