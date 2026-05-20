from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.core.security import oauth

router = APIRouter()

# Note: SessionMiddleware needs to be added to the main FastAPI app in app.main.py
# For now, we'll assume it's there or will be added.

@router.get("/login")
async def login(request: Request):
    """
    Initiates the SSO login process.
    Redirects the user to the SSO provider's login page.
    """
    redirect_uri = request.url_for('auth_callback')
    return await oauth.sso.authorize_redirect(request, redirect_uri)

@router.get("/callback", name="auth_callback")
async def auth_callback(request: Request):
    """
    Handles the callback from the SSO provider after successful authentication.
    Exchanges the authorization code for tokens and fetches user info.
    """
    try:
        token = await oauth.sso.authorize_access_token(request)
        user_info = await oauth.sso.parse_id_token(request, token)
        
        # Store user info in session (or database)
        request.session['user'] = dict(user_info)
        
        # Redirect to the frontend dashboard or a success page
        return RedirectResponse(url="/") # Adjust this to your frontend's dashboard URL
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {e}"
        )