/**
 * Carbon Sequestration Calculator - Client-side JavaScript
 * Handles scenario buttons, real-time slider updates, and form interactions
 */

document.addEventListener("DOMContentLoaded", function () {
  // Initialize all interactive elements
  initSliders();
  initScenarioButtons();
  initFormValidation();
  initPdfGeneration();
});

/**
 * Initialize slider inputs with real-time value display
 */
function initSliders() {
  // Sequestration percentage slider
  const seqSlider = document.getElementById("sequestration_percent");
  const seqValue = document.getElementById("seqPercentValue");

  if (seqSlider && seqValue) {
    seqSlider.addEventListener("input", function () {
      seqValue.textContent = this.value + "%";
    });
  }

  // Forest/Coastal split slider
  const forestSlider = document.getElementById("forest_percent");
  const forestValue = document.getElementById("forestPercentValue");

  if (forestSlider && forestValue) {
    forestSlider.addEventListener("input", function () {
      const forest = parseInt(this.value);
      const coastal = 100 - forest;
      forestValue.textContent = forest + "% / " + coastal + "%";
    });
  }

  // Degradation rate slider
  const degradationSlider = document.getElementById("degradation_rate");
  const degradationValue = document.getElementById("degradationRateValue");

  if (degradationSlider && degradationValue) {
    degradationSlider.addEventListener("input", function () {
      degradationValue.textContent = this.value + "%";
    });
  }
}

/**
 * Initialize scenario preset buttons
 */
function initScenarioButtons() {
  const buttons = document.querySelectorAll(".scenario-btn");
  const scenarioInput = document.getElementById("scenarioInput");
  const forestSlider = document.getElementById("new_planting_forest_percent");
  const forestValue = document.getElementById("forestPercentValue");
  const belowGroundCheckbox = document.getElementById("include_below_ground");

  buttons.forEach((button) => {
    button.addEventListener("click", function () {
      // Remove active class from all buttons
      buttons.forEach((btn) => btn.classList.remove("active"));

      // Add active class to clicked button
      this.classList.add("active");

      // Get scenario data
      const scenario = this.dataset.scenario;
      const forestPercent = parseFloat(this.dataset.forest);
      const includeBelowGround = this.dataset.belowGround === "true";

      // Update hidden input
      if (scenarioInput) {
        scenarioInput.value = scenario;
      }

      // Update forest slider
      if (forestSlider) {
        forestSlider.value = forestPercent;
        if (forestValue) {
          const coastal = 100 - forestPercent;
          forestValue.textContent = forestPercent + "% / " + coastal + "%";
        }
      }

      // Update below-ground checkbox
      if (belowGroundCheckbox) {
        belowGroundCheckbox.checked = includeBelowGround;
      }

      // Auto-submit form for instant results
      const form = document.getElementById("calculatorForm");
      if (form) {
        form.submit();
      }
    });
  });
}

/**
 * Initialize form validation
 */
function initFormValidation() {
  const form = document.getElementById("calculatorForm");

  if (form) {
    form.addEventListener("submit", function (e) {
      // Validate year range
      const initialYear = parseInt(
        document.getElementById("initial_year").value
      );
      const targetYear = parseInt(document.getElementById("target_year").value);

      if (targetYear <= initialYear) {
        e.preventDefault();
        alert("Target year must be greater than initial year");
        return false;
      }

      // Validate emission targets
      const emissionsInitial = parseFloat(
        document.getElementById("emissions_initial").value
      );
      const target2050 = parseFloat(
        document.getElementById("target_2050").value
      );

      if (target2050 > emissionsInitial) {
        if (
          !confirm(
            "Target emissions are higher than initial emissions. This means no reduction is needed. Continue?"
          )
        ) {
          e.preventDefault();
          return false;
        }
      }

      return true;
    });
  }
}

/**
 * Format number with thousands separator
 * @param {number} num - Number to format
 * @returns {string} Formatted number string
 */
function formatNumber(num) {
  return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

/**
 * Update result display without page reload (for future AJAX implementation)
 * @param {object} result - Calculation result from API
 */
function updateResults(result) {
  // This function can be used for future AJAX-based updates
  // Currently, the form submits traditionally for simplicity
  console.log("Results:", result);
}

/**
 * Initialize PDF generation button
 */
function initPdfGeneration() {
  const btn = document.getElementById("generatePdfBtn");
  if (btn) {
    btn.addEventListener("click", generatePdf);
  }
}

/**
 * Generates a professional PDF report of the calculation results and charts
 */
async function generatePdf() {
  const btn = document.getElementById("generatePdfBtn");
  const originalText = btn.innerHTML;
  btn.innerHTML = "⏳ Generating Report...";
  btn.disabled = true;

  try {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF("p", "mm", "a4");
    const pageWidth = doc.internal.pageSize.getWidth();
    const margin = 15;
    let yPos = 20;

    // --- PAGE 1: HEADER & SUMMARY ---
    doc.setFont("helvetica", "bold");
    doc.setFontSize(22);
    doc.setTextColor(0, 0, 0); // Black for header
    doc.text(
      "Technical Report: Carbon Sequestration Potential",
      pageWidth / 2,
      yPos,
      { align: "center" }
    );
    yPos += 10;

    doc.setFontSize(14);
    doc.setTextColor(0, 0, 0); // Black for subtitle
    doc.text("Indonesia 2050 Net Zero Pathway Analysis", pageWidth / 2, yPos, {
      align: "center",
    });
    yPos += 15;

    // Report Metadata
    doc.setFontSize(10);
    doc.setFont("helvetica", "normal");
    const today = new Date().toLocaleDateString("en-GB", {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
    doc.text(`Generated on: ${today}`, margin, yPos);
    doc.text("Methodology: IPCC 2006 AFOLU Tier 1", pageWidth - margin, yPos, {
      align: "right",
    });
    yPos += 10;

    doc.setDrawColor(229, 231, 235);
    doc.line(margin, yPos, pageWidth - margin, yPos);
    yPos += 15;

    // Calculation Parameters
    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.setTextColor(0, 0, 0); // Black for sections
    doc.text("1. Input Parameters", margin, yPos);
    yPos += 8;

    doc.setFont("helvetica", "normal");
    doc.setFontSize(10);
    const params = [
      [
        "Initial Emissions",
        document.getElementById("emissions_initial").value + " MtCO2e",
      ],
      [
        "Peak Emissions",
        document.getElementById("emissions_peak").value + " MtCO2e",
      ],
      [
        "Target Emissions 2050",
        document.getElementById("target_2050").value + " MtCO2e",
      ],
      [
        "Sequestration Target Allocation",
        document.getElementById("sequestration_percent").value + "%",
      ],
      [
        "New Planting Allocation",
        document.getElementById("new_planting_forest_percent").value +
          "% Forest",
      ],
      [
        "Forest Degradation Rate",
        document.getElementById("degradation_rate").value + "% / year",
      ],
      [
        "Include Below-ground Biomass",
        document.getElementById("include_below_ground").checked
          ? "Yes (+37%)"
          : "No",
      ],
    ];

    params.forEach(([label, value]) => {
      doc.text(label + ":", margin + 5, yPos);
      doc.text(value, margin + 70, yPos);
      yPos += 6;
    });
    yPos += 10;

    // Key Results Summary from cards
    doc.setFont("helvetica", "bold");
    doc.setFontSize(14);
    doc.text("2. Key Results Summary", margin, yPos);
    yPos += 8;

    const resultItems = document.querySelectorAll(".result-item");
    doc.setFontSize(11);

    resultItems.forEach((item, index) => {
      if (index > 5) return; // Limit to main summary metrics
      const value = item.querySelector(".value").innerText;
      const label = item.querySelector(".label").innerText;
      doc.setFont("helvetica", "bold");
      doc.text(value, margin + 5, yPos);
      doc.setFont("helvetica", "normal");
      doc.text("  " + label, margin + 45, yPos);
      yPos += 8;
    });

    // Feasibility status badge
    const badge = document.querySelector(".card-header .badge");
    if (badge) {
      doc.setDrawColor(
        badge.classList.contains("badge-success") ? 16 : 239,
        185,
        129
      );
      doc.setFillColor(243, 244, 246);
      doc.rect(margin, yPos, pageWidth - 2 * margin, 12, "F");
      doc.setFont("helvetica", "bold");
      doc.setTextColor(0, 0, 0); // Black for status text
      doc.text(
        "Scientific Feasibility Status: " + badge.innerText,
        pageWidth / 2,
        yPos + 8,
        { align: "center" }
      );
      yPos += 20;
    }

    // --- PAGES 2-6: CHARTS (LANDSCAPE, ONE PER PAGE) ---
    const charts = [
      {
        id: "existingForestRateChart",
        chartKey: "existingRate",
        title: "Existing Forest Carbon Reduction",
      },
      {
        id: "grossEmissionsChart",
        chartKey: "grossEmissions",
        title: "Gross Emission Trajectory",
      },
      {
        id: "balanceChart",
        chartKey: "balance",
        title: "Carbon Balance",
      },
      {
        id: "annualPlantingChart",
        chartKey: "annualPlanting",
        title: "Annual New Planting Area",
      },
      {
        id: "cumulativeAreaChart",
        chartKey: "cumulativeArea",
        title: "Cumulative Planted Area",
      },
      {
        id: "netZeroBalanceChart",
        chartKey: "netZeroBalance",
        title: "National Net Carbon Balance",
      },
    ];

    for (let i = 0; i < charts.length; i++) {
      // Add a new page for each chart, in landscape
      doc.addPage("a4", "l");
      const lWidth = doc.internal.pageSize.getWidth();
      const lHeight = doc.internal.pageSize.getHeight();
      const lMargin = 20;

      const chartInfo = charts[i];
      const canvas = document.getElementById(chartInfo.id);
      const chartInstance = window.dashboardCharts
        ? window.dashboardCharts[chartInfo.chartKey]
        : null;

      if (canvas && chartInstance) {
        // 1. Temporarily switch chart to "printer-friendly" mode (black text)
        const originalOptions = JSON.parse(
          JSON.stringify(chartInstance.options)
        );

        const setBlack = (obj) => {
          if (obj && obj.color) obj.color = "#000000";
          if (obj && obj.ticks && obj.ticks.color) obj.ticks.color = "#000000";
          if (obj && obj.title && obj.title.color) obj.title.color = "#000000";
          if (obj && obj.grid && obj.grid.color)
            obj.grid.color = "rgba(0,0,0,0.1)";
        };

        setBlack(chartInstance.options.plugins.legend.labels);
        setBlack(chartInstance.options.plugins.title);
        setBlack(chartInstance.options.scales.x);
        setBlack(chartInstance.options.scales.y);
        if (chartInstance.options.scales.y.title)
          setBlack(chartInstance.options.scales.y.title);

        chartInstance.update("none");

        // 2. Capture and draw
        doc.setFont("helvetica", "bold");
        doc.setFontSize(16);
        doc.setTextColor(0, 0, 0); // Black for titles
        doc.text(`${i + 3}. ${chartInfo.title}`, lMargin, 20);

        const tempCanvas = document.createElement("canvas");
        tempCanvas.width = canvas.width;
        tempCanvas.height = canvas.height;
        const ctx = tempCanvas.getContext("2d");

        ctx.fillStyle = "#FFFFFF";
        ctx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
        ctx.drawImage(canvas, 0, 0);

        const imgData = tempCanvas.toDataURL("image/png", 1.0);

        const imgWidth = lWidth - 2 * lMargin;
        const imgHeight = (canvas.height * imgWidth) / canvas.width;
        const finalHeight = Math.min(imgHeight, lHeight - 40);
        const finalWidth = (canvas.width * finalHeight) / canvas.height;

        doc.addImage(
          imgData,
          "PNG",
          (lWidth - finalWidth) / 2,
          30,
          finalWidth,
          finalHeight
        );

        // 3. Restore dashboard theme
        chartInstance.options = originalOptions;
        chartInstance.update("none");
      }
    }

    // Footer on all pages
    const pageCount = doc.internal.getNumberOfPages();
    for (let i = 1; i <= pageCount; i++) {
      doc.setPage(i);
      doc.setFont("helvetica", "normal");
      doc.setFontSize(8);
      doc.setTextColor(0, 0, 0); // Black for footer
      doc.text(
        `Page ${i} of ${pageCount} | Indonesia Carbon Sequestration Calculator | https://sequestration-calculator.ansyar-world.top | IPCC Tier 1 Methodology`,
        pageWidth / 2,
        doc.internal.pageSize.getHeight() - 10,
        { align: "center" }
      );
    }

    doc.save("Indonesia_Sequestration_Technical_Report.pdf");
  } catch (error) {
    console.error("PDF Generation Error:", error);
    alert("Error generating PDF. Please check console for details.");
  } finally {
    btn.innerHTML = originalText;
    btn.disabled = false;
  }
}
