"""Exercise remote rendering, camera motion, and arbitrary seeks through the actual UI."""

from playwright.sync_api import sync_playwright
from PIL import Image, ImageChops, ImageStat
from io import BytesIO

base = "http://127.0.0.1:8765/garden-bill-cafe/"
with sync_playwright() as pw:
    b = pw.chromium.launch(args=["--no-sandbox"])
    p = b.new_page(viewport={"width": 1100, "height": 870})
    errors = []
    p.on("pageerror", lambda e: errors.append(str(e)))
    p.goto(base)
    p.wait_for_url("**/live.html")
    p.wait_for_function(
        'Number(document.querySelector("#screen").dataset.frames)>=2', timeout=600000
    )

    def frame():
        return Image.open(BytesIO(p.locator("#screen").screenshot())).convert("RGB")

    def changed(f):
        start = int(p.locator("#screen").get_attribute("data-frames"))
        f()
        p.wait_for_function(
            'n=>Number(document.querySelector("#screen").dataset.frames)>=n+2',
            arg=start,
            timeout=60000,
        )

    a = frame()
    a.save("/tmp/cafe-live-room.jpg")

    def orbit():
        bounds = p.locator("#screen").bounding_box()
        x = bounds["x"] + bounds["width"] / 2
        y = bounds["y"] + bounds["height"] / 2
        p.mouse.move(x, y)
        p.mouse.down()
        p.mouse.move(x + 65, y + 15, steps=3)
        p.mouse.up()

    changed(orbit)
    assert max(ImageStat.Stat(ImageChops.difference(a, frame())).mean) > 4
    changed(lambda: p.select_option("#view", "mug"))
    mug = frame()
    mug.save("/tmp/cafe-live-mug.jpg")
    assert max(ImageStat.Stat(ImageChops.difference(a, mug)).mean) > 8
    changed(
        lambda: p.locator("#seek").evaluate(
            "s=>{s.value=13.55;s.dispatchEvent(new Event('input'))}"
        )
    )
    c = frame()
    c.save("/tmp/cafe-live-impact.jpg")
    assert max(ImageStat.Stat(ImageChops.difference(mug, c)).mean) > 0.12
    changed(lambda: p.get_by_role("button", name="Play", exact=True).click())
    p.get_by_role("button", name="Pause", exact=True).click()
    assert float(p.locator("#seek").input_value()) > 13.55
    p.get_by_role("link", name="Physics Lab").click()
    p.locator("#lab").wait_for()
    p.get_by_role("link", name="Café Catalogue").click()
    p.locator(".card").first.wait_for()
    p.goto(base + "#film")
    p.wait_for_url("**/live.html")
    assert p.locator("video, dialog").count() == 0
    assert p.locator("footer").inner_text().count("Sparsha Srinath") == 1
    for w in (390, 1100):
        p.set_viewport_size({"width": w, "height": 844})
        assert p.evaluate("document.documentElement.scrollWidth <= innerWidth")
        for selector in ("#speed", "#view"):
            assert p.locator(selector).evaluate(
                "s => getComputedStyle(s).appearance==='none' && getComputedStyle(s).borderTopStyle==='solid'"
            )
    assert not errors, errors
    print(
        "Remote frames, camera, seek, playback, and return navigation passed.",
        flush=True,
    )
