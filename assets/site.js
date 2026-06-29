const toggle = document.querySelector(".nav-toggle");
const nav = document.querySelector(".site-nav");

if (toggle && nav) {
  toggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
}

const galleryDataElement = document.getElementById("gallery-data");
const galleryBrowser = document.querySelector("[data-gallery-browser]");

if (galleryDataElement && galleryBrowser) {
  const tabs = Array.from(galleryBrowser.querySelectorAll("[data-gallery-tab]"));
  const grid = galleryBrowser.querySelector("[data-gallery-grid]");
  const title = galleryBrowser.querySelector("[data-gallery-title]");
  const count = galleryBrowser.querySelector("[data-gallery-count]");
  let sections = [];

  try {
    sections = JSON.parse(galleryDataElement.textContent);
  } catch (error) {
    sections = [];
  }

  const setActiveTab = (activeIndex) => {
    tabs.forEach((tab, index) => {
      const isActive = index === activeIndex;
      tab.classList.toggle("is-active", isActive);
      tab.setAttribute("aria-selected", String(isActive));
      tab.tabIndex = isActive ? 0 : -1;
    });
  };

  const renderSection = (index) => {
    const section = sections[index];

    if (!section || !grid) {
      return;
    }

    const images = section.images || [];
    const fragment = document.createDocumentFragment();

    images.forEach((image) => {
      const link = document.createElement("a");
      const img = document.createElement("img");

      link.className = "gallery-item";
      link.href = image.fullSrc;
      img.src = image.src;
      img.alt = image.alt || "";
      img.loading = "lazy";
      img.decoding = "async";
      link.appendChild(img);
      fragment.appendChild(link);
    });

    if (title) {
      title.textContent = section.title;
    }

    if (count) {
      count.textContent = `${images.length} photo${images.length === 1 ? "" : "s"}`;
    }

    grid.replaceChildren(fragment);
    setActiveTab(index);
  };

  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => {
      renderSection(index);
    });

    tab.addEventListener("keydown", (event) => {
      const currentIndex = tabs.indexOf(tab);
      let nextIndex = currentIndex;

      if (event.key === "ArrowRight") {
        nextIndex = (currentIndex + 1) % tabs.length;
      } else if (event.key === "ArrowLeft") {
        nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
      } else if (event.key === "Home") {
        nextIndex = 0;
      } else if (event.key === "End") {
        nextIndex = tabs.length - 1;
      } else {
        return;
      }

      event.preventDefault();
      tabs[nextIndex].focus();
      renderSection(nextIndex);
    });
  });
}

if (document.querySelector(".gallery-item, [data-gallery-browser]")) {
  const lightbox = document.createElement("div");
  const lightboxImage = document.createElement("img");
  const closeButton = document.createElement("button");
  let lastFocusedElement = null;

  lightbox.className = "lightbox";
  lightbox.hidden = true;
  lightbox.setAttribute("role", "dialog");
  lightbox.setAttribute("aria-modal", "true");
  lightbox.setAttribute("aria-label", "Expanded gallery image");

  closeButton.className = "lightbox-close";
  closeButton.type = "button";
  closeButton.textContent = "X";
  closeButton.setAttribute("aria-label", "Close image");

  lightbox.appendChild(closeButton);
  lightbox.appendChild(lightboxImage);
  document.body.appendChild(lightbox);

  const closeLightbox = () => {
    lightbox.hidden = true;
    lightboxImage.removeAttribute("src");
    document.body.classList.remove("lightbox-open");

    if (lastFocusedElement) {
      lastFocusedElement.focus();
    }
  };

  const openLightbox = (item) => {
    const thumbnail = item.querySelector("img");

    lastFocusedElement = document.activeElement;
    lightboxImage.src = item.href;
    lightboxImage.alt = thumbnail ? thumbnail.alt : "";
    lightbox.hidden = false;
    document.body.classList.add("lightbox-open");
    closeButton.focus();
  };

  document.addEventListener("click", (event) => {
    const item = event.target.closest ? event.target.closest(".gallery-item") : null;

    if (!item) {
      return;
    }

    event.preventDefault();
    openLightbox(item);
  });

  lightbox.addEventListener("click", (event) => {
    if (
      event.target === lightbox ||
      event.target === lightboxImage ||
      event.target === closeButton
    ) {
      closeLightbox();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (!lightbox.hidden && event.key === "Escape") {
      closeLightbox();
    }
  });
}
