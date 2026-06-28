"""Constants for the Yeelight Matrix integration."""

DOMAIN = "yeelight_matrix"

# Config entry keys.
CONF_LAYOUT_ORIENTATION = "layout_orientation"
CONF_BASE_POSITION = "base_position"
CONF_MODULES = "modules"
CONF_DOT_ENTITIES = "dot_entities"

# Defaults.
DEFAULT_PORT = 55443
DEFAULT_DOT_ENTITIES = False

# Service names.
SERVICE_SET_PIXEL = "set_pixel"
SERVICE_SET_PIXELS = "set_pixels"
SERVICE_SET_MODULE_COLOR = "set_module_color"
SERVICE_SET_MODULE_COLORS = "set_module_colors"
SERVICE_SET_IMAGE = "set_image"
SERVICE_CLEAR = "clear"
SERVICE_SET_FX_MODE = "set_fx_mode"
