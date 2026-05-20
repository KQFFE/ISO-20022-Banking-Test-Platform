import os
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config

# Load configuration from environment variables or a .env file
config = Config(".env")
oauth = OAuth(config)

# The 'sso' name matches the reference in backend/app/api/auth.py
oauth.register(
    name='sso',
    client_id=os.getenv("OIDC_CLIENT_ID", "your-client-id"),
    client_secret=os.getenv("OIDC_CLIENT_SECRET", "your-client-secret"),
    server_metadata_url=os.getenv(
        "OIDC_CONF_URL", 
        "https://example.com/auth/realms/myrealm/.well-known/openid-configuration"
    ),
    client_kwargs={
        'scope': 'openid email profile',
        'timeout': 10.0
    }
)