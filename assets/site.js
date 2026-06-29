const toggle = document.querySelector(".nav-toggle");
const nav = document.querySelector(".site-nav");

if (toggle && nav) {
  toggle.addEventListener("click", () => {
    const isOpen = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });
}

const galleryItems = document.querySelectorAll(".gallery-item");

if (galleryItems.length) {
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

  galleryItems.forEach((item) => {
    item.addEventListener("click", (event) => {
      event.preventDefault();
      openLightbox(item);
    });
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
