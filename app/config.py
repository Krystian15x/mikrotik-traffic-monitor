from functools import lru_cache
from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
	app_name: str = "Monitor Ruchu Sieciowego"
	app_description: str = "Panel do monitorowania zużycia danych."

	db_user: str
	db_password: str
	db_host: str
	db_port: int
	db_name: str

	router_host: str
	router_api_port: int = 8729
	router_username: str
	router_password: str
	lte_nr_interface: str
	use_ssl: bool = True

	secret_key: str
	access_token_algorithm: str
	access_token_expire_days: int

	model_config = SettingsConfigDict(
		env_file=".env",
		env_file_encoding="utf-8",
		extra="ignore"
	)

	@computed_field
	@property
	def database_url(self) -> str:
		return (
			f"mysql+pymysql://{self.db_user}:{self.db_password}"
			f"@{self.db_host}:{self.db_port}/{self.db_name}"
		)

@lru_cache
def get_settings() -> Settings:
	return Settings()

settings = get_settings()