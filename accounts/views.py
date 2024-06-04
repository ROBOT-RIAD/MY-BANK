from django.contrib.auth.forms import AuthenticationForm
from django.http import HttpResponse
from django.shortcuts import render,redirect
from django.views.generic import FormView
from .forms import UserRegistrationForm,UserUpdateForm
from django.contrib.auth import login,logout
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView,LogoutView
from django.views import View
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.template.loader import render_to_string
from  django.core.mail import EmailMessage,EmailMultiAlternatives
from django.contrib.auth.mixins import LoginRequiredMixin

# Create your views here.

def send__email(user,subject,template):
    message = render_to_string(template,{'user': user })
    send_email =EmailMultiAlternatives(subject,"",to =[user.email])
    send_email.attach_alternative(message,"text/html")
    send_email.send()

class UserRegistrationView(FormView):
    template_name ='accounts/user_registration.html'
    form_class =UserRegistrationForm
    success_url =reverse_lazy("profile")

    def form_valid(self, form):
        print(form.cleaned_data)
        user = form.save()
        login(self.request,user)
        print(user)
        return super().form_valid(form)
    


class UserLoginView(LoginView):
    template_name ='accounts/user_login.html'
    def get_success_url(self):
        return reverse_lazy('home')
    def form_valid(self,form):
        messages.success(self.request,"Login successfully")
        return super().form_valid(form)
    

# class UserLogoutView(LogoutView):
#    def get_success_url(self):
#         if self.request.user.is_authenticated:
#             logout(self.request)
#         return reverse_lazy('home')


class UserLogoutView(LogoutView):
    next_page = reverse_lazy('home') 
    
    def dispatch(self, request, *args, **kwargs):
        if request.method == 'GET':
            if request.user.is_authenticated:
                logout(self.request)
            return redirect(self.next_page)
        else:
            return super().dispatch(request, *args, **kwargs)
        



class UserBankAccountUpdateView(LoginRequiredMixin,View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the user's profile page
        return render(request, self.template_name, {'form': form})
    


class PasswordChangeView(LoginRequiredMixin,FormView):
    template_name = 'accounts/pass_change.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('profile')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, 'Password Updated Successfully')
        update_session_auth_hash(self.request, form.user)
        send__email(self.request.user,"change password","accounts/pass_ch_email.html")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs