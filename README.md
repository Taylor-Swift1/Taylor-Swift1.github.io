# Zhuangzhuang Gu static site

This site is generated from editable source files in `src/content`.

## Edit content

- Site title, navigation, homepage text: `src/content/site.json`
- Blog posts: one file per post in `src/content/posts/`
- Gallery sections, groups, and optional manual image paths: `src/content/gallery.json`
- Profile page: `src/content/profile.html`

Gallery photos live in `assets/photos/<destination>/`, grouped by trip/place. The build automatically scans each trip folder and adds image files to that gallery section. Empty planned-trip folders contain a `.gitkeep` placeholder so GitHub keeps the folder; remove it after adding real photos. Site and blog support images live in `assets/images/`. Use those relative paths in content files, for example `assets/photos/greece/photo.jpeg`.

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
