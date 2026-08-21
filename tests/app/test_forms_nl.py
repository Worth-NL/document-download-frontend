import pytest
from werkzeug.datastructures import MultiDict

from app.forms import EmailAddressForm


@pytest.mark.parametrize(
    "email_address,error",
    [
        ("invalid_email", "Geen geldig e-mailadres"),
        ("", "Vul uw e-mailadres in"),
    ],
)
def test_email_address_form_validates_nl(client, email_address, error):
    form = EmailAddressForm(formdata=MultiDict([("email_address", email_address)]))

    form.validate()

    assert form.email_address.errors == [error]
