from django.conf.urls import url

from ideal.contrib.django.ideal_compat import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='ideal_tests_index'),
    url(r'^get_issuers/$', views.GetIssuersView.as_view(), name='ideal_tests_get_issuers'),
    url(r'^start_transaction/$', views.StartTransactionView.as_view(), name='ideal_tests_start_transaction'),
    url(r'^get_transaction_status/$', views.GetTransactionStatusView.as_view(),
        name='ideal_tests_get_transaction_status'),
]
