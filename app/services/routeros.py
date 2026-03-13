from routeros_api import RouterOsApiPool
from app.config import settings

def fetch_traffic_stats(interface_name: str):
	api_pool = RouterOsApiPool(
		host=settings.router_host,
		port=settings.router_api_port,
		use_ssl=settings.use_ssl,
		plaintext_login=True,
		username=settings.router_username,
		password=settings.router_password,
	)
	try:
		api = api_pool.get_api()
		resource = api.get_resource("/interface")
		stats = resource.get(name=interface_name)
		if not stats:
			raise RuntimeError(f"Nie znaleziono podanego interfejsu: {interface_name}")
		stat = stats[0]
		return (
			int(stat.get("rx-byte", 0)),
			int(stat.get("tx-byte", 0)),
			int(stat.get("rx-packet", 0)),
			int(stat.get("tx-packet", 0)),
		)
	except Exception as exc:
		raise RuntimeError(f"Błąd pobierania statystyk z routera: {exc}") from exc
	finally:
		try:
			api_pool.disconnect()
		except Exception:
			pass