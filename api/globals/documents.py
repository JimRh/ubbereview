from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

BBE_LOGO_PATH = 'assets/BBE_LOGO.png'
BBE_LOGO_HEIGHT = 1 * inch
BBE_LOGO_WIDTH = (526 / 417) * BBE_LOGO_HEIGHT
PAGE_SIZE = letter
PAGE_OFFSET = 0.25 * inch
SANS_FONT = 'Helvetica'
MONO_FONT = 'Courier'
TABLE_LINE_THICKNESS = 0.75
BBE_BLUE = colors.PCMYKColor(100, 95, 25, 20)
TABLE_HEADER_COLOUR = colors.white
PAGE_WIDTH, PAGE_HEIGHT = letter
