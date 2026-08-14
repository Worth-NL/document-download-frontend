import re
from datetime import date, timedelta

import pytest
from bs4 import BeautifulSoup
from flask import current_app, url_for
from freezegun import freeze_time
from notifications_utils.base64_uuid import uuid_to_base64
from notifications_utils.testing.comparisons import AnySupersetOf

from tests import normalize_spaces


@pytest.mark.parametrize(
    "view, method",
    [
        ("main.landing", "get"),
        ("main.download_document", "get"),
        ("main.confirm_email_address", "get"),
        ("main.confirm_email_address", "post"),
    ],
)
def test_404_if_no_key_in_query_string_nl(service_id, document_id, view, method, client):
    response = client.open(
        url_for(
            view,
            service_id=service_id,
            document_id=document_id,
        ),
        method=method,
    )
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert response.status_code == 404
    assert normalize_spaces(page.title.text) == "Pagina niet gevonden – NotifyNL"
    assert normalize_spaces(page.h1.text) == "Pagina niet gevonden"


@pytest.mark.parametrize(
    "view, method",
    [
        ("main.landing", "get"),
        ("main.download_document", "get"),
        ("main.confirm_email_address", "get"),
        ("main.confirm_email_address", "post"),
    ],
)
def test_when_document_is_unavailable_nl(
    view, method, service_id, document_id, key, client, sample_service, rmock, mocker
):
    mocker.patch(
        "notifications_utils.request_helper.NotifyRequest.get_onwards_request_headers",
        return_value={"some-onwards": "request-header"},
    )
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    rmock.get(
        "{}/services/{}/documents/{}/check?key={}".format(
            current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"], service_id, document_id, key
        ),
        status_code=404,
        json={"Error": "Nope"},
    )

    response = client.open(
        url_for(
            view,
            service_id=service_id,
            document_id=document_id,
            key=key,
        ),
        method=method,
    )

    assert response.status_code == 404
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.h1.text) == "Pagina niet gevonden"
    # ensure this is our contextualized 404 page
    assert any((sample_service["name"] in elem.text) for elem in page.select("main p"))

    assert len(rmock.request_history) == 1
    assert rmock.request_history[0].method == "GET"
    assert rmock.request_history[0].url == "{}/services/{}/documents/{}/check?key={}".format(
        current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"],
        service_id,
        document_id,
        key,
    )
    assert rmock.request_history[0].headers == AnySupersetOf({"some-onwards": "request-header"})


@pytest.mark.parametrize(
    "view, method",
    [
        ("main.landing", "get"),
        ("main.download_document", "get"),
        ("main.confirm_email_address", "get"),
        ("main.confirm_email_address", "post"),
    ],
)
def test_when_document_is_unavailable_old_api_nl(
    view, method, service_id, document_id, key, client, sample_service, rmock, mocker
):
    mocker.patch(
        "notifications_utils.request_helper.NotifyRequest.get_onwards_request_headers",
        return_value={"some-onwards": "request-header"},
    )
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    rmock.get(
        "{}/services/{}/documents/{}/check?key={}".format(
            current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"], service_id, document_id, key
        ),
        status_code=200,
        json={"document": None},
    )

    response = client.open(
        url_for(
            view,
            service_id=service_id,
            document_id=document_id,
            key=key,
        ),
        method=method,
    )

    # old-style api can't differentiate between missing and gone - all treated as gone
    assert response.status_code == 410
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.h1.text) == "Niet langer beschikbaar"

    contact_link = page.select("main a")[0]
    assert normalize_spaces(contact_link.text) == "Neem contact op met Sample Service"
    assert contact_link["href"] == "https://sample-service.gov.uk"

    assert len(rmock.request_history) == 1
    assert rmock.request_history[0].method == "GET"
    assert rmock.request_history[0].url == "{}/services/{}/documents/{}/check?key={}".format(
        current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"],
        service_id,
        document_id,
        key,
    )
    assert rmock.request_history[0].headers == AnySupersetOf({"some-onwards": "request-header"})


@pytest.mark.parametrize("view", ("main.landing", "main.confirm_email_address", "main.download_document"))
def test_download_document_returns_file_unavailable_if_file_past_expiry_date_nl(
    service_id, document_id, key, client, sample_service, view, rmock, mocker
):
    mocker.patch(
        "notifications_utils.request_helper.NotifyRequest.get_onwards_request_headers",
        return_value={"some-onwards": "request-header"},
    )
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    rmock.get(
        "{}/services/{}/documents/{}/check?key={}".format(
            current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"], service_id, document_id, key
        ),
        status_code=410,
        json={"Error": "Gone"},
    )

    response = client.get(url_for(view, service_id=service_id, document_id=document_id, key=key))

    assert response.status_code == 410
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.h1.text) == "Niet langer beschikbaar"

    contact_link = page.select("main a")[0]
    assert normalize_spaces(contact_link.text) == "Neem contact op met Sample Service"
    assert contact_link["href"] == "https://sample-service.gov.uk"

    assert len(rmock.request_history) == 1
    assert rmock.request_history[0].method == "GET"
    assert rmock.request_history[0].url == "{}/services/{}/documents/{}/check?key={}".format(
        current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"],
        service_id,
        document_id,
        key,
    )
    assert rmock.request_history[0].headers == AnySupersetOf({"some-onwards": "request-header"})


@pytest.mark.parametrize("view", ("main.landing", "main.confirm_email_address", "main.download_document"))
def test_download_document_returns_file_unavailable_if_file_past_expiry_date_old_api_nl(
    service_id, document_id, key, client, sample_service, view, rmock, mocker
):
    mocker.patch(
        "notifications_utils.request_helper.NotifyRequest.get_onwards_request_headers",
        return_value={"some-onwards": "request-header"},
    )
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    rmock.get(
        "{}/services/{}/documents/{}/check?key={}".format(
            current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"], service_id, document_id, key
        ),
        status_code=200,
        json={
            "document": {
                "direct_file_url": "url",
                "confirm_email": False,
                "size_in_bytes": 712099,
                "file_extension": "pdf",
                "available_until": str(date.today() - timedelta(days=1)),
            }
        },
    )

    response = client.get(url_for(view, service_id=service_id, document_id=document_id, key=key))

    assert response.status_code == 410
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.h1.text) == "Niet langer beschikbaar"

    contact_link = page.select("main a")[0]
    assert normalize_spaces(contact_link.text) == "Neem contact op met Sample Service"
    assert contact_link["href"] == "https://sample-service.gov.uk"

    assert len(rmock.request_history) == 1
    assert rmock.request_history[0].method == "GET"
    assert rmock.request_history[0].url == "{}/services/{}/documents/{}/check?key={}".format(
        current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"],
        service_id,
        document_id,
        key,
    )
    assert rmock.request_history[0].headers == AnySupersetOf({"some-onwards": "request-header"})


@pytest.mark.parametrize(
    "view, method",
    [
        ("main.landing", "get"),
        ("main.download_document", "get"),
        ("main.confirm_email_address", "get"),
        ("main.confirm_email_address", "post"),
    ],
)
@pytest.mark.parametrize(
    "json_response",
    [
        {"error": "Missing decryption key"},
        {"error": "Invalid decryption key"},
        {"error": "Forbidden"},
    ],
)
@pytest.mark.parametrize(
    "api_status_code",
    [
        400,
        404,
        403,
    ],
)
def test_404_hides_incorrect_credentials_nl(
    view,
    method,
    api_status_code,
    client,
    service_id,
    document_id,
    key,
    rmock,
    mocker,
    json_response,
    sample_service,
):
    mocker.patch(
        "notifications_utils.request_helper.NotifyRequest.get_onwards_request_headers",
        return_value={"some-onwards": "request-header"},
    )
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    rmock.get(
        "{}/services/{}/documents/{}/check?key={}".format(
            current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"], service_id, document_id, key
        ),
        status_code=api_status_code,
        json=json_response,
    )
    response = client.open(
        url_for(view, service_id=service_id, document_id=document_id, key=key),
        method=method,
    )
    assert response.status_code == 404
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.h1.text) == "Pagina niet gevonden"
    # ensure this is our contextualized 404 page
    assert any((sample_service["name"] in elem.text) for elem in page.select("main p"))

    assert len(rmock.request_history) == 1
    assert rmock.request_history[0].method == "GET"
    assert rmock.request_history[0].url == "{}/services/{}/documents/{}/check?key={}".format(
        current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"],
        service_id,
        document_id,
        key,
    )
    assert rmock.request_history[0].headers == AnySupersetOf({"some-onwards": "request-header"})


def test_landing_page_creates_link_for_document_nl(
    service_id, document_id, key, document_has_metadata_no_confirmation, client, mocker, sample_service
):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    response = client.get(
        url_for(
            "main.landing",
            service_id=service_id,
            document_id=document_id,
            key=key,
        )
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.title.text) == "U heeft een bestand om te downloaden – NotifyNL"
    assert normalize_spaces(page.h1.text) == "U heeft een bestand om te downloaden"
    assert page.find("a", string=re.compile("Doorgaan"))["href"] == url_for(
        "main.download_document", service_id=service_id, document_id=document_id, key="1234"
    )


def test_landing_page_creates_link_to_confirm_email_address_nl(
    service_id, document_id, key, document_has_metadata_requires_confirmation, client, mocker, sample_service
):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    response = client.get(
        url_for(
            "main.landing",
            service_id=service_id,
            document_id=document_id,
            key=key,
        )
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.title.text) == "U heeft een bestand om te downloaden – NotifyNL"
    assert normalize_spaces(page.h1.text) == "U heeft een bestand om te downloaden"
    assert page.find("a", string=re.compile("Doorgaan"))["href"] == url_for(
        "main.confirm_email_address", service_id=service_id, document_id=document_id, key="1234"
    )


def test_confirm_email_address_page_shows_email_address_form_and_contact_details_nl(
    service_id,
    document_id,
    key,
    document_has_metadata_requires_confirmation,
    client,
    mocker,
    sample_service,
):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    response = client.get(
        url_for(
            "main.confirm_email_address",
            service_id=service_id,
            document_id=document_id,
            key=key,
        )
    )
    assert response.status_code == 200

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.title.text) == "Bevestig uw e-mailadres – NotifyNL"
    assert normalize_spaces(page.h1.text) == "Bevestig uw e-mailadres"
    assert page.select_one("form")
    assert not page.select(".govuk-error-summary")

    contact_link = page.select("main a")[0]
    assert contact_link.text.strip() == "Neem contact op met Sample Service"
    assert contact_link["href"] == "https://sample-service.gov.uk"


def test_confirm_email_address_page_shows_an_error_if_the_email_address_is_invalid_nl(
    service_id,
    document_id,
    key,
    document_has_metadata_requires_confirmation,
    client,
    mocker,
    sample_service,
):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    response = client.post(
        url_for(
            "main.confirm_email_address",
            service_id=service_id,
            document_id=document_id,
            key=key,
        ),
        data={"email_address": "fake address"},
    )
    assert response.status_code == 400

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.title.text) == "Fout: Bevestig uw e-mailadres – NotifyNL"
    assert normalize_spaces(page.h1.text) == "Bevestig uw e-mailadres"

    # Error summary in banner at the top of the page
    assert normalize_spaces(page.select_one(".govuk-error-summary__title").text) == "Er is een probleem"
    assert normalize_spaces(page.select_one(".govuk-error-summary__list").text) == "Geen geldig e-mailadres"

    # Error above the form input
    assert normalize_spaces(page.select_one("#email_address-error").text) == "Error: Geen geldig e-mailadres"


def test_confirm_email_address_page_shows_error_if_wrong_email_address_nl(
    service_id,
    document_id,
    key,
    document_has_metadata_requires_confirmation,
    client,
    mocker,
    sample_service,
    rmock,
):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    rmock.post(
        "{}/services/{}/documents/{}/authenticate".format(
            current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"],
            service_id,
            document_id,
        ),
        status_code=400,
        json={"error": "Authentication failure"},
    )

    response = client.post(
        url_for(
            "main.confirm_email_address",
            service_id=service_id,
            document_id=document_id,
            key=key,
        ),
        data={"email_address": "me@example.com"},
    )
    assert response.status_code == 400

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.title.text) == "Fout: Bevestig uw e-mailadres – NotifyNL"
    assert normalize_spaces(page.h1.text) == "Bevestig uw e-mailadres"

    # Error summary in banner at the top of the page
    assert normalize_spaces(page.select_one(".govuk-error-summary__title").text) == "Er is een probleem"
    assert normalize_spaces(page.select_one(".govuk-error-summary__list").text) == (
        "Dit is niet het e-mailadres waar het bestand naartoe is gestuurd."
        "Voer het e-mailadres in waar Sample Service het bestand naartoe heeft gestuurd "
        "om te bevestigen dat het bestand voor u bedoeld was."
    )

    # Error above the form input
    assert not page.select_one("#email_address-error")


def test_confirm_email_address_page_shows_429_error_page_if_auth_rate_limited_nl(
    service_id,
    document_id,
    key,
    document_has_metadata_requires_confirmation,
    client,
    mocker,
    sample_service,
    rmock,
):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    rmock.post(
        "{}/services/{}/documents/{}/authenticate".format(
            current_app.config["DOCUMENT_DOWNLOAD_API_HOST_NAME_INTERNAL"],
            service_id,
            document_id,
        ),
        status_code=429,
        json={"error": "Too many requests"},
    )

    response = client.post(
        url_for(
            "main.confirm_email_address",
            service_id=service_id,
            document_id=document_id,
            key=key,
        ),
        data={"email_address": "me@example.com"},
    )
    assert response.status_code == 429

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.title.text) == "Kan document niet openen – NotifyNL"
    assert normalize_spaces(page.h1.text) == "Kan document niet openen"

    assert page.find("a", string="Ga terug naar bevestig uw e-mailadres").get("href") == (
        "http://document-download-frontend.gov/"
        f"d/{uuid_to_base64(service_id)}/{uuid_to_base64(document_id)}/confirm-email-address?key=1234"
    )

    assert "support@notificatie.nl" in page.text
    # the UK support address must not leak into the Dutch page
    assert "notify-support@digital.cabinet-office.gov.uk" not in page.text


def test_download_document_creates_link_to_actual_doc_from_api_nl(
    service_id, document_id, key, document_has_metadata_no_confirmation, client, mocker, sample_service
):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    response = client.get(url_for("main.download_document", service_id=service_id, document_id=document_id, key=key))

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert normalize_spaces(page.title.text) == "Download uw bestand – NotifyNL"
    assert normalize_spaces(page.h1.text) == "Download uw bestand"
    assert page.select("main a")[0]["href"] == "url"
    assert page.select("main a")[0].text == "Download dit tekstbestand (0.7MB) naar uw apparaat"


@pytest.mark.parametrize(
    "file_extension,expected_pretty_file_type",
    [
        ("csv", "CSV-bestand"),
        ("doc", "Microsoft Word-document"),
        ("docx", "Microsoft Word-document"),
        ("odt", "tekstbestand"),
        ("pdf", "PDF"),
        ("png", "PNG-bestand"),
        ("rtf", "tekstbestand"),
        ("txt", "tekstbestand"),
        ("jpeg", "JPEG-bestand"),
        ("json", "JSON-bestand"),
        ("xlsx", "Microsoft Excel-spreadsheet"),
    ],
)
def test_download_document_shows_pretty_file_type_nl(
    service_id, document_id, key, client, mocker, sample_service, file_extension, expected_pretty_file_type
):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})
    mocked_metadata = {
        "direct_file_url": "url",
        "confirm_email": False,
        "size_in_bytes": 712099,
        "file_extension": file_extension,
        "available_until": str(date.today() + timedelta(days=5)),
    }
    mocker.patch("app.main.views.index._get_document_metadata", return_value=mocked_metadata)

    response = client.get(url_for("main.download_document", service_id=service_id, document_id=document_id, key=key))

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.select("main a")[0].text == f"Download dit {expected_pretty_file_type} (0.7MB) naar uw apparaat"


def test_download_document_handles_missing_expiry_nl(service_id, document_id, key, client, mocker, sample_service):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})
    mocked_metadata = {
        "direct_file_url": "url",
        "confirm_email": False,
        "size_in_bytes": 712099,
        "file_extension": "csv",
        "available_until": None,
    }
    mocker.patch("app.main.views.index._get_document_metadata", return_value=mocked_metadata)

    response = client.get(url_for("main.download_document", service_id=service_id, document_id=document_id, key=key))

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert any(
        ("Informatie over de vervaldatum van het bestand is tijdelijk niet beschikbaar" in elem.text)
        for elem in page.select("main p")
    )


def test_download_document_shows_contact_information_nl(
    service_id, document_id, key, document_has_metadata_no_confirmation, client, mocker, sample_service
):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    response = client.get(url_for("main.download_document", service_id=service_id, document_id=document_id, key=key))

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")

    contact_link = page.select("main a")[1]
    assert contact_link.text.strip() == "Neem contact op met Sample Service"
    assert contact_link["href"] == "https://sample-service.gov.uk"


@freeze_time("2022-10-12 13:30")
@pytest.mark.parametrize(
    "days_till_expiry,expected_content",
    [
        (28, "woensdag 9 november 2022"),
        (30, "vrijdag 11 november 2022"),
        (31, "12 november 2022"),
        (50, "1 december 2022"),
    ],
)
def test_download_document_shows_expiry_date_nl(
    service_id, document_id, key, client, mocker, sample_service, days_till_expiry, expected_content
):
    mocker.patch("app.service_api_client.get_service", return_value={"data": sample_service})

    mocked_metadata = {
        "direct_file_url": "url",
        "confirm_email": False,
        "size_in_bytes": 712099,
        "file_extension": "pdf",
        "available_until": str(date.today() + timedelta(days=days_till_expiry)),
    }
    mocker.patch("app.main.views.index._get_document_metadata", return_value=mocked_metadata)

    response = client.get(url_for("main.download_document", service_id=service_id, document_id=document_id, key=key))

    assert response.status_code == 200

    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    content_about_expiry_date = page.select("main p")[0]

    assert f"Dit bestand is te downloaden tot {expected_content}." in content_about_expiry_date.text


def test_landing_page_has_supplier_contact_info_number_nl(
    service_id,
    document_id,
    key,
    document_has_metadata_no_confirmation,
    client,
    mocker,
):
    service = {"name": "Sample Service", "contact_link": "07123456789"}
    mocker.patch("app.service_api_client.get_service", return_value={"data": service})

    response = client.get(
        url_for(
            "main.landing",
            service_id=service_id,
            document_id=document_id,
            key=key,
        )
    )

    assert response.status_code == 200
    page = BeautifulSoup(response.data.decode("utf-8"), "html.parser")
    assert page.find_all(string=re.compile("Bel 07123456789"))
