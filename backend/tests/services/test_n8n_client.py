import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

backend_dir = Path(__file__).resolve().parent.parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config.settings import settings
from app.schemas.campaign import PublishPayload
from app.services.n8n_client import trigger_publish


@pytest.fixture
def sample_payload():
    return PublishPayload(
        campaign_id="camp_101",
        business_id="biz_101",
        final_caption="Treat yourself to Chocolate Truffle Cake!",
        image_url="https://example.com/poster.png",
        destination_channels=["Instagram"],
    )


def test_n8n_client_mock_logging(sample_payload):
    settings.n8n_mock = True
    trigger_publish(sample_payload)


@patch("requests.post")
def test_n8n_client_sends_correct_headers_and_payload(mock_post, sample_payload):
    settings.n8n_mock = False
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    trigger_publish(sample_payload)

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args

    assert args[0] == settings.n8n_webhook_url
    assert kwargs["headers"]["X-Webhook-Secret"] == settings.n8n_shared_secret
    assert kwargs["headers"]["Content-Type"] == "application/json"
    assert kwargs["json"] == sample_payload.model_dump()


@patch("requests.post")
def test_n8n_client_raises_on_simulated_500_response(mock_post, sample_payload):
    settings.n8n_mock = False
    import requests
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.raise_for_status.side_effect = requests.HTTPError("500 Internal Server Error")
    mock_post.return_value = mock_response

    with pytest.raises(RuntimeError) as exc_info:
        trigger_publish(sample_payload)

    assert "n8n publish failed" in str(exc_info.value)
