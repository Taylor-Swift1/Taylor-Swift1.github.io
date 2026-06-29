#!/usr/bin/env python3
"""Build the static site from files in src/content."""

import calendar
import datetime as dt
import html
import json
import re
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTENT = ROOT / "src" / "content"
POSTS_DIR = CONTENT / "posts"

URL_ATTR_RE = re.compile(r'(<(?:a|img)\b[^>]*\s(?:href|src)=")([^"]+)(")', re.I)
IMAGE_SIZE_RE = re.compile(r"-(\d+)x(\d+)$")


def read_json(path):
    with open(str(path), "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path):
    with open(str(path), "r", encoding="utf-8") as handle:
        return handle.read()


def write_file(relative_path, content):
    path = ROOT / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(str(path), "w", encoding="utf-8") as handle:
        handle.write(content)


def esc(value):
    return html.escape(str(value), quote=True)


def rel_prefix(relative_path):
    parent = Path(relative_path).parent
    if str(parent) == ".":
        return ""
    return "../" * len(parent.parts)


def site_link(url, prefix):
    if not url:
        return ""
    if url.startswith("#") or re.match(r"^[a-z][a-z0-9+.-]*:", url, re.I):
        return url
    url = url[1:] if url.startswith("/") else url
    if url.endswith("/"):
        url += "index.html"
    return prefix + url


def image_base(stem):
    return IMAGE_SIZE_RE.sub("", stem)


def image_score(path):
    match = IMAGE_SIZE_RE.search(path.stem)
    if match:
        return int(match.group(1)) * int(match.group(2))
    return 10 ** 12


def full_size_image(src):
    if not src or re.match(r"^[a-z][a-z0-9+.-]*:", src, re.I):
        return src

    path = ROOT / src
    if not path.exists():
        return src

    base = image_base(path.stem)
    candidates = []
    for candidate in path.parent.glob("*{}".format(path.suffix)):
        candidate_base = image_base(candidate.stem)
        if candidate_base == base or candidate.stem.startswith(base + "-"):
            candidates.append(candidate)

    if not candidates:
        return src

    best = max(candidates, key=lambda candidate: (image_score(candidate), len(candidate.name)))
    return str(best.relative_to(ROOT))


def rewrite_content_links(content, prefix):
    def replace(match):
        return match.group(1) + site_link(match.group(2), prefix) + match.group(3)

    return URL_ATTR_RE.sub(replace, content)


def parse_content_file(path):
    text = read_text(path)
    if not text.startswith("---"):
        raise ValueError("{} is missing front matter".format(path))
    _, front_matter, body = text.split("---", 2)
    meta = {}
    for line in front_matter.strip().splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    meta["categories"] = [
        item.strip()
        for item in meta.get("categories", "").split(",")
        if item.strip()
    ]
    meta["content"] = body.strip()
    meta["date_obj"] = dt.datetime.strptime(meta["date"], "%Y-%m-%d").date()
    return meta


def strip_tags(value):
    return re.sub(r"<[^>]+>", "", value or "").strip()


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "section"


def format_date(value):
    try:
        return value.strftime("%B %-d, %Y")
    except ValueError:
        return value.strftime("%B %d, %Y").replace(" 0", " ")


def month_title(year, month):
    return "{} {}".format(calendar.month_name[month], year)


def load_posts():
    posts = []
    for path in sorted(POSTS_DIR.glob("*.html")):
        post = parse_content_file(path)
        post["source"] = str(path.relative_to(ROOT))
        posts.append(post)
    posts.sort(key=lambda post: post["date_obj"], reverse=True)
    return posts


def make_nav(site, active, prefix):
    links = []
    for item in site["navigation"]:
        is_active = active and item["label"].lower() == active
        attrs = ' class="is-active"' if is_active else ""
        current = ' aria-current="page"' if is_active else ""
        links.append(
            '<a{}{} href="{}">{}</a>'.format(
                attrs,
                current,
                esc(site_link(item["href"], prefix)),
                esc(item["label"]),
            )
        )
    return "\n".join(links)


def render_page(site, relative_path, title, body, active="", description=None, page_class=""):
    prefix = rel_prefix(relative_path)
    description = description or site["description"]
    page_title = site["title"] if title == site["title"] else "{} | {}".format(title, site["title"])
    nav = make_nav(site, active, prefix)
    year = dt.date.today().year
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{page_title}</title>
  <meta name="description" content="{description}">
  <link rel="stylesheet" href="{css}">
</head>
<body class="{page_class}">
  <a class="skip-link" href="#main">Skip to content</a>
  <header class="site-header">
    <div class="header-inner">
      <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-menu">
        <span class="screen-reader-text">Menu</span>
        <span></span><span></span><span></span>
      </button>
      <nav class="site-nav" id="site-menu" aria-label="Main navigation">
        {nav}
      </nav>
    </div>
  </header>
  <main id="main">
{body}
  </main>
  <footer class="site-footer">
    <p>&copy; {year} {author}. {footer}</p>
  </footer>
  <script src="{js}"></script>
</body>
</html>
""".format(
        page_title=esc(page_title),
        description=esc(description),
        css=esc(site_link("assets/site.css", prefix)),
        js=esc(site_link("assets/site.js", prefix)),
        nav=nav,
        body=body,
        page_class=esc(page_class),
        year=year,
        author=esc(site["author"]),
        footer=esc(site.get("footer", "")),
    )


def page_heading(title, text=None):
    text_html = "\n      <p>{}</p>".format(esc(text)) if text else ""
    return """  <section class="page-heading">
    <div class="container narrow">
      <h1>{}</h1>{}
    </div>
  </section>
""".format(esc(title), text_html)


def category_label(slug, categories):
    return categories.get(slug, {}).get("name", slug.replace("-", " ").title())


def category_tags(post, categories, prefix):
    tags = []
    for slug in post.get("categories", []):
        href = site_link("index.php/category/{}/index.html".format(slug), prefix)
        tags.append('<a class="tag" href="{}">{}</a>'.format(esc(href), esc(category_label(slug, categories))))
    return "".join(tags)


def post_card(post, categories, prefix):
    excerpt = post.get("excerpt") or strip_tags(post["content"])[:180]
    return """      <article class="post-card">
        <p class="meta">{date}</p>
        <h2><a href="{href}">{title}</a></h2>
        <p>{excerpt}</p>
        <div class="tags">{tags}</div>
      </article>
""".format(
        date=esc(format_date(post["date_obj"])),
        href=esc(site_link(post["path"], prefix)),
        title=esc(post["title"]),
        excerpt=esc(excerpt),
        tags=category_tags(post, categories, prefix),
    )


def render_post_list(posts, categories, prefix):
    return "\n".join(post_card(post, categories, prefix) for post in posts)


def render_home(site, posts, categories):
    home = site["home"]
    prefix = rel_prefix("index.html")
    link_cards = []
    for item in home.get("links", []):
        link_cards.append(
            """        <a class="link-card" href="{href}">
          <span>{label}</span>
          <p>{description}</p>
        </a>""".format(
                href=esc(site_link(item["href"], prefix)),
                label=esc(item["label"]),
                description=esc(item["description"]),
            )
        )
    latest = render_post_list(posts[:3], categories, prefix)
    subtitle = (home.get("hero_subtitle") or "").strip()
    subtitle_html = "\n      <p>{}</p>".format(esc(subtitle)) if subtitle else ""
    primary_button = home.get("primary_button") or {}
    button_html = ""
    if primary_button.get("label") and primary_button.get("href"):
        button_html = '\n      <a class="button" href="{}">{}</a>'.format(
            esc(site_link(primary_button["href"], prefix)),
            esc(primary_button["label"]),
        )
    body = """  <section class="hero" style="background-image: linear-gradient(rgba(15, 23, 42, .28), rgba(15, 23, 42, .12)), url('{image}')">
    <div class="container hero-content">
      <h1>{title}</h1>{subtitle}{button}
    </div>
  </section>
  <section class="section">
    <div class="container">
      <h2>{links_title}</h2>
      <div class="link-grid">
{link_cards}
      </div>
    </div>
  </section>
  <section class="section soft">
    <div class="container">
      <div class="section-head">
        <h2>Latest Posts</h2>
        <a href="{blog_href}">View all</a>
      </div>
      <div class="post-grid">
{latest}
      </div>
    </div>
  </section>
  <section class="callout">
    <div class="container">
      <h2>{callout}</h2>
    </div>
  </section>
""".format(
        image=esc(site_link(home["hero_image"], prefix)),
        title=esc(home["hero_title"]),
        subtitle=subtitle_html,
        button=button_html,
        links_title=esc(home["links_title"]),
        link_cards="\n".join(link_cards),
        latest=latest,
        blog_href=esc(site_link("index.php/blog/index.html", prefix)),
        callout=esc(home["callout"]),
    )
    return render_page(site, "index.html", site["title"], body, active="home", page_class="home-page")


def render_collection(site, relative_path, title, description, posts, categories, show_heading=True):
    prefix = rel_prefix(relative_path)
    body = page_heading(title, description) if show_heading else ""
    body += """  <section class="section">
    <div class="container">
      <div class="post-grid">
{}
      </div>
    </div>
  </section>
""".format(render_post_list(posts, categories, prefix))
    return render_page(site, relative_path, title, body, active="blog", description=description, page_class="archive-page")


def render_post(site, post, categories):
    prefix = rel_prefix(post["path"])
    content = rewrite_content_links(post["content"], prefix)
    body = """  <article class="article container narrow">
    <header class="article-header">
      <p class="meta">{date}</p>
      <h1>{title}</h1>
      <div class="tags">{tags}</div>
    </header>
    <div class="content-body">
{content}
    </div>
  </article>
""".format(
        date=esc(format_date(post["date_obj"])),
        title=esc(post["title"]),
        tags=category_tags(post, categories, prefix),
        content=content,
    )
    return render_page(site, post["path"], post["title"], body, active="blog", description=post.get("excerpt"))


def render_gallery(site, sections):
    relative_path = "index.php/gallery/index.html"
    prefix = rel_prefix(relative_path)
    nav = []
    section_html = []
    for section in sections:
        section_id = slugify(section["title"])
        nav.append('<a href="#{}">{}</a>'.format(esc(section_id), esc(section["title"])))
        images = []
        for image in section.get("images", []):
            src = site_link(image["src"], prefix)
            full_src = site_link(full_size_image(image["src"]), prefix)
            images.append(
                """          <a class="gallery-item" href="{full_src}">
            <img src="{src}" alt="{alt}" loading="lazy">
          </a>""".format(full_src=esc(full_src), src=esc(src), alt=esc(image.get("alt", "")))
            )
        grid = '\n        <div class="gallery-grid">\n{}\n        </div>'.format("\n".join(images)) if images else ""
        section_html.append(
            """      <section class="gallery-section" id="{id}">
        <h2>{title}</h2>{grid}
      </section>""".format(id=esc(section_id), title=esc(section["title"]), grid=grid)
        )
    body = """  <section class="section">
    <div class="container">
      <nav class="anchor-list" aria-label="Gallery sections">
        {nav}
      </nav>
{sections}
    </div>
  </section>
""".format(nav="\n        ".join(nav), sections="\n".join(section_html))
    return render_page(site, relative_path, "Gallery", body, active="gallery", page_class="gallery-page")


def render_profile(site):
    relative_path = "index.php/contact/index.html"
    prefix = rel_prefix(relative_path)
    content = rewrite_content_links(read_text(CONTENT / "profile.html"), prefix)
    body = """  <section class="section">
    <div class="container narrow content-body profile-body">
{}
    </div>
  </section>
""".format(content)
    return render_page(site, relative_path, "Profile", body, active="profile", page_class="profile-page")


def render_404(site):
    relative_path = "404_not_found/index.html"
    prefix = rel_prefix(relative_path)
    body = """  <section class="page-heading">
    <div class="container narrow">
      <h1>Page Not Found</h1>
      <p>The page may have moved or no longer exists.</p>
      <a class="button" href="{home}">Home</a>
    </div>
  </section>
""".format(home=esc(site_link("index.html", prefix)))
    return render_page(site, relative_path, "Page Not Found", body)


def render_feed(site, relative_path, title, posts):
    site_url = site.get("url", "https://illusionarydream.com").rstrip("/")
    items = []
    for post in posts:
        link = "{}/{}".format(site_url, post["path"])
        pub_date = post["date_obj"].strftime("%a, %d %b %Y 00:00:00 +0000")
        description = post.get("excerpt") or strip_tags(post["content"])[:220]
        items.append(
            """    <item>
      <title>{title}</title>
      <link>{link}</link>
      <guid>{link}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{description}</description>
    </item>""".format(
                title=esc(post["title"]),
                link=esc(link),
                pub_date=esc(pub_date),
                description=esc(description),
            )
        )
    feed = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{title}</title>
    <link>{link}</link>
    <description>{description}</description>
{items}
  </channel>
</rss>
""".format(
        title=esc(title),
        link=esc(site_url),
        description=esc(site["description"]),
        items="\n".join(items),
    )
    write_file(relative_path, feed)


def build():
    site = read_json(CONTENT / "site.json")
    categories_list = read_json(CONTENT / "categories.json")
    categories = {item["slug"]: item for item in categories_list}
    posts = load_posts()
    gallery = read_json(CONTENT / "gallery.json")

    write_file("index.html", render_home(site, posts, categories))
    write_file("index.php/blog/index.html", render_collection(site, "index.php/blog/index.html", "Blog", "Notes, tutorials, and research-related posts.", posts, categories, show_heading=False))
    write_file("index.php/gallery/index.html", render_gallery(site, gallery))
    write_file("index.php/contact/index.html", render_profile(site))
    write_file("404_not_found/index.html", render_404(site))

    for post in posts:
        write_file(post["path"], render_post(site, post, categories))

    by_category = defaultdict(list)
    for post in posts:
        for slug in post["categories"]:
            by_category[slug].append(post)
    for slug, category in categories.items():
        filtered = by_category.get(slug, [])
        path = "index.php/category/{}/index.html".format(slug)
        title = "Category: {}".format(category["name"])
        description = category.get("description") or "Posts filed under {}.".format(category["name"])
        write_file(path, render_collection(site, path, title, description, filtered, categories))
        render_feed(site, "index.php/category/{}/feed/index.html".format(slug), title, filtered)

    by_month = defaultdict(list)
    for post in posts:
        by_month[(post["date_obj"].year, post["date_obj"].month)].append(post)
    for (year, month), filtered in by_month.items():
        path = "index.php/{}/{:02d}/index.html".format(year, month)
        title = "Archive: {}".format(month_title(year, month))
        write_file(path, render_collection(site, path, title, "Posts from {}.".format(month_title(year, month)), filtered, categories))

    write_file(
        "index.php/author/zg5/index.html",
        render_collection(site, "index.php/author/zg5/index.html", "Posts by {}".format(site["author"]), "All posts by {}.".format(site["author"]), posts, categories),
    )
    render_feed(site, "index.php/feed/index.html", "{} Feed".format(site["title"]), posts)
    render_feed(site, "index.php/author/zg5/feed/index.html", "Posts by {}".format(site["author"]), posts)
    render_feed(site, "index.php/comments/feed/index.html", "{} Comments Feed".format(site["title"]), [])
    for post in posts:
        comments_path = post["path"].replace("index.html", "feed/index.html")
        render_feed(site, comments_path, "Comments on: {}".format(post["title"]), [])


if __name__ == "__main__":
    build()
