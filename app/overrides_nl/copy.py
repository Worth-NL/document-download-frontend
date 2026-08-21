"""Dutch copy for document-download-frontend.

Kept separate from app/forms.py and app/main/views/index.py (which import
these constants/functions in place of the original English literals) so
those upstream files keep their original structure and diff minimally --
see .claude/rules/overrides-and-overwrites.md.
"""

EMAIL_ADDRESS_LABEL = "E-mailadres"
EMAIL_ADDRESS_REQUIRED_MESSAGE = "Vul uw e-mailadres in"
EMAIL_ADDRESS_INVALID_MESSAGE = "Geen geldig e-mailadres"

CONFIRM_EMAIL_PAGE_NAME = "bevestig uw e-mailadres"


def email_mismatch_error(service_name):
    return (
        "Dit is niet het e-mailadres waar het bestand naartoe is gestuurd.<br><br>"
        f"Voer het e-mailadres in waar {service_name} het bestand naartoe heeft gestuurd "
        "om te bevestigen dat het bestand voor u bedoeld was."
    )
