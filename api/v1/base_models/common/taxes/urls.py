from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import TaxJurisdictionViewSet, TaxCategoryViewSet, TaxRateViewSet

app_name = 'taxes'

router = DefaultRouter()
router.register(r'jurisdictions', TaxJurisdictionViewSet, basename='taxjurisdiction')
router.register(r'categories', TaxCategoryViewSet, basename='taxcategory')
router.register(r'rates', TaxRateViewSet, basename='taxrate')

urlpatterns = router.urls 