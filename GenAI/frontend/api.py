
import os
import requests

API_BASE_URL = os.getenv(
    "KAPRUKA_API_URL",
    "http://127.0.0.1:8000"
)


def send_message(query: str, thread_id: str, selected_product_id: str | None = None) -> dict:
    url = f"{API_BASE_URL}/chat"

    payload = {
        "query": query,
        "thread_id": thread_id,
        "selected_product_id": selected_product_id
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=120,
        )

        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        raise RuntimeError(
            "The AI assistant took too long to respond. Please try again."
        )

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "Could not connect to the Kapruka AI Shopper API. "
            "Please check whether the backend is running."
        )

    except requests.exceptions.HTTPError as exc:
        try:
            detail = response.json().get("detail", str(exc))
        except ValueError:
            detail = str(exc)

        raise RuntimeError(f"API Error: {detail}")

    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Request failed: {exc}")
