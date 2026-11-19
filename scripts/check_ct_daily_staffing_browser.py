"""Verify the facility drilldown in Edge at phone and desktop widths."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

from playwright.sync_api import expect, sync_playwright



def main():
    root = Path(__file__).resolve().parents[1]
    with ThreadingHTTPServer(("127.0.0.1", 0), partial(SimpleHTTPRequestHandler, directory=root)) as server:
        Thread(target=server.serve_forever, daemon=True).start()
        try:
            with sync_playwright() as driver:
                browser = driver.chromium.launch(channel="msedge")
                for width in (390, 1280):
                    page = browser.new_page(viewport={"width": width, "height": 850})
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    url = f"http://127.0.0.1:{server.server_port}/staffing/tools/nursing-home-staffing-explorer.html"
                    page.goto(url + "?ccn=075319&role=7&day=2026-06-15#daily-staffing")
                    expect(page.locator("#pbj-rows")).to_contain_text("Registered nurse")
                    expect(page.locator("#pbj-day")).to_have_value("2026-06-15")
                    expect(page.locator("#pbj-rows tr")).to_have_count(2)
                    page.click("#pbj-prev")
                    expect(page.locator("#pbj-day")).to_have_value("2026-06-14")
                    page.click("#pbj-next")
                    expect(page.locator("#pbj-day")).to_have_value("2026-06-15")
                    page.select_option("#pbj-role", "")
                    expect(page.locator("#pbj-rows")).to_contain_text("Paid feeding assistant")
                    with page.expect_download() as download:
                        page.click("#pbj-export")
                    assert "075319-2026Q2" in download.value.suggested_filename
                    assert len(download.value.path().read_text().splitlines()) == 91 * 32 + 1
                    page.click("#pbj-support > summary")
                    expect(page.locator("#pbj-annual")).to_contain_text("housekeeping")
                    page.select_option("#pbj-quarter", "2020Q1")
                    expect(page.locator("#pbj-census")).to_contain_text("roles: —")
                    page.select_option("#pbj-quarter", "2026Q2")
                    expect(page.locator("#pbj-day")).to_have_value("2026-06-30")
                    assert page.locator(".pbj-scroll").evaluate("e => e.getBoundingClientRect().right <= innerWidth")
                    page.select_option("#pbj-archive", index=1)
                    expect(page.locator("#pbj-rows")).to_contain_text("Registered nurse")
                    archive = page.locator("#pbj-archive").input_value()
                    expect(page.locator("#pbj-home")).to_contain_text(archive)
                    permalink = page.locator("#pbj-link").get_attribute("href")
                    assert "pbj_home=" + archive in permalink
                    page.goto(permalink)
                    expect(page.locator("#pbj-archive")).to_have_value(archive)
                    expect(page.locator("#pbj-home")).to_contain_text(archive)
                    assert not errors, errors
                    page.close()
                    print(f"{width}px passed")
                browser.close()
        finally:
            server.shutdown()


if __name__ == "__main__":
    main()
