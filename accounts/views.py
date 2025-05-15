from django.shortcuts import render, redirect
from django.contrib.auth import authenticate,login,logout
import logging
from django.contrib.auth.models import Group

logger = logging.getLogger(__name__)

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        logger.debug(f"Attempting to authenticate user: {username}")

        user = authenticate(request, username=username, password=password)
        logger.debug(f"Authentication result: {user}")

        if user is not None:
            if user.is_active:
                login(request, user)
                logger.debug(f"User logged in: {username}")
                if user.groups.filter(name="Employe").exists():
                    logger.debug(f"User {username} is in group 'Employe'")
                    return redirect('wellcome')
                else:
                    logger.debug(f"User {username} is not in group 'Employe', redirecting to dashboard")
                    return redirect('dashboard')
            else:
                logger.debug(f"User is not active: {username}")
                return render(request, "accounts/login.html", {
                    "message": "Account is inactive"
                })
        else:
            logger.debug(f"Authentication failed for user: {username}")
            return render(request, "accounts/login.html", {
                "message": "Incorrect username or password"
            })
    logger.debug("Rendering login page")
    return render(request, "accounts/login.html")

def logout_view(request):
    logout(request)
    return render(request, "accounts/login.html", {
        "message": "Logged out"
    })