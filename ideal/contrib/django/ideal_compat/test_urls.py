from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

from ideal.contrib.django.ideal_compat.views import GetIssuersView, StartTransactionView, GetTransactionStatusView


urlpatterns = patterns('',
    url(r'^$', TemplateView.as_view(template_name='ideal/tests/index.html'), name='ideal_tests_index'),
    url(r'^get_issuers/$', GetIssuersView.as_view(), name='ideal_tests_get_issuers'),
    url(r'^start_transaction/$', StartTransactionView.as_view(), name='ideal_tests_start_transaction'),
    url(r'^get_transaction_status/$', GetTransactionStatusView.as_view(), name='ideal_tests_get_transaction_status'),
)
