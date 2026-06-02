from pathlib import Path
import matplotlib

# Input/output directory

INPUT_DIR = Path("/home/node0/Documents/csv_output")
OUTPUT_DIR = INPUT_DIR.parent / "figures"
TABLE_DIR = OUTPUT_DIR / "tables"

# Color palette
RACE_COLORS = {
    'White':                     '#FF6361',
    'Hispanic or Latino':        '#58508d',
    'Black or African American': '#FFA600',
    'Asian':                     '#bc5090',
    'Two or More Races':         '#003F5C'}

FEMALE_COLOR = '#665191'
MALE_COLOR   = '#FF7C43'
BAR_EDGE_COLOR = '#888888'

# Display order for race and organizational size categories
RACE_ORDER_5 = ['White', 'Hispanic or Latino', 'Black or African American', 'Asian', 'Two or More Races']
PIE_ORDER = ['White', 'Two or More Races', 'Asian', 'Black or African American', 'Hispanic or Latino']
ORG_SIZE_ORDER = ['Very Large', 'Large', 'Medium', 'Small']

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
