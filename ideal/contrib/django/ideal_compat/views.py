from django import forms
from django.views.generic.edit import FormView
from django.core.urlresolvers import reverse

from ideal.conf import settings
from ideal.client import IdealClient
from ideal.exceptions import IdealException


class IdealViewMixin(object):
    client = IdealClient()

    def get_default_context(self):
        return {
            'settings': settings,
            'acquirer_url': settings.get_acquirer_url(),
        }

class IdealFormMixin(object):
    error_css_class = 'error'
    required_css_class = 'required'


class GetIssuerForm(forms.Form, IdealFormMixin):
    pass


class GetIssuersView(FormView, IdealViewMixin):
    template_name = 'ideal/tests/get_issuers.html'
    form_class = GetIssuerForm

    def get_context_data(self, **kwargs):
        context = super(GetIssuersView, self).get_context_data(**kwargs)

        context.update(self.get_default_context())
        context.update({
            'start_transaction_url': reverse('ideal_tests_start_transaction')
        })

        return context

    def form_valid(self, form):
        error_message = None
        response = None

        try:
            response = self.client.get_issuers()
        except IdealException, e:
            error_message = e.message

        return self.render_to_response(self.get_context_data(form=form, response=response, error_message=error_message))


class StartTransactionForm(forms.Form, IdealFormMixin):
    issuer_id = forms.CharField(max_length=11)
    purchase_id = forms.CharField(max_length=16)
    amount = forms.DecimalField(max_digits=12, decimal_places=2)
    description = forms.CharField(max_length=32)
    entrance_code = forms.CharField(max_length=40, required=False)
    merchant_return_url = forms.URLField(required=False)
    expiration_period = forms.CharField(max_length=10, required=False)
    language = forms.ChoiceField(choices=(('nl', 'nl'), ('en', 'en')), required=False)


class StartTransactionView(FormView, IdealViewMixin):
    template_name = 'ideal/tests/start_transaction.html'
    form_class = StartTransactionForm

    def get_initial(self):
        initial = super(StartTransactionView, self).get_initial()
        initial.update({
            'issuer_id': self.request.GET.get('issuer_id', ''),
            'merchant_return_url': settings.MERCHANT_RETURN_URL,
            'expiration_period': settings.EXPIRATION_PERIOD,
            'language': settings.LANGUAGE,
        })
        return initial

    def get_context_data(self, **kwargs):
        context = super(StartTransactionView, self).get_context_data(**kwargs)

        context.update(self.get_default_context())
        context.update({
            'get_transaction_status_url': reverse('ideal_tests_get_transaction_status'),
        })

        return context

    def form_valid(self, form):
        kwargs = form.cleaned_data

        # Make sure we pass None for entrance code instead of an empty string.
        if not kwargs.get('entrance_code'):
            kwargs.update({'entrance_code': None})

        error_message = None
        response = None

        try:
            response = self.client.start_transaction(**kwargs)
        except IdealException, e:
            error_message = e.message

        return self.render_to_response(self.get_context_data(form=form, response=response, error_message=error_message))


class GetTransactionStatusForm(forms.Form, IdealFormMixin):
    transaction_id = forms.CharField(max_length=16)


class GetTransactionStatusView(FormView, IdealViewMixin):
    template_name = 'ideal/tests/get_transaction_status.html'
    form_class = GetTransactionStatusForm

    def get_context_data(self, **kwargs):
        context = super(GetTransactionStatusView, self).get_context_data(**kwargs)

        context.update(self.get_default_context())

        return context

    def get_initial(self):
        initial = super(GetTransactionStatusView, self).get_initial()
        initial.update({
            'transaction_id': self.request.GET.get('trxid', ''),
        })
        return initial

    def form_valid(self, form):
        error_message = None
        response = None

        try:
            response = self.client.get_transaction_status(form.cleaned_data['transaction_id'])
        except IdealException, e:
            error_message = e.message

        return self.render_to_response(self.get_context_data(form=form, response=response, error_message=error_message))
