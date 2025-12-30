/**
 * Carbon Sequestration Calculator - Client-side JavaScript
 * Handles scenario buttons, real-time slider updates, and form interactions
 */

document.addEventListener("DOMContentLoaded", function () {
  // Initialize all interactive elements
  initSliders();
  initScenarioButtons();
  initFormValidation();
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

  // Risk factor slider
  const riskSlider = document.getElementById("risk_factor");
  const riskValue = document.getElementById("riskFactorValue");

  if (riskSlider && riskValue) {
    riskSlider.addEventListener("input", function () {
      riskValue.textContent = this.value + "%";
    });
  }
}

/**
 * Initialize scenario preset buttons
 */
function initScenarioButtons() {
  const buttons = document.querySelectorAll(".scenario-btn");
  const scenarioInput = document.getElementById("scenarioInput");
  const forestSlider = document.getElementById("forest_percent");
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
      const startYear = parseInt(document.getElementById("start_year").value);
      const targetYear = parseInt(document.getElementById("target_year").value);

      if (targetYear <= startYear) {
        e.preventDefault();
        alert("Target year must be greater than start year");
        return false;
      }

      // Validate emission targets
      const emissions2030 = parseFloat(
        document.getElementById("emissions_2030").value
      );
      const target2050 = parseFloat(
        document.getElementById("target_2050").value
      );

      if (target2050 > emissions2030) {
        if (
          !confirm(
            "Target emissions are higher than baseline. This means no reduction is needed. Continue?"
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
