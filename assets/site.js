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
  const highlightsGroup = "__highlights";
  const groupButtons = Array.from(galleryBrowser.querySelectorAll("[data-gallery-group]"));
  const destinations = galleryBrowser.querySelector("[data-gallery-destinations]");
  const grid = galleryBrowser.querySelector("[data-gallery-grid]");
  const title = galleryBrowser.querySelector("[data-gallery-title]");
  const count = galleryBrowser.querySelector("[data-gallery-count]");
  let sections = [];
  let activeIndex = 0;

  try {
    sections = JSON.parse(galleryDataElement.textContent);
  } catch (error) {
    sections = [];
  }

  const photoCount = (images) => {
    const total = images.length;
    return `${total} photo${total === 1 ? "" : "s"}`;
  };

  const sectionInitials = (section) => {
    const words = section.title.match(/[A-Za-z0-9]+/g) || [];
    return words.slice(0, 2).map((word) => word[0]).join("").toUpperCase() || "G";
  };

  const sectionGroups = (section) => {
    if (Array.isArray(section.groups) && section.groups.length) {
      return section.groups;
    }

    return [section.group || "Other"];
  };

  const setActiveGroup = (group) => {
    groupButtons.forEach((button) => {
      const isActive = button.dataset.galleryGroup === group;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });
  };

  const setActiveDestination = (index) => {
    if (!destinations) {
      return;
    }

    destinations.querySelectorAll("[data-gallery-section]").forEach((button) => {
      const isActive = Number(button.dataset.gallerySection) === index;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-pressed", String(isActive));
    });
  };

  const highlightIndexes = () => {
    const selected = sections
      .map((section, index) => ({ section, index }))
      .filter((item) => item.section.highlight)
      .sort((a, b) => {
        const aOrder = Number.isFinite(Number(a.section.highlightOrder))
          ? Number(a.section.highlightOrder)
          : a.index;
        const bOrder = Number.isFinite(Number(b.section.highlightOrder))
          ? Number(b.section.highlightOrder)
          : b.index;

        return aOrder - bOrder || a.index - b.index;
      })
      .map((item) => item.index);

    if (selected.length) {
      return selected;
    }

    const groups = new Set();
    const fallback = [];

    sections.forEach((section, index) => {
      const group = sectionGroups(section)[0];

      if (groups.has(group)) {
        return;
      }

      groups.add(group);
      fallback.push(index);
    });

    return fallback;
  };

  const createDestinationCard = (section, index) => {
    const button = document.createElement("button");
    const content = document.createElement("span");
    const titleText = document.createElement("span");
    const countText = document.createElement("span");
    const images = section.images || [];

    button.className = "gallery-destination";
    button.type = "button";
    button.setAttribute("aria-pressed", "false");
    button.dataset.gallerySection = String(index);

    if (section.coverSrc) {
      const image = document.createElement("img");
      image.src = section.coverSrc;
      image.alt = "";
      image.loading = "lazy";
      image.decoding = "async";
      button.appendChild(image);
    } else {
      const initials = document.createElement("span");
      initials.className = "gallery-destination-initials";
      initials.textContent = sectionInitials(section);
      button.classList.add("is-empty");
      button.appendChild(initials);
    }

    content.className = "gallery-destination-content";
    titleText.className = "gallery-destination-title";
    titleText.textContent = section.title;
    countText.className = "gallery-destination-count";
    countText.textContent = photoCount(images);

    content.appendChild(titleText);
    content.appendChild(countText);
    button.appendChild(content);

    return button;
  };

  const renderDestinations = (group, selectedIndex) => {
    if (!destinations) {
      return;
    }

    const fragment = document.createDocumentFragment();
    const indexes = group === highlightsGroup ? highlightIndexes() : null;

    sections.forEach((section, index) => {
      if (indexes ? !indexes.includes(index) : !sectionGroups(section).includes(group)) {
        return;
      }

      fragment.appendChild(createDestinationCard(section, index));
    });

    destinations.replaceChildren(fragment);
    setActiveDestination(selectedIndex);
  };

  const renderSection = (index, options = {}) => {
    const section = sections[index];

    if (!section || !grid) {
      return;
    }

    const syncGroup = options.syncGroup !== false;
    const images = section.images || [];
    const fragment = document.createDocumentFragment();
    activeIndex = index;

    if (images.length) {
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
    } else {
      const empty = document.createElement("p");
      empty.className = "gallery-empty";
      empty.textContent = "Photos coming soon.";
      fragment.appendChild(empty);
    }

    if (title) {
      title.textContent = section.title;
    }

    if (count) {
      count.textContent = photoCount(images);
    }

    grid.replaceChildren(fragment);
    setActiveDestination(index);

    if (syncGroup) {
      const group = sectionGroups(section)[0];
      setActiveGroup(group);
      renderDestinations(group, index);
    }
  };

  galleryBrowser.addEventListener("click", (event) => {
    if (!event.target.closest) {
      return;
    }

    const groupButton = event.target.closest("[data-gallery-group]");
    const destinationButton = event.target.closest("[data-gallery-section]");

    if (groupButton && galleryBrowser.contains(groupButton)) {
      const group = groupButton.dataset.galleryGroup;
      const indexes = group === highlightsGroup
        ? highlightIndexes()
        : sections
            .map((section, index) => ({ section, index }))
            .filter((item) => sectionGroups(item.section).includes(group))
            .map((item) => item.index);
      const firstIndex = indexes.includes(activeIndex) ? activeIndex : indexes[0];

      if (typeof firstIndex === "number") {
        setActiveGroup(group);
        renderDestinations(group, firstIndex);
        renderSection(firstIndex, { syncGroup: false });
      }

      return;
    }

    if (destinationButton && galleryBrowser.contains(destinationButton)) {
      renderSection(Number(destinationButton.dataset.gallerySection), { syncGroup: false });
    }
  });

  if (sections[0]) {
    setActiveGroup(highlightsGroup);
    renderDestinations(highlightsGroup, activeIndex);
  }
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
