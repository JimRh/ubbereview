"""
    Title: Accounts Views
    Description: The file will contain on the Accounts views of the management website:
        - Accounts
    Created: October 27, 2020
    Author: Carmichael
    Edited By:
    Edited Date:
"""
from django.contrib.auth import authenticate, login

from django.shortcuts import redirect, render
from django.views.generic.base import TemplateView


class Login(TemplateView):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            return redirect("schema-redoc")

        return render(request, self.template_name, {})

    def post(self, request, *args, **kwargs):

        username = request.POST.get('username')
        password = request.POST.get('password')
        message = "Username Password combination not found."

        try:
            user = authenticate(username=username.lower().strip(), password=password)
        except Exception:
            return render(request, self.template_name, context={"is_invalid": True, "message": message})

        if user is not None:
            login(request, user)
            return redirect('schema-redoc')

        return render(request, self.template_name, context={"is_invalid": True, "message": message})
