from datetime import date
import pytest
from app import app, birthdays, calculate_days_until


@pytest.fixture(autouse=True)
def clean_birthdays():
    """Reset the in-memory birthdays list before and after each test."""
    birthdays.clear()
    yield
    birthdays.clear()


@pytest.fixture
def client():
    """Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_home_page_empty(client):
    """GET / should render successfully with form, sections, and footer."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert "Birthday Reminder Board" in html
    assert 'action="/add"' in html
    assert 'name="name"' in html
    assert 'name="date"' in html
    assert "This Month" in html
    assert "All Birthdays" in html
    assert "Commit:" in html
    assert "local" in html


def test_footer_commit_id_truncated(client, monkeypatch):
    """Footer should display RENDER_GIT_COMMIT truncated to 7 chars."""
    monkeypatch.setenv("RENDER_GIT_COMMIT", "abcdef1234567890")
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert "abcdef1" in html
    assert "abcdef1234567890" not in html


def test_add_birthday_success(client):
    """POST /add with valid fields appends and redirects to /."""
    response = client.post(
        "/add",
        data={"name": "Alice", "date": "1995-10-25"},
        follow_redirects=False,
    )
    assert response.status_code == 302
    assert response.headers["Location"] == "/"

    assert len(birthdays) == 1
    assert birthdays[0] == {"name": "Alice", "date": "1995-10-25"}

    # Verify rendered on home page
    home_resp = client.get("/")
    assert "Alice" in home_resp.get_data(as_text=True)


def test_add_duplicate_birthday_rejected(client):
    """Adding the same birthday twice returns 400 and rejects duplicate."""
    first_resp = client.post(
        "/add",
        data={"name": "Alice", "date": "1995-10-25"},
        follow_redirects=False,
    )
    assert first_resp.status_code == 302
    assert len(birthdays) == 1

    # Second addition with same name (even with whitespace) and date
    second_resp = client.post(
        "/add",
        data={"name": "  Alice  ", "date": "1995-10-25"},
        follow_redirects=False,
    )
    assert second_resp.status_code == 400
    assert "Error: Birthday already exists." in second_resp.get_data(
        as_text=True
    )
    assert len(birthdays) == 1


@pytest.mark.parametrize(
    "invalid_data,expected_error",
    [
        ({"name": "", "date": "1995-10-25"}, "Name cannot be empty"),
        ({"name": "   ", "date": "1995-10-25"}, "Name cannot be empty"),
        ({"name": "Alice", "date": ""}, "Date cannot be empty"),
        ({"name": "Alice", "date": "1995/10/25"}, "YYYY-MM-DD"),
        ({"name": "Alice", "date": "25-10-1995"}, "YYYY-MM-DD"),
        ({"name": "Alice", "date": "invalid-date"}, "YYYY-MM-DD"),
        ({"name": "Alice", "date": "2024-02-30"}, "not a valid"),
        ({"name": "Alice", "date": "2023-02-29"}, "not a valid"),
        ({"name": "Alice", "date": "2024-13-01"}, "not a valid"),
        ({"name": "Alice", "date": "2024-00-10"}, "not a valid"),
    ],
)
def test_add_birthday_validation_failures(
    client, invalid_data, expected_error
):
    """POST /add should reject invalid input with 400 and clear error."""
    response = client.post("/add", data=invalid_data)
    assert response.status_code == 400
    assert expected_error in response.get_data(as_text=True)
    assert len(birthdays) == 0


def test_this_month_section_computation(client):
    """GET / correctly computes the 'This Month' list in Flask view."""
    today = date.today()
    # Same month, e.g. 15th
    this_month_date = f"1990-{today.month:02d}-15"
    # Other month
    other_month = (today.month % 12) + 1
    other_month_date = f"1990-{other_month:02d}-15"

    birthdays.append({"name": "Current Month Person", "date": this_month_date})
    birthdays.append({"name": "Other Month Person", "date": other_month_date})

    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    # Extract This Month section
    assert "this-month-section" in html
    section_start = html.find('id="this-month-section"')
    section_end = html.find('id="all-birthdays-section"')
    this_month_html = html[section_start:section_end]

    assert "Current Month Person" in this_month_html
    assert "Other Month Person" not in this_month_html


def test_all_birthdays_sorted_by_days_until(client):
    """All Birthdays should be sorted by soonest upcoming birthday."""
    from datetime import timedelta
    today = date.today()
    yesterday = today - timedelta(days=1)
    bday_today = f"1990-{today.month:02d}-{today.day:02d}"
    bday_yesterday = f"1990-{yesterday.month:02d}-{yesterday.day:02d}"

    # Add items to birthdays: yesterday (wrapped) and today (0 days)
    birthdays.append({"name": "Yesterday Person", "date": bday_yesterday})
    birthdays.append({"name": "Today Person", "date": bday_today})

    response = client.get("/")
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    today_pos = html.find("Today Person")
    yesterday_pos = html.find("Yesterday Person")
    assert today_pos != -1
    assert yesterday_pos != -1
    # Today Person should appear before Yesterday Person in sorted list
    assert today_pos < yesterday_pos
    assert "0 days (Today!)" in html


def test_calculate_days_until_logic():
    """Unit test calculate_days_until date logic with wrapping."""
    # Test today
    ref_today = date(2026, 6, 15)

    # Birthday today
    assert calculate_days_until(date(1990, 6, 15), ref_today) == 0

    # Birthday tomorrow
    assert calculate_days_until(date(1990, 6, 16), ref_today) == 1

    # Birthday yesterday (already passed this year -> wraps to 2027)
    # Days until 2027-06-14 from 2026-06-15 = 364 days
    assert calculate_days_until(date(1990, 6, 14), ref_today) == 364

    # Feb 29 leap year birthday in non-leap year (celebrated Feb 28)
    # 2026 is non-leap year. Passed (Feb 28 < June 15) -> wraps to 2027-02-28
    days = calculate_days_until(date(2000, 2, 29), ref_today)
    expected = (date(2027, 2, 28) - ref_today).days
    assert days == expected


def test_xss_escaping(client):
    """User input must be auto-escaped and not rendered with |safe."""
    payload = "<script>alert('pwned')</script>"
    client.post("/add", data={"name": payload, "date": "1995-05-05"})

    response = client.get("/")
    html = response.get_data(as_text=True)

    assert "<script>alert('pwned')</script>" not in html
    assert "&lt;script&gt;alert(&#39;pwned&#39;)&lt;/script&gt;" in html or \
           "&lt;script&gt;alert('pwned')&lt;/script&gt;" in html


def test_api_birthdays(client):
    """GET /api/birthdays returns full list as JSON."""
    birthdays.append({"name": "Alice", "date": "1995-01-01"})
    birthdays.append({"name": "Bob", "date": "1992-05-15"})

    response = client.get("/api/birthdays")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert len(data) == 2
    assert data[0] == {"name": "Alice", "date": "1995-01-01"}
    assert data[1] == {"name": "Bob", "date": "1992-05-15"}


def test_get_birthday_by_name_success(client):
    """GET /api/birthdays/<name> returns matching birthday with 200."""
    birthdays.append({"name": "Alice Smith", "date": "1995-10-25"})

    # Exact match
    resp = client.get("/api/birthdays/Alice Smith")
    assert resp.status_code == 200
    assert resp.get_json() == {"name": "Alice Smith", "date": "1995-10-25"}

    # Case-insensitive match
    resp_lower = client.get("/api/birthdays/alice smith")
    assert resp_lower.status_code == 200
    assert resp_lower.get_json() == {
        "name": "Alice Smith",
        "date": "1995-10-25"
    }

    # Leading / trailing whitespace match
    resp_ws = client.get("/api/birthdays/%20alice%20smith%20")
    assert resp_ws.status_code == 200
    assert resp_ws.get_json() == {
        "name": "Alice Smith",
        "date": "1995-10-25"
    }


def test_get_birthday_by_name_not_found(client):
    """GET /api/birthdays/<name> returns 404 when name is not found."""
    birthdays.append({"name": "Alice Smith", "date": "1995-10-25"})

    resp = client.get("/api/birthdays/Unknown Person")
    assert resp.status_code == 404
    assert resp.is_json
    assert resp.get_json() == {"error": "Birthday not found"}


def test_health_endpoint_default(client):
    """GET /health returns status ok and default 'local' commit."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data == {"status": "ok", "commit": "local"}


def test_health_endpoint_with_env(client, monkeypatch):
    """GET /health returns commit truncated to 7 characters."""
    monkeypatch.setenv("RENDER_GIT_COMMIT", "123456789abcdef")
    response = client.get("/health")
    assert response.status_code == 200
    assert response.is_json
    data = response.get_json()
    assert data == {"status": "ok", "commit": "1234567"}
