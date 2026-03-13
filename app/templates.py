from fastapi.templating import Jinja2Templates

def floatformat(value, precision=2):
	return f"{value:.{precision}f}"

def datetimeformat(value, format="%Y-%m-%d %H:%M:%S"):
	return value.strftime(format)

def bytes_to_human(value):
	if value is None:
		return "0 B"
	if value >= 1_099_511_627_776:
		return f"{value / 1_099_511_627_776:.2f} TB"
	if value >= 1_073_741_824:
		return f"{value / 1_073_741_824:.2f} GB"
	if value >= 1_048_576:
		return f"{value / 1_048_576:.2f} MB"
	if value >= 1024:
		return f"{value / 1024:.2f} KB"
	return f"{value} B"

templates = Jinja2Templates(directory="templates")

templates.env.filters.update({
	"floatformat": floatformat,
	"datetimeformat": datetimeformat,
	"bytes_to_human": bytes_to_human,
})