from pathlib import Path
import matplotlib

# Input/output directory

# INPUT_DIR = Path("/home/node0/Documents/csv_output")
INPUT_DIR = Path("/Users/anthonytsehuang/Documents/work_projects/eeo_pipeline/EEO-4_FILES/adjusted_tables")
OUTPUT_DIR = INPUT_DIR.parent / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"

# Color palette
RACE_COLORS = {
    'White':                     '#FF6361',
    'Hispanic or Latino':        '#58508d',
    'Black or African American': '#FFA600',
    'Asian':                     '#bc5090',
    'Two or More Races':         '#003F5C'}

SALARY_COLORS = {
    '$0.1 - 42.9':  '#388557',
    '$43.0 - 54.9': '#CD0D0D',
    '$55.0 - 69.9': '#14558F',
    '$70.0 PLUS':   '#F6C51B'}

FEMALE_COLOR = '#665191'
MALE_COLOR   = '#FF7C43'
BAR_EDGE_COLOR = '#888888'

# Display order for race, organizational size, and salary categories
RACE_ORDER_5 = ['White', 'Hispanic or Latino', 'Black or African American', 'Asian', 'Two or More Races']
PIE_ORDER = ['White', 'Two or More Races', 'Asian', 'Black or African American', 'Hispanic or Latino']
ORG_SIZE_ORDER = ['Very Large', 'Large', 'Medium', 'Small']
SALARY_ORDER = ['$0.1 - 42.9', '$43.0 - 54.9', '$55.0 - 69.9', '$70.0 PLUS']

# Text style for salary labels
SALARY_LABELS_K = {
    '$0.1 - 42.9':  r'≤$42.9k',
    '$43.0 - 54.9': r'\$43.0-\$54.9k',
    '$55.0 - 69.9': r'\$55.0-\$69.9k',
    '$70.0 PLUS':   r'\$70.0k+'}
SALARY_LABELS_K_TABLE = {
    '$0.1 - 42.9':  r'≤$42.9k',
    '$43.0 - 54.9': r'$43.0-$54.9k',
    '$55.0 - 69.9': r'$55.0-$69.9k',
    '$70.0 PLUS':   r'$70.0k+'}

def apply_style():
    # Font configuration.  Make sure to have the Montserrat font installed on your system.
    matplotlib.rcParams.update({
        'font.family':     'Montserrat',
        'text.color':      'black',
        'axes.labelcolor': 'black',
        'xtick.color':     'black',
        'ytick.color':     'black',
        'hatch.linewidth': 1.5,
        'patch.linewidth': 1.5,
    })

# Pattern hatching for better differentiation
# Currently unused, can be applied if needed.
GENDER_HATCHES = {
    'Female': '//',
    'Male':   '\\\\'}

RACE_HATCHES = {
    'White':                     None,
    'Hispanic or Latino':        'xx',
    'Black or African American': '..',
    'Asian':                     'O',
    'Two or More Races':         '\\\\'}

SALARY_HATCHES = {
    '$0.1 - 42.9':  '\\\\',
    '$43.0 - 54.9': '..',
    '$55.0 - 69.9': 'xx',
    '$70.0 PLUS':   None,
}
