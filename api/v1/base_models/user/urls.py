from django.urls import path
from .views import MyProfileView

app_name = 'user'

urlpatterns = [
    path('profiles/me/', MyProfileView.as_view(), name='my-profile'),
    # Add user URLs here
] 