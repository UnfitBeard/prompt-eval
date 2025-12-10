// Abstract data based on your Drive files
const abstractData = {
  invention: {
    english:
      "This presentation explores the NgaoSafe innovation in the field of community safety and technology. NgaoSafe is a community-based security solution that leverages mobile technology and local networks to enhance safety in urban and rural areas. The system allows community members to report incidents, request assistance, and receive safety alerts in real-time.",
    kiswahili:
      "Uwasilishaji huu unachunguza uvumbuzi wa NgaoSafe katika nyanja ya usalama wa jamii na teknolojia. NgaoSafe ni suluhisho la usalama linalotokana na jamii linalotumia teknolojia ya rununu na mitandao ya ndani kuboresha usalama katika maeneo ya mijini na vijijini.",
    kikuyu:
      "Racio iji ikoragwo na innovation ya NgaoSafe thutha wa thome na teknologia. NgaoSafe ni njira ya gwikira thome wendo wa guthoma teknologia ya thimu na network cia handu.",
    docLink:
      "https://docs.google.com/document/d/1S6HrsTF_NYIrdLduVFKA44CnvB7-EJ4y_BAI0_RnkUM/edit",
  },
  culture: {
    english:
      "This presentation examines the cultural significance of traditional gender roles in African societies and the importance of gender awareness in contemporary contexts. Focusing on specific cultural practices from East African communities.",
    kiswahili:
      "Uwasilishaji huu unachunguza umuhimu wa kitamaduni wa jinsi majukumu ya kijinsia katika jamii za Kiafrika na umuhimu wa ufahamu wa kijinsia katika miktadha ya kisasa.",
    kikuyu:
      "Racio iji ikoragwo na uumithia wa kitamaduni wa role cia gender katika society cia Africa na uumithia wa kumenya gender katika handu.",
    docLink:
      "https://docs.google.com/document/d/1nAzq_4ddFU2wx_mGdpauyQaMIGfdRvXwX3mhRw-eAtQ/edit",
  },
  society: {
    english:
      "This presentation addresses the challenge of digital inequality in African societies, where rapid technological advancement has created a significant divide between those with access to digital resources and those without.",
    kiswahili:
      "Uwasilishaji huu unashughulikia changamoto ya ukosefu wa usawa wa kidijitali katika jamii za Kiafrika, ambapo maendeleo ya haraka ya kiteknolojia yameunda mgawanyiko mkubwa.",
    kikuyu:
      "Racio iji ikoragwo na gwikira digital inequality katika society cia Africa, thutha wa guthoma teknologia na guthoma digital resources.",
    docLink:
      "https://docs.google.com/document/d/1R2NDsqCV4IgfK9uWPo76wZFB7_2N42dHUQn_GjlgJKo/edit",
  },
};

// DOM Elements
const modal = document.getElementById("abstractModal");
const closeModalBtn = document.querySelector(".close-modal");
const abstractBtns = document.querySelectorAll(".abstract-btn");
const languageTabs = document.querySelectorAll(".language-tab");
const currentYearSpan = document.getElementById("currentYear");

// Set current year in footer
currentYearSpan.textContent = new Date().getFullYear();

// Navigation highlighting
document.querySelectorAll("nav a").forEach((link) => {
  link.addEventListener("click", function (e) {
    // Update active nav link
    document
      .querySelectorAll("nav a")
      .forEach((a) => a.classList.remove("active"));
    this.classList.add("active");

    // Smooth scroll to section
    const targetId = this.getAttribute("href");
    const targetSection = document.querySelector(targetId);
    if (targetSection) {
      e.preventDefault();
      window.scrollTo({
        top: targetSection.offsetTop - 80,
        behavior: "smooth",
      });
    }
  });
});

// Open abstract modal
abstractBtns.forEach((btn) => {
  btn.addEventListener("click", function () {
    const abstractType = this.getAttribute("data-abstract");
    updateModalContent(abstractType);
    modal.style.display = "flex";
  });
});

// Close modal when X is clicked
closeModalBtn.addEventListener("click", () => {
  modal.style.display = "none";
});

// Close modal when clicking outside content
window.addEventListener("click", (e) => {
  if (e.target === modal) {
    modal.style.display = "none";
  }
});

// Switch between language tabs
languageTabs.forEach((tab) => {
  tab.addEventListener("click", function () {
    const lang = this.getAttribute("data-lang");

    // Update active tab
    languageTabs.forEach((t) => t.classList.remove("active"));
    this.classList.add("active");

    // Show corresponding content
    document.querySelectorAll(".abstract-content").forEach((content) => {
      content.classList.remove("active");
    });
    document
      .getElementById(`abstract${capitalizeFirstLetter(lang)}`)
      .classList.add("active");
  });
});

// Update modal content based on abstract type
function updateModalContent(abstractType) {
  const data = abstractData[abstractType];
  if (!data) return;

  // Update modal title
  let title = "";
  switch (abstractType) {
    case "invention":
      title = "Abstract: NgaoSafe Innovation Presentation";
      break;
    case "culture":
      title = "Abstract: African Culture & Gender Awareness";
      break;
    case "society":
      title = "Abstract: Modern Society Challenges";
      break;
  }
  document.getElementById("modalTitle").textContent = title;

  // Update abstract content for each language
  document.getElementById("englishContent").textContent = data.english;
  document.getElementById("kiswahiliContent").textContent = data.kiswahili;
  document.getElementById("kikuyuContent").textContent = data.kikuyu;

  // Update abstract document link
  const abstractDocLink = document.getElementById("abstract-doc-link");
  if (data.docLink && data.docLink !== "#") {
    abstractDocLink.href = data.docLink;
    abstractDocLink.style.display = "block";
  } else {
    abstractDocLink.style.display = "none";
  }

  // Reset to English tab
  languageTabs.forEach((t) => t.classList.remove("active"));
  document.querySelector('[data-lang="english"]').classList.add("active");

  document.querySelectorAll(".abstract-content").forEach((content) => {
    content.classList.remove("active");
  });
  document.getElementById("abstractEnglish").classList.add("active");
}

// Helper function to capitalize first letter
function capitalizeFirstLetter(string) {
  return string.charAt(0).toUpperCase() + string.slice(1);
}

// Initialize with first abstract
updateModalContent("invention");
