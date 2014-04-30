import django
if django.VERSION[0:2] < (1,4):
    from django.conf.urls.defaults import patterns, url
else:
    from django.conf.urls import patterns, url

from ideal.contrib.django.ideal_compat.views import IndexView, GetIssuersView, StartTransactionView, GetTransactionStatusView


urlpatterns = patterns('',
    url(r'^$', IndexView.as_view(), name='ideal_tests_index'),
    url(r'^get_issuers/$', GetIssuersView.as_view(), name='ideal_tests_get_issuers'),
    url(r'^start_transaction/$', StartTransactionView.as_view(), name='ideal_tests_start_transaction'),
    url(r'^get_transaction_status/$', GetTransactionStatusView.as_view(), name='ideal_tests_get_transaction_status'),
)
