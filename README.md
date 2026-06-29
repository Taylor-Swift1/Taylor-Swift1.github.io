# Zhuangzhuang Gu static site

This site is generated from editable source files in `src/content`.

## Edit content

- Site title, navigation, homepage text: `src/content/site.json`
- Blog posts: one file per post in `src/content/posts/`
- Gallery sections and image paths: `src/content/gallery.json`
- Profile page: `src/content/profile.html`

Images can stay in `wp-content/uploads/`. Use paths like `wp-content/uploads/2024/04/photo.jpeg` in content files.

## Rebuild

Run this after editing content:

```bash
python3 scripts/build.py
```

The build writes the public HTML files, including `index.html`, blog pages, gallery, profile, category pages, archive pages, and RSS feeds.

## Preview

Open `index.html` in a browser, or run:

```bash
python3 -m http.server 8000
```

Then visit `http://localhost:8000`.
