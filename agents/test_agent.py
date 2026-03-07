from playwright.sync_api import sync_playwright
from datetime import datetime


def run_website_test(url: str, test_case: dict = None) -> dict:
    """
    Run automated tests on a given URL.
    Optionally accepts a test_case dict with custom steps/assertions.
    """
    results = {
        "url": url,
        "timestamp": datetime.utcnow().isoformat(),
        "status": "success",
        "checks": {}
    }

    # Merge custom test case steps if provided
    custom_checks = test_case.get("checks", []) if test_case else []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            response = page.goto(url, timeout=15000)

            # ── Basic page info ──────────────────────────────────────────
            results["title"] = page.title()
            results["checks"]["http_status"] = response.status if response else None
            results["checks"]["page_loaded"] = True

            # ── Element counts ───────────────────────────────────────────
            results["checks"]["links_found"]   = page.locator("a").count()
            results["checks"]["buttons_found"] = page.locator("button").count()
            results["checks"]["images_found"]  = page.locator("img").count()
            results["checks"]["forms_found"]   = page.locator("form").count()

            # ── Performance timing ───────────────────────────────────────
            timing = page.evaluate("""() => {
                const t = performance.timing;
                return {
                    domContentLoaded: t.domContentLoadedEventEnd - t.navigationStart,
                    loadComplete:     t.loadEventEnd - t.navigationStart
                };
            }""")
            results["checks"]["performance_ms"] = timing

            # ── Custom checks from test case ─────────────────────────────
            custom_results = []
            for check in custom_checks:
                check_type = check.get("type")
                value      = check.get("value", "")
                passed     = False
                detail     = ""

                if check_type == "element_exists":
                    count  = page.locator(value).count()
                    passed = count > 0
                    detail = f"Selector '{value}' found {count} element(s)"

                elif check_type == "text_present":
                    content = page.content()
                    passed  = value.lower() in content.lower()
                    detail  = f"Text '{value}' {'found' if passed else 'not found'} on page"

                elif check_type == "title_contains":
                    passed = value.lower() in results["title"].lower()
                    detail = f"Title '{results['title']}' {'contains' if passed else 'does not contain'} '{value}'"

                elif check_type == "url_contains":
                    current = page.url
                    passed  = value.lower() in current.lower()
                    detail  = f"URL '{current}' {'contains' if passed else 'does not contain'} '{value}'"

                custom_results.append({
                    "type":   check_type,
                    "value":  value,
                    "passed": passed,
                    "detail": detail
                })

            if custom_results:
                results["checks"]["custom"] = custom_results
                all_passed = all(c["passed"] for c in custom_results)
                results["custom_checks_passed"] = all_passed

        except Exception as e:
            results["status"] = "error"
            results["error"]  = str(e)
            results["checks"]["page_loaded"] = False

        finally:
            browser.close()

    return results